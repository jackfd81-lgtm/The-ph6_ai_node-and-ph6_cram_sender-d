"""
TOK-1.0 Advisory Audit Chain Reconstruction

Lane: 2
Authority: ZERO
Write domain: MRAM-S only (receipts/)

Replays the tok_advisory_audit.jsonl chain to:
- validate hash chain integrity
- count events by type
- emit a rebuild receipt

Important:
  TOK rebuild PASS ≠ PH6 evidence PASS.
  This module is advisory-only and never touches Lane-1.
"""

from __future__ import annotations

import json
import hashlib
from pathlib import Path
from typing import Optional

from ph6.tok.rebuild import emit_rebuild_receipt, canonical_json, blake2b256_hex


def validate_chain_integrity(audit_path: Path) -> tuple[bool, int, str]:
    """
    Walk the JSONL audit chain and verify each event_hash.

    Returns (is_valid, event_count, error_or_empty).
    """
    if not audit_path.exists():
        return False, 0, "audit file does not exist"

    prev_hash = "GENESIS"
    count = 0

    try:
        with open(audit_path, "rb") as f:
            for raw_line in f:
                raw_line = raw_line.strip()
                if not raw_line:
                    continue

                event = json.loads(raw_line.decode("utf-8"))
                stored_hash = event.get("event_hash", "")

                # Remove event_hash before recomputing
                check = {k: v for k, v in event.items() if k != "event_hash"}
                computed = blake2b256_hex(check)

                if computed != stored_hash:
                    return False, count, f"hash mismatch at event {count}: {stored_hash!r} != {computed!r}"

                if event.get("prev_event_hash") != prev_hash:
                    return False, count, f"chain break at event {count}"

                prev_hash = stored_hash
                count += 1

    except Exception as e:
        return False, count, str(e)

    return True, count, ""


def count_events_by_type(audit_path: Path) -> dict:
    """Return a dict of event_type → count from the audit chain."""
    counts: dict = {}

    if not audit_path.exists():
        return counts

    with open(audit_path, "rb") as f:
        for raw_line in f:
            raw_line = raw_line.strip()
            if not raw_line:
                continue
            try:
                event = json.loads(raw_line.decode("utf-8"))
                etype = event.get("event_type", "UNKNOWN")
                counts[etype] = counts.get(etype, 0) + 1
            except Exception:
                counts["PARSE_ERROR"] = counts.get("PARSE_ERROR", 0) + 1

    return counts


def reconstruct_and_emit_receipt(
    base_dir: str,
    live_store=None,
    audit_path: Optional[Path] = None,
) -> dict:
    """
    Validate the audit chain and emit a rebuild receipt.

    live_store: optional loaded TokenStore to count current live state.
    audit_path: defaults to base_dir/tok_advisory_audit.jsonl.
    """
    base = Path(base_dir)

    if audit_path is None:
        audit_path = base / "tok_advisory_audit.jsonl"

    chain_valid, event_count, _err = validate_chain_integrity(audit_path)

    rt_count = len(live_store.rt_store) if live_store else 0
    vdt_count = len(live_store.vdt_store) if live_store else 0
    vlt_count = len(live_store.vlt_store) if live_store else 0

    archive_dir = base / "archive"
    archive_count = len(list(archive_dir.glob("*.json"))) if archive_dir.exists() else 0

    return emit_rebuild_receipt(
        base_dir=str(base),
        input_event_count=event_count,
        rt_count=rt_count,
        vdt_count=vdt_count,
        vlt_count=vlt_count,
        archive_count=archive_count,
        audit_chain_valid=chain_valid,
    )
