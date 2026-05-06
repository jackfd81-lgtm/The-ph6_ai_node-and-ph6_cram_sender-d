"""
TOK-1.0 Token Validation

Lane: 2
Authority: ZERO
Write domain: none (pure validation)

Validates token fields and config schemas without touching CRAM,
PSEUDO, EvidencePacket, or any Lane-1 component.
"""

from __future__ import annotations

from typing import List, Optional


REQUIRED_CONFIG_KEYS = {
    "N",
    "W_ms",
    "iou_min",
    "C_min",
    "VDT_TTL_ms",
    "VDT_inactive_prune_ms",
    "vdt_min_confidence",
    "promotion_window_ms",
    "VLT_max_lifetime_ms",
    "VLT_inactive_prune_ms",
    "vlt_min_confidence",
}


def validate_token_base(token) -> Optional[str]:
    """
    Return error string if token violates Authority ZERO invariants, else None.
    """
    if not getattr(token, "token_id", None):
        return "token_id is empty"

    if not getattr(token, "cram_ref_hash", None):
        return "cram_ref_hash is empty"

    if getattr(token, "authority", None) != "ZERO":
        return f"authority must be ZERO, got {token.authority!r}"

    if getattr(token, "advisory_only", None) is not True:
        return "advisory_only must be True"

    if getattr(token, "timestamp_ms", 0) <= 0:
        return "timestamp_ms must be positive"

    return None


def validate_cram_ref_hash(h: str) -> bool:
    """Return True if h looks like a plausible BLAKE2b-256 hex hash."""
    if not isinstance(h, str):
        return False
    h = h.strip()
    if len(h) != 64:
        return False
    try:
        int(h, 16)
        return True
    except ValueError:
        return False


def validate_config(config: dict) -> List[str]:
    """Return list of config errors. Empty list means config is valid."""
    errors = []

    if config.get("authority") != "ZERO":
        errors.append(f"config.authority must be ZERO, got {config.get('authority')!r}")

    if config.get("advisory_only") is not True:
        errors.append("config.advisory_only must be True")

    for key in REQUIRED_CONFIG_KEYS:
        if key not in config:
            errors.append(f"config missing required key: {key!r}")

    if "N" in config and config["N"] < 1:
        errors.append("config.N must be >= 1")

    if "iou_min" in config and not (0.0 <= config["iou_min"] <= 1.0):
        errors.append("config.iou_min must be in [0.0, 1.0]")

    if "C_min" in config and not (0.0 <= config["C_min"] <= 1.0):
        errors.append("config.C_min must be in [0.0, 1.0]")

    return errors


def validate_rt(rt) -> Optional[str]:
    err = validate_token_base(rt)
    if err:
        return err
    if getattr(rt, "token_type", None) != "RT":
        return f"expected token_type RT, got {rt.token_type!r}"
    return None


def validate_vdt(vdt) -> Optional[str]:
    err = validate_token_base(vdt)
    if err:
        return err
    if getattr(vdt, "token_type", None) != "VDT":
        return f"expected token_type VDT, got {vdt.token_type!r}"
    if getattr(vdt, "support_count", 0) < 1:
        return "VDT support_count must be >= 1"
    return None


def validate_vlt(vlt) -> Optional[str]:
    err = validate_token_base(vlt)
    if err:
        return err
    if getattr(vlt, "token_type", None) != "VLT":
        return f"expected token_type VLT, got {vlt.token_type!r}"
    if getattr(vlt, "first_seen_ms", 0) > getattr(vlt, "last_seen_ms", 0):
        return "VLT first_seen_ms must be <= last_seen_ms"
    if getattr(vlt, "support_count", 0) < 1:
        return "VLT support_count must be >= 1"
    return None
