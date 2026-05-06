"""
PH6 / CRAM-PU — Canonical Helpers

Lane: 1 (authority support)
Purpose: shared canonical JSON, BLAKE2b-256, and fixed-point encoding.

All Lane-1 authority paths must use these helpers.
No alternate serializer is permitted in the authority path.
"""

from __future__ import annotations

import hashlib
import json
from decimal import Decimal, ROUND_HALF_EVEN
from typing import Any

# Fixed-point scale: 4 decimal places (1/10000)
C1_SCALE = Decimal("10000")

ALLOWED_EVENT_TYPES = frozenset({
    "CRAM0_INTAKE",
    "PSEUDO_MEASURE",
    "PSEUDO_ADJUDICATE",
    "CRAM_PASS_COMMIT",
    "CRAM_DROP_COMMIT",
    "CRAM_RECOVERY",
    "EXPORT_START",
    "EXPORT_COMPLETE",
    "RECOVERY_SWEEP",
    "DRIFT_FAIL",
})

FORBIDDEN_EVENT_TYPES = frozenset({
    "PROMOTE",
    "REJECT",
    "ACCEPT",
    "FLAG",
    "HOLD",
    "REVIEW",
    "RETAIN",
})


def canonical_json(obj: Any) -> bytes:
    """
    PH6 canonical JSON serialization.

    Required: sort_keys, no NaN, UTF-8, compact separators.
    Same input always produces the same bytes and the same BLAKE2b-256 hash.
    """
    return json.dumps(
        obj,
        ensure_ascii=False,
        sort_keys=True,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")


def blake2b_256(data: bytes) -> str:
    """
    BLAKE2b-256 hash. Primary evidentiary hash for PH6.
    Returns lowercase 64-character hex string.
    """
    h = hashlib.blake2b(digest_size=32)
    h.update(data)
    return h.hexdigest()


def blake2b_256_obj(obj: Any) -> str:
    """Canonical JSON + BLAKE2b-256 in one call."""
    return blake2b_256(canonical_json(obj))


def fp_int(value: Any) -> int:
    """
    Convert a numeric value to a fixed-point integer (4 decimal places).

    Uses Decimal ROUND_HALF_EVEN to avoid float rounding bias.
    Raises ValueError for non-finite values (NaN, Infinity).

    Example: fp_int(3.5) → 35000
    """
    d = Decimal(str(value))
    if not d.is_finite():
        raise ValueError(f"non-finite value forbidden in Lane-1 path: {value!r}")
    return int((d * C1_SCALE).to_integral_value(rounding=ROUND_HALF_EVEN))


def fp_from_int(fp: int) -> Decimal:
    """Reverse fixed-point: integer → Decimal with 4 decimal places."""
    return Decimal(fp) / C1_SCALE


def validate_event_type(event_type: str) -> None:
    """Raise ValueError if event_type is forbidden or unknown."""
    if event_type in FORBIDDEN_EVENT_TYPES:
        raise ValueError(
            f"Forbidden event type {event_type!r}. "
            f"Allowed: {sorted(ALLOWED_EVENT_TYPES)}"
        )
    if event_type not in ALLOWED_EVENT_TYPES:
        raise ValueError(
            f"Unknown event type {event_type!r}. "
            f"Allowed: {sorted(ALLOWED_EVENT_TYPES)}"
        )
