"""
CRAM-PU verdict logger.
PSEUDO verdict: deterministic, pure-stdlib, SoSo advisory only.
SoSo never alters verdict — authority NONE throughout.

Canonical PH6 PSEUDO metrics (stdlib/synthetic path):
  entropy_fp       — Shannon entropy in bits; gate: entropy >= ENTROPY_MIN
  laplacian_var_fp — 1-D second-difference variance; gate: lap_var >= LAP1D_MIN
  motion_fraction_fp — fraction of bytes differing > 15 from previous frame;
                       REPORTED but NOT gated in this synthetic path.
                       Real-camera motion gate lives in cram_pu_verdict_runner.py.

Metrics use Decimal ROUND_HALF_EVEN fixed-point (4 decimal places).
Raw floats are forbidden in the Lane-1 authority path.
"""

import json
import math
import os
import time
from collections import Counter
from pathlib import Path

from ph6.cram_pu.schemas.canonical import fp_int

ENTROPY_MIN = 1.0    # bits — reject near-constant / zero-information payloads
LAP1D_MIN   = 500.0  # 1-D laplacian variance — reject flat byte signals

_MOTION_DIFF_THRESHOLD = 15  # byte-level diff threshold (matches cram_pu_verdict_runner)


def _append_jsonl(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, sort_keys=True, separators=(",", ":"),
                           ensure_ascii=False, allow_nan=False))
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())


def _pseudo_metrics(payload: bytes, prev_payload: bytes | None) -> dict:
    """
    Compute canonical PSEUDO metrics as fixed-point integers.
    No raw floats in the authority path.
    """
    if not payload:
        return {
            "entropy_fp":         0,
            "laplacian_var_fp":   0,
            "motion_fraction_fp": 0,
        }

    n = len(payload)

    # Shannon entropy (bits)
    counts = Counter(payload)
    h = 0.0
    for c in counts.values():
        p = c / n
        h -= p * math.log2(p)

    # 1-D Laplacian variance (second differences)
    if n >= 3:
        laps = [payload[i] - 2 * payload[i - 1] + payload[i - 2]
                for i in range(2, n)]
        lmean = sum(laps) / len(laps)
        lvar = sum((x - lmean) ** 2 for x in laps) / len(laps)
    else:
        lvar = 0.0

    # Motion fraction (cross-frame byte diff > threshold)
    if prev_payload is not None:
        pn = min(n, len(prev_payload))
        changed = sum(
            1 for a, b in zip(payload[:pn], prev_payload[:pn])
            if abs(a - b) > _MOTION_DIFF_THRESHOLD
        )
        mf = changed / pn if pn > 0 else 0.0
    else:
        mf = 0.0

    return {
        "entropy_fp":         fp_int(h),
        "laplacian_var_fp":   fp_int(lvar),
        "motion_fraction_fp": fp_int(mf),
    }


def _pseudo_verdict(metrics: dict) -> tuple:
    reasons = []
    ent = metrics["entropy_fp"]
    lv  = metrics["laplacian_var_fp"]
    # motion_fraction_fp is reported but not gated in the synthetic path
    if ent < fp_int(ENTROPY_MIN):  reasons.append("entropy_low")
    if lv  < fp_int(LAP1D_MIN):   reasons.append("blur_low_detail")
    return ("PASS" if not reasons else "DROP"), reasons


def _soso_advisory(metrics: dict) -> dict:
    ent = metrics["entropy_fp"]
    if ent > fp_int(6.0):   state = "STABLE"
    elif ent > fp_int(3.0): state = "MODERATE"
    else:                    state = "UNSTABLE"
    return {"state": state, "authority": "NONE"}


class VerdictLogger:
    def __init__(self, log_path: Path):
        self.log_path = log_path
        self._prev_payload: bytes | None = None

    def log(self, frame_id: int, payload: bytes,
            payload_hash: str) -> dict:
        metrics = _pseudo_metrics(payload, self._prev_payload)
        verdict, reasons = _pseudo_verdict(metrics)
        soso = _soso_advisory(metrics)
        self._prev_payload = payload
        record = {
            "schema":              "ph6.pseudo_verdict.v2",
            "frame_id":            frame_id,
            "verdict":             verdict,
            "reasons":             reasons,
            "metrics":             metrics,
            "motion_gate":         "SYNTHETIC_BYPASS",
            "input_hash":          payload_hash,
            "hash_algorithm":      "BLAKE2b-256",
            "fixed_point_scale":   10000,
            "authority":           "LANE_1",
            "soso_advisory":       soso,
            "timestamp_utc":       time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        _append_jsonl(self.log_path, record)
        return record
