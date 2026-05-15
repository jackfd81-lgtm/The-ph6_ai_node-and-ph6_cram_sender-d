"""
PH6 / CRAM-PU — Calibration Gate Replay Parity Proof

Runs laplacian_variance, brightness_mean, and contrast_stddev twice on two
anchor frames.  Asserts byte-identical metric hashes across both runs.
Emits a sealed JSON receipt.

Lane: 1 (arithmetic only — no model inference)
Authority: NONE
Ref: PH6-CALIBRATION-GATE-BLOCK-v1.0 §6
"""

from __future__ import annotations

import sys
import json
import time
import hashlib
import datetime
from pathlib import Path

import cv2
import numpy as np

# Resolve the cram_pu package from this tools/ subdirectory
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from ph6.cram_pu.schemas.canonical import canonical_json, blake2b_256, fp_int


ANCHORS = {
    "anchor_soft": Path(
        "/home/jack/frame_filter/frames_pseudo_soso_5min_4/frame_001130.jpg"
    ),
    "anchor_sharp": Path(
        "/home/jack/frame_filter/frames_ph6_forced_drop_20260428_090045/frame_000001.jpg"
    ),
}


def compute_metrics(image_path: Path) -> dict:
    """Compute deterministic Lane-1 image quality metrics from raw bytes."""
    raw_bytes = image_path.read_bytes()
    arr = np.frombuffer(raw_bytes, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise ValueError(f"cv2 could not decode {image_path}")

    brightness_mean   = float(np.mean(img))
    contrast_stddev   = float(np.std(img))
    laplacian_variance = float(cv2.Laplacian(img, cv2.CV_64F).var())

    return {
        "brightness_mean":    fp_int(brightness_mean),
        "contrast_stddev":    fp_int(contrast_stddev),
        "laplacian_variance": fp_int(laplacian_variance),
    }


def apply_blur_gate(lv_fp: int) -> str:
    """Return gate verdict string from fixed-point laplacian_variance."""
    lv = lv_fp / 10000.0
    if lv < 25.0:
        return "DROP"
    if lv < 80.0:
        return "WARN"
    return "PASS"


def apply_exposure_gate(bm_fp: int) -> str:
    bm = bm_fp / 10000.0
    if bm < 60.0:
        return "LOW_LIGHT_WARN"
    if bm > 190.0:
        return "OVERBRIGHT_WARN"
    return "nominal"


def run_proof() -> dict:
    ts_start = time.time()
    results = {}

    for anchor_id, path in ANCHORS.items():
        if not path.exists():
            raise FileNotFoundError(f"Anchor image not found: {path}")

        raw_hash = blake2b_256(path.read_bytes())

        run_1 = compute_metrics(path)
        run_2 = compute_metrics(path)

        payload_1 = {"anchor": anchor_id, "metrics": run_1}
        payload_2 = {"anchor": anchor_id, "metrics": run_2}

        hash_1 = blake2b_256(canonical_json(payload_1))
        hash_2 = blake2b_256(canonical_json(payload_2))

        parity = hash_1 == hash_2

        blur_verdict     = apply_blur_gate(run_1["laplacian_variance"])
        exposure_verdict = apply_exposure_gate(run_1["brightness_mean"])

        results[anchor_id] = {
            "image_path":       str(path),
            "raw_bytes_hash":   raw_hash,
            "run_1_hash":       hash_1,
            "run_2_hash":       hash_2,
            "parity":           parity,
            "metrics_fp":       run_1,
            "blur_gate":        blur_verdict,
            "exposure_gate":    exposure_verdict,
        }

        status = "PASS" if parity else "DRIFT_FAIL"
        print(f"  {anchor_id}: parity={status}  blur={blur_verdict}  "
              f"lv={run_1['laplacian_variance']/10000:.1f}  bm={run_1['brightness_mean']/10000:.1f}")

    all_pass = all(v["parity"] for v in results.values())
    verdict  = "REPLAY_PARITY_PASS" if all_pass else "REPLAY_PARITY_DRIFT_FAIL"

    receipt = {
        "schema":         "ph6.calibration_gate.replay_parity.v1",
        "document_ref":   "PH6-CALIBRATION-GATE-BLOCK-v1.0",
        "hash_algorithm": "BLAKE2b-256",
        "authority":      "LANE_1",
        "ai_authority":   "NONE",
        "timestamp":      ts_start,
        "iso_timestamp":  datetime.datetime.fromtimestamp(
                              ts_start, datetime.timezone.utc
                          ).strftime("%Y%m%dT%H%M%SZ"),
        "verdict":        verdict,
        "anchors":        results,
        "notes": (
            "anchor_soft laplacian=76.9 (WARN boundary — DROP-zone fixture images "
            "not available locally; replay parity proof holds at any laplacian value)"
        ),
    }

    receipt_bytes  = canonical_json(receipt)
    receipt["receipt_hash"] = blake2b_256(receipt_bytes)

    return receipt


if __name__ == "__main__":
    print("PH6 Calibration Gate — Replay Parity Proof")
    print(f"Ref: PH6-CALIBRATION-GATE-BLOCK-v1.0 §6")
    print()

    receipt = run_proof()

    out_dir = Path("/home/jack/ph6/cram_pu/calibration")
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = receipt["iso_timestamp"]
    out_path = out_dir / f"replay_parity_receipt_{ts}.json"
    out_path.write_text(json.dumps(receipt, indent=2))

    print()
    print(f"Verdict : {receipt['verdict']}")
    print(f"Receipt : {out_path}")
    print(f"Hash    : {receipt['receipt_hash']}")

    if receipt["verdict"] != "REPLAY_PARITY_PASS":
        print("\nDRIFT_FAIL — schema promotion blocked.")
        sys.exit(1)
