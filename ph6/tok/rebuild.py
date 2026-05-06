#!/usr/bin/env python3
"""
TOK-1.0 advisory rebuild receipt.

This module rebuilds only TOK advisory topology.
It does not certify Lane-1 evidence.
It is never required for Lane-1 replay.

Lane: 2
Authority: ZERO
Write domain: MRAM-S only
"""

from __future__ import annotations

import json
import hashlib
from pathlib import Path


def canonical_json(obj) -> bytes:
    return json.dumps(
        obj,
        sort_keys=True,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")


def blake2b256_hex(obj) -> str:
    return hashlib.blake2b(canonical_json(obj), digest_size=32).hexdigest()


def emit_rebuild_receipt(
    base_dir: str,
    input_event_count: int,
    rt_count: int,
    vdt_count: int,
    vlt_count: int,
    archive_count: int,
    audit_chain_valid: bool,
) -> dict:
    receipt = {
        "schema": "ph6.tok.rebuild_receipt.v1",
        "authority": "ZERO",
        "advisory_only": True,
        "replay_dependency": False,
        "input_event_count": input_event_count,
        "rt_count": rt_count,
        "vdt_count": vdt_count,
        "vlt_count": vlt_count,
        "archive_count": archive_count,
        "audit_chain_valid": audit_chain_valid,
        "result": "PASS" if audit_chain_valid else "WARN",
    }

    receipt["rebuilt_state_hash"] = blake2b256_hex(receipt)

    out_dir = Path(base_dir) / "receipts"
    out_dir.mkdir(parents=True, exist_ok=True)

    out_path = out_dir / "tok_rebuild_receipt.json"
    out_path.write_text(
        json.dumps(receipt, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    return receipt
