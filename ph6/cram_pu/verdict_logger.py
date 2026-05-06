"""
CRAM-PU verdict logger.
PSEUDO verdict: deterministic, pure-stdlib, SoSo advisory only.
SoSo never alters verdict — authority NONE throughout.

PSEUDO thresholds:
  brightness_min:  20   (mean byte value)
  brightness_max: 235
  variance_min:    15.0 (byte variance — low-detail rejection)

Metrics use Decimal ROUND_HALF_EVEN fixed-point (4 decimal places).
Raw floats are forbidden in the Lane-1 authority path.
"""

import json
import os
import time
from pathlib import Path

from ph6.cram_pu.schemas.canonical import fp_int

BRIGHT_MIN = 20
BRIGHT_MAX = 235
VAR_MIN    = 15.0


def _append_jsonl(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, sort_keys=True, separators=(",", ":"),
                           ensure_ascii=False, allow_nan=False))
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())


def _pseudo_metrics(payload: bytes) -> dict:
    """
    Compute brightness and variance as fixed-point integers.
    No raw floats in the authority path.
    """
    if not payload:
        return {"mean_brightness_fp": 0, "byte_variance_fp": 0}
    n = len(payload)
    mean = sum(payload) / n
    variance = sum((b - mean) ** 2 for b in payload) / n
    return {
        "mean_brightness_fp": fp_int(mean),
        "byte_variance_fp":   fp_int(variance),
    }


def _pseudo_verdict(metrics: dict) -> tuple:
    reasons = []
    # Compare against fixed-point thresholds (4 decimal places)
    mb = metrics["mean_brightness_fp"]
    bv = metrics["byte_variance_fp"]
    if mb < fp_int(BRIGHT_MIN):  reasons.append("brightness_low")
    if mb > fp_int(BRIGHT_MAX):  reasons.append("brightness_high")
    if bv < fp_int(VAR_MIN):     reasons.append("low_detail")
    return ("PASS" if not reasons else "DROP"), reasons


def _soso_advisory(metrics: dict) -> dict:
    mb = metrics["mean_brightness_fp"]
    if mb > fp_int(150):   state = "STABLE"
    elif mb > fp_int(80):  state = "MODERATE"
    else:                  state = "UNSTABLE"
    return {"state": state, "authority": "NONE"}


class VerdictLogger:
    def __init__(self, log_path: Path):
        self.log_path = log_path

    def log(self, frame_id: int, payload: bytes,
            payload_hash: str) -> dict:
        metrics = _pseudo_metrics(payload)
        verdict, reasons = _pseudo_verdict(metrics)
        soso = _soso_advisory(metrics)
        record = {
            "schema":         "ph6.pseudo_verdict.v1",
            "frame_id":       frame_id,
            "verdict":        verdict,
            "reasons":        reasons,
            "metrics":        metrics,
            "input_hash":     payload_hash,
            "hash_algorithm": "BLAKE2b-256",
            "fixed_point_scale": 10000,
            "authority":      "LANE_1",
            "soso_advisory":  soso,
            "timestamp_utc":  time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        _append_jsonl(self.log_path, record)
        return record
