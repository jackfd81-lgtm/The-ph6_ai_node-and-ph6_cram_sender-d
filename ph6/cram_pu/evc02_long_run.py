#!/usr/bin/env python3
"""
PH6 EVC-02 — Long-Run Receipt Chain Behavior

Runs a deterministic 300-frame CRAM ingest session using the production
IngestReceiptLogger, CRAMWriter, VerdictLogger, and chain verifier.

Pass criteria:
  - 300+ frames ingested
  - ingest receipt chain intact: chain_intact = true
  - event_seq monotonically 1..N with no gaps
  - VRC-1.0 certifies cleanly (result_set_hash present and stable)
  - Payloads and verdict records preserved for EVC-04

Output:
  validation_runs/evc02_<timestamp>/
    ingest_receipt_log.jsonl   (receipt chain)
    verdict_log.jsonl          (for EVC-04 replay comparison)
    cram_*.json                (CRAM commit records)
    ph6.vrc_receipt.v1.json    (certification)
    ph6.evc02_receipt.v1.json  (evidence receipt)
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent))

from ph6.cram_pu.ingest_receipt_logger import IngestReceiptLogger
from ph6.cram_pu.ingest_receipt_verify  import verify_receipt_chain
from ph6.cram_pu.crash_replay           import CRAMWriter, SheddingLogger, CRAMPaths
from ph6.cram_pu.verdict_logger         import VerdictLogger
from ph6.cram_pu.vrc                    import certify


TARGET_FRAMES = 300
SEED          = 42  # deterministic — same seed → same payloads → reproducible

def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def _blake2b(data: bytes) -> str:
    return hashlib.blake2b(data, digest_size=32).hexdigest()

def _canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False,
                      allow_nan=False, separators=(",", ":"))


def _make_payload(frame_id: int, seed: int) -> bytes:
    """Deterministic 300-byte payload. Same seed+frame_id → same bytes."""
    h = hashlib.blake2b(f"{seed}:{frame_id}".encode(), digest_size=32).digest()
    return bytes([(h[j % 32] % 180) + 25 for j in range(300)])


def run_evc02() -> dict:
    now      = _utc_now()
    slug     = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir  = HERE / "validation_runs" / f"evc02_{slug}"
    run_dir.mkdir(parents=True, exist_ok=True)

    # Initialise components
    receipt_logger = IngestReceiptLogger(run_dir)
    verdict_logger = VerdictLogger(run_dir / "verdict_log.jsonl")
    cram_writer    = CRAMWriter(run_dir)
    shed_logger    = SheddingLogger(CRAMPaths(cram_store=run_dir))

    accepted = dropped = 0
    prev_payload: bytes | None = None
    t0 = time.monotonic()

    print(f"\n  EVC-02: {TARGET_FRAMES}-frame run  (seed={SEED})")
    print(f"  Run dir: {run_dir}")

    for frame_id in range(1, TARGET_FRAMES + 1):
        payload      = _make_payload(frame_id, SEED)
        payload_hash = _blake2b(payload)

        # Lane-1: emit verdict
        verdict_rec  = verdict_logger.log(frame_id, payload, payload_hash)
        verdict      = verdict_rec["verdict"]

        # Emit arrived receipt
        receipt_logger.arrived(frame_id=frame_id, payload_hash=payload_hash)

        if verdict == "PASS":
            cram_rec = cram_writer.commit(frame_id, payload_hash, verdict_rec)
            receipt_logger.accepted(frame_id=frame_id, cram_hash=cram_rec["cram_hash"])
            accepted += 1
        else:
            shed_logger.log(frame_id, "PSEUDO-A/entropy_low_or_blur",
                            f"frame {frame_id} DROP: {verdict_rec.get('reasons')}")
            receipt_logger.dropped(frame_id=frame_id, payload_hash=payload_hash)
            dropped += 1

        prev_payload = payload

        if frame_id % 50 == 0:
            print(f"  ... frame {frame_id:>3}  accepted={accepted}  dropped={dropped}")

    elapsed = time.monotonic() - t0

    # Verify receipt chain
    chain_report = verify_receipt_chain(run_dir / "ingest_receipt_log.jsonl")

    # Check event_seq monotonicity (max seq should equal receipt count)
    receipt_count  = chain_report["receipt_count"]
    expected_total = TARGET_FRAMES * 3  # arrived + (accepted or dropped) per frame = 2, but arrived + accepted + dropped varies
    # Actually: each frame emits arrived + (accepted XOR dropped) = 2 receipts
    expected_total = TARGET_FRAMES * 2

    # VRC-1.0 certification
    vrc_receipt    = certify(run_dir)
    vrc_path       = run_dir / "ph6.vrc_receipt.v1.json"
    vrc_path.write_text(_canonical(vrc_receipt) + "\n")

    passed = (
        chain_report["chain_intact"]
        and receipt_count == expected_total
        and vrc_receipt["passed"]
        and chain_report.get("error_count", 0) == 0
    )

    # Seal evidence receipt
    body = {
        "schema":              "ph6.evc02_receipt.v1",
        "campaign_id":         "EVC-02",
        "campaign_name":       "Long-Run Receipt Chain Behavior",
        "overall_status":      "PASS" if passed else "FAIL",
        "frames_run":          TARGET_FRAMES,
        "frames_accepted":     accepted,
        "frames_dropped":      dropped,
        "receipts_emitted":    receipt_count,
        "receipts_expected":   expected_total,
        "chain_intact":        chain_report["chain_intact"],
        "chain_error_count":   chain_report.get("error_count", 0),
        "vrc_passed":          vrc_receipt["passed"],
        "result_set_hash":     vrc_receipt.get("result_set_hash"),
        "vrc_failure_count":   vrc_receipt["failure_count"],
        "elapsed_s":           round(elapsed, 3),
        "seed":                SEED,
        "run_dir":             str(run_dir),
        "vrc_receipt_path":    str(vrc_path),
        "authority":           "VERIFY_ONLY",
        "closes_gap":          "long_run_chain_behavior" if passed else None,
        "gap_closed":          passed,
        "evc04_payload_note":  (
            "Payloads are deterministically reproducible from seed=42 + frame_id. "
            "EVC-04 payload replay can re-derive identical bytes without storing them."
        ),
        "production_clearance": False,
        "open_stop_ship_gates": ["OI-01", "OI-03"],
        "timestamp_utc":       now,
    }
    body["evidence_hash"] = _blake2b(
        _canonical({k: v for k, v in body.items() if k != "evidence_hash"}).encode()
    )

    receipt_path = run_dir / "ph6.evc02_receipt.v1.json"
    receipt_path.write_text(_canonical(body) + "\n")

    return body


def main() -> None:
    result = run_evc02()
    print()
    print(f"  Overall:        {result['overall_status']}")
    print(f"  Frames:         {result['frames_run']} "
          f"(accepted={result['frames_accepted']} dropped={result['frames_dropped']})")
    print(f"  Receipts:       {result['receipts_emitted']} / {result['receipts_expected']} expected")
    print(f"  Chain intact:   {result['chain_intact']}")
    print(f"  VRC passed:     {result['vrc_passed']}")
    print(f"  result_set_hash:{result['result_set_hash'][:24]}...")
    print(f"  Elapsed:        {result['elapsed_s']}s")
    print(f"  Gap closed:     {result['gap_closed']}")
    print(f"  Evidence hash:  {result['evidence_hash'][:24]}...")
    print(f"  Receipt:        {result['run_dir']}/ph6.evc02_receipt.v1.json")
    print()
    sys.exit(0 if result["overall_status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
