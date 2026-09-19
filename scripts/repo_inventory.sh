#!/usr/bin/env bash
# Repo inventory report: file tree, hash manifest, targeted file checks,
# folder-structure match, test-file state, and branch/PR summary.
# Read-only: does not modify the working tree, stage, commit, or checkout branches.
#
# Usage: ./scripts/repo_inventory.sh > repo_inventory.out 2>&1
#        INCLUDE_EVIDENCE_DIRS=1 ./scripts/repo_inventory.sh   (also walk evidence dirs)
# Requires: git, sha256sum, python3. jq and curl are optional (used only for
# the "Open PRs" lookup in section 6; that check is skipped if either is missing).
#
# By default, directories named `validation_runs` are excluded from the file
# find in sections 2 and 5. Per CLAUDE.md, these hold generated CRAM evidence
# artifacts (hundreds of thousands of small files in this repo) rather than
# source or docs, and are explicitly "do not stage for commit" / outside the
# governance scan tree. Set INCLUDE_EVIDENCE_DIRS=1 to walk them anyway.

set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

evidence_prune=()
if [[ "${INCLUDE_EVIDENCE_DIRS:-0}" != "1" ]]; then
  evidence_prune=(-name validation_runs -prune -o)
fi

for cmd in git sha256sum python3; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "MISSING_REQUIREMENT: $cmd not found" >&2
    exit 2
  fi
done

origin_url=$(git remote get-url origin 2>/dev/null || echo "")
owner_repo=""
if [[ -n "$origin_url" ]]; then
  if [[ "$origin_url" =~ ^git@github\.com:([^/]+)/([^/.]+)(\.git)?$ ]]; then
    owner_repo="${BASH_REMATCH[1]}/${BASH_REMATCH[2]}"
  elif [[ "$origin_url" =~ ^https?://github\.com/([^/]+)/([^/.]+)(\.git)? ]]; then
    owner_repo="${BASH_REMATCH[1]}/${BASH_REMATCH[2]}"
  fi
fi

default_branch="UNKNOWN"
if git remote show origin >/dev/null 2>&1; then
  default_branch=$(git remote show origin | awk -F': ' '/HEAD branch/ {print $2; exit}' || true)
  [[ -z "$default_branch" ]] && default_branch="UNKNOWN"
elif git rev-parse --abbrev-ref HEAD >/dev/null 2>&1; then
  default_branch=$(git rev-parse --abbrev-ref HEAD)
fi

declare -A seen
unique_branches=()
while IFS= read -r b; do
  nb="${b#origin/}"
  if [[ -z "${seen[$nb]:-}" ]]; then
    seen[$nb]=1
    unique_branches+=("$nb")
  fi
done < <(git for-each-ref --format='%(refname:short)' refs/heads refs/remotes 2>/dev/null || true)

# ---------------------------------------------------------------------------
echo "1. FULL FILE TREE"
echo "Default branch: $default_branch"
echo "All branches (deduped):"
for b in "${unique_branches[@]}"; do echo " - $b"; done
echo

for b in "${unique_branches[@]}"; do
  echo "=== BRANCH: $b ==="
  if git rev-parse --verify "$b" >/dev/null 2>&1; then
    echo "Top-level entries:"
    git ls-tree --name-only "$b" | sed 's/^/  /'
    echo "Duplicate-like top-level folder heuristics (suffixes _old, -old, _copy, -copy, bak, backup):"
    dupe_found=0
    while IFS= read -r d; do
      if [[ "$d" =~ (_old$|-old$|_copy$|-copy$|bak$|backup$) ]]; then
        echo "  - $d"
        dupe_found=1
      fi
    done < <(git ls-tree -d --name-only "$b" 2>/dev/null || true)
    if [[ $dupe_found -eq 0 ]]; then
      echo "  (none)"
    fi
  else
    echo "  UNKNOWN (branch not found locally)"
  fi
  echo
done

# ---------------------------------------------------------------------------
echo "2. HASH MANIFEST (working tree: *.py, *.md, *.txt, *.json)"
if [[ "${INCLUDE_EVIDENCE_DIRS:-0}" != "1" ]]; then
  echo "(validation_runs/ directories excluded — set INCLUDE_EVIDENCE_DIRS=1 to include)"
fi
mapfile -t files < <(find . -path './.git' -prune -o "${evidence_prune[@]}" -type f \
  \( -name "*.py" -o -name "*.md" -o -name "*.txt" -o -name "*.json" \) -print \
  | sed 's|^\./||' | sort)
echo "RAW_SHA256SUM_OUTPUT_BEGIN"
if [[ ${#files[@]} -eq 0 ]]; then
  echo "(no matching files found)"
else
  printf '%s\0' "${files[@]}" | xargs -0 sha256sum
fi
echo "RAW_SHA256SUM_OUTPUT_END"
echo

# ---------------------------------------------------------------------------
echo "3. SPECIFIC FILE CHECK"

search_across_branches() {
  local filename="$1" found=0
  for b in "${unique_branches[@]}"; do
    local hits
    hits=$(git ls-tree -r --name-only "$b" 2>/dev/null | grep -F -- "$filename" || true)
    if [[ -n "$hits" ]]; then
      echo "$hits" | sed "s|^|FOUND in branch $b: |"
      found=1
    fi
  done
  if [[ $found -eq 0 ]]; then
    echo "NOT FOUND (any branch): $filename"
  fi
}

specific_files=(
  "drift_gate.py"
  "eve_governor.py"
  "soso_validate.py"
  "audit.py"
  "cert_core.py"
  "evaluate_frame.py"
  "soso/gate_interface.py"
  "capture_session.py"
  "validator_run_report.json"
  "MANIFEST_SHA256.txt"
)
for f in "${specific_files[@]}"; do
  echo "Check: $f"
  search_across_branches "$f"
  echo
done

echo "audit.py: append_audit body + event_seq/authority_hash usage"
for b in "${unique_branches[@]}"; do
  paths=$(git ls-tree -r --name-only "$b" 2>/dev/null | grep -F "audit.py" || true)
  [[ -z "$paths" ]] && continue
  while IFS= read -r p; do
    echo "BRANCH $b - FILE $p"
    git show "$b:$p" | awk '
      /^def append_audit/ { ins=1 }
      ins && /^def / && !/^def append_audit/ { exit }
      ins { print }
    '
    has_event_seq=$(git show "$b:$p" | grep -n "event_seq" || true)
    has_authority_hash=$(git show "$b:$p" | grep -n "authority_hash" || true)
    if [[ -n "$has_event_seq" ]]; then
      echo "  Contains 'event_seq' occurrences:"
      echo "$has_event_seq" | sed 's/^/    /'
    else
      echo "  'event_seq' not found in file"
    fi
    if [[ -n "$has_authority_hash" ]]; then
      echo "  Contains 'authority_hash' occurrences:"
      echo "$has_authority_hash" | sed 's/^/    /'
    else
      echo "  'authority_hash' not found in file"
    fi
  done <<< "$paths"
done
echo

echo "capture_session.py: import/dependency check"
for b in "${unique_branches[@]}"; do
  paths=$(git ls-tree -r --name-only "$b" 2>/dev/null | grep -F "capture_session.py" || true)
  [[ -z "$paths" ]] && continue
  while IFS= read -r p; do
    echo "BRANCH $b - FILE $p"
    tmp_py=$(mktemp)
    git show "$b:$p" > "$tmp_py"
    echo "Imports found:"
    python3 - "$tmp_py" <<'PY'
import ast, sys
with open(sys.argv[1], "r", encoding="utf-8", errors="ignore") as f:
    src = f.read()
try:
    tree = ast.parse(src)
except SyntaxError as e:
    print("  PYTHON_PARSE_ERROR:", e)
    sys.exit(0)
for node in ast.walk(tree):
    if isinstance(node, ast.Import):
        for n in node.names:
            print("  import", n.name)
    elif isinstance(node, ast.ImportFrom):
        mod = node.module or ""
        for n in node.names:
            print("  from", mod, "import", n.name)
PY
    echo "Local resolution heuristic (module -> file present in branch?):"
    mods=$(python3 - "$tmp_py" <<'PY'
import ast, sys
with open(sys.argv[1], "r", encoding="utf-8", errors="ignore") as f:
    src = f.read()
try:
    tree = ast.parse(src)
except SyntaxError:
    sys.exit(0)
mods = set()
for node in ast.walk(tree):
    if isinstance(node, ast.Import):
        for n in node.names:
            mods.add(n.name.split(".")[0])
    elif isinstance(node, ast.ImportFrom):
        if node.module:
            mods.add(node.module.split(".")[0])
for m in sorted(mods):
    print(m)
PY
)
    rm -f "$tmp_py"
    if [[ -z "$mods" ]]; then
      echo "  (no imports detected or parse error)"
    else
      branch_tree=$(git ls-tree -r --name-only "$b" 2>/dev/null || true)
      while IFS= read -r m; do
        [[ -z "$m" ]] && continue
        if echo "$branch_tree" | grep -qE "(^|/)${m}\.py$|(^|/)${m}/__init__\.py$"; then
          echo "  $m -> local file present"
        else
          echo "  $m -> not found in repo (stdlib or external)"
        fi
      done <<< "$mods"
    fi
  done <<< "$paths"
done
echo

echo "validator_run_report.json: content check"
found_any=0
for b in "${unique_branches[@]}"; do
  paths=$(git ls-tree -r --name-only "$b" 2>/dev/null | grep -F "validator_run_report.json" || true)
  [[ -z "$paths" ]] && continue
  found_any=1
  while IFS= read -r p; do
    echo "BRANCH $b - FILE $p"
    content=$(git show "$b:$p")
    if command -v jq >/dev/null 2>&1 && echo "$content" | jq -e '.summary' >/dev/null 2>&1; then
      echo "SUMMARY JSON BLOCK (verbatim):"
      echo "$content" | jq -r '.summary' | sed 's/^/  /'
    else
      echo "SUMMARY: UNKNOWN (not valid JSON, .summary missing, or jq unavailable). Raw excerpt:"
      echo "$content" | sed -n '1,200p' | sed 's/^/  /'
    fi
  done <<< "$paths"
done
if [[ $found_any -eq 0 ]]; then
  echo "validator_run_report.json: NOT FOUND in any branch"
fi
echo

echo "MANIFEST_SHA256.txt: presence and format check (repo root, per branch)"
for b in "${unique_branches[@]}"; do
  if git ls-tree -r --name-only "$b" 2>/dev/null | grep -qx "MANIFEST_SHA256.txt"; then
    echo "BRANCH $b - MANIFEST_SHA256.txt FOUND at repo root"
    git show "$b:MANIFEST_SHA256.txt" | sed 's/^/  /'
    if git show "$b:MANIFEST_SHA256.txt" | awk 'NF>=2 { if ($1 !~ /^[0-9a-f]{64}$/) { bad=1; exit } } END { exit bad }'; then
      echo "  CONTENT_FORMAT: ALL_LINES_MATCH_SHA256SUM_OUTPUT_FORMAT"
    else
      echo "  CONTENT_FORMAT: CONTAINS_NON_STANDARD_LINES_OR_ANNOTATIONS"
    fi
  else
    echo "BRANCH $b - MANIFEST_SHA256.txt NOT FOUND at repo root"
  fi
done
echo

# ---------------------------------------------------------------------------
echo "4. FOLDER STRUCTURE MATCH"
candidateA=(00_INDEX SOURCE_INBOX 01_CORE_DOCTRINE 02_GOVERNANCE 03_ARCHITECTURE 04_REQUIREMENTS 05_HARDWARE 06_RESEARCH 07_SOPS 08_HANDOFFS 09_ADMIN 10_ARCHIVE)
candidateB=(PH6_SOURCE SUBSYSTEMS INDEPENDENT_PEERS ADJACENT_TOOLING GOVERNANCE EXPERIMENTAL ARCHIVE)

if [[ "$default_branch" != "UNKNOWN" ]] && git rev-parse --verify "$default_branch" >/dev/null 2>&1; then
  mapfile -t top_level_dirs < <(git ls-tree -d --name-only "$default_branch" 2>/dev/null || true)
else
  mapfile -t top_level_dirs < <(git ls-tree -d --name-only HEAD 2>/dev/null || true)
fi
echo "Top-level directories on default branch:"
for d in "${top_level_dirs[@]}"; do echo " - $d"; done

count_matches() {
  local -n candidate=$1
  local match=0
  for c in "${candidate[@]}"; do
    for d in "${top_level_dirs[@]}"; do
      if [[ "$d" == "$c" ]]; then ((match++)); break; fi
    done
  done
  echo "$match"
}

countA_match=$(count_matches candidateA)
countB_match=$(count_matches candidateB)
countA_total=${#candidateA[@]}
countB_total=${#candidateB[@]}

echo "Candidate A: $countA_match / $countA_total top-level entries present"
echo "Candidate B: $countB_match / $countB_total top-level entries present"

for pair in "A:$countA_match:$countA_total" "B:$countB_match:$countB_total"; do
  IFS=: read -r label m t <<< "$pair"
  if [[ "$m" -eq "$t" ]]; then
    echo "MATCH_STATUS: Repository matches Candidate $label"
  elif [[ "$m" -gt 0 ]]; then
    echo "MATCH_STATUS: Repository partially matches Candidate $label"
  else
    echo "MATCH_STATUS: Repository does NOT match Candidate $label"
  fi
done
echo

# ---------------------------------------------------------------------------
echo "5. TEST STATE"
echo "Test files in working tree (syntax check + static import resolution):"
mapfile -t test_files_head < <(find . -path './.git' -prune -o "${evidence_prune[@]}" -type f \
  \( -name "test_*.py" -o -name "*_test.py" -o -path "*/tests/*.py" \) -print \
  | sed 's|^\./||' | sort)

if [[ ${#test_files_head[@]} -eq 0 ]]; then
  echo "  (no test files in working tree)"
else
  for tf in "${test_files_head[@]}"; do
    echo "  - $tf"
    if python3 -m py_compile "$tf" 2>/dev/null; then
      syntax_ok="SYNTAX_OK"
    else
      syntax_ok="SYNTAX_ERROR"
    fi
    mods=$(python3 - "$tf" <<'PY'
import ast, sys
try:
    with open(sys.argv[1], "r", encoding="utf-8", errors="ignore") as f:
        tree = ast.parse(f.read())
except (SyntaxError, OSError):
    sys.exit(0)
mods = set()
for node in ast.walk(tree):
    if isinstance(node, ast.Import):
        for n in node.names:
            mods.add(n.name.split(".")[0])
    elif isinstance(node, ast.ImportFrom):
        if node.module:
            mods.add(node.module.split(".")[0])
for m in sorted(mods):
    print(m)
PY
)
    local_res="LOCAL_MODULES:"
    if [[ -z "$mods" ]]; then
      local_res="$local_res NONE_DETECTED_OR_PARSE_ERROR"
    else
      while IFS= read -r m; do
        [[ -z "$m" ]] && continue
        if [[ -f "${m}.py" ]] || [[ -f "${m}/__init__.py" ]]; then
          local_res="$local_res $m(PRESENT)"
        else
          local_res="$local_res $m(UNKNOWN_OR_EXTERNAL)"
        fi
      done <<< "$mods"
    fi
    echo "      $syntax_ok; $local_res"
  done
fi

echo "Test files found in other branches (branch:path):"
current_branch=$(git rev-parse --abbrev-ref HEAD)
for b in "${unique_branches[@]}"; do
  [[ "$b" == "$current_branch" ]] && continue
  tpaths=$(git ls-tree -r --name-only "$b" 2>/dev/null \
    | grep -E '(^|/)test_[^/]*\.py$|_test\.py$|(^|/)tests/.*\.py$' || true)
  [[ -z "$tpaths" ]] && continue
  while IFS= read -r tp; do echo "  $b:$tp"; done <<< "$tpaths"
done
echo

# ---------------------------------------------------------------------------
echo "6. BRANCHES AND PRs"
echo "Branches (all refs deduped):"
for b in "${unique_branches[@]}"; do echo " - $b"; done

echo "Open PRs:"
if [[ -z "$owner_repo" ]]; then
  echo "UNKNOWN (origin remote not parseable to owner/repo)"
elif ! command -v curl >/dev/null 2>&1 || ! command -v jq >/dev/null 2>&1; then
  echo "UNKNOWN (curl and/or jq not available)"
else
  if [[ -n "${GITHUB_TOKEN:-}" ]]; then
    prs_json=$(curl -sS -H "Authorization: token ${GITHUB_TOKEN}" -H "Accept: application/vnd.github+json" \
      "https://api.github.com/repos/${owner_repo}/pulls?state=open&per_page=100" || echo "")
  else
    prs_json=$(curl -sS -H "Accept: application/vnd.github+json" \
      "https://api.github.com/repos/${owner_repo}/pulls?state=open&per_page=100" || echo "")
  fi
  if [[ -z "$prs_json" ]] || ! echo "$prs_json" | jq -e 'type == "array"' >/dev/null 2>&1; then
    api_message=$(echo "$prs_json" | jq -r '.message // empty' 2>/dev/null || true)
    if [[ -n "$api_message" ]]; then
      echo "UNKNOWN (GitHub API did not return a PR list: $api_message)"
    else
      echo "UNKNOWN (could not fetch or parse PRs via GitHub API)"
    fi
  else
    count=$(echo "$prs_json" | jq 'length')
    if [[ "$count" == "0" ]]; then
      echo "  (no open PRs)"
    else
      echo "Open PRs count: $count"
      echo "$prs_json" | jq -r '.[] | "  - #\(.number): \(.title)"'
    fi
  fi
fi
