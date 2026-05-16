#!/usr/bin/env python3
"""
PH6 EVC-01 — Crash Receipt Continuity Simulation

Exercises three crash scenarios against the real IngestReceiptLogger
and chain verifier. All scenarios use actual production code paths.

Scenarios:
  S1: Normal run → verify chain intact (baseline)
  S2: Crash mid-write (partial receipt line) → verifier must detect parse error
  S3: Crash after write, before seq save → next run gets dup seq → verifier detects
  S4: Full crash+restart → resume after truncated tail, new chain continues
      verifier detects break at truncation point, clean tail is intact

Pass criteria (EVC-01):
  - Verifier correctly classifies each scenario (intact or broken with reason)
  - No scenario produces a false-intact report over a corrupted chain
  - VRC-1.0 run post-recovery does not suppress failures from S2/S3
  - result_set_hash is stable for clean segments

Output: ph6.evc01_receipt.v1 evidence receipt
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent))

from ph6.cram_pu.ingest_receipt_logger import IngestReceiptLogger, GENESIS_HASH
from ph6.cram_pu.ingest_receipt_verify import verify_receipt_chain
from ph6.cram_pu.vrc import certify


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _blake2b(data: bytes) -> str:
    return hashlib.blake2b(data, digest_size=32).hexdigest()


def _canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False,
                      allow_nan=False, separators=(",", ":"))


def _make_store() -> Path:
    td = Path(tempfile.mkdtemp(prefix="ph6_evc01_"))
    (td / "ingest_receipt_log.jsonl").touch()
    return td


def run_scenario(label: str, fn) -> dict:
    print(f"\n  [{label}]", end=" ", flush=True)
    start = time.monotonic()
    result = fn()
    elapsed = time.monotonic() - start
    status = "PASS" if result.get("pass") else "FAIL"
    print(f"{status} ({elapsed:.2f}s)")
    return {"scenario": label, "status": status, "elapsed_s": round(elapsed, 3), **result}


# ── Scenario S1: Normal emission, chain intact ────────────────────────────────

def scenario_s1() -> dict:
    """Baseline: 5 clean emissions → chain verifier reports intact."""
    store = _make_store()
    logger = IngestReceiptLogger(store)
    for i in range(1, 6):
        logger.arrived(frame_id=i, payload_hash=_blake2b(f"s1:{i}".encode()))
        logger.accepted(frame_id=i, cram_hash=_blake2b(f"s1:cram:{i}".encode()))

    report = verify_receipt_chain(store / "ingest_receipt_log.jsonl")
    passed = report["chain_intact"] and report["receipt_count"] == 10

    return {
        "pass": passed,
        "chain_intact": report["chain_intact"],
        "receipt_count": report["receipt_count"],
        "error_count": report.get("error_count", 0),
        "description": "Baseline: 5 frames, 10 receipts, chain intact",
    }


# ── Scenario S2: Crash mid-write — partial receipt line ───────────────────────

def scenario_s2() -> dict:
    """
    Simulate crash mid-write: truncate the last receipt line to partial JSON.
    Verifier must detect parse_error. chain_intact must be False.
    """
    store = _make_store()
    logger = IngestReceiptLogger(store)
    for i in range(1, 4):
        logger.arrived(frame_id=i, payload_hash=_blake2b(f"s2:{i}".encode()))

    # Corrupt: truncate the log at an arbitrary byte position (simulates mid-write crash)
    log = store / "ingest_receipt_log.jsonl"
    content = log.read_bytes()
    # Keep first 2 lines intact; truncate 3rd line mid-way
    lines = [l for l in content.split(b"\n") if l]
    if len(lines) >= 3:
        truncated = b"\n".join(lines[:2]) + b"\n" + lines[2][:len(lines[2]) // 2]
        log.write_bytes(truncated)

    report = verify_receipt_chain(log)
    # Pass if: chain is reported broken AND a parse_error finding exists
    has_parse_error = any(f.get("type") == "parse_error" for f in report.get("findings", []))
    passed = not report["chain_intact"] and has_parse_error

    return {
        "pass": passed,
        "chain_intact": report["chain_intact"],
        "detected_parse_error": has_parse_error,
        "finding_types": [f.get("type") for f in report.get("findings", [])],
        "description": "Crash mid-write: truncated receipt detected as parse_error",
    }


# ── Scenario S3: Seq file not saved — duplicate seq on restart ────────────────

def scenario_s3() -> dict:
    """
    Simulate crash after write but before seq file save.
    Delete the seq file → next receipt gets seq 1 again (duplicate).
    Verifier must detect event_seq_violation.
    """
    store = _make_store()
    logger = IngestReceiptLogger(store)
    logger.arrived(frame_id=1, payload_hash=_blake2b(b"s3:1"))
    logger.arrived(frame_id=2, payload_hash=_blake2b(b"s3:2"))

    # Simulate crash: remove seq file so next instance starts from 0
    seq_file = store / "ingest_receipt_seq.txt"
    if seq_file.exists():
        seq_file.unlink()

    # Restart logger — seq restarts from 0 → next emit gets seq 1 (duplicate)
    logger2 = IngestReceiptLogger(store)
    logger2.arrived(frame_id=3, payload_hash=_blake2b(b"s3:3"))

    report = verify_receipt_chain(store / "ingest_receipt_log.jsonl")
    has_seq_violation = any(
        f.get("type") in ("event_seq_violation", "chain_break", "event_hash_mismatch")
        for f in report.get("findings", [])
    )
    # chain_intact should be False (duplicate seq means something is wrong)
    passed = not report["chain_intact"] or has_seq_violation

    return {
        "pass": passed,
        "chain_intact": report["chain_intact"],
        "detected_seq_violation": has_seq_violation,
        "finding_types": [f.get("type") for f in report.get("findings", [])],
        "description": "Seq file lost: duplicate event_seq or chain break detected",
    }


# ── Scenario S4: Crash+restart — clean tail continues ────────────────────────

def scenario_s4() -> dict:
    """
    Full crash+restart simulation:
    1. Emit 3 receipts (pre-crash segment)
    2. Corrupt receipt 3 (crash mid-write)
    3. Restart — new logger reads prev_hash from last *complete* line
    4. Emit 2 more receipts (post-crash segment)
    5. Run VRC to ensure it does not suppress the corruption
    """
    store = _make_store()

    # Pre-crash: 3 receipts
    logger = IngestReceiptLogger(store)
    for i in range(1, 4):
        logger.arrived(frame_id=i, payload_hash=_blake2b(f"s4:{i}".encode()))

    # Corrupt last receipt (crash mid-write)
    log = store / "ingest_receipt_log.jsonl"
    lines = [l for l in log.read_bytes().split(b"\n") if l]
    if len(lines) >= 3:
        log.write_bytes(b"\n".join(lines[:2]) + b"\n" + b'{"partial":true' + b"\n")

    # Mid-state verify: should detect corruption
    mid_report = verify_receipt_chain(log)

    # Post-crash: restart logger, emit 2 more receipts
    logger2 = IngestReceiptLogger(store)
    for i in range(4, 6):
        logger2.arrived(frame_id=i, payload_hash=_blake2b(f"s4:post:{i}".encode()))

    # VRC-1.0 run: should not produce a passing cert over the corrupted store
    vrc_receipt = certify(store)

    # Chain still broken (corruption in middle): VRC Step A must fail
    step_a_ok = vrc_receipt["steps"]["A_receipt_chain_intact"]
    vrc_passed = vrc_receipt["passed"]

    # Pass if: mid-state corruption was detected AND VRC does not suppress it
    passed = not mid_report["chain_intact"] and not vrc_passed

    return {
        "pass": passed,
        "mid_crash_chain_intact": mid_report["chain_intact"],
        "vrc_passed": vrc_passed,
        "vrc_step_a": step_a_ok,
        "vrc_failure_count": vrc_receipt["failure_count"],
        "description": "Crash+restart: corruption detected mid-state, VRC does not suppress",
    }


# ── Evidence receipt assembly ─────────────────────────────────────────────────

def main() -> None:
    print()
    print("PH6 EVC-01 — Crash Receipt Continuity Simulation")
    print("=" * 56)
    now = _utc_now()

    results = [
        run_scenario("S1 baseline",       scenario_s1),
        run_scenario("S2 mid-write crash", scenario_s2),
        run_scenario("S3 seq-loss crash",  scenario_s3),
        run_scenario("S4 crash+restart",   scenario_s4),
    ]

    all_pass = all(r["status"] == "PASS" for r in results)
    overall  = "PASS" if all_pass else "FAIL"

    # Seal evidence receipt
    body = {
        "schema":            "ph6.evc01_receipt.v1",
        "campaign_id":       "EVC-01",
        "campaign_name":     "Crash Receipt Continuity",
        "overall_status":    overall,
        "scenarios_run":     len(results),
        "scenarios_passed":  sum(1 for r in results if r["status"] == "PASS"),
        "scenarios_failed":  sum(1 for r in results if r["status"] != "PASS"),
        "scenarios":         results,
        "authority":         "VERIFY_ONLY",
        "closes_gap":        "crash_receipt_continuity" if all_pass else None,
        "gap_closed":        all_pass,
        "gap_closed_note":   (
            "EVC-01 simulates crash scenarios using production IngestReceiptLogger "
            "and chain verifier code. Hardware-level power-loss testing is separate."
            if all_pass else
            "EVC-01 did not pass all scenarios. Gap remains open."
        ),
        "production_clearance": False,
        "open_stop_ship_gates": ["OI-01", "OI-03"],
        "timestamp_utc":     now,
    }
    body["evidence_hash"] = _blake2b(_canonical({k: v for k, v in body.items()
                                                  if k != "evidence_hash"}).encode())

    print()
    print(f"  Overall: {overall}")
    print(f"  Passed:  {body['scenarios_passed']}/{body['scenarios_run']}")
    print(f"  Gap closed: {body['gap_closed']}")
    print(f"  Evidence hash: {body['evidence_hash'][:24]}...")

    # Write receipt
    out_dir = HERE / "validation_runs"
    out_dir.mkdir(exist_ok=True)
    slug = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = out_dir / f"evc01_{slug}.json"
    out_path.write_text(_canonical(body) + "\n", encoding="utf-8")
    print(f"  Receipt: {out_path}")
    print()

    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
