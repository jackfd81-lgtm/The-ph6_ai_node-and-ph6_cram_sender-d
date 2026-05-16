#!/usr/bin/env python3
"""
PH6 EVC-04 — Payload Replay Verdict and Metric Comparison

Replays the EVC-02 deterministic payload stream (seed=42, 300 frames)
and proves byte-equivalent verdict and fixed-point metric outputs.

This closes the named open gap in VRC-1.0:
  "verdict_metric_payload_replay" — comparison that requires payload access.

Pass criteria:
  1. Same seed, same frame count as EVC-02
  2. Every replay verdict == original verdict
  3. Every replay entropy_fp == original entropy_fp
  4. Every replay laplacian_var_fp == original laplacian_var_fp
  5. Every replay motion_fraction_fp == original motion_fraction_fp
  6. metric_schema matches: ph6.metrics.fixedpoint.v1
  7. metric_scale matches: 10000
  8. PSEUDO code hash recorded (hash of verdict_logger.py)
  9. Generator hash recorded (hash of payload generation function source)
  10. replay_verdict_hash == original_verdict_hash (canonical hash of all verdicts)

This is NOT "something similar." It must be byte-equivalent or fail.
"""

from __future__ import annotations

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

# ── EVC-02 baseline ───────────────────────────────────────────────────────────

EVC02_DIR   = HERE / "validation_runs" / "evc02_20260516T110650Z"
EVC02_SEED  = 42
EVC02_FRAMES = 300
EXPECTED_METRIC_SCHEMA = "ph6.metrics.fixedpoint.v1"
EXPECTED_METRIC_SCALE  = 10000


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _blake2b(data: bytes) -> str:
    return hashlib.blake2b(data, digest_size=32).hexdigest()


def _canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False,
                      allow_nan=False, separators=(",", ":"))


def _make_payload(frame_id: int, seed: int) -> bytes:
    """Identical generator to evc02_long_run.py — must not diverge."""
    h = hashlib.blake2b(f"{seed}:{frame_id}".encode(), digest_size=32).digest()
    return bytes([(h[j % 32] % 180) + 25 for j in range(300)])


def _pseudo_code_hash() -> str:
    """BLAKE2b-256 of the verdict_logger.py source file."""
    path = Path(_vl_module.__file__)
    return _blake2b(path.read_bytes())


def _generator_source_hash() -> str:
    """BLAKE2b-256 of the _make_payload function source (this file's generator)."""
    src = inspect.getsource(_make_payload)
    return _blake2b(src.encode("utf-8"))


def _load_original_verdicts() -> list[dict]:
    log = EVC02_DIR / "verdict_log.jsonl"
    if not log.exists():
        sys.exit(f"FATAL: EVC-02 verdict log not found: {log}")
    return [json.loads(line) for line in log.read_text().splitlines() if line.strip()]


def _original_verdict_hash(verdicts: list[dict]) -> str:
    """Canonical hash of the ordered list of original verdict records."""
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


def run_evc04() -> dict:
    now     = _utc_now()
    slug    = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = HERE / "validation_runs" / f"evc04_{slug}"
    out_dir.mkdir(parents=True, exist_ok=True)

    originals = _load_original_verdicts()
    if len(originals) != EVC02_FRAMES:
        sys.exit(f"FATAL: expected {EVC02_FRAMES} original verdicts, found {len(originals)}")

    pseudo_hash    = _pseudo_code_hash()
    generator_hash = _generator_source_hash()

    print(f"\n  EVC-04: Payload replay — {EVC02_FRAMES} frames (seed={EVC02_SEED})")
    print(f"  PSEUDO code hash:    {pseudo_hash[:24]}...")
    print(f"  Generator hash:      {generator_hash[:24]}...")

    # Run replay using an in-memory VerdictLogger (temp file, discarded after)
    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as tf:
        tmp_log = Path(tf.name)

    replay_logger = VerdictLogger(tmp_log)

    mismatches: list[dict] = []
    t0 = time.monotonic()

    for orig in originals:
        frame_id    = orig["frame_id"]
        payload     = _make_payload(frame_id, EVC02_SEED)
        payload_hash = _blake2b(payload)

        # Verify payload hash matches what EVC-02 recorded
        if payload_hash != orig.get("input_hash"):
            mismatches.append({
                "frame_id": frame_id,
                "type":     "payload_hash_mismatch",
                "expected": orig.get("input_hash"),
                "observed": payload_hash,
            })
            continue

        replay_rec = replay_logger.log(frame_id, payload, payload_hash)

        # Compare verdict
        if replay_rec["verdict"] != orig["verdict"]:
            mismatches.append({
                "frame_id": frame_id,
                "type":     "verdict_mismatch",
                "expected": orig["verdict"],
                "observed": replay_rec["verdict"],
            })

        # Compare fixed-point metrics (exact match required)
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

        # Compare metric_schema and metric_scale
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

    # Read replay records before cleanup
    replay_records = [json.loads(l) for l in
                      Path(replay_logger.log_path).read_text().splitlines() if l.strip()]
    tmp_log.unlink(missing_ok=True)

    orig_hash   = _original_verdict_hash(originals)
    replay_hash = _original_verdict_hash(replay_records)
    hashes_match = orig_hash == replay_hash

    if not hashes_match:
        mismatches.append({
            "type":     "verdict_hash_mismatch",
            "expected": orig_hash,
            "observed": replay_hash,
        })

    passed = len(mismatches) == 0

    # Seal evidence receipt
    body = {
        "schema":               "ph6.evc04_receipt.v1",
        "campaign_id":          "EVC-04",
        "campaign_name":        "Payload Replay Verdict and Metric Comparison",
        "overall_status":       "PASS" if passed else "FAIL",
        "frames_replayed":      EVC02_FRAMES,
        "seed":                 EVC02_SEED,
        "mismatches":           len(mismatches),
        "mismatch_details":     mismatches,
        "pseudo_code_hash":     pseudo_hash,
        "generator_hash":       generator_hash,
        "original_verdict_hash": orig_hash,
        "replay_verdict_hash":  replay_hash,
        "hashes_match":         hashes_match,
        "metric_schema_verified": EXPECTED_METRIC_SCHEMA,
        "metric_scale_verified":  EXPECTED_METRIC_SCALE,
        "evc02_baseline_dir":   str(EVC02_DIR),
        "elapsed_s":            round(elapsed, 3),
        "authority":            "VERIFY_ONLY",
        "closes_gap":           "verdict_metric_payload_replay" if passed else None,
        "gap_closed":           passed,
        "production_clearance": False,
        "open_stop_ship_gates": ["OI-01", "OI-03"],
        "timestamp_utc":        now,
    }
    body["evidence_hash"] = _blake2b(
        _canonical({k: v for k, v in body.items() if k != "evidence_hash"}).encode()
    )

    out_path = out_dir / "ph6.evc04_receipt.v1.json"
    out_path.write_text(_canonical(body) + "\n")
    return body


def main() -> None:
    result = run_evc04()
    print()
    print(f"  Overall:         {result['overall_status']}")
    print(f"  Frames replayed: {result['frames_replayed']}")
    print(f"  Mismatches:      {result['mismatches']}")
    print(f"  Hashes match:    {result['hashes_match']}")
    print(f"    original:      {result['original_verdict_hash'][:24]}...")
    print(f"    replay:        {result['replay_verdict_hash'][:24]}...")
    print(f"  metric_schema:   {result['metric_schema_verified']}")
    print(f"  metric_scale:    {result['metric_scale_verified']}")
    print(f"  PSEUDO hash:     {result['pseudo_code_hash'][:24]}...")
    print(f"  Generator hash:  {result['generator_hash'][:24]}...")
    print(f"  Gap closed:      {result['gap_closed']}")
    print(f"  Evidence hash:   {result['evidence_hash'][:24]}...")
    print()
    sys.exit(0 if result["overall_status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
