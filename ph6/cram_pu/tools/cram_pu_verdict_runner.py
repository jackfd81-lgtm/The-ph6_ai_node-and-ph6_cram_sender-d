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
from pathlib import Path

import cv2
import numpy as np

BRIGHT_MIN  = 20
BRIGHT_MAX  = 235
LAP_MIN     = 15.0
MOTION_MAX  = 0.40


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
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    mb   = float(np.mean(gray))
    lv   = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    if prev_gray is not None:
        diff = cv2.absdiff(gray, prev_gray)
        mf   = float(np.mean(diff > 15))
    else:
        mf   = 0.0
    return {"mean_brightness": round(mb, 4),
            "laplacian_var":   round(lv, 4),
            "motion_fraction": round(mf, 4)}


def _pseudo_verdict(metrics: dict) -> tuple:
    reasons = []
    mb  = metrics["mean_brightness"]
    lv  = metrics["laplacian_var"]
    mf  = metrics["motion_fraction"]
    if mb < BRIGHT_MIN:  reasons.append("brightness_low")
    if mb > BRIGHT_MAX:  reasons.append("brightness_high")
    if lv < LAP_MIN:     reasons.append("blur_low_detail")
    if mf > MOTION_MAX:  reasons.append("motion_high")
    return ("PASS" if not reasons else "DROP"), reasons


def _soso_advisory(metrics: dict) -> dict:
    """Advisory only. Authority NONE. Must not affect verdict."""
    mb = metrics["mean_brightness"]
    if mb > 150:
        state, confidence = "STABLE", 0.85
    elif mb > 80:
        state, confidence = "MODERATE", 0.60
    else:
        state, confidence = "UNSTABLE", 0.30
    return {"state": state, "confidence": confidence, "authority": "NONE"}


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
            "schema":        "ph6.pseudo_verdict.v1",
            "packet_id":     pid,
            "verdict":       verdict,
            "reasons":       reasons,
            "metrics":       metrics,
            "input_hash":    arr["received_hash"],
            "authority":     "LANE_1",
            "soso_advisory": soso,
            "timestamp":     time.time(),
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
