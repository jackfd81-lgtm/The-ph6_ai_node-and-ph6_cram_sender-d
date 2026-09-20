#!/usr/bin/env python3
"""
PH6 Canon Linter — automated drift and contradiction scanner.

Lane: 2 (advisory tooling — does not modify any authority path)
Authority: ZERO

Checks:
  1. Forbidden float epoch timestamp patterns in authority paths
  2. Old float metric field names in authoritative PSEUDO/replay paths
  3. Unsafe .blake2b write_text() marker writes
  4. Duplicate canonical_json / blake2b helper warnings
  5. Forbidden audit event types
  6. Missing audit required fields (static check on source)
  7. Forbidden Lane-2 authority terms in production source
  8. TOK advisory_result field naming

Usage:
  python3 scripts/ph6_canon_lint.py
  python3 scripts/ph6_canon_lint.py --path ph6/

Returns exit code 0 on PASS, 1 on FAIL.
"""

from __future__ import annotations

import sys
import argparse
import re
from pathlib import Path
from typing import List, Tuple


WARN = "WARN"
FAIL = "FAIL"
PASS_STR = "PASS"

# ---------------------------------------------------------------------------
# Check definitions
# ---------------------------------------------------------------------------

def check_float_timestamp_in_authority_paths(root: Path) -> List[Tuple[str, str, str]]:
    """
    Flag: "timestamp": time.time() in authority-path source files.
    Advisory/debug files with Authority NONE are exempt.
    """
    issues = []
    authority_paths = [
        "cram_pu/tools/cram_pu_verdict_runner.py",
        "cram_pu/tools/cram_pu_replay_verify.py",
        "cram_pu/tools/cram_pu_atomic_commit.py",
        "cram_pu/crash_replay.py",
        "ssmt/audit_log.py",
    ]
    pattern = re.compile(r'"timestamp"\s*:\s*time\.time\(\)')
    for rel in authority_paths:
        p = root / rel
        if not p.exists():
            continue
        for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            if pattern.search(line):
                issues.append((FAIL, str(p), f"line {i}: float epoch timestamp in authority path: {line.strip()}"))
    return issues


def check_old_float_metric_fields(root: Path) -> List[Tuple[str, str, str]]:
    """
    Flag: old float metric field names used as JSON keys in production verdict/replay files.
    """
    issues = []
    targets = [
        "cram_pu/tools/cram_pu_verdict_runner.py",
        "cram_pu/tools/cram_pu_replay_verify.py",
    ]
    forbidden_keys = ['"mean_brightness":', '"laplacian_var":', '"motion_fraction":']
    for rel in targets:
        p = root / rel
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8")
        for key in forbidden_keys:
            if key in text:
                issues.append((FAIL, str(p), f"Old float field {key} found in authority PSEUDO path"))
    return issues


def check_unsafe_blake2b_write_text(root: Path) -> List[Tuple[str, str, str]]:
    """
    Flag: write_text() used for .blake2b marker creation in authority paths.
    """
    issues = []
    pattern = re.compile(r'\.write_text\(.*\.blake2b', re.DOTALL)
    for p in root.rglob("*.py"):
        if "__pycache__" in str(p) or "test_" in p.name:
            continue
        text = p.read_text(encoding="utf-8")
        if ".blake2b" in text and "write_text" in text:
            # Check if they appear near each other
            for i, line in enumerate(text.splitlines(), 1):
                if "write_text" in line and ".blake2b" in text.splitlines()[max(0, i-5):i+5].__str__():
                    issues.append((FAIL, str(p), f"line {i}: write_text() near .blake2b — may be non-atomic marker write"))
                    break
    return issues


def check_duplicate_canonical_helpers(root: Path) -> List[Tuple[str, str, str]]:
    """
    Warn: multiple files defining their own canonical_json or blake2b helpers
    instead of importing from schemas/canonical.py.
    """
    issues = []
    canonical_source = root / "cram_pu/schemas/canonical.py"
    pattern = re.compile(r'def (canonical_json|_canonical_bytes|canonical_bytes|canonical_dumps|blake2b256|_blake2b256|blake2b_256)\b')
    for p in root.rglob("*.py"):
        if "__pycache__" in str(p) or p == canonical_source:
            continue
        for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            if pattern.search(line):
                issues.append((WARN, str(p), f"line {i}: duplicate canonical/blake2b helper: {line.strip()}"))
    return issues


def check_forbidden_audit_event_types(root: Path) -> List[Tuple[str, str, str]]:
    """
    Flag: forbidden audit event type strings in source files.
    Excludes test files and the glossary/docs.
    """
    issues = []
    forbidden = {"PROMOTE", "REJECT", "ACCEPT", "FLAG", "HOLD", "REVIEW", "RETAIN"}
    pattern = re.compile(r'"event_type"\s*:\s*"(' + "|".join(forbidden) + r')"')
    for p in root.rglob("*.py"):
        if "__pycache__" in str(p) or "test_" in p.name:
            continue
        for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            if pattern.search(line):
                issues.append((FAIL, str(p), f"line {i}: forbidden audit event type: {line.strip()}"))
    return issues


def check_missing_audit_required_fields(root: Path) -> List[Tuple[str, str, str]]:
    """
    Flag: SSMT audit_log.py missing required fields from the emitted event dict.
    Static source check — does not execute code.

    Direct fields must appear as literal string keys in audit_log.py.
    chain_event() fields (event_hash, prev_event_hash) are injected by
    chain_event() — verified by confirming chain_event() is called.
    """
    issues = []
    audit_log = root / "ssmt/audit_log.py"
    if not audit_log.exists():
        return issues

    direct_fields = {
        "schema", "event_seq", "event_type", "object_id",
        "authority_hash", "node_id", "stage", "status", "timestamp_utc",
    }
    chain_injected = {"event_hash", "prev_event_hash"}

    text = audit_log.read_text(encoding="utf-8")

    for field in sorted(direct_fields):
        if f'"{field}"' not in text:
            issues.append((FAIL, str(audit_log), f"audit_log.py missing required field: {field!r}"))

    if "chain_event(" not in text:
        issues.append((FAIL, str(audit_log),
                       f"audit_log.py does not call chain_event() — "
                       f"fields {sorted(chain_injected)} will be absent"))

    return issues


def check_tok_advisory_result_naming(root: Path) -> List[Tuple[str, str, str]]:
    """
    Warn: TOK rebuild.py using "result": "PASS"/"WARN" instead of "advisory_result".
    """
    issues = []
    rebuild = root / "tok/rebuild.py"
    if not rebuild.exists():
        return issues
    text = rebuild.read_text(encoding="utf-8")
    if '"result":' in text and '"advisory_result":' not in text:
        issues.append((WARN, str(rebuild), 'TOK rebuild uses "result" — should be "advisory_result" to avoid Lane-1 ambiguity'))
    return issues


def check_lane2_authority_leakage(root: Path) -> List[Tuple[str, str, str]]:
    """
    Flag: Lane-2 source files emitting PASS/DROP verdicts as authority.
    Checks ssmt/ and tok/ only.
    """
    issues = []
    lane2_dirs = [root / "ssmt", root / "tok"]
    # Look for "verdict": "PASS" or "verdict": "DROP" being emitted (not just referenced)
    verdict_pattern = re.compile(r'"verdict"\s*:\s*"(PASS|DROP)"')
    for d in lane2_dirs:
        if not d.exists():
            continue
        for p in d.rglob("*.py"):
            if "__pycache__" in str(p) or "test_" in p.name:
                continue
            for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
                if verdict_pattern.search(line) and "authority" not in line.lower():
                    issues.append((WARN, str(p), f"line {i}: potential Lane-2 verdict field — verify advisory_only: {line.strip()}"))
    return issues


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_lint(root: Path) -> int:
    all_issues: List[Tuple[str, str, str]] = []

    checks = [
        ("Float epoch timestamps in authority paths", check_float_timestamp_in_authority_paths),
        ("Old float metric field names", check_old_float_metric_fields),
        ("Unsafe .blake2b write_text()", check_unsafe_blake2b_write_text),
        ("Duplicate canonical helpers", check_duplicate_canonical_helpers),
        ("Forbidden audit event types", check_forbidden_audit_event_types),
        ("Missing audit required fields", check_missing_audit_required_fields),
        ("Lane-2 authority leakage", check_lane2_authority_leakage),
        ("TOK advisory_result naming", check_tok_advisory_result_naming),
    ]

    fail_count = 0
    warn_count = 0

    for name, fn in checks:
        issues = fn(root)
        all_issues.extend(issues)
        fails = [x for x in issues if x[0] == FAIL]
        warns = [x for x in issues if x[0] == WARN]
        fail_count += len(fails)
        warn_count += len(warns)

        if not issues:
            print(f"  [PASS] {name}")
        else:
            level = FAIL if fails else WARN
            print(f"  [{level}] {name}: {len(issues)} issue(s)")
            for sev, path, msg in issues:
                print(f"         [{sev}] {path}: {msg}")

    print()
    if fail_count > 0:
        print(f"CANON LINT: FAIL — {fail_count} FAIL, {warn_count} WARN")
        return 1
    elif warn_count > 0:
        print(f"CANON LINT: WARN — 0 FAIL, {warn_count} WARN")
        return 0
    else:
        print("CANON LINT: PASS")
        return 0


def main():
    ap = argparse.ArgumentParser(description="PH6 Canon Linter")
    ap.add_argument("--path", default="ph6", help="Root path to scan (default: ph6/)")
    args = ap.parse_args()
    root = Path(args.path)
    if not root.exists():
        print(f"ERROR: path {root} does not exist")
        sys.exit(1)
    sys.exit(run_lint(root))


if __name__ == "__main__":
    main()
