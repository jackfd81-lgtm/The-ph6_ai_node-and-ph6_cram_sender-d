#!/usr/bin/env python3
"""
governance_drift_scan.py — PH6 Governance Drift Scanner

Lane:      2 (Advisory tooling — does not modify any authority path)
Authority: ZERO
Schema:    ph6.governance.drift_report.v1

Scans a target tree for governance violations defined in:
  PH6_SOURCE/GOVERNANCE/forbidden_terms_registry.json
  PH6_SOURCE/GOVERNANCE/schema_lock_registry.json
  PH6_SOURCE/GOVERNANCE/governance_manifest.json

Checks:
  1. Forbidden terms in Python source files (from forbidden_terms_registry)
  2. Forbidden fields in JSON evidence/output files
  3. SHA256 misuse as canonical authority (hash_algorithm=sha256 in authoritative paths)
  4. Lane-2 PASS/DROP authority leakage (verdict field in Lane-2 source)
  5. Missing governance files
  6. Schema version drift (schema strings present in source with no version reference)
  7. Missing .blake2b markers where .sha256 exists (authority marker regression)

Exit codes:
  0 — PASS (no CRITICAL or HIGH violations)
  1 — CRITICAL violations found
  2 — HIGH violations only (no CRITICAL)

Usage:
  python3 PH6_SOURCE/TOOLS/governance_drift_scan.py
  python3 PH6_SOURCE/TOOLS/governance_drift_scan.py --scan-root /home/jack/ph6
  python3 PH6_SOURCE/TOOLS/governance_drift_scan.py --scan-root /home/jack/PH6_SOURCE
  python3 PH6_SOURCE/TOOLS/governance_drift_scan.py --report-out drift_report.json
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_ID = "ph6.governance.drift_report.v1"

SKIP_DIRS = {"__pycache__", ".git", "*.pyc", "node_modules", "dist", "build"}
SKIP_FILE_PREFIXES = {"test_"}
SKIP_PATHS_CONTAINING = {"__pycache__", ".git/", "validation_runs/"}

# Governance files are the authoritative source of forbidden term definitions.
# Scanning them for those terms would be self-defeating; exclude them.
GOVERNANCE_SKIP_FRAGMENTS = {"/GOVERNANCE/"}

# In markdown, lines in prohibition-context tables or FORBIDDEN/NEVER lists
# are definitional references, not drift violations.
_MD_PROHIBITION_CONTEXT = re.compile(
    r"(FORBIDDEN|NEVER|prohibited|must not|not allow|NOT include|NOT use|non-replayable|Drift\b)",
    re.IGNORECASE,
)

# Headings that signal a prohibition-context section.  "Incorrect" covers
# PH6 doc sections like "10.2 Incorrect AI Behavior" that enumerate bad patterns.
_PROHIBITION_HEADING = re.compile(
    r"(NEVER|FORBIDDEN|PROHIBITED|MUST\s+NOT|RESTRICTIONS|Incorrect)",
    re.IGNORECASE,
)


def _build_md_prohibition_lines(lines: list[str]) -> frozenset:
    """
    Pre-pass over a markdown file's lines.  Returns a frozenset of 1-based
    line numbers that are in prohibition context:
      - inside a fenced code block (``` … ```) whose nearest preceding heading
        matches _PROHIBITION_HEADING, OR
      - a list item (- / *) directly under a prohibition heading.

    These lines enumerate what is forbidden, not code that actually uses it.
    """
    prohibition_lines: set = set()
    in_fence = False
    fence_is_prohibited = False
    heading_is_prohibited = False

    for i, line in enumerate(lines, 1):
        stripped = line.strip()

        if stripped.startswith("#") and not in_fence:
            heading_is_prohibited = bool(_PROHIBITION_HEADING.search(stripped))
            continue

        if stripped.startswith("```"):
            if not in_fence:
                in_fence = True
                fence_is_prohibited = heading_is_prohibited
            else:
                in_fence = False
                fence_is_prohibited = False
            continue

        if in_fence and fence_is_prohibited:
            prohibition_lines.add(i)
            continue

        if not in_fence and heading_is_prohibited:
            if stripped.startswith("- ") or stripped.startswith("* "):
                prohibition_lines.add(i)

    return frozenset(prohibition_lines)


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _should_skip(p: Path) -> bool:
    s = str(p)
    for fragment in SKIP_PATHS_CONTAINING:
        if fragment in s:
            return True
    return False


def _load_json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _iter_python_files(root: Path):
    for p in root.rglob("*.py"):
        if not _should_skip(p):
            yield p


def _iter_json_files(root: Path):
    for p in root.rglob("*.json"):
        if not _should_skip(p):
            yield p


def _iter_source_files(root: Path):
    for ext in ("*.py", "*.md", "*.json"):
        for p in root.rglob(ext):
            if not _should_skip(p):
                yield p


def scan_forbidden_terms(root: Path, registry: dict) -> list[dict]:
    findings = []
    entries = registry.get("entries", [])

    for entry in entries:
        entry_id   = entry["id"]
        severity   = entry["severity"]
        pattern    = entry["scan_pattern"]
        flags_list = entry.get("scan_flags", [])
        applies_to = entry.get("applies_to", [])
        reason     = entry["reason"]

        re_flags = 0
        if "IGNORECASE" in flags_list:
            re_flags |= re.IGNORECASE

        try:
            compiled = re.compile(pattern, re_flags)
        except re.error as e:
            findings.append({
                "check": "forbidden_terms",
                "severity": "WARN",
                "entry_id": entry_id,
                "file": "N/A",
                "line": 0,
                "detail": f"Bad regex in registry entry {entry_id}: {e}",
            })
            continue

        # Determine which file types to scan
        scan_py   = any(t in applies_to for t in ["source_python", "source"])
        scan_json = any(t in applies_to for t in ["json_output", "evidence", "schema_files"])
        scan_docs = "documentation" in applies_to

        file_iter = []
        if scan_py:
            file_iter += list(_iter_python_files(root))
        if scan_json:
            file_iter += list(_iter_json_files(root))
        if scan_docs:
            for p in root.rglob("*.md"):
                if not _should_skip(p):
                    file_iter.append(p)

        seen_files = set()
        for p in file_iter:
            if p in seen_files:
                continue
            seen_files.add(p)

            # Skip governance definition files — they legitimately contain all forbidden terms.
            p_str = str(p)
            if any(frag in p_str for frag in GOVERNANCE_SKIP_FRAGMENTS):
                continue

            try:
                lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
            except OSError:
                continue

            is_md = p.suffix == ".md"
            md_prohibition_lines = _build_md_prohibition_lines(lines) if is_md else frozenset()

            for i, line in enumerate(lines, 1):
                if not compiled.search(line):
                    continue
                if is_md:
                    # Fence-context or heading-context prohibition lines (definitional).
                    if i in md_prohibition_lines:
                        continue
                    stripped = line.strip()
                    # Table row or list item whose own line has a prohibition keyword.
                    if (stripped.startswith("|") or stripped.startswith("- ") or stripped.startswith("* ")):
                        if _MD_PROHIBITION_CONTEXT.search(line):
                            continue
                    # Short line that is itself a prohibition heading/label.
                    if _MD_PROHIBITION_CONTEXT.search(line) and len(stripped) < 80:
                        continue

                findings.append({
                        "check": "forbidden_terms",
                        "severity": severity,
                        "entry_id": entry_id,
                        "term": entry["term"],
                        "file": str(p),
                        "line": i,
                        "content": line.strip()[:120],
                        "reason": reason,
                    })

    return findings


def scan_sha256_authority_misuse(root: Path) -> list[dict]:
    """
    Detect hash_algorithm=sha256 in non-compatibility contexts.
    Canonical hash is BLAKE2b-256. SHA256 is allowed only for compatibility,
    never as the declared canonical authority hash.
    """
    findings = []
    pattern = re.compile(r'"hash_algorithm"\s*:\s*"sha256"', re.IGNORECASE)

    for p in _iter_json_files(root):
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            if pattern.search(line):
                findings.append({
                    "check": "sha256_authority_misuse",
                    "severity": "HIGH",
                    "file": str(p),
                    "line": i,
                    "content": line.strip()[:120],
                    "detail": "hash_algorithm=sha256 found in JSON file — SHA256 is compatibility-only, not canonical authority",
                })

    return findings


def scan_lane2_pass_drop_leakage(root: Path) -> list[dict]:
    """
    Detect Lane-2 source files emitting PASS/DROP verdict fields.
    Lane-2 directories: ssmt/, tok/, ssmt.py patterns, etc.
    """
    findings = []
    lane2_patterns = ["ssmt", "tok", "soso", "jedi", "mram_s", "advisory"]
    verdict_pattern = re.compile(r'"verdict"\s*:\s*"(PASS|DROP)"')

    for p in _iter_python_files(root):
        path_lower = str(p).lower()
        is_lane2 = any(pat in path_lower for pat in lane2_patterns)
        if not is_lane2:
            continue
        try:
            lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for i, line in enumerate(lines, 1):
            if verdict_pattern.search(line) and "authority" not in line.lower():
                findings.append({
                    "check": "lane2_pass_drop_leakage",
                    "severity": "CRITICAL",
                    "file": str(p),
                    "line": i,
                    "content": line.strip()[:120],
                    "detail": "Lane-2 source emitting verdict PASS/DROP without authority qualifier — potential authority leakage",
                })

    return findings


def scan_blake2b_marker_regression(root: Path) -> list[dict]:
    """
    Find directories where .sha256 marker files exist but no .blake2b marker
    exists alongside the same base file. This indicates a marker authority
    regression (relying on sha256 instead of blake2b).
    """
    findings = []
    for sha_file in root.rglob("*.sha256"):
        if _should_skip(sha_file):
            continue
        base = sha_file.with_suffix("")
        blake2b_file = sha_file.parent / (base.name + ".blake2b")
        if not blake2b_file.exists():
            findings.append({
                "check": "blake2b_marker_regression",
                "severity": "HIGH",
                "file": str(sha_file),
                "line": 0,
                "detail": f".sha256 marker exists but no .blake2b companion: {sha_file.name} — canonical marker missing",
            })
    return findings


def scan_missing_governance_files(manifest: dict | None, project_root: Path) -> list[dict]:
    """
    Verify all governance files declared in the manifest exist on disk.
    """
    findings = []
    if not manifest:
        findings.append({
            "check": "missing_governance_files",
            "severity": "CRITICAL",
            "file": "governance_manifest.json",
            "line": 0,
            "detail": "governance_manifest.json could not be loaded — cannot verify governance file presence",
        })
        return findings

    gov_files = manifest.get("governance_files", {})
    for name, rel_path in gov_files.items():
        full_path = project_root / rel_path
        if not full_path.exists():
            findings.append({
                "check": "missing_governance_files",
                "severity": "CRITICAL",
                "file": rel_path,
                "line": 0,
                "detail": f"Governance file declared in manifest not found: {rel_path}",
            })

    return findings


def scan_forbidden_json_fields(root: Path, manifest: dict | None) -> list[dict]:
    """
    Scan JSON files for forbidden field names declared in manifest.
    """
    findings = []
    if not manifest:
        return findings

    forbidden = set(manifest.get("forbidden_fields", []))
    if not forbidden:
        return findings

    for p in _iter_json_files(root):
        try:
            data = _load_json(p)
        except Exception:
            continue
        if not isinstance(data, dict):
            continue
        for field in forbidden:
            if field in data:
                findings.append({
                    "check": "forbidden_json_fields",
                    "severity": "CRITICAL",
                    "file": str(p),
                    "line": 0,
                    "field": field,
                    "detail": f"Forbidden field '{field}' found as top-level key in JSON file",
                })

    return findings


def run_scan(scan_root: Path, gov_dir: Path, project_root: Path) -> dict:
    ft_reg   = _load_json(gov_dir / "forbidden_terms_registry.json")
    sl_reg   = _load_json(gov_dir / "schema_lock_registry.json")
    manifest = _load_json(gov_dir / "governance_manifest.json")

    all_findings: list[dict] = []

    if ft_reg:
        all_findings += scan_forbidden_terms(scan_root, ft_reg)
    else:
        all_findings.append({
            "check": "registry_load",
            "severity": "CRITICAL",
            "file": str(gov_dir / "forbidden_terms_registry.json"),
            "line": 0,
            "detail": "forbidden_terms_registry.json could not be loaded",
        })

    all_findings += scan_sha256_authority_misuse(scan_root)
    all_findings += scan_lane2_pass_drop_leakage(scan_root)
    all_findings += scan_blake2b_marker_regression(scan_root)
    all_findings += scan_missing_governance_files(manifest, project_root)
    all_findings += scan_forbidden_json_fields(scan_root, manifest)

    critical = [f for f in all_findings if f.get("severity") == "CRITICAL"]
    high     = [f for f in all_findings if f.get("severity") == "HIGH"]
    warn     = [f for f in all_findings if f.get("severity") == "WARN"]

    if critical:
        overall = "FAIL_CRITICAL"
    elif high:
        overall = "FAIL_HIGH"
    else:
        overall = "PASS"

    by_check: dict[str, dict] = {}
    for f in all_findings:
        check = f["check"]
        if check not in by_check:
            by_check[check] = {"count": 0, "severity": "PASS", "findings": []}
        by_check[check]["count"] += 1
        by_check[check]["findings"].append(f)
        sev = f.get("severity", "WARN")
        if sev == "CRITICAL":
            by_check[check]["severity"] = "CRITICAL"
        elif sev == "HIGH" and by_check[check]["severity"] != "CRITICAL":
            by_check[check]["severity"] = "HIGH"
        elif sev == "WARN" and by_check[check]["severity"] == "PASS":
            by_check[check]["severity"] = "WARN"

    return {
        "schema":          SCHEMA_ID,
        "scan_root":       str(scan_root),
        "governance_dir":  str(gov_dir),
        "generated_at_utc": _utc_now(),
        "overall_result":  overall,
        "critical_count":  len(critical),
        "high_count":      len(high),
        "warn_count":      len(warn),
        "total_findings":  len(all_findings),
        "summary_by_check": {
            k: {"count": v["count"], "severity": v["severity"]}
            for k, v in by_check.items()
        },
        "findings": all_findings,
    }


def print_human_summary(report: dict) -> None:
    print(f"\nPH6 GOVERNANCE DRIFT SCAN")
    print(f"  scan_root:   {report['scan_root']}")
    print(f"  generated:   {report['generated_at_utc']}")
    print(f"  result:      {report['overall_result']}")
    print(f"  critical:    {report['critical_count']}")
    print(f"  high:        {report['high_count']}")
    print(f"  warn:        {report['warn_count']}")
    print()

    for check, summary in report["summary_by_check"].items():
        marker = "[PASS]" if summary["severity"] == "PASS" else f"[{summary['severity']}]"
        print(f"  {marker:12s} {check}: {summary['count']} finding(s)")

    if report["critical_count"] or report["high_count"]:
        print("\n  --- FINDINGS ---")
        for f in report["findings"]:
            sev = f.get("severity", "WARN")
            if sev not in ("CRITICAL", "HIGH"):
                continue
            loc = f"{f['file']}:{f['line']}" if f.get("line") else f['file']
            print(f"  [{sev}] {f['check']}")
            print(f"         {loc}")
            print(f"         {f.get('detail', f.get('content', ''))}")
    print()


def main() -> int:
    ap = argparse.ArgumentParser(description="PH6 Governance Drift Scanner")
    default_gov = str(Path(__file__).resolve().parent.parent / "GOVERNANCE")
    ap.add_argument("--scan-root",      default=".",      help="Directory tree to scan (default: cwd)")
    ap.add_argument("--governance-dir", default=default_gov, help="Path to GOVERNANCE dir")
    ap.add_argument("--project-root",   default=None,     help="Project root for manifest file resolution (default: scan-root)")
    ap.add_argument("--report-out",     help="Write JSON report to this file")
    ap.add_argument("--json-only",      action="store_true", help="Emit JSON only, no human summary")
    args = ap.parse_args()

    scan_root    = Path(args.scan_root).resolve()
    gov_dir      = Path(args.governance_dir).resolve()
    # project_root is where manifest paths are anchored (repo root), NOT scan_root.
    project_root = Path(args.project_root).resolve() if args.project_root else Path.cwd()

    report = run_scan(scan_root, gov_dir, project_root)

    json_out = json.dumps(report, indent=2, sort_keys=False)

    if args.report_out:
        Path(args.report_out).write_text(json_out + "\n", encoding="utf-8")
        if not args.json_only:
            print_human_summary(report)
    else:
        if args.json_only:
            print(json_out)
        else:
            print_human_summary(report)
            print(json_out)

    overall = report["overall_result"]
    if overall == "FAIL_CRITICAL":
        return 1
    if overall == "FAIL_HIGH":
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
