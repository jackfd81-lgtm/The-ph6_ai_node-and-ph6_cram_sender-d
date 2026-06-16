#!/usr/bin/env python3
"""
PH6 PSEUDO-M + PSEUDO-A

Lane 1. Measurement authority + PASS/DROP verdict authority.
SoSo, Tokens, AI have zero authority over verdicts issued here.

PASS/DROP is issued by PseudoA only.
motion_fraction is the only permitted motion metric.
BLAKE2b-256 (digest_size=32) is the canonical measurement hash.
SHA-256 is the raw frame hash (compatibility sidecar).
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, Optional, Tuple

import cv2
import numpy as np

PERMITTED_MOTION_FIELD = "motion_fraction"

PASS = "PASS"
DROP = "DROP"

DROP_FRAME_READ_FAILED   = "FRAME_READ_FAILED"
DROP_EMPTY_FRAME         = "EMPTY_FRAME"
DROP_DIMENSION_CHANGE    = "DIMENSION_CHANGE"
DROP_TIMESTAMP_REVERSAL  = "TIMESTAMP_REVERSAL"
DROP_HASH_ERROR          = "HASH_ERROR"
DROP_MEASUREMENT_ERROR   = "MEASUREMENT_ERROR"
DROP_EXTREME_BLUR        = "EXTREME_BLUR"
DROP_EXTREME_BLACK_FRAME = "EXTREME_BLACK_FRAME"
DROP_EXTREME_WHITE_FRAME = "EXTREME_WHITE_FRAME"

ALL_DROP_REASONS = frozenset({
    DROP_FRAME_READ_FAILED, DROP_EMPTY_FRAME, DROP_DIMENSION_CHANGE,
    DROP_TIMESTAMP_REVERSAL, DROP_HASH_ERROR, DROP_MEASUREMENT_ERROR,
    DROP_EXTREME_BLUR, DROP_EXTREME_BLACK_FRAME, DROP_EXTREME_WHITE_FRAME,
})

# Deterministic thresholds — immutable, never overridden by advisory layers
_BLUR_DROP_LOW    = 0.3    # Laplacian variance below → EXTREME_BLUR
                            # Calibrated for MJPEG 1280x720: LIGHT floor ~0.47,
                            # calibration floor ~1.49 (BLUR_CAL_720p.json 2026-06-01)
                            # Ratified by jack 2026-06-01
_LUMA_BLACK_MAX   = 3.0    # mean luma below → EXTREME_BLACK_FRAME
_LUMA_WHITE_MIN   = 252.0  # mean luma above → EXTREME_WHITE_FRAME
_MOTION_PIX_DIFF  = 15     # pixel diff threshold for motion_fraction


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _blake2b256_hex(data: bytes) -> str:
    return hashlib.blake2b(data, digest_size=32).hexdigest()


def _canonical_measurement_hash(m: Dict[str, Any]) -> str:
    fields = [
        "frame_number", "timestamp_monotonic_ns", "capture_delta_ms",
        "width", "height", "mean_luma", "std_luma", "blur_laplacian",
        "motion_fraction", "frame_hash_sha256",
    ]
    payload = json.dumps(
        {k: m[k] for k in fields},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return _blake2b256_hex(payload)


class PseudoM:
    """Deterministic per-frame measurement. Lane 1."""

    def __init__(self, expected_width: int, expected_height: int) -> None:
        self.expected_width  = expected_width
        self.expected_height = expected_height
        self._prev_gray: Optional[np.ndarray] = None
        self._prev_ts_ns: Optional[int] = None

    def measure(
        self,
        frame: Optional[np.ndarray],
        frame_number: int,
        timestamp_ns: int,
    ) -> Dict[str, Any]:
        capture_delta_ms = (
            (timestamp_ns - self._prev_ts_ns) / 1_000_000.0
            if self._prev_ts_ns is not None
            else 0.0
        )

        if frame is None or frame.size == 0:
            rec: Dict[str, Any] = {
                "frame_number": frame_number,
                "timestamp_monotonic_ns": timestamp_ns,
                "capture_delta_ms": round(capture_delta_ms, 3),
                "width": 0,
                "height": 0,
                "mean_luma": 0.0,
                "std_luma": 0.0,
                "blur_laplacian": 0.0,
                "motion_fraction": 0.0,
                "frame_hash_sha256": "",
                "measurement_hash_blake2b256": "",
                "_null_frame": True,
            }
            self._prev_ts_ns = timestamp_ns
            return rec

        h, w = frame.shape[:2]
        gray = (
            cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            if frame.ndim == 3
            else frame.copy()
        )

        mean_luma = float(np.mean(gray))
        std_luma  = float(np.std(gray))

        try:
            blur_lap = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        except Exception:
            blur_lap = 0.0

        if self._prev_gray is not None and self._prev_gray.shape == gray.shape:
            diff = np.abs(gray.astype(np.int16) - self._prev_gray.astype(np.int16))
            motion_fraction = float(np.mean(diff > _MOTION_PIX_DIFF))
        else:
            motion_fraction = 0.0

        frame_hash = _sha256_hex(frame.tobytes())

        rec = {
            "frame_number": frame_number,
            "timestamp_monotonic_ns": timestamp_ns,
            "capture_delta_ms": round(capture_delta_ms, 3),
            "width": w,
            "height": h,
            "mean_luma": round(mean_luma, 4),
            "std_luma": round(std_luma, 4),
            "blur_laplacian": round(blur_lap, 4),
            "motion_fraction": round(motion_fraction, 6),
            "frame_hash_sha256": frame_hash,
            "measurement_hash_blake2b256": "",
        }
        rec["measurement_hash_blake2b256"] = _canonical_measurement_hash(rec)

        self._prev_gray  = gray
        self._prev_ts_ns = timestamp_ns
        return rec


class PseudoA:
    """PASS/DROP verdict authority. Lane 1. Advisory layers have zero authority."""

    def __init__(self, expected_width: int, expected_height: int) -> None:
        self.expected_width  = expected_width
        self.expected_height = expected_height
        self._prev_ts_ns: Optional[int] = None

    def verdict(self, m: Dict[str, Any]) -> Tuple[str, Optional[str]]:
        """Return (verdict, drop_reason). verdict ∈ {PASS, DROP}."""

        if m.get("_null_frame"):
            return DROP, DROP_FRAME_READ_FAILED

        if m["width"] == 0 or m["height"] == 0:
            return DROP, DROP_EMPTY_FRAME

        if m["width"] != self.expected_width or m["height"] != self.expected_height:
            return DROP, DROP_DIMENSION_CHANGE

        if (
            self._prev_ts_ns is not None
            and m["timestamp_monotonic_ns"] < self._prev_ts_ns
        ):
            return DROP, DROP_TIMESTAMP_REVERSAL

        if not m["frame_hash_sha256"] or not m["measurement_hash_blake2b256"]:
            return DROP, DROP_HASH_ERROR

        if m["blur_laplacian"] < _BLUR_DROP_LOW:
            return DROP, DROP_EXTREME_BLUR

        if m["mean_luma"] < _LUMA_BLACK_MAX:
            return DROP, DROP_EXTREME_BLACK_FRAME

        if m["mean_luma"] > _LUMA_WHITE_MIN:
            return DROP, DROP_EXTREME_WHITE_FRAME

        self._prev_ts_ns = m["timestamp_monotonic_ns"]
        return PASS, None
