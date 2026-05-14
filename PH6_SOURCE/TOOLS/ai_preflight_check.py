#!/usr/bin/env python3
"""
ai_preflight_check.py — PH6 AI Session Preflight Check

Lane:      2 (Advisory tooling — does not modify any authority path)
Authority: ZERO
Schema:    ph6.governance.preflight_report.v1

Run before any AI session that modifies PH6 code. Checks:
  1. All governance files present and parseable
  2. Governance manifest valid
  3. Stop-ship gates (informational — does not block unless UNKNOWN gate found)
  4. Canonical hash algorithm confirmed
  5. Lane-2 authority confirmed ZERO
  6. Forbidden terms registry loaded and non-empty
  7. Schema lock registry loaded and non-empty
  8. RSYNC priority confirmed ABSOLUTE

Exit codes:
  0 — PREFLIGHT PASS
  1 — PREFLIGHT FAIL (one or more CRITICAL checks failed)

Usage:
  python3 PH6_SOURCE/TOOLS/ai_preflight_check.py
  python3 PH6_SOURCE/TOOLS/ai_preflight_check.py --governance-dir /path/to/GOVERNANCE
  python3 PH6_SOURCE/TOOLS/ai_preflight_check.py --report-out preflight.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_ID = "ph6.governance.preflight_report.v1"


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_json(path: Path) -> tuple[dict | None, str | None]:
    if not path.exists():
        return None, f"file not found: {path}"
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except json.JSONDecodeError as e:
        return None, f"JSON parse error in {path}: {e}"


def check_governance_files_present(gov_dir: Path) -> dict:
    required = {
        "forbidden_terms_registry": gov_dir / "forbidden_terms_registry.json",
        "schema_lock_registry":     gov_dir / "schema_lock_registry.json",
        "governance_manifest":      gov_dir / "governance_manifest.json",
    }
    missing = [name for name, p in required.items() if not p.exists()]
    if missing:
        return {
            "result": "FAIL",
            "severity": "CRITICAL",
            "detail": f"Missing governance files: {missing}",
        }
    return {"result": "PASS", "detail": f"All {len(required)} governance files present"}


def check_manifest_valid(manifest: dict | None, err: str | None) -> dict:
    if err:
        return {"result": "FAIL", "severity": "CRITICAL", "detail": err}
    required_fields = [
        "schema", "version", "canonical_hash_algorithm", "canonical_commit_marker",
        "lane2_authority", "rsync_priority", "minimum_valid_test_frames",
        "forbidden_fields", "stop_ship_gates", "lane_authority_map",
    ]
    missing = [f for f in required_fields if f not in manifest]
    if missing:
        return {
            "result": "FAIL",
            "severity": "CRITICAL",
            "detail": f"governance_manifest.json missing required fields: {missing}",
        }
    if manifest.get("schema") != "ph6.governance.manifest.v1":
        return {
            "result": "FAIL",
            "severity": "CRITICAL",
            "detail": f"manifest schema mismatch: got {manifest.get('schema')}",
        }
    return {"result": "PASS", "detail": f"manifest v{manifest.get('version')} valid, schema confirmed"}


def check_canonical_hash(manifest: dict | None) -> dict:
    if not manifest:
        return {"result": "FAIL", "severity": "CRITICAL", "detail": "manifest unavailable"}
    algo = manifest.get("canonical_hash_algorithm", "")
    if algo != "BLAKE2b-256":
        return {
            "result": "FAIL",
            "severity": "CRITICAL",
            "detail": f"canonical_hash_algorithm is '{algo}', expected 'BLAKE2b-256'",
        }
    marker = manifest.get("canonical_commit_marker", "")
    if marker != ".blake2b":
        return {
            "result": "FAIL",
            "severity": "CRITICAL",
            "detail": f"canonical_commit_marker is '{marker}', expected '.blake2b'",
        }
    return {"result": "PASS", "detail": "canonical_hash_algorithm=BLAKE2b-256, commit_marker=.blake2b"}


def check_lane2_authority(manifest: dict | None) -> dict:
    if not manifest:
        return {"result": "FAIL", "severity": "CRITICAL", "detail": "manifest unavailable"}
    lane2 = manifest.get("lane2_authority", "")
    if lane2 != "ZERO":
        return {
            "result": "FAIL",
            "severity": "CRITICAL",
            "detail": f"lane2_authority is '{lane2}', must be 'ZERO'",
        }
    return {"result": "PASS", "detail": "lane2_authority=ZERO confirmed"}


def check_rsync_priority(manifest: dict | None) -> dict:
    if not manifest:
        return {"result": "FAIL", "severity": "CRITICAL", "detail": "manifest unavailable"}
    prio = manifest.get("rsync_priority", "")
    if prio != "ABSOLUTE":
        return {
            "result": "FAIL",
            "severity": "CRITICAL",
            "detail": f"rsync_priority is '{prio}', must be 'ABSOLUTE'",
        }
    return {"result": "PASS", "detail": "rsync_priority=ABSOLUTE confirmed"}


def check_min_test_frames(manifest: dict | None) -> dict:
    if not manifest:
        return {"result": "FAIL", "severity": "CRITICAL", "detail": "manifest unavailable"}
    val = manifest.get("minimum_valid_test_frames")
    if val != 300:
        return {
            "result": "FAIL",
            "severity": "CRITICAL",
            "detail": f"minimum_valid_test_frames is {val}, must be 300",
        }
    return {"result": "PASS", "detail": "minimum_valid_test_frames=300 confirmed"}


def check_forbidden_terms_registry(reg: dict | None, err: str | None) -> dict:
    if err:
        return {"result": "FAIL", "severity": "CRITICAL", "detail": err}
    entries = reg.get("entries", [])
    if not entries:
        return {"result": "FAIL", "severity": "CRITICAL", "detail": "forbidden_terms_registry has no entries"}
    critical = [e["id"] for e in entries if e.get("severity") == "CRITICAL"]
    return {
        "result": "PASS",
        "detail": f"{len(entries)} entries loaded ({len(critical)} CRITICAL)",
        "entry_count": len(entries),
        "critical_count": len(critical),
    }


def check_schema_lock_registry(reg: dict | None, err: str | None) -> dict:
    if err:
        return {"result": "FAIL", "severity": "CRITICAL", "detail": err}
    schemas = reg.get("locked_schemas", [])
    if not schemas:
        return {"result": "FAIL", "severity": "CRITICAL", "detail": "schema_lock_registry has no locked schemas"}
    lane1 = [s["schema_id"] for s in schemas if s.get("lane") == 1]
    lane2 = [s["schema_id"] for s in schemas if s.get("lane") == 2]
    return {
        "result": "PASS",
        "detail": f"{len(schemas)} schemas locked (Lane-1: {len(lane1)}, Lane-2: {len(lane2)})",
        "schema_count": len(schemas),
        "lane1_count": len(lane1),
        "lane2_count": len(lane2),
    }


def check_stop_ship_gates(manifest: dict | None) -> dict:
    if not manifest:
        return {"result": "FAIL", "severity": "CRITICAL", "detail": "manifest unavailable"}
    gates = manifest.get("stop_ship_gates", [])
    open_gates = [g for g in gates if g.get("status") == "OPEN"]
    return {
        "result": "PASS",
        "detail": f"{len(open_gates)} open STOP-SHIP gate(s): {[g['id'] for g in open_gates]}",
        "open_gates": [{"id": g["id"], "description": g["description"]} for g in open_gates],
        "note": "STOP-SHIP gates are informational in preflight — they block production release, not AI session work",
    }


def run_preflight(gov_dir: Path) -> dict:
    manifest, manifest_err = _load_json(gov_dir / "governance_manifest.json")
    ft_reg, ft_err       = _load_json(gov_dir / "forbidden_terms_registry.json")
    sl_reg, sl_err       = _load_json(gov_dir / "schema_lock_registry.json")

    checks: dict[str, dict] = {}
    checks["governance_files_present"]   = check_governance_files_present(gov_dir)
    checks["manifest_valid"]             = check_manifest_valid(manifest, manifest_err)
    checks["canonical_hash_algorithm"]   = check_canonical_hash(manifest)
    checks["lane2_authority_zero"]       = check_lane2_authority(manifest)
    checks["rsync_priority_absolute"]    = check_rsync_priority(manifest)
    checks["minimum_test_frames_300"]    = check_min_test_frames(manifest)
    checks["forbidden_terms_registry"]   = check_forbidden_terms_registry(ft_reg, ft_err)
    checks["schema_lock_registry"]       = check_schema_lock_registry(sl_reg, sl_err)
    checks["stop_ship_gates"]            = check_stop_ship_gates(manifest)

    critical_fails = [k for k, v in checks.items() if v.get("result") == "FAIL" and v.get("severity") == "CRITICAL"]
    overall = "FAIL" if critical_fails else "PASS"

    return {
        "schema":            SCHEMA_ID,
        "generated_at_utc":  _utc_now(),
        "governance_dir":    str(gov_dir),
        "overall_result":    overall,
        "critical_fail_count": len(critical_fails),
        "checks":            checks,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="PH6 AI Session Preflight Check")
    ap.add_argument(
        "--governance-dir",
        default=str(Path(__file__).resolve().parent.parent / "GOVERNANCE"),
        help="Path to GOVERNANCE directory (default: ../GOVERNANCE relative to this script)",
    )
    ap.add_argument("--report-out", help="Write JSON report to this file (default: stdout)")
    ap.add_argument("--quiet", action="store_true", help="Suppress human-readable output")
    args = ap.parse_args()

    gov_dir = Path(args.governance_dir)
    report = run_preflight(gov_dir)

    json_out = json.dumps(report, indent=2, sort_keys=False)

    if args.report_out:
        Path(args.report_out).write_text(json_out + "\n", encoding="utf-8")
    else:
        if not args.quiet:
            print(json_out)

    if not args.quiet:
        result = report["overall_result"]
        fails  = report["critical_fail_count"]
        label  = f"PREFLIGHT {result}"
        if fails:
            label += f" — {fails} CRITICAL check(s) failed"
        print(f"\n{label}", file=sys.stderr)

    return 0 if report["overall_result"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
