#!/usr/bin/env python3
"""
PH6 / CRAM System Status Check

Read-only governance/evidence/tooling status test.

This script:
- validates governance JSON
- prints campaign state
- checks unauthorized CLOSED states
- checks expected C09-C13 campaign presence
- inventories validation artifacts
- scans open material
- scans forbidden authority drift terms with classification-needed status
- optionally compile-checks Python trees
- writes JSON and Markdown reports

It does not:
- delete evidence
- rerun campaigns
- close campaigns
- declare production clearance
- mutate governance state
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple


ROOT = Path.cwd()
GOV_DIR = ROOT / "PH6_SOURCE" / "GOVERNANCE"
CLOSURE_PATH = GOV_DIR / "closure_status.json"
MATRIX_PATH = GOV_DIR / "evidence_campaign_matrix.json"
REPORT_JSON = GOV_DIR / "ph6_system_status_report.json"
REPORT_MD = GOV_DIR / "ph6_system_status_report.md"

VALIDATION_RUNS = ROOT / "ph6" / "cram_pu" / "validation_runs"
LOGS_DIR = ROOT / "ph6" / "cram_pu" / "logs"

EXPECTED_CAMPAIGNS = [
    "C09_12000_STAGED_LOCAL_PI",
    "C10_6000_15FPS_SLOW_ABSORPTION",
    "C11_6000_30FPS_STANDARD_ABSORPTION",
    "C12_3000_50FPS_HIGH_RATE_ABSORPTION",
    "C13",
]

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


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def run_cmd(cmd: List[str], timeout: int = 60) -> Tuple[int, str, str]:
    try:
        p = subprocess.run(
            cmd,
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=timeout,
        )
        return p.returncode, p.stdout.strip(), p.stderr.strip()
    except FileNotFoundError as e:
        return 127, "", str(e)
    except subprocess.TimeoutExpired as e:
        return 124, e.stdout or "", e.stderr or "timeout"


def load_json(path: Path) -> Tuple[bool, Any, str]:
    try:
        return True, json.loads(path.read_text(encoding="utf-8")), ""
    except Exception as e:
        return False, None, str(e)


def iter_text_files() -> List[Path]:
    out: List[Path] = []
    for root in SCAN_ROOTS:
        if not root.exists():
            continue
        for p in root.rglob("*"):
            if p.is_file() and p.suffix.lower() in TEXT_SUFFIXES:
                out.append(p)
    return out


def scan_pattern(pattern: re.Pattern, limit: int = 300) -> List[Dict[str, Any]]:
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
                    "classification": "CLASSIFICATION_REQUIRED",
                })
                if len(hits) >= limit:
                    return hits
    return hits


def inventory_artifacts() -> Dict[str, Any]:
    required_names = [
        "campaign_manifest.json",
        "result_set_hash.txt",
        "artifact_hashes.blake2b",
        "final_report.md",
        "failure_register.json",
    ]

    files: List[str] = []
    by_name = {name: 0 for name in required_names}

    if VALIDATION_RUNS.exists():
        for p in VALIDATION_RUNS.rglob("*"):
            if p.is_file():
                rel = str(p.relative_to(ROOT))
                files.append(rel)
                if p.name in by_name:
                    by_name[p.name] += 1

    missing_classes = [name for name, count in by_name.items() if count == 0]

    return {
        "validation_runs_dir_exists": VALIDATION_RUNS.exists(),
        "logs_dir_exists": LOGS_DIR.exists(),
        "artifact_inventory_count": len(files),
        "required_artifact_name_counts": by_name,
        "missing_artifact_classes": missing_classes,
        "sample_artifacts": files[:100],
    }


def check_campaign_integrity(closure_data: Any, matrix_data: Any) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "campaigns_block_exists": False,
        "campaign_count": 0,
        "known_campaigns_present": {},
        "unauthorized_closed_states": [],
        "misplaced_campaign_top_level_entries": [],
        "campaign_states": {},
    }

    if not isinstance(closure_data, dict):
        return result

    campaigns = closure_data.get("campaigns", {})
    result["campaigns_block_exists"] = isinstance(campaigns, dict)

    if not isinstance(campaigns, dict):
        return result

    result["campaign_count"] = len(campaigns)

    for expected in EXPECTED_CAMPAIGNS:
        present = expected in campaigns or any(k.startswith(expected) for k in campaigns.keys())
        result["known_campaigns_present"][expected] = present

    for k, v in campaigns.items():
        if isinstance(v, dict):
            state = v.get("state")
            closed = v.get("closed")
            result["campaign_states"][k] = {
                "state": state,
                "closed": closed,
            }
            if closed is True:
                required = ["reviewer", "reviewed_at_utc", "closure_decision", "closed_at_utc"]
                missing = [r for r in required if not v.get(r)]
                if missing:
                    result["unauthorized_closed_states"].append({
                        "campaign": k,
                        "missing": missing,
                    })
        else:
            result["campaign_states"][k] = {
                "malformed_type": type(v).__name__,
            }

    for src_name, data in [("closure_status", closure_data), ("evidence_campaign_matrix", matrix_data)]:
        if isinstance(data, dict):
            for k in data.keys():
                if k.startswith("C") and k != "campaigns":
                    result["misplaced_campaign_top_level_entries"].append({
                        "source": src_name,
                        "key": k,
                    })

    return result


def compile_check() -> Dict[str, Any]:
    targets = [p for p in ["ph6", "PH6_SOURCE", "scripts", "tools", "tests"] if (ROOT / p).exists()]
    if not targets:
        return {
            "ran": False,
            "returncode": None,
            "stdout_tail": "",
            "stderr_tail": "No compile targets found.",
        }

    rc, out, err = run_cmd([sys.executable, "-m", "compileall", *targets], timeout=180)
    return {
        "ran": True,
        "returncode": rc,
        "stdout_tail": out[-4000:],
        "stderr_tail": err[-4000:],
    }


def determine_status(report: Dict[str, Any]) -> str:
    if not report["governance"]["closure_status_json_valid"]:
        return "FAIL_GOVERNANCE"
    if not report["governance"]["evidence_campaign_matrix_json_valid"]:
        return "FAIL_GOVERNANCE"
    if report["campaign_integrity"]["unauthorized_closed_states"]:
        return "FAIL_GOVERNANCE"
    if report["campaign_integrity"]["misplaced_campaign_top_level_entries"]:
        return "FAIL_GOVERNANCE"

    known = report["campaign_integrity"]["known_campaigns_present"]
    missing_known = [k for k, present in known.items() if not present]
    if missing_known:
        return "FAIL_EVIDENCE"

    if report["artifact_integrity"]["missing_artifact_classes"]:
        return "PASS_WITH_WARNINGS"

    if report["tooling"]["compileall_result"].get("returncode") not in (0, None):
        return "FAIL_TOOLING"

    if report["scans"]["open_material_hit_count"] or report["scans"]["forbidden_authority_drift_hit_count"]:
        return "PASS_WITH_WARNINGS"

    return "PASS"


def write_markdown(report: Dict[str, Any]) -> str:
    ci = report["campaign_integrity"]
    ai = report["artifact_integrity"]
    scans = report["scans"]
    tooling = report["tooling"]

    lines: List[str] = []
    lines.append("# PH6 / CRAM — System Status Report")
    lines.append("")
    lines.append(f"Generated UTC: {report['generated_at_utc']}")
    lines.append(f"Overall Status: **{report['overall_status']}**")
    lines.append("")
    lines.append("## Governance")
    lines.append("")
    lines.append(f"- closure_status.json valid: {report['governance']['closure_status_json_valid']}")
    lines.append(f"- evidence_campaign_matrix.json valid: {report['governance']['evidence_campaign_matrix_json_valid']}")
    lines.append(f"- campaigns block exists: {ci['campaigns_block_exists']}")
    lines.append(f"- campaign count: {ci['campaign_count']}")
    lines.append("")
    lines.append("## Known Campaign Presence")
    lines.append("")
    for k, v in ci["known_campaigns_present"].items():
        lines.append(f"- {k}: {v}")
    lines.append("")
    lines.append("## Unauthorized CLOSED States")
    lines.append("")
    if ci["unauthorized_closed_states"]:
        for item in ci["unauthorized_closed_states"]:
            lines.append(f"- {item['campaign']}: missing {item['missing']}")
    else:
        lines.append("- None detected.")
    lines.append("")
    lines.append("## Evidence Artifact Inventory")
    lines.append("")
    lines.append(f"- validation_runs exists: {ai['validation_runs_dir_exists']}")
    lines.append(f"- logs exists: {ai['logs_dir_exists']}")
    lines.append(f"- artifact count: {ai['artifact_inventory_count']}")
    lines.append(f"- missing artifact classes: {ai['missing_artifact_classes']}")
    lines.append("")
    lines.append("## Scans")
    lines.append("")
    lines.append(f"- open material hits: {scans['open_material_hit_count']}")
    lines.append(f"- forbidden authority drift hits: {scans['forbidden_authority_drift_hit_count']}")
    lines.append("")
    lines.append("## Tooling")
    lines.append("")
    cr = tooling["compileall_result"]
    lines.append(f"- compileall ran: {cr.get('ran')}")
    lines.append(f"- compileall returncode: {cr.get('returncode')}")
    lines.append("")
    lines.append("## Recommended Next Action")
    lines.append("")
    lines.append(f"- {report['recommended_next_action']}")
    lines.append("")
    lines.append("## Evidence Deletion")
    lines.append("")
    lines.append("- Evidence deleted: NO")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    GOV_DIR.mkdir(parents=True, exist_ok=True)

    git_rc, git_head, git_err = run_cmd(["git", "rev-parse", "--short", "HEAD"])
    status_rc, git_status, status_err = run_cmd(["git", "status", "--short"])

    closure_valid, closure_data, closure_err = load_json(CLOSURE_PATH)
    matrix_valid, matrix_data, matrix_err = load_json(MATRIX_PATH)

    campaign_integrity = check_campaign_integrity(
        closure_data if closure_valid else None,
        matrix_data if matrix_valid else None,
    )

    artifact_integrity = inventory_artifacts()
    open_hits = scan_pattern(OPEN_MATERIAL_PATTERN)
    forbidden_hits = scan_pattern(FORBIDDEN_AUTHORITY_PATTERN)
    compile_result = compile_check()

    report: Dict[str, Any] = {
        "schema": "ph6.system_status_report.v1",
        "generated_at_utc": utc_now(),
        "repository": {
            "root": str(ROOT),
            "git_available": git_rc == 0,
            "git_head": git_head if git_rc == 0 else None,
            "git_error": git_err if git_rc != 0 else None,
            "git_dirty_status": git_status,
        },
        "governance": {
            "closure_status_json_valid": closure_valid,
            "closure_status_error": closure_err,
            "evidence_campaign_matrix_json_valid": matrix_valid,
            "evidence_campaign_matrix_error": matrix_err,
        },
        "campaign_integrity": campaign_integrity,
        "artifact_integrity": artifact_integrity,
        "scans": {
            "open_material_hit_count": len(open_hits),
            "open_material_sample": open_hits[:50],
            "forbidden_authority_drift_hit_count": len(forbidden_hits),
            "forbidden_authority_drift_sample": forbidden_hits[:50],
        },
        "tooling": {
            "compileall_result": compile_result,
        },
        "evidence_deleted": False,
    }

    report["overall_status"] = determine_status(report)

    if report["overall_status"] == "PASS":
        report["recommended_next_action"] = "Proceed to whole-system governance audit or human review queue."
    elif report["overall_status"] == "PASS_WITH_WARNINGS":
        report["recommended_next_action"] = "Review warnings, classify scan hits, and decide whether targeted fixes are needed."
    elif report["overall_status"] == "FAIL_GOVERNANCE":
        report["recommended_next_action"] = "Stop. Repair governance JSON, misplaced campaign entries, or unauthorized CLOSED states before continuing."
    elif report["overall_status"] == "FAIL_EVIDENCE":
        report["recommended_next_action"] = "Stop. Verify expected campaign evidence and artifact integrity before continuing."
    elif report["overall_status"] == "FAIL_TOOLING":
        report["recommended_next_action"] = "Stop. Review compile errors and fix only targeted syntax/path issues."
    else:
        report["recommended_next_action"] = "Review report manually."

    REPORT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    REPORT_MD.write_text(write_markdown(report), encoding="utf-8")

    print("PH6 system status check complete.")
    print(f"Overall status: {report['overall_status']}")
    print(f"JSON report: {REPORT_JSON}")
    print(f"Markdown report: {REPORT_MD}")
    print("Evidence deleted: NO")
    print(f"Recommended next action: {report['recommended_next_action']}")

    return 0 if report["overall_status"] in {"PASS", "PASS_WITH_WARNINGS"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
