"""
Phase 5 — CRAM-PU verdict runner.
Runs deterministic PSEUDO metrics on frame payload bytes.
SoSo is advisory only — authority NONE — and must not alter the verdict.
Writes verdicts.jsonl.

PSEUDO thresholds (fixed, deterministic):
  brightness_min:  20
  brightness_max: 235
  laplacian_min:   15.0
  motion_max:       0.40
"""

import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np

from ph6.cram_pu.schemas.canonical import fp_int

BRIGHT_MIN  = 20
BRIGHT_MAX  = 235
LAP_MIN     = 15.0
MOTION_MAX  = 0.40

# Precomputed fixed-point thresholds (scale 10000)
_FP_BRIGHT_MIN  = fp_int(BRIGHT_MIN)
_FP_BRIGHT_MAX  = fp_int(BRIGHT_MAX)
_FP_LAP_MIN     = fp_int(LAP_MIN)
_FP_MOTION_MAX  = fp_int(MOTION_MAX)


def _append_jsonl(path: Path, record: dict) -> None:
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, sort_keys=True, separators=(",", ":"),
                           ensure_ascii=False, allow_nan=False))
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())


def _decode_frame(payload: bytes) -> np.ndarray:
    arr = np.frombuffer(payload, dtype=np.uint8)
    frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if frame is None:
        # Treat raw bytes as flat gray if not a valid image
        side = max(1, int(len(payload) ** 0.5))
        gray_bytes = payload[:side * side]
        if len(gray_bytes) < side * side:
            gray_bytes = gray_bytes.ljust(side * side, b'\x80')
        frame = np.frombuffer(gray_bytes, dtype=np.uint8).reshape(side, side)
        frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
    return frame


def _pseudo_metrics(frame: np.ndarray, prev_gray=None) -> dict:
    """
    Compute PSEUDO metrics as fixed-point integers (scale 10000).
    No raw floats in the authority path.
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    mb   = float(np.mean(gray))
    lv   = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    if prev_gray is not None:
        diff = cv2.absdiff(gray, prev_gray)
        mf   = float(np.mean(diff > 15))
    else:
        mf   = 0.0
    return {
        "mean_brightness_fp": fp_int(mb),
        "laplacian_var_fp":   fp_int(lv),
        "motion_fraction_fp": fp_int(mf),
    }


def _pseudo_verdict(metrics: dict) -> tuple:
    reasons = []
    mb  = metrics["mean_brightness_fp"]
    lv  = metrics["laplacian_var_fp"]
    mf  = metrics["motion_fraction_fp"]
    if mb < _FP_BRIGHT_MIN:  reasons.append("brightness_low")
    if mb > _FP_BRIGHT_MAX:  reasons.append("brightness_high")
    if lv < _FP_LAP_MIN:     reasons.append("blur_low_detail")
    if mf > _FP_MOTION_MAX:  reasons.append("motion_high")
    return ("PASS" if not reasons else "DROP"), reasons


def _soso_advisory(metrics: dict) -> dict:
    """Advisory only. Authority NONE. Must not affect verdict."""
    mb = metrics["mean_brightness_fp"]
    if mb > fp_int(150):
        state = "STABLE"
    elif mb > fp_int(80):
        state = "MODERATE"
    else:
        state = "UNSTABLE"
    return {"state": state, "authority": "NONE"}


def run_verdicts(arrivals: list, payloads: dict,
                 verdict_log: Path) -> list:
    verdict_log.parent.mkdir(parents=True, exist_ok=True)
    results = []
    prev_gray = None
    for arr in arrivals:
        pid     = arr["packet_id"]
        payload = payloads.get(pid, b"")
        frame   = _decode_frame(payload)
        metrics = _pseudo_metrics(frame, prev_gray)
        verdict, reasons = _pseudo_verdict(metrics)
        soso    = _soso_advisory(metrics)   # advisory only, never changes verdict

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        prev_gray = gray

        record = {
            "schema":            "ph6.pseudo_verdict.v1",
            "packet_id":         pid,
            "verdict":           verdict,
            "reasons":           reasons,
            "metrics":           metrics,
            "fixed_point_scale": 10000,
            "input_hash":        arr["received_hash"],
            "hash_algorithm":    "BLAKE2b-256",
            "authority":         "LANE_1",
            "soso_advisory":     soso,
            "timestamp_utc":     datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        _append_jsonl(verdict_log, record)
        results.append(record)
    return results


if __name__ == "__main__":
    import argparse, base64
    ap = argparse.ArgumentParser()
    ap.add_argument("--arrival-log",   required=True)
    ap.add_argument("--payloads-json", required=True)
    ap.add_argument("--verdict-log",   required=True)
    args = ap.parse_args()

    with Path(args.arrival_log).open() as f:
        arrivals = [json.loads(l) for l in f if l.strip()]
    raw = json.loads(Path(args.payloads_json).read_text())
    payloads = {k: base64.b64decode(v) for k, v in raw.items()}
    results = run_verdicts(arrivals, payloads, Path(args.verdict_log))
    passes = sum(1 for r in results if r["verdict"] == "PASS")
    drops  = sum(1 for r in results if r["verdict"] == "DROP")
    print(f"VERDICTS: {len(results)} total  PASS={passes}  DROP={drops}")
