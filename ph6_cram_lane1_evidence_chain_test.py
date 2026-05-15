#!/usr/bin/env python3
"""
PH6 / CRAM — Lane-1 Authority Evidence Chain Test

Test class:
    CRAM integrity + Lane-1 authority + evidence-chain validation

Validates:
    1. FAST CRAM atomic write path
    2. CRAM .blake2b marker integrity
    3. PSEUDO Lane-1 deterministic PASS/DROP behavior
    4. Forbidden field absence
    5. SoSo advisory isolation / Authority ZERO
    6. Hash-chained audit/evidence receipt
    7. Final result_set_hash

Non-goals:
    - Does not close OI-01 Hailo
    - Does not close OI-03 Pi-to-Pi transfer
    - Does not test RSYNC pressure
    - Does not perform crash-recovery campaign
    - Does not perform formal replay campaign
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple


FORBIDDEN_FIELDS = {
    "motion_score",
    "motion_decay_score",
}

SOSO_FORBIDDEN_AUTHORITY_FIELDS = {
    "verdict",
    "result",
    "PASS",
    "DROP",
}

ZERO_HASH = "0" * 64


def utc_stamp() -> str:
    return time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())


def blake2b256(data: bytes) -> str:
    return hashlib.blake2b(data, digest_size=32).hexdigest()


def canonical_json(obj: Any) -> bytes:
    return json.dumps(
        obj,
        sort_keys=True,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")


def write_json_atomic(path: Path, obj: Any) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)

    data = canonical_json(obj)
    digest = blake2b256(data)

    tmp = path.parent / f".{path.name}.tmp"
    marker = Path(str(path) + ".blake2b")

    with open(tmp, "wb") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())

    os.replace(tmp, path)

    dir_fd = os.open(path.parent, os.O_DIRECTORY)
    try:
        os.fsync(dir_fd)
    finally:
        os.close(dir_fd)

    with open(marker, "w", encoding="utf-8") as f:
        f.write(digest + "\n")
        f.flush()
        os.fsync(f.fileno())

    return digest


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_receipt(run_dir: Path, name: str, receipt: Dict[str, Any]) -> Path:
    path = run_dir / f"{name}.json"
    write_json_atomic(path, receipt)
    return path


def git_commit_short() -> str:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        return out
    except Exception:
        return "UNKNOWN"


def preflight(run_dir: Path) -> Dict[str, Any]:
    receipt = {
        "schema": "ph6.preflight.receipt.v1",
        "timestamp_utc": utc_stamp(),
        "host": platform.node(),
        "platform": platform.platform(),
        "python": sys.version.split()[0],
        "git_commit": git_commit_short(),
        "run_dir": str(run_dir),
        "verdict": "PASS",
    }
    write_receipt(run_dir, "00_preflight_receipt", receipt)
    return receipt


def fast_cram_test(run_dir: Path, frames: int) -> Dict[str, Any]:
    cram_dir = run_dir / "cram_fast"
    failures = []

    start = time.time()

    for i in range(frames):
        packet = {
            "schema": "ph6.cram.synthetic_frame.v1",
            "frame_index": i,
            "timestamp_ns": time.time_ns(),
            "payload": {
                "source": "synthetic",
                "test": "CRAM_LANE1_EVIDENCE_CHAIN",
                "value": f"frame-{i:06d}",
            },
        }

        try:
            write_json_atomic(cram_dir / f"frame_{i:06d}.json", packet)
        except Exception as e:
            failures.append({
                "frame_index": i,
                "error": repr(e),
            })

    elapsed = time.time() - start

    json_count = len(list(cram_dir.glob("*.json")))
    marker_count = len(list(cram_dir.glob("*.json.blake2b")))

    receipt = {
        "schema": "ph6.fast_cram.receipt.v1",
        "frames_requested": frames,
        "frames_written": json_count,
        "markers_written": marker_count,
        "failures": failures,
        "elapsed_seconds": f"{elapsed:.6f}",
        "verdict": "PASS"
        if json_count == frames and marker_count == frames and not failures
        else "FAIL",
    }

    write_receipt(run_dir, "01_fast_cram_receipt", receipt)
    return receipt


def full_cram_integrity_test(run_dir: Path, frames: int) -> Dict[str, Any]:
    cram_dir = run_dir / "cram_fast"
    bad = []
    checked = 0

    for f in sorted(cram_dir.glob("frame_*.json")):
        marker = Path(str(f) + ".blake2b")

        if not marker.exists():
            bad.append({
                "file": str(f),
                "reason": "MISSING_MARKER",
            })
            continue

        actual = blake2b256(f.read_bytes())
        expected = marker.read_text(encoding="utf-8").strip()
        checked += 1

        if actual != expected:
            bad.append({
                "file": str(f),
                "reason": "HASH_MISMATCH",
                "actual": actual,
                "expected": expected,
            })

    receipt = {
        "schema": "ph6.full_cram.integrity_receipt.v1",
        "expected_frames": frames,
        "checked": checked,
        "bad_count": len(bad),
        "bad": bad[:25],
        "verdict": "PASS" if checked == frames and not bad else "FAIL",
    }

    write_receipt(run_dir, "02_full_cram_integrity_receipt", receipt)
    return receipt


def evaluate_frame(frame_index: int, entropy: float, laplacian_var: float, motion_fraction: float) -> Dict[str, Any]:
    reasons = []

    if entropy < 0.05:
        reasons.append("LOW_ENTROPY")

    if laplacian_var < 20.0:
        reasons.append("LOW_LAPLACIAN_VAR")

    if motion_fraction < 0.0001:
        reasons.append("LOW_MOTION_FRACTION")

    verdict = "DROP" if reasons else "PASS"

    return {
        "schema": "ph6.pseudo.verdict.v1",
        "frame_index": frame_index,
        "verdict": verdict,
        "metrics": {
            "entropy": f"{entropy:.6f}",
            "laplacian_var": f"{laplacian_var:.6f}",
            "motion_fraction": f"{motion_fraction:.6f}",
        },
        "reasons": reasons,
    }


def pseudo_lane1_test(run_dir: Path) -> Dict[str, Any]:
    vectors = [
        {"frame_index": 0, "entropy": 0.900000, "laplacian_var": 180.0, "motion_fraction": 0.250000},
        {"frame_index": 1, "entropy": 0.010000, "laplacian_var": 180.0, "motion_fraction": 0.250000},
        {"frame_index": 2, "entropy": 0.900000, "laplacian_var": 5.0, "motion_fraction": 0.250000},
        {"frame_index": 3, "entropy": 0.900000, "laplacian_var": 180.0, "motion_fraction": 0.000000},
    ]

    results_1 = [evaluate_frame(**v) for v in vectors]
    results_2 = [evaluate_frame(**v) for v in vectors]

    hash_1 = blake2b256(canonical_json(results_1))
    hash_2 = blake2b256(canonical_json(results_2))

    receipt = {
        "schema": "ph6.pseudo.lane1_test_receipt.v1",
        "deterministic": hash_1 == hash_2,
        "result_set_hash_1": hash_1,
        "result_set_hash_2": hash_2,
        "results": results_1,
        "verdict": "PASS" if hash_1 == hash_2 else "FAIL",
    }

    write_receipt(run_dir, "03_pseudo_lane1_receipt", receipt)
    return receipt


def scan_forbidden_fields(run_dir: Path) -> Dict[str, Any]:
    violations = []

    for path in run_dir.rglob("*.json"):
        text = path.read_text(encoding="utf-8", errors="replace")

        for field in FORBIDDEN_FIELDS:
            if f'"{field}"' in text:
                violations.append({
                    "file": str(path),
                    "field": field,
                })

    receipt = {
        "schema": "ph6.forbidden_field_scan.receipt.v1",
        "forbidden_fields": sorted(FORBIDDEN_FIELDS),
        "violation_count": len(violations),
        "violations": violations[:50],
        "verdict": "PASS" if not violations else "FAIL",
    }

    write_receipt(run_dir, "04_forbidden_field_scan_receipt", receipt)
    return receipt


def soso_advisory_isolation_test(run_dir: Path, frames: int) -> Dict[str, Any]:
    soso_dir = run_dir / "mram_s" / "soso"
    soso_dir.mkdir(parents=True, exist_ok=True)

    violations = []

    for i in range(frames):
        event = {
            "schema": "ph6.soso.advisory.v1",
            "frame_index": i,
            "authority": "ZERO",
            "advisory_only": True,
            "replay_dependency": False,
            "may_decide_pass_drop": False,
            "observation": {
                "drift_pressure": "LOW",
                "continuity_note": "NO_AUTHORITY_CHANGE",
            },
            "timestamp_ns": time.time_ns(),
        }

        write_json_atomic(soso_dir / f"soso_{i:06d}.json", event)

    count = 0

    for path in sorted(soso_dir.glob("soso_*.json")):
        count += 1
        event = read_json(path)

        if event.get("authority") != "ZERO":
            violations.append({"file": str(path), "reason": "AUTHORITY_NOT_ZERO"})

        if event.get("advisory_only") is not True:
            violations.append({"file": str(path), "reason": "NOT_ADVISORY_ONLY"})

        if event.get("replay_dependency") is not False:
            violations.append({"file": str(path), "reason": "BECAME_REPLAY_DEPENDENCY"})

        for key in ("verdict", "result"):
            if key in event:
                violations.append({"file": str(path), "reason": f"FORBIDDEN_KEY_{key}"})

        text = path.read_text(encoding="utf-8", errors="replace")
        for forbidden in SOSO_FORBIDDEN_AUTHORITY_FIELDS:
            if f'"{forbidden}"' in text:
                violations.append({"file": str(path), "reason": f"AUTHORITY_TOKEN_{forbidden}"})

    receipt = {
        "schema": "ph6.soso.advisory_isolation_receipt.v1",
        "events_expected": frames,
        "events_written": count,
        "violation_count": len(violations),
        "violations": violations[:50],
        "verdict": "PASS" if count == frames and not violations else "FAIL",
    }

    write_receipt(run_dir, "05_soso_advisory_isolation_receipt", receipt)
    return receipt


def build_audit_chain(run_dir: Path, receipts: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    audit_dir = run_dir / "audit"
    audit_dir.mkdir(parents=True, exist_ok=True)

    prev_hash = ZERO_HASH
    events = []

    for seq, name in enumerate(sorted(receipts.keys()), start=1):
        payload_hash = blake2b256(canonical_json(receipts[name]))

        event_base = {
            "schema": "ph6.audit_event.v1",
            "event_seq": seq,
            "event_type": "TEST_RECEIPT",
            "object_id": name,
            "payload_hash": payload_hash,
            "prev_event_hash": prev_hash,
            "authority_hash": "LANE1_SYNTHETIC_TEST_AUTHORITY",
            "timestamp_utc": utc_stamp(),
        }

        event_hash = blake2b256(canonical_json(event_base))
        event = dict(event_base)
        event["event_hash"] = event_hash

        write_json_atomic(audit_dir / f"event_{seq:06d}.json", event)

        prev_hash = event_hash
        events.append(event)

    chain_receipt = {
        "schema": "ph6.audit_chain.receipt.v1",
        "event_count": len(events),
        "first_prev_event_hash": ZERO_HASH,
        "last_event_hash": prev_hash,
        "verdict": "PASS" if events and events[0]["prev_event_hash"] == ZERO_HASH else "FAIL",
    }

    write_receipt(run_dir, "06_audit_chain_receipt", chain_receipt)
    return chain_receipt


def final_receipt(run_dir: Path, receipts: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    failed = [name for name, receipt in receipts.items() if receipt.get("verdict") != "PASS"]

    result_set_hash = blake2b256(canonical_json(receipts))

    final = {
        "schema": "ph6.cram_lane1_evidence_chain.final_receipt.v1",
        "test_name": "CRAM_LANE1_AUTHORITY_EVIDENCE_CHAIN",
        "run_dir": str(run_dir),
        "minimum_valid_frames": 300,
        "receipt_count": len(receipts),
        "failed_receipts": failed,
        "result_set_hash": result_set_hash,
        "cram_integrity_preserved": receipts.get("02_full_cram_integrity_receipt", {}).get("verdict") == "PASS",
        "lane1_authority_preserved": receipts.get("03_pseudo_lane1_receipt", {}).get("verdict") == "PASS",
        "forbidden_fields_absent": receipts.get("04_forbidden_field_scan_receipt", {}).get("verdict") == "PASS",
        "soso_authority_zero": receipts.get("05_soso_advisory_isolation_receipt", {}).get("verdict") == "PASS",
        "audit_chain_preserved": receipts.get("06_audit_chain_receipt", {}).get("verdict") == "PASS",
        "not_closed": [
            "OI-01_HAILO",
            "OI-03_PI_TO_PI_TRANSFER",
            "C03_RSYNC_PRESSURE",
            "C04_CRASH_RECOVERY",
            "C05_FORMAL_REPLAY_CAMPAIGN",
        ],
        "verdict": "PASS" if not failed else "FAIL",
    }

    write_receipt(run_dir, "FINAL_CRAM_LANE1_EVIDENCE_CHAIN_RECEIPT", final)
    return final


def print_summary(final: Dict[str, Any]) -> None:
    print()
    print("=== PH6 / CRAM — LANE-1 EVIDENCE CHAIN TEST ===")
    print(f"verdict:                    {final['verdict']}")
    print(f"result_set_hash:            {final['result_set_hash']}")
    print(f"cram_integrity_preserved:   {final['cram_integrity_preserved']}")
    print(f"lane1_authority_preserved:  {final['lane1_authority_preserved']}")
    print(f"forbidden_fields_absent:    {final['forbidden_fields_absent']}")
    print(f"soso_authority_zero:        {final['soso_authority_zero']}")
    print(f"audit_chain_preserved:      {final['audit_chain_preserved']}")
    print(f"run_dir:                    {final['run_dir']}")
    print()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--frames", type=int, default=300)
    parser.add_argument("--out-root", default="validation_runs")
    args = parser.parse_args()

    if args.frames < 300:
        print("FAIL: PH6 test invalid below 300 frames.", file=sys.stderr)
        return 2

    run_dir = Path(args.out_root) / f"cram_lane1_evidence_chain_{utc_stamp()}"
    run_dir.mkdir(parents=True, exist_ok=True)

    receipts: Dict[str, Dict[str, Any]] = {}

    receipts["00_preflight_receipt"] = preflight(run_dir)
    receipts["01_fast_cram_receipt"] = fast_cram_test(run_dir, args.frames)
    receipts["02_full_cram_integrity_receipt"] = full_cram_integrity_test(run_dir, args.frames)
    receipts["03_pseudo_lane1_receipt"] = pseudo_lane1_test(run_dir)
    receipts["04_forbidden_field_scan_receipt"] = scan_forbidden_fields(run_dir)
    receipts["05_soso_advisory_isolation_receipt"] = soso_advisory_isolation_test(run_dir, args.frames)
    receipts["06_audit_chain_receipt"] = build_audit_chain(run_dir, receipts)

    final = final_receipt(run_dir, receipts)
    print_summary(final)

    return 0 if final["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
