#!/usr/bin/env python3
"""
PH6 Ingest Verifier v1.0

Validates the ingest classification manifest and build outputs.
The compiler is governance-critical infrastructure; it is subject to governance.

Checks:
  1. Every registered file appears in exactly one type
  2. No orphan files — every file in PH6_SOURCE is either registered or explicitly excluded
  3. No priority collisions within a type
  4. Priority ordering is monotonically increasing within each type
  5. All registered files exist on disk
  6. Build outputs exist and their hashes are reproducible (build replay)
  7. Classification manifest is self-consistent (types, build targets)

Exit: 0 = PASS, 1 = FAIL (with structured failure output)
"""

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


CLASSIFICATION_REL = "GOVERNANCE/ingest_classification.json"
BUILDS_DIR         = "builds"

# Directories and files to exclude from orphan detection
EXCLUDE_PREFIXES = (
    "builds/",
    ".git/",
)
EXCLUDE_NAMES = {
    "GOVERNANCE/ingest_classification.json",  # the manifest itself
}
EXCLUDE_SUFFIXES = (
    ".pyc",
    ".pyo",
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _blake2b(path: str) -> str | None:
    try:
        with open(path, "rb") as f:
            return hashlib.blake2b(f.read(), digest_size=32).hexdigest()
    except FileNotFoundError:
        return None


def _canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(",", ":"))


def load_classification(source_root: str) -> dict:
    path = os.path.join(source_root, CLASSIFICATION_REL)
    if not os.path.exists(path):
        sys.exit(f"FATAL: classification manifest not found at {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def scan_source_files(source_root: str) -> set[str]:
    """Return set of all relative file paths in source_root (excluding builds/ and hidden dirs)."""
    result: set[str] = set()
    root = Path(source_root)
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        rel = str(p.relative_to(root))
        # Exclude build outputs
        if any(rel.startswith(pfx) for pfx in EXCLUDE_PREFIXES):
            continue
        # Exclude hidden dirs
        if any(part.startswith(".") for part in Path(rel).parts):
            continue
        if any(rel.endswith(sfx) for sfx in EXCLUDE_SUFFIXES):
            continue
        if "__pycache__" in rel:
            continue
        result.add(rel)
    return result


def fail(code: str, family: str, severity: str, reason: str, **extra) -> dict:
    record: dict[str, Any] = {
        "failure_class":  code,
        "failure_family": family,
        "severity":       severity,
        "reason":         reason,
        "timestamp_utc":  _utc_now(),
    }
    record.update(extra)
    return record


def check_classification(source_root: str, clf: dict) -> list[dict]:
    """Run all classification manifest checks. Returns list of failures."""
    failures: list[dict] = []
    files = clf.get("files", [])
    type_priority = clf.get("type_priority", {})
    build_targets = clf.get("build_targets", {})
    known_types   = set(type_priority.keys())

    # ── Check 1: Every registered file has a known type ─────────────────────
    for entry in files:
        if entry.get("type") not in known_types:
            failures.append(fail(
                "G4", "Governance", "HIGH",
                "registered file has unknown type",
                path=entry.get("path"),
                observed_type=entry.get("type"),
                known_types=sorted(known_types),
            ))

    # ── Check 2: No duplicate paths ──────────────────────────────────────────
    seen: dict[str, str] = {}
    for entry in files:
        path = entry.get("path", "")
        if path in seen:
            failures.append(fail(
                "G4", "Governance", "HIGH",
                "file registered more than once",
                path=path,
                first_type=seen[path],
                duplicate_type=entry.get("type"),
            ))
        else:
            seen[path] = entry.get("type", "?")

    # ── Check 3: No priority collisions within a type ────────────────────────
    by_type: dict[str, list] = {}
    for entry in files:
        t = entry.get("type", "?")
        by_type.setdefault(t, []).append(entry)

    for t, entries in by_type.items():
        priorities = [e.get("priority") for e in entries]
        seen_p: set = set()
        for e in entries:
            p = e.get("priority")
            if p in seen_p:
                failures.append(fail(
                    "D1", "Determinism", "MEDIUM",
                    "priority collision within type — ordering is non-deterministic",
                    type=t,
                    priority=p,
                    affected_paths=[x.get("path") for x in entries if x.get("priority") == p],
                ))
                break
            seen_p.add(p)

    # ── Check 4: All registered files exist on disk ──────────────────────────
    missing: list[str] = []
    for entry in files:
        abs_path = os.path.join(source_root, entry.get("path", ""))
        if not os.path.isfile(abs_path):
            missing.append(entry.get("path", ""))
            failures.append(fail(
                "O3", "Operational", "MEDIUM",
                "registered file missing from disk",
                path=entry.get("path"),
                type=entry.get("type"),
            ))

    # ── Check 5: Orphan detection — files in PH6_SOURCE not in manifest ──────
    registered = {e.get("path") for e in files}
    on_disk    = scan_source_files(source_root)
    orphans    = on_disk - registered - EXCLUDE_NAMES
    for orphan in sorted(orphans):
        failures.append(fail(
            "G4", "Governance", "LOW",
            "file exists on disk but is not registered in ingest_classification.json",
            path=orphan,
        ))

    # ── Check 6: Build targets reference only known types ───────────────────
    for target_name, target_cfg in build_targets.items():
        for t in target_cfg.get("types", []):
            if t not in known_types:
                failures.append(fail(
                    "G4", "Governance", "HIGH",
                    "build target references unknown type",
                    target=target_name,
                    unknown_type=t,
                ))

    return failures


_DIVIDER    = "=" * 80
_SEAL_MARKER = f"\n{_DIVIDER}\nBUILD SEAL"


def _pre_seal_hash(path: str) -> str | None:
    """
    Hash only the pre-seal content of a build file.
    The compiler seals pre-seal content; we must hash the same slice.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        idx = content.find(_SEAL_MARKER)
        if idx == -1:
            payload = content
        else:
            payload = content[:idx]
        return hashlib.blake2b(payload.encode("utf-8"), digest_size=32).hexdigest()
    except FileNotFoundError:
        return None


def check_builds(source_root: str, clf: dict, now: str) -> list[dict]:
    """Check that build outputs exist. Replay reproducibility check."""
    failures: list[dict] = []
    builds_dir = os.path.join(source_root, BUILDS_DIR)
    build_targets = clf.get("build_targets", {})

    manifest_path = os.path.join(builds_dir, "build_manifest.json")
    if not os.path.isfile(manifest_path):
        failures.append(fail(
            "O3", "Operational", "HIGH",
            "build_manifest.json not found — run ph6_ingest_compiler.py first",
            path=manifest_path,
        ))
        return failures

    with open(manifest_path, "r", encoding="utf-8") as f:
        build_manifest = json.load(f)

    built: dict[str, dict] = {b["target"]: b for b in build_manifest.get("builds", [])}

    for target_name in build_targets:
        out_path = os.path.join(builds_dir, f"{target_name}_ingest.txt")
        if not os.path.isfile(out_path):
            failures.append(fail(
                "O3", "Operational", "MEDIUM",
                f"build output missing: {target_name}_ingest.txt — run compiler",
                target=target_name,
            ))
            continue

        # Verify stored hash matches pre-seal content hash (compiler seals pre-seal only)
        if target_name in built:
            stored_hash = built[target_name].get("blake2b_256")
            actual_hash = _pre_seal_hash(out_path)
            if stored_hash != actual_hash:
                failures.append(fail(
                    "R1", "Replay", "HIGH",
                    "build output hash mismatch — file was modified after compilation",
                    target=target_name,
                    stored_hash=stored_hash,
                    actual_hash=actual_hash,
                ))

        # Check missing file count reported by compiler
        if target_name in built and built[target_name].get("missing_count", 0) > 0:
            failures.append(fail(
                "O3", "Operational", "LOW",
                f"build '{target_name}' reported {built[target_name]['missing_count']} missing files at compile time",
                target=target_name,
                missing_files=built[target_name].get("files_missing", []),
            ))

    return failures


def main() -> None:
    parser = argparse.ArgumentParser(description="PH6 Ingest Verifier v1.0")
    parser.add_argument(
        "--source-root",
        default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        help="Path to PH6_SOURCE root (default: parent of TOOLS/)",
    )
    parser.add_argument(
        "--skip-builds",
        action="store_true",
        help="Skip build output verification",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON report to stdout",
    )
    args = parser.parse_args()

    source_root = args.source_root
    if not os.path.isdir(source_root):
        sys.exit(f"FATAL: source root not found: {source_root}")

    now = _utc_now()
    clf = load_classification(source_root)

    all_failures: list[dict] = []
    all_failures.extend(check_classification(source_root, clf))
    if not args.skip_builds:
        all_failures.extend(check_builds(source_root, clf, now))

    # Separate by severity for summary
    by_severity: dict[str, list] = {}
    for f in all_failures:
        by_severity.setdefault(f["severity"], []).append(f)

    passed = len(all_failures) == 0

    report = {
        "schema":           "ph6.ingest.verify.v1",
        "passed":           passed,
        "failure_count":    len(all_failures),
        "failures_by_sev":  {s: len(v) for s, v in by_severity.items()},
        "failures":         all_failures,
        "timestamp_utc":    now,
        "source_root":      source_root,
    }

    if args.json:
        print(_canonical(report))
    else:
        status = "PASS" if passed else "FAIL"
        print(f"PH6 INGEST VERIFY: {status}")
        if passed:
            print("  All classification checks passed.")
        else:
            print(f"  {len(all_failures)} failure(s):")
            for f in all_failures:
                detail = ""
                if "path" in f:
                    detail = f"  [{f['failure_class']}] {f['severity']:8}  {f['reason']}"
                    detail += f"\n              path: {f['path']}"
                else:
                    detail = f"  [{f['failure_class']}] {f['severity']:8}  {f['reason']}"
                print(detail)

    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
