#!/usr/bin/env python3
"""
pseudo_soso_agent.py

PH6 local PSEUDO + SoSo agent.

PSEUDO:
- deterministic authority checker
- emits PASS / HOLD / BLOCK
- evaluates repo state, tests, missing files, package health

SoSo:
- advisory-only pattern observer
- detects drift patterns, repeated failures, mismatch signatures
- NEVER controls PASS/DROP
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import pathlib
import subprocess
import sys
from typing import Any, Dict, List


APP_DIR = pathlib.Path.home() / ".ph6_pseudo_soso"
MEMORY_DIR = APP_DIR / "memory"
REPORT_DIR = APP_DIR / "reports"
CHECKPOINT_DIR = APP_DIR / "checkpoints"

MEMORY_FILE = MEMORY_DIR / "soso_memory.jsonl"


FRAME_FILTER = pathlib.Path.home() / "frame_filter"
STORAGE_MONITOR = pathlib.Path.home() / "ph6_storage_monitor"

SYSTEM_PYTHON = "/usr/bin/python3"


PSEUDO_RULES = [
    "PSEUDO is deterministic authority.",
    "PSEUDO may emit PASS, HOLD, or BLOCK.",
    "PSEUDO must not use AI judgment for authority.",
    "PSEUDO must not accept SoSo advisory notes as verdict inputs.",
    "PSEUDO must preserve CRAM atomic write doctrine.",
    "PSEUDO must preserve RSYNC Priority Zero.",
]


SOSO_RULES = [
    "SoSo is advisory only.",
    "SoSo has Authority NONE.",
    "SoSo may detect patterns, drift, and repeated issues.",
    "SoSo may not emit PASS/DROP as authority.",
    "SoSo may not modify PSEUDO thresholds.",
    "SoSo may not become replay dependency.",
]


DANGEROUS_PATTERNS = [
    "rm -rf /",
    "sudo rm -rf /",
    "mkfs",
    "dd if=",
    "chmod -R 777 /",
    "chown -R /",
    ":(){",
]


def now() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def ensure_dirs() -> None:
    for p in [APP_DIR, MEMORY_DIR, REPORT_DIR, CHECKPOINT_DIR]:
        p.mkdir(parents=True, exist_ok=True)


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def hash_obj(obj: Any) -> str:
    h = hashlib.blake2b(digest_size=32)
    h.update(canonical_json(obj).encode("utf-8"))
    return h.hexdigest()


def run(cmd: List[str], cwd: pathlib.Path | None = None, timeout: int = 30) -> Dict[str, Any]:
    try:
        p = subprocess.run(
            cmd,
            cwd=str(cwd) if cwd else None,
            text=True,
            capture_output=True,
            timeout=timeout,
        )
        return {
            "cmd": cmd,
            "cwd": str(cwd) if cwd else None,
            "returncode": p.returncode,
            "stdout": p.stdout[-8000:],
            "stderr": p.stderr[-8000:],
        }
    except Exception as e:
        return {
            "cmd": cmd,
            "cwd": str(cwd) if cwd else None,
            "returncode": 999,
            "stdout": "",
            "stderr": repr(e),
        }


def append_memory(entry: Dict[str, Any]) -> None:
    ensure_dirs()
    entry = dict(entry)
    entry["ts"] = now()
    with MEMORY_FILE.open("a", encoding="utf-8") as f:
        f.write(canonical_json(entry) + "\n")


def recent_memory(limit: int = 12) -> List[Dict[str, Any]]:
    if not MEMORY_FILE.exists():
        return []

    lines = MEMORY_FILE.read_text(encoding="utf-8", errors="replace").splitlines()
    out = []

    for line in lines[-limit:]:
        try:
            out.append(json.loads(line))
        except Exception:
            continue

    return out


def save_report(report: Dict[str, Any]) -> pathlib.Path:
    ensure_dirs()
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = REPORT_DIR / f"pseudo_soso_report_{stamp}.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    latest = CHECKPOINT_DIR / "latest.json"
    latest.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    return path


def git_status(path: pathlib.Path) -> Dict[str, Any]:
    if not path.exists():
        return {
            "exists": False,
            "path": str(path),
            "status_short": "MISSING",
        }

    result = run(["git", "status", "--short"], cwd=path)
    return {
        "exists": True,
        "path": str(path),
        "returncode": result["returncode"],
        "status_short": result["stdout"].strip(),
        "stderr": result["stderr"].strip(),
    }


def file_exists(path: pathlib.Path, names: List[str]) -> Dict[str, bool]:
    return {name: (path / name).exists() for name in names}


def pseudo_collect_state() -> Dict[str, Any]:
    frame_files = [
        "frame_filter.py",
        "cram_writer.py",
        "test_segment_cram_writer.py",
        "ph6lite_coherence_check.py",
        "run_ph6lite_check.sh",
        "test_ph6lite_phase2.py",
    ]

    storage_files = [
        "ph6_storage_score_history.py",
        "test_storage_monitor.py",
    ]

    state = {
        "ts": now(),
        "frame_filter": {
            "git": git_status(FRAME_FILTER),
            "files": file_exists(FRAME_FILTER, frame_files),
        },
        "ph6_storage_monitor": {
            "git": git_status(STORAGE_MONITOR),
            "files": file_exists(STORAGE_MONITOR, storage_files),
        },
        "system": {
            "python": run(["python3", "--version"]),
            "dpkg_audit": run(["sudo", "dpkg", "--audit"], timeout=20),
            "failed_services": run(["systemctl", "--failed"], timeout=20),
            "reboot_required": pathlib.Path("/var/run/reboot-required").exists(),
        },
    }

    return state


def pseudo_run_tests() -> Dict[str, Any]:
    tests = {}

    if FRAME_FILTER.exists():
        if (FRAME_FILTER / "test_segment_cram_writer.py").exists():
            tests["segment_cram_writer"] = run(
                [SYSTEM_PYTHON, "test_segment_cram_writer.py"],
                cwd=FRAME_FILTER,
                timeout=60,
            )

        if (FRAME_FILTER / "ph6lite_coherence_check.py").exists():
            tests["ph6lite_coherence"] = run(
                [SYSTEM_PYTHON, "ph6lite_coherence_check.py"],
                cwd=FRAME_FILTER,
                timeout=90,
            )

        if (FRAME_FILTER / "test_ph6lite_phase2.py").exists():
            tests["phase2"] = run(
                [SYSTEM_PYTHON, "test_ph6lite_phase2.py"],
                cwd=FRAME_FILTER,
                timeout=60,
            )

    if STORAGE_MONITOR.exists():
        if (STORAGE_MONITOR / "test_storage_monitor.py").exists():
            tests["storage_monitor"] = run(
                [SYSTEM_PYTHON, "test_storage_monitor.py"],
                cwd=STORAGE_MONITOR,
                timeout=60,
            )

    return tests


def pseudo_evaluate(state: Dict[str, Any], tests: Dict[str, Any]) -> Dict[str, Any]:
    reasons: List[str] = []
    score = 0

    ff = state["frame_filter"]
    sm = state["ph6_storage_monitor"]

    if not ff["git"]["exists"]:
        score += 5
        reasons.append("BLOCK: ~/frame_filter is missing.")

    if not sm["git"]["exists"]:
        score += 2
        reasons.append("HOLD: ~/ph6_storage_monitor is missing.")

    ff_status = ff["git"].get("status_short", "")
    sm_status = sm["git"].get("status_short", "")

    if ff_status:
        score += 2
        reasons.append("HOLD: frame_filter has uncommitted or untracked files.")

    if sm_status:
        score += 1
        reasons.append("HOLD: ph6_storage_monitor has uncommitted or untracked files.")

    for name, exists in ff["files"].items():
        if not exists:
            score += 1
            reasons.append(f"HOLD: frame_filter missing expected file: {name}")

    for name, exists in sm["files"].items():
        if not exists:
            score += 1
            reasons.append(f"HOLD: storage monitor missing expected file: {name}")

    for test_name, result in tests.items():
        if result["returncode"] != 0:
            score += 3
            reasons.append(f"HOLD: test failed or timed out: {test_name}")

    if state["system"]["reboot_required"]:
        score += 1
        reasons.append("HOLD: system reboot is required.")

    failed_services_text = state["system"]["failed_services"]["stdout"]
    if "0 loaded units listed" not in failed_services_text and "UNIT" in failed_services_text:
        score += 2
        reasons.append("HOLD: one or more systemd services are failed.")

    if score == 0:
        verdict = "PASS"
        reasons.append("PASS: deterministic checks found no blocking issue.")
    elif score >= 5:
        verdict = "BLOCK"
    else:
        verdict = "HOLD"

    return {
        "agent": "PSEUDO",
        "authority": "YES",
        "verdict": verdict,
        "score": score,
        "reasons": reasons,
        "rules": PSEUDO_RULES,
    }


def soso_observe(state: Dict[str, Any], tests: Dict[str, Any], pseudo: Dict[str, Any]) -> Dict[str, Any]:
    notes: List[str] = []
    drift_flags: List[str] = []
    suggested_focus: List[str] = []

    ff_status = state["frame_filter"]["git"].get("status_short", "")
    sm_status = state["ph6_storage_monitor"]["git"].get("status_short", "")

    if "ph6lite_coherence_report.json" in ff_status:
        notes.append("Generated coherence report remains uncommitted/unremoved.")
        drift_flags.append("generated_artifact_leftover")

    if "__pycache__" in sm_status:
        notes.append("Python cache folder remains visible in storage monitor repo.")
        drift_flags.append("cache_artifact_leftover")

    phase2 = tests.get("phase2")
    if phase2 and phase2["returncode"] != 0:
        text = phase2.get("stdout", "") + "\n" + phase2.get("stderr", "")
        if "run_log.jsonl" in text or "spike_events.jsonl" in text:
            notes.append("Phase 2 likely still has run_log.jsonl vs hot/spike_events.jsonl mismatch.")
            drift_flags.append("event_log_path_mismatch")
            suggested_focus.append("Patch Phase 2 test to resolve current event log path.")

    recent = recent_memory(limit=12)
    recent_verdicts = [x.get("pseudo_verdict") for x in recent if "pseudo_verdict" in x]

    if recent_verdicts.count("HOLD") >= 3:
        notes.append("Repeated HOLD pattern detected in recent SoSo memory.")
        drift_flags.append("repeated_hold_pattern")

    if not notes:
        notes.append("No advisory pattern warning detected.")

    if any(f in drift_flags for f in ("repeated_hold_pattern", "event_log_path_mismatch")):
        advisory_result = "DRIFT_WARNING"
    elif drift_flags:
        advisory_result = "UNSTABLE"
    else:
        advisory_result = "STABLE"

    return {
        "schema": "ph6.soso.advisory.v1",
        "agent": "SoSo",
        "authority": "NONE",
        "advisory_only": True,
        "replay_dependency": False,
        "affects_pass_drop": False,
        "affects_thresholds": False,
        "affects_cram_commit": False,
        "affects_rsync": False,
        "advisory_result": advisory_result,
        "notes": notes,
        "drift_flags": drift_flags,
        "suggested_focus": suggested_focus,
        "rules": SOSO_RULES,
        "important": "SoSo notes do not change PSEUDO verdict.",
    }


def command_plan(pseudo: Dict[str, Any], soso: Dict[str, Any]) -> List[str]:
    cmds: List[str] = []

    if "generated_artifact_leftover" in soso["drift_flags"]:
        cmds.append("cd ~/frame_filter && rm -f ph6lite_coherence_report.json && git status --short")

    if "cache_artifact_leftover" in soso["drift_flags"]:
        cmds.append("cd ~/ph6_storage_monitor && rm -rf __pycache__ && git status --short")

    if "event_log_path_mismatch" in soso["drift_flags"]:
        cmds.extend([
            "cd ~/frame_filter && grep -nE 'run_log|spike_events|jsonl|hot/' test_ph6lite_phase2.py frame_filter.py ph6lite_coherence_check.py run_ph6lite_check.sh",
            "cd ~/frame_filter && cp test_ph6lite_phase2.py test_ph6lite_phase2.py.bak.$(date +%Y%m%d_%H%M%S)",
            "# Add fallback: run_log.jsonl -> hot/spike_events.jsonl",
            "cd ~/frame_filter && python3 test_ph6lite_phase2.py",
        ])

    if not cmds:
        cmds.append("cd ~/frame_filter && git status --short")
        cmds.append("cd ~/ph6_storage_monitor && git status --short")

    blocked = []
    for cmd in cmds:
        for bad in DANGEROUS_PATTERNS:
            if bad in cmd:
                blocked.append(cmd)

    if blocked:
        return ["BLOCKED: dangerous command pattern detected. Manual review required."]

    return cmds


def print_human(report: Dict[str, Any]) -> None:
    pseudo = report["pseudo"]
    soso = report["soso"]

    print("==================================================")
    print("PH6 PSEUDO + SOSO REPORT")
    print("==================================================")
    print("Time:", report["ts"])
    print("Report:", report["report_path"])
    print()

    print("PSEUDO VERDICT")
    print("--------------")
    print("Authority:", pseudo["authority"])
    print("Verdict:", pseudo["verdict"])
    print("Score:", pseudo["score"])
    for r in pseudo["reasons"]:
        print("-", r)

    print()
    print("SOSO ADVISORY")
    print("-------------")
    print("Authority:", soso["authority"])
    for n in soso["notes"]:
        print("-", n)

    if soso["drift_flags"]:
        print()
        print("Drift flags:")
        for f in soso["drift_flags"]:
            print("-", f)

    if soso["suggested_focus"]:
        print()
        print("Suggested focus:")
        for f in soso["suggested_focus"]:
            print("-", f)

    print()
    print("COMMAND PLAN")
    print("------------")
    for c in report["commands"]:
        print(c)

    print()
    print("AUTHORITY LOCK")
    print("--------------")
    print("PSEUDO may issue PASS/HOLD/BLOCK.")
    print("SoSo is advisory only and cannot change verdict.")


def main() -> int:
    parser = argparse.ArgumentParser(description="PH6 PSEUDO + SoSo local checker")
    parser.add_argument("--no-tests", action="store_true", help="Collect state only; skip tests")
    parser.add_argument("--json", action="store_true", help="Print JSON")
    parser.add_argument("--memory", action="store_true", help="Show recent SoSo memory")
    args = parser.parse_args()

    ensure_dirs()

    if args.memory:
        print(json.dumps(recent_memory(), ensure_ascii=False, indent=2))
        return 0

    state = pseudo_collect_state()
    tests = {} if args.no_tests else pseudo_run_tests()
    pseudo = pseudo_evaluate(state, tests)
    soso = soso_observe(state, tests, pseudo)
    cmds = command_plan(pseudo, soso)

    report = {
        "ts": now(),
        "state": state,
        "tests": tests,
        "pseudo": pseudo,
        "soso": soso,
        "commands": cmds,
    }

    report_hash = hash_obj(report)
    report["report_hash"] = report_hash

    path = save_report(report)
    report["report_path"] = str(path)

    append_memory({
        "pseudo_verdict": pseudo["verdict"],
        "pseudo_score": pseudo["score"],
        "soso_drift_flags": soso["drift_flags"],
        "report_hash": report_hash,
    })

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print_human(report)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
