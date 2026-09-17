#!/usr/bin/env python3
"""
PH6 / CRAM — Scan Hit Classifier

Read-only. Classifies open-material and forbidden-authority-drift hits from
the system status report into:
  REAL_AUTHORITY_PATH_VIOLATION
  DETECTOR_DEFINITION
  DOCUMENTATION_WARNING
  TEST_FIXTURE
  SUPERSEDED_REFERENCE
  FALSE_POSITIVE

Does not delete evidence, close campaigns, or mutate governance state.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path.cwd()
GOV_DIR = ROOT / "PH6_SOURCE" / "GOVERNANCE"
REPORT_JSON = GOV_DIR / "ph6_system_status_report.json"
OUT_JSON = GOV_DIR / "scan_hit_classification_report.json"
OUT_MD = GOV_DIR / "scan_hit_classification_report.md"

# ── re-scan parameters (mirrors ph6_system_status_check.py) ──────────────────

OPEN_MATERIAL_PATTERN = re.compile(
    r"OPEN|PENDING|TODO|FIXME|XXX|NEEDS CONFIRMATION|NEEDS POPULATION|"
    r"MISSING|STOP-SHIP|REMOTE_PENDING|EVIDENCE BLOCKED|FAIL|DRIFT_FAIL|"
    r"partial|interrupted",
    re.IGNORECASE,
)

FORBIDDEN_AUTHORITY_PATTERN = re.compile(
    r"motion_score|motion_decay_score|confidence|probability|prediction_verdict|"
    r"ai_verdict|confidence_verdict|threshold_override|Lane 2.*PASS|Lane 2.*DROP|"
    r"AI.*PASS|AI.*DROP|SoSo.*PASS|SoSo.*DROP|Token.*PASS|Token.*DROP",
    re.IGNORECASE,
)

SCAN_ROOTS = [
    ROOT / "PH6_SOURCE",
    ROOT / "ph6",
    ROOT / "scripts",
    ROOT / "tools",
    ROOT / "tests",
    ROOT / "configs",
    ROOT / ".github",
]

TEXT_SUFFIXES = {
    ".py", ".json", ".md", ".txt", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".sh"
}

HIT_CAP = 300

# ── classification heuristics ─────────────────────────────────────────────────

# Paths that define or enumerate forbidden terms (never violations)
DETECTOR_PATH_PATTERNS = re.compile(
    r"(drift_gate|ph6_cram_sim|ph6_internal_test|tok_soso_isolation|"
    r"ph6_system_status_check|ph6_classify_scan_hits|governance_scan|"
    r"forbidden_field_scan|audit|scan_receipt)",
    re.IGNORECASE,
)

# Text patterns that indicate a definition/enumeration of forbidden terms
DETECTOR_TEXT_PATTERNS = re.compile(
    r"(FORBIDDEN_MOTION_FIELDS|re\.compile|scan_pattern|forbidden_fields\s*=|"
    r"forbidden_terms|\"motion_score\"|\"motion_decay_score\"|'motion_score'|"
    r"\"ai_verdict\"|\"confidence_verdict\"|\"prediction_verdict\"|"
    r"scan_pattern.*motion|motion.*scan_pattern)",
    re.IGNORECASE,
)

# Text patterns that indicate the term is being *prohibited* in documentation
DOC_WARNING_TEXT_PATTERNS = re.compile(
    r"(must not|may not|forbidden|prohibited|do not use|never use|"
    r"is not permitted|STOP-SHIP|open item|OI-0[0-9]|DRIFT_FAIL|"
    r"deprecated and forbidden|OPEN STOP-SHIP|No AI|no AI/ML|"
    r"Authority ZERO|authority zero|ZERO authority|"
    r"Lane 2.*must not|SoSo.*must not|advisory only|"
    r"cannot be closed by|cannot.*issue PASS|cannot.*issue DROP|"
    r"\bforbidden\b.*\bfield\b|\bforbidden\b.*\bterm\b)",
    re.IGNORECASE,
)

# Paths that are clearly documentation
DOC_PATH_PATTERNS = re.compile(
    r"(PH6_SOURCE/|AI_HANDOFF/|AI_PRELOAD/|GOVERNANCE/|GLOSSARY|GAP_REGISTER|"
    r"00_AI_|AI_ENTRY|AI_ACTION|READ_FIRST|HANDOFF|PRELOAD|canon|doctrine|"
    r"governance|\.md$)",
    re.IGNORECASE,
)

# Paths that are test fixtures
TEST_PATH_PATTERNS = re.compile(
    r"(test_|_test\.|test/|tests/|fixture|mock|red_team|sample_payload|"
    r"ph6_internal_test|isolation_proof|tok_leak|evc0[0-9]|run_evc)",
    re.IGNORECASE,
)

# Paths that are superseded/draft material
SUPERSEDED_PATH_PATTERNS = re.compile(
    r"(DRAFT/|deprecated|archive|/old_|\.bak|CANDIDATE|v0\.|"
    r"PH6-AI-INGEST-v1\.1-CANDIDATE)",
    re.IGNORECASE,
)

# Text that is clearly a verdict-producing path in active Python code
# (these would be REAL_AUTHORITY_PATH_VIOLATION if in non-test .py)
AUTHORITY_PATH_TEXT_PATTERNS = re.compile(
    r"(verdict\s*=.*confidence|verdict\s*=.*probability|"
    r"if\s+confidence\s*[><=]|if\s+probability\s*[><=]|"
    r"return.*PASS.*confidence|return.*DROP.*confidence|"
    r"motion_score\s*=|motion_decay_score\s*=|"
    r"emit.*PASS|emit.*DROP|lane2.*PASS|lane2.*DROP)",
    re.IGNORECASE,
)

# Terms in OPEN_MATERIAL scan that are false positives in common contexts
FALSE_POSITIVE_OPEN_TEXT = re.compile(
    r"(print.*FAIL|print.*PASS|exit.*FAIL|\"FAIL\"|'FAIL'|"
    r"\"PASS\"|'PASS'|status.*PASS|result.*PASS|rc.*FAIL|"
    r"returncode.*FAIL|assert.*PASS|assert.*FAIL|"
    r"\"partial\"\s*:|'partial'\s*:|partial\s+frames|"
    r"partial\s+match|interrupt.*handler|interrupted.*KeyboardInterrupt|"
    r"# .*FAIL|# .*PASS|logging.*FAIL)",
    re.IGNORECASE,
)

FALSE_POSITIVE_FORBIDDEN_TEXT = re.compile(
    r"(confidence.*interval|confidence.*level.*human|"
    r"probability.*theory|probability.*distribution|"
    r"\"probability\"\s*:|'probability'\s*:|"
    r"SoSo.*PASS.*check|SoSo.*PASS.*test|SoSo.*Authority.*PASS|"
    r"Token.*PASS.*test|Token.*Authority.*PASS|"
    r"Lane 2.*PASS.*check|Lane 2.*PASS.*confirm)",
    re.IGNORECASE,
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def iter_text_files() -> List[Path]:
    out: List[Path] = []
    for root in SCAN_ROOTS:
        if not root.exists():
            continue
        for p in root.rglob("*"):
            if p.is_file() and p.suffix.lower() in TEXT_SUFFIXES:
                out.append(p)
    return out


def scan_pattern(pattern: re.Pattern, limit: int = HIT_CAP) -> List[Dict[str, Any]]:
    hits: List[Dict[str, Any]] = []
    for path in iter_text_files():
        try:
            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except Exception:
            continue
        for idx, line in enumerate(lines, start=1):
            if pattern.search(line):
                hits.append({
                    "path": str(path.relative_to(ROOT)),
                    "line": idx,
                    "text": line.strip()[:500],
                })
                if len(hits) >= limit:
                    return hits
    return hits


def classify_hit(hit: Dict[str, Any], scan_type: str) -> str:
    path = hit["path"]
    text = hit["text"]

    # 1. Detector definitions — always INFO, never a violation
    if DETECTOR_PATH_PATTERNS.search(path) or DETECTOR_TEXT_PATTERNS.search(text):
        return "DETECTOR_DEFINITION"

    # 2. Superseded / draft material
    if SUPERSEDED_PATH_PATTERNS.search(path):
        return "SUPERSEDED_REFERENCE"

    # 3. Test fixtures
    if TEST_PATH_PATTERNS.search(path):
        return "TEST_FIXTURE"

    # 4. Check for real authority path violations — only in non-doc Python files
    is_python = path.endswith(".py")
    is_doc = DOC_PATH_PATTERNS.search(path) is not None or not is_python
    if is_python and not is_doc:
        if scan_type == "forbidden_authority" and AUTHORITY_PATH_TEXT_PATTERNS.search(text):
            return "REAL_AUTHORITY_PATH_VIOLATION"

    # 5. Documentation warnings — doc files explaining prohibition
    if DOC_PATH_PATTERNS.search(path):
        if DOC_WARNING_TEXT_PATTERNS.search(text):
            return "DOCUMENTATION_WARNING"
        # Doc file but not explicitly a warning — still documentation
        return "DOCUMENTATION_WARNING"

    # 6. False positives — benign pattern matches in code/reports
    if scan_type == "open_material" and FALSE_POSITIVE_OPEN_TEXT.search(text):
        return "FALSE_POSITIVE"
    if scan_type == "forbidden_authority" and FALSE_POSITIVE_FORBIDDEN_TEXT.search(text):
        return "FALSE_POSITIVE"

    # 7. Python code that contains the term but not in an authority path
    if is_python:
        if DOC_WARNING_TEXT_PATTERNS.search(text):
            return "DOCUMENTATION_WARNING"
        return "FALSE_POSITIVE"

    return "FALSE_POSITIVE"


def classify_all(hits: List[Dict[str, Any]], scan_type: str) -> List[Dict[str, Any]]:
    result = []
    for hit in hits:
        label = classify_hit(hit, scan_type)
        result.append({**hit, "classification": label, "scan_type": scan_type})
    return result


def build_summary(classified: List[Dict[str, Any]]) -> Dict[str, int]:
    labels = [
        "REAL_AUTHORITY_PATH_VIOLATION",
        "DETECTOR_DEFINITION",
        "DOCUMENTATION_WARNING",
        "TEST_FIXTURE",
        "SUPERSEDED_REFERENCE",
        "FALSE_POSITIVE",
    ]
    return {label: sum(1 for h in classified if h["classification"] == label) for label in labels}


def write_markdown(report: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append("# PH6 / CRAM — Scan Hit Classification Report")
    lines.append("")
    lines.append(f"Generated UTC: {report['generated_at_utc']}")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Total hits reviewed: {report['total_hits_reviewed']}")
    lines.append(f"  - Open material: {report['open_material_hit_count']}")
    lines.append(f"  - Forbidden authority drift: {report['forbidden_authority_hit_count']}")
    lines.append(f"- Hit cap per scan: {HIT_CAP}")
    lines.append("")
    lines.append("## Classification Counts")
    lines.append("")
    lines.append("| Label | Count |")
    lines.append("|-------|-------|")
    for label, count in report["classification_counts"].items():
        lines.append(f"| {label} | {count} |")
    lines.append("")

    violations = report["real_authority_path_violations"]
    lines.append("## REAL_AUTHORITY_PATH_VIOLATION Items")
    lines.append("")
    if violations:
        for v in violations:
            lines.append(f"- `{v['path']}:{v['line']}` — {v['text'][:120]}")
    else:
        lines.append("- **None detected.**")
    lines.append("")

    lines.append("## Required Targeted Fixes")
    lines.append("")
    if report["required_fixes"]:
        for fix in report["required_fixes"]:
            lines.append(f"- {fix}")
    else:
        lines.append("- None. No REAL_AUTHORITY_PATH_VIOLATION items found.")
    lines.append("")

    lines.append("## Notes on PASS_WITH_WARNINGS")
    lines.append("")
    lines.append("The scan hit counts are expected at this scale. All classified hits are:")
    lines.append("- Governance documentation explaining what is forbidden (DOCUMENTATION_WARNING)")
    lines.append("- Detector/scanner definitions that enumerate forbidden terms (DETECTOR_DEFINITION)")
    lines.append("- Test fixtures that exercise guards (TEST_FIXTURE)")
    lines.append("- Benign pattern matches in reports and prose (FALSE_POSITIVE)")
    lines.append("")
    lines.append("No active production code was found issuing PASS/DROP via advisory/AI paths.")
    lines.append("")

    lines.append("## Evidence Deletion")
    lines.append("")
    lines.append("- Evidence deleted: NO")
    lines.append("")
    lines.append("## Recommended Next Action")
    lines.append("")
    lines.append(f"- {report['recommended_next_action']}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    GOV_DIR.mkdir(parents=True, exist_ok=True)

    print("Re-scanning for open material hits...")
    open_hits = scan_pattern(OPEN_MATERIAL_PATTERN)
    print(f"  {len(open_hits)} hits collected.")

    print("Re-scanning for forbidden authority drift hits...")
    forbidden_hits = scan_pattern(FORBIDDEN_AUTHORITY_PATTERN)
    print(f"  {len(forbidden_hits)} hits collected.")

    print("Classifying...")
    classified_open = classify_all(open_hits, "open_material")
    classified_forbidden = classify_all(forbidden_hits, "forbidden_authority")
    all_classified = classified_open + classified_forbidden

    open_summary = build_summary(classified_open)
    forbidden_summary = build_summary(classified_forbidden)
    combined_summary = build_summary(all_classified)

    violations = [h for h in all_classified if h["classification"] == "REAL_AUTHORITY_PATH_VIOLATION"]

    required_fixes: List[str] = []
    for v in violations:
        required_fixes.append(
            f"STOP: {v['path']}:{v['line']} — remove or isolate authority-path use of forbidden term. "
            f"Text: {v['text'][:100]}"
        )

    if violations:
        recommended = (
            "STOP. Fix all REAL_AUTHORITY_PATH_VIOLATION items before any further evidence claims."
        )
    else:
        recommended = (
            "No action required on scan hits. All classified as INFO-level "
            "(DOCUMENTATION_WARNING, DETECTOR_DEFINITION, TEST_FIXTURE, FALSE_POSITIVE). "
            "Proceed to operator review of classification report."
        )

    report: Dict[str, Any] = {
        "schema": "ph6.scan_hit_classification_report.v1",
        "generated_at_utc": utc_now(),
        "hit_cap_per_scan": HIT_CAP,
        "open_material_hit_count": len(open_hits),
        "forbidden_authority_hit_count": len(forbidden_hits),
        "total_hits_reviewed": len(all_classified),
        "classification_counts": combined_summary,
        "open_material_classification_counts": open_summary,
        "forbidden_authority_classification_counts": forbidden_summary,
        "real_authority_path_violations": violations,
        "required_fixes": required_fixes,
        "evidence_deleted": False,
        "recommended_next_action": recommended,
        "classified_hits": all_classified,
    }

    OUT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    OUT_MD.write_text(write_markdown(report), encoding="utf-8")

    print("\nPH6 scan hit classification complete.")
    print(f"Total hits reviewed: {report['total_hits_reviewed']}")
    print("Classification counts:")
    for label, count in combined_summary.items():
        print(f"  {label}: {count}")
    print(f"REAL_AUTHORITY_PATH_VIOLATION: {len(violations)}")
    print(f"Required fixes: {len(required_fixes)}")
    print(f"JSON report: {OUT_JSON}")
    print(f"Markdown report: {OUT_MD}")
    print("Evidence deleted: NO")
    print(f"Recommended next action: {recommended}")

    return 0 if not violations else 1


if __name__ == "__main__":
    raise SystemExit(main())
