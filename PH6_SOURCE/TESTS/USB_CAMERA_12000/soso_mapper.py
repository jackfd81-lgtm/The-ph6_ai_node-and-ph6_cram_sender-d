#!/usr/bin/env python3
"""
PH6 SoSo — Advisory continuity mapper.

Authority: ZERO
advisory_only: True on every record.

SoSo observes and maps continuity across frames.
SoSo does not issue PASS or DROP.
SoSo output never overrides PSEUDO-A verdicts.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Dict, List, Optional

STABLE          = "STABLE"
WATCH           = "WATCH"
DRIFTING        = "DRIFTING"
UNSTABLE        = "UNSTABLE"
RESET_SUSPECTED = "RESET_SUSPECTED"

ALL_SOSO_STATES = (STABLE, WATCH, DRIFTING, UNSTABLE, RESET_SUSPECTED)

_WINDOW         = 30
_Z_WATCH        = 2.0
_Z_DRIFT        = 3.5
_Z_UNSTABLE     = 5.5
_RESET_BLUR_JUMP = 50.0
_RESET_LUMA_JUMP = 55.0


def _rolling_zscore(value: float, window: deque) -> float:
    if len(window) < 4:
        return 0.0
    vals = list(window)
    mean = sum(vals) / len(vals)
    variance = sum((v - mean) ** 2 for v in vals) / len(vals)
    std = variance ** 0.5
    if std < 1e-6:
        return 0.0
    return abs(value - mean) / std


class SoSoMapper:
    """Advisory continuity mapper. Authority ZERO."""

    def __init__(self) -> None:
        self._luma_win:   deque = deque(maxlen=_WINDOW)
        self._blur_win:   deque = deque(maxlen=_WINDOW)
        self._motion_win: deque = deque(maxlen=_WINDOW)
        self._delta_win:  deque = deque(maxlen=_WINDOW)
        self._prev_luma:  Optional[float] = None
        self._prev_blur:  Optional[float] = None
        self._seen_hashes: deque = deque(maxlen=_WINDOW * 3)

    def map_frame(
        self,
        measurement: Dict[str, Any],
        verdict: str,
        drop_reason: Optional[str],
    ) -> Dict[str, Any]:
        fn       = measurement["frame_number"]
        luma     = measurement.get("mean_luma", 0.0)
        blur     = measurement.get("blur_laplacian", 0.0)
        motion   = measurement.get("motion_fraction", 0.0)
        delta_ms = measurement.get("capture_delta_ms", 0.0)
        fhash    = measurement.get("frame_hash_sha256", "")

        drift_flags: List[str] = []
        observed_change = "NONE"

        # Duplicate frame detection
        if fhash and fhash in self._seen_hashes:
            drift_flags.append("duplicate_frame")
            observed_change = "DUPLICATE_FRAME"
        if fhash:
            self._seen_hashes.append(fhash)

        # Z-score anomaly detection against rolling windows
        luma_z   = _rolling_zscore(luma,     self._luma_win)
        blur_z   = _rolling_zscore(blur,     self._blur_win)
        motion_z = _rolling_zscore(motion,   self._motion_win)
        delta_z  = _rolling_zscore(delta_ms, self._delta_win) if delta_ms > 0 else 0.0

        # Reset detection: simultaneous large jump in blur + luma
        reset_suspect = False
        if self._prev_blur is not None and self._prev_luma is not None:
            if (abs(blur - self._prev_blur) > _RESET_BLUR_JUMP and
                    abs(luma - self._prev_luma) > _RESET_LUMA_JUMP):
                reset_suspect = True
                drift_flags.append("reset_signal")

        if luma_z > _Z_WATCH:
            drift_flags.append("luma_shift")
            if observed_change == "NONE":
                observed_change = "BRIGHTNESS_CHANGE"
        if blur_z > _Z_WATCH:
            drift_flags.append("blur_shift")
            if observed_change == "NONE":
                observed_change = "BLUR_CHANGE"
        if motion_z > _Z_WATCH:
            drift_flags.append("motion_change")
            if observed_change == "NONE":
                observed_change = "MOTION_CHANGE"
        if delta_z > _Z_WATCH:
            drift_flags.append("timestamp_jitter")
            if observed_change == "NONE":
                observed_change = "TIMESTAMP_JITTER"
        if verdict == "DROP":
            drift_flags.append("pseudo_drop_observed")

        # Determine SoSo state
        anomaly_count = sum(
            1 for z in (luma_z, blur_z, motion_z, delta_z)
            if z > _Z_WATCH
        )
        if reset_suspect:
            state = RESET_SUSPECTED
        elif any(z > _Z_UNSTABLE for z in (luma_z, blur_z, motion_z)):
            state = UNSTABLE
        elif anomaly_count >= 3 or any(z > _Z_DRIFT for z in (luma_z, blur_z, motion_z)):
            state = DRIFTING
        elif anomaly_count >= 1:
            state = WATCH
        else:
            state = STABLE

        # Update rolling windows for valid frames only
        if not measurement.get("_null_frame"):
            self._luma_win.append(luma)
            self._blur_win.append(blur)
            self._motion_win.append(motion)
            if delta_ms > 0:
                self._delta_win.append(delta_ms)
            self._prev_luma = luma
            self._prev_blur = blur

        return {
            "frame": fn,
            "soso_state": state,
            "continuity_class": _continuity_class(motion),
            "observed_change": observed_change,
            "drift_flags": sorted(set(drift_flags)),
            "luma_z": round(luma_z, 3),
            "blur_z": round(blur_z, 3),
            "motion_z": round(motion_z, 3),
            "timestamp_delta_z": round(delta_z, 3),
            "advisory_only": True,
        }


def _continuity_class(motion_fraction: float) -> str:
    if motion_fraction < 0.01:
        return "STATIC"
    if motion_fraction < 0.05:
        return "LOW_MOTION"
    if motion_fraction < 0.20:
        return "ROOM"
    return "HIGH_MOTION"
