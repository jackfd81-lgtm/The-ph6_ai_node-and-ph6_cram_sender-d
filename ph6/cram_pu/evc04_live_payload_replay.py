#!/usr/bin/env python3
"""
PH6 EVC-04-LIVE — Live Payload Replay Verdict and Metric Comparison

Closes GAP-16: replay parity proven only on synthetic oracle; live ingest replay unproven.

Reads live payload bytes from cram_store/payloads/frame_<id>.bin, re-runs PSEUDO
VerdictLogger over the exact same bytes, and proves byte-equivalent verdicts and
fixed-point metrics against the stored verdict_log.jsonl.

Pass criteria:
  1. For every frame: payload bytes load cleanly
  2. BLAKE2b-256 of loaded payload == input_hash in verdict_log
  3. Replayed verdict == stored verdict
  4. Replayed entropy_fp == stored entropy_fp
  5. Replayed laplacian_var_fp == stored laplacian_var_fp
  6. Replayed motion_fraction_fp == stored motion_fraction_fp
  7. metric_schema == ph6.metrics.fixedpoint.v1
  8. metric_scale == 10000
  9. replay_verdict_hash == original_verdict_hash

CLI:
  python evc04_live_payload_replay.py --source-dir <cram_store> [--out-dir PATH]

  --source-dir: cram_store directory containing verdict_log.jsonl and payloads/
  --out-dir:    output directory for receipt (default: auto-generated under validation_runs/)
"""

from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent))

from ph6.cram_pu import verdict_logger as _vl_module
from ph6.cram_pu.verdict_logger import VerdictLogger

EXPECTED_METRIC_SCHEMA = "ph6.metrics.fixedpoint.v1"
EXPECTED_METRIC_SCALE  = 10000


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _blake2b(data: bytes) -> str:
    return hashlib.blake2b(data, digest_size=32).hexdigest()


def _canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False,
                      allow_nan=False, separators=(",", ":"))


def _pseudo_code_hash() -> str:
    path = Path(_vl_module.__file__)
    return _blake2b(path.read_bytes())


def _load_verdicts(source_dir: Path) -> list[dict]:
    log = source_dir / "verdict_log.jsonl"
    if not log.exists():
        sys.exit(f"FATAL: verdict_log.jsonl not found in {source_dir}")
    records = [json.loads(l) for l in log.read_text().splitlines() if l.strip()]
    if not records:
        sys.exit(f"FATAL: verdict_log.jsonl is empty: {log}")
    return sorted(records, key=lambda r: r["frame_id"])


def _load_payload(payloads_dir: Path, frame_id: int) -> bytes | None:
    path = payloads_dir / f"frame_{frame_id:010d}.bin"
    if not path.exists():
        return None
    return path.read_bytes()


def _verdict_hash(verdicts: list[dict]) -> str:
    canonical_list = [
        {
            "frame_id": v["frame_id"],
            "verdict":  v["verdict"],
            "metrics":  {
                k: val for k, val in sorted(v["metrics"].items())
                if k in ("entropy_fp", "laplacian_var_fp", "motion_fraction_fp",
                         "metric_schema", "metric_scale")
            },
        }
        for v in verdicts
    ]
    return _blake2b(_canonical(canonical_list).encode("utf-8"))


def run_evc04_live(
    source_dir: Path,
    out_dir: Path | None = None,
) -> dict:
    now  = _utc_now()
    slug = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    source_dir   = Path(source_dir)
    payloads_dir = source_dir / "payloads"

    if out_dir is None:
        out_dir = HERE / "validation_runs" / f"evc04_live_{slug}"
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    originals   = _load_verdicts(source_dir)
    frame_count = len(originals)
    pseudo_hash = _pseudo_code_hash()

    print(f"\n  EVC-04-LIVE: Payload replay — {frame_count} frames")
    print(f"  Source dir:      {source_dir}")
    print(f"  Payloads dir:    {payloads_dir}")
    print(f"  PSEUDO code hash:{pseudo_hash[:24]}...")

    if not payloads_dir.exists():
        sys.exit(f"FATAL: payloads/ directory not found in {source_dir}\n"
                 f"  Run with a cram_store produced by cram_pu_live.py v2+ "
                 f"(which writes cram_store/payloads/frame_*.bin)")

    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as tf:
        tmp_log = Path(tf.name)

    replay_logger = VerdictLogger(tmp_log)
    mismatches: list[dict] = []
    missing_payloads: list[int] = []
    t0 = time.monotonic()

    for orig in originals:
        frame_id = orig["frame_id"]
        payload  = _load_payload(payloads_dir, frame_id)

        if payload is None:
            missing_payloads.append(frame_id)
            mismatches.append({
                "frame_id": frame_id,
                "type":     "payload_file_missing",
                "expected": str(payloads_dir / f"frame_{frame_id:010d}.bin"),
            })
            continue

        payload_hash = _blake2b(payload)

        if payload_hash != orig.get("input_hash"):
            mismatches.append({
                "frame_id": frame_id,
                "type":     "payload_hash_mismatch",
                "expected": orig.get("input_hash"),
                "observed": payload_hash,
            })
            continue

        replay_rec = replay_logger.log(frame_id, payload, payload_hash)

        if replay_rec["verdict"] != orig["verdict"]:
            mismatches.append({
                "frame_id": frame_id,
                "type":     "verdict_mismatch",
                "expected": orig["verdict"],
                "observed": replay_rec["verdict"],
            })

        for field in ("entropy_fp", "laplacian_var_fp", "motion_fraction_fp"):
            orig_val   = orig["metrics"][field]
            replay_val = replay_rec["metrics"][field]
            if orig_val != replay_val:
                mismatches.append({
                    "frame_id": frame_id,
                    "type":     f"metric_mismatch:{field}",
                    "expected": orig_val,
                    "observed": replay_val,
                })

        if replay_rec["metrics"].get("metric_schema") != EXPECTED_METRIC_SCHEMA:
            mismatches.append({
                "frame_id": frame_id,
                "type":     "metric_schema_mismatch",
                "expected": EXPECTED_METRIC_SCHEMA,
                "observed": replay_rec["metrics"].get("metric_schema"),
            })
        if replay_rec["metrics"].get("metric_scale") != EXPECTED_METRIC_SCALE:
            mismatches.append({
                "frame_id": frame_id,
                "type":     "metric_scale_mismatch",
                "expected": EXPECTED_METRIC_SCALE,
                "observed": replay_rec["metrics"].get("metric_scale"),
            })

    elapsed = time.monotonic() - t0

    replay_records = [json.loads(l) for l in
                      Path(replay_logger.log_path).read_text().splitlines() if l.strip()]
    tmp_log.unlink(missing_ok=True)

    orig_hash    = _verdict_hash(originals)
    replay_hash  = _verdict_hash(replay_records) if replay_records else ""
    hashes_match = orig_hash == replay_hash and bool(replay_records)

    if not hashes_match:
        mismatches.append({
            "type":     "verdict_hash_mismatch",
            "expected": orig_hash,
            "observed": replay_hash,
        })

    passed = len(mismatches) == 0

    body = {
        "schema":                "ph6.evc04_live_receipt.v1",
        "campaign_id":           "EVC-04-LIVE",
        "campaign_name":         "Live Payload Replay Verdict and Metric Comparison",
        "closes_gap":            "GAP-16" if passed else None,
        "gap_closed":            passed,
        "overall_status":        "PASS" if passed else "FAIL",
        "frames_replayed":       frame_count,
        "frames_missing_payload": len(missing_payloads),
        "missing_payload_ids":   missing_payloads,
        "mismatches":            len(mismatches),
        "mismatch_details":      mismatches,
        "pseudo_code_hash":      pseudo_hash,
        "original_verdict_hash": orig_hash,
        "replay_verdict_hash":   replay_hash,
        "hashes_match":          hashes_match,
        "metric_schema_verified": EXPECTED_METRIC_SCHEMA,
        "metric_scale_verified":  EXPECTED_METRIC_SCALE,
        "source_dir":            str(source_dir),
        "payloads_dir":          str(payloads_dir),
        "elapsed_s":             round(elapsed, 3),
        "authority":             "VERIFY_ONLY",
        "production_clearance":  False,
        "open_stop_ship_gates":  ["OI-01", "OI-03"],
        "timestamp_utc":         now,
    }
    body["evidence_hash"] = _blake2b(
        _canonical({k: v for k, v in body.items() if k != "evidence_hash"}).encode()
    )

    out_path = out_dir / "ph6.evc04_live_receipt.v1.json"
    out_path.write_text(_canonical(body) + "\n")
    return body


def main() -> None:
    ap = argparse.ArgumentParser(
        description="EVC-04-LIVE: Live Payload Replay Verdict and Metric Comparison (GAP-16)"
    )
    ap.add_argument("--source-dir", type=Path, required=True,
                    help="cram_store directory containing verdict_log.jsonl and payloads/")
    ap.add_argument("--out-dir", type=Path, default=None,
                    help="output directory for receipt (default: auto-generated under validation_runs/)")
    args = ap.parse_args()

    result = run_evc04_live(source_dir=args.source_dir, out_dir=args.out_dir)
    print()
    print(f"  Overall:              {result['overall_status']}")
    print(f"  Frames replayed:      {result['frames_replayed']}")
    print(f"  Missing payloads:     {result['frames_missing_payload']}")
    print(f"  Mismatches:           {result['mismatches']}")
    print(f"  Hashes match:         {result['hashes_match']}")
    print(f"    original:           {result['original_verdict_hash'][:24]}...")
    print(f"    replay:             {result['replay_verdict_hash'][:24] if result['replay_verdict_hash'] else 'N/A'}...")
    print(f"  metric_schema:        {result['metric_schema_verified']}")
    print(f"  PSEUDO hash:          {result['pseudo_code_hash'][:24]}...")
    print(f"  Gap closed (GAP-16):  {result['gap_closed']}")
    print(f"  Evidence hash:        {result['evidence_hash'][:24]}...")
    print()
    sys.exit(0 if result["overall_status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
