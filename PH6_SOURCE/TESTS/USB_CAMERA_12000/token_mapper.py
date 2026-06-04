#!/usr/bin/env python3
"""
PH6 Token Mapper — Advisory symbolic behavior compression.

Authority: ZERO
Tokens do not affect PSEUDO-A verdicts.
Tokens are symbolic labels only.
advisory_only: True on every record.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

TOKEN_STABLE_SCENE         = "TOKEN_STABLE_SCENE"
TOKEN_LIGHT_SHIFT          = "TOKEN_LIGHT_SHIFT"
TOKEN_MOTION_PRESENT       = "TOKEN_MOTION_PRESENT"
TOKEN_MOTION_LOW           = "TOKEN_MOTION_LOW"
TOKEN_MOTION_HIGH          = "TOKEN_MOTION_HIGH"
TOKEN_BLUR_LOW             = "TOKEN_BLUR_LOW"
TOKEN_BLUR_HIGH            = "TOKEN_BLUR_HIGH"
TOKEN_TIMESTAMP_STABLE     = "TOKEN_TIMESTAMP_STABLE"
TOKEN_TIMESTAMP_JITTER     = "TOKEN_TIMESTAMP_JITTER"
TOKEN_FRAME_DUPLICATE      = "TOKEN_FRAME_DUPLICATE"
TOKEN_FRAME_DROP_SUSPECT   = "TOKEN_FRAME_DROP_SUSPECT"
TOKEN_AUTOFOCUS_SHIFT      = "TOKEN_AUTOFOCUS_SHIFT"
TOKEN_EXPOSURE_SHIFT       = "TOKEN_EXPOSURE_SHIFT"
TOKEN_USB_JITTER           = "TOKEN_USB_JITTER"
TOKEN_CAMERA_RESET_SUSPECT = "TOKEN_CAMERA_RESET_SUSPECT"
TOKEN_PSEUDO_DROP          = "TOKEN_PSEUDO_DROP"
TOKEN_SOSO_WATCH           = "TOKEN_SOSO_WATCH"
TOKEN_SOSO_DRIFT           = "TOKEN_SOSO_DRIFT"

ALL_TOKENS = [
    TOKEN_STABLE_SCENE, TOKEN_LIGHT_SHIFT, TOKEN_MOTION_PRESENT,
    TOKEN_MOTION_LOW, TOKEN_MOTION_HIGH, TOKEN_BLUR_LOW, TOKEN_BLUR_HIGH,
    TOKEN_TIMESTAMP_STABLE, TOKEN_TIMESTAMP_JITTER, TOKEN_FRAME_DUPLICATE,
    TOKEN_FRAME_DROP_SUSPECT, TOKEN_AUTOFOCUS_SHIFT, TOKEN_EXPOSURE_SHIFT,
    TOKEN_USB_JITTER, TOKEN_CAMERA_RESET_SUSPECT, TOKEN_PSEUDO_DROP,
    TOKEN_SOSO_WATCH, TOKEN_SOSO_DRIFT,
]

# Advisory thresholds — never affect PSEUDO-A
_MOTION_LOW_THRESH  = 0.01
_MOTION_HIGH_THRESH = 0.15
_BLUR_LOW_THRESH    = 30.0
_BLUR_HIGH_THRESH   = 300.0

# Advisory instability token states
_SOSO_DRIFT_STATES = frozenset({"DRIFTING", "UNSTABLE", "RESET_SUSPECTED"})


class TokenMapper:
    """Advisory symbolic behavior compression. Authority ZERO."""

    def __init__(self, target_fps: float = 15.0) -> None:
        self._target_delta_ms = 1000.0 / max(target_fps, 1.0)

    def map_frame(
        self,
        measurement: Dict[str, Any],
        verdict: str,
        drop_reason: Optional[str],
        soso_record: Dict[str, Any],
    ) -> Dict[str, Any]:
        tokens: List[str] = []

        motion      = measurement.get("motion_fraction", 0.0)
        blur        = measurement.get("blur_laplacian", 0.0)
        delta_ms    = measurement.get("capture_delta_ms", 0.0)
        drift_flags = soso_record.get("drift_flags", [])
        soso_state  = soso_record.get("soso_state", "STABLE")

        # Motion tokens
        if motion > _MOTION_LOW_THRESH:
            tokens.append(TOKEN_MOTION_PRESENT)
            tokens.append(
                TOKEN_MOTION_HIGH if motion > _MOTION_HIGH_THRESH else TOKEN_MOTION_LOW
            )

        # Blur tokens
        if blur < _BLUR_LOW_THRESH:
            tokens.append(TOKEN_BLUR_LOW)
        elif blur > _BLUR_HIGH_THRESH:
            tokens.append(TOKEN_BLUR_HIGH)

        # Brightness / focus / exposure shift
        if "luma_shift" in drift_flags:
            tokens.append(TOKEN_LIGHT_SHIFT)
            if "blur_shift" in drift_flags:
                tokens.append(TOKEN_AUTOFOCUS_SHIFT)
            else:
                tokens.append(TOKEN_EXPOSURE_SHIFT)
        elif "blur_shift" in drift_flags:
            tokens.append(TOKEN_AUTOFOCUS_SHIFT)

        # Timestamp tokens
        jitter = delta_ms > self._target_delta_ms * 2.5 if delta_ms > 0 else False
        if jitter or "timestamp_jitter" in drift_flags:
            tokens.append(TOKEN_TIMESTAMP_JITTER)
            tokens.append(TOKEN_USB_JITTER)
        else:
            tokens.append(TOKEN_TIMESTAMP_STABLE)

        # Duplicate frame
        if "duplicate_frame" in drift_flags:
            tokens.append(TOKEN_FRAME_DUPLICATE)

        # PSEUDO drop tokens
        if verdict == "DROP":
            tokens.append(TOKEN_PSEUDO_DROP)
            tokens.append(TOKEN_FRAME_DROP_SUSPECT)

        # Camera reset
        if "reset_signal" in drift_flags or soso_state == "RESET_SUSPECTED":
            tokens.append(TOKEN_CAMERA_RESET_SUSPECT)

        # SoSo advisory state tokens
        if soso_state == "WATCH":
            tokens.append(TOKEN_SOSO_WATCH)
        elif soso_state in _SOSO_DRIFT_STATES:
            tokens.append(TOKEN_SOSO_DRIFT)

        # Stable scene: nothing interesting observed
        noise_tokens = {
            TOKEN_MOTION_HIGH, TOKEN_LIGHT_SHIFT, TOKEN_TIMESTAMP_JITTER,
            TOKEN_BLUR_LOW, TOKEN_PSEUDO_DROP, TOKEN_SOSO_DRIFT,
            TOKEN_CAMERA_RESET_SUSPECT,
        }
        if not any(t in noise_tokens for t in tokens):
            tokens.append(TOKEN_STABLE_SCENE)

        unique = sorted(set(tokens))
        return {
            "frame": measurement["frame_number"],
            "tokens": unique,
            "token_count": len(unique),
            "advisory_only": True,
        }
