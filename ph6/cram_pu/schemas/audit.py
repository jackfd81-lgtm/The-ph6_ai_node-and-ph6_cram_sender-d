"""
PH6 / CRAM-PU — Canonical Audit Event Emitter

Lane: 1 (authority support)
Purpose: append_audit() with all required fields per PH6-CLAUDE-PATCH-HANDOFF-1.0.

Required fields per event:
  schema, event_seq, event_type, object_id, event_hash,
  prev_event_hash, authority_hash, timestamp_utc, node_id, stage, status

event_hash is computed from canonical JSON of the event excluding event_hash itself.
authority_hash is BLAKE2b-256 of the object payload (supplied by caller).
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .canonical import canonical_json, blake2b_256, blake2b_256_obj, validate_event_type

GENESIS_HASH = "0" * 64


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_last(audit_path: Path) -> tuple[str, int]:
    """Return (prev_event_hash, last_seq) from the audit file."""
    if not audit_path.exists():
        return GENESIS_HASH, 0

    last = None
    with open(audit_path, "rb") as f:
        for line in f:
            line = line.strip()
            if line:
                last = line

    if last is None:
        return GENESIS_HASH, 0

    try:
        obj = json.loads(last.decode("utf-8"))
        return obj.get("event_hash", GENESIS_HASH), obj.get("event_seq", 0)
    except Exception:
        return GENESIS_HASH, 0


def append_audit(
    audit_path: Path,
    event_type: str,
    object_id: str,
    authority_hash: str,
    node_id: str,
    stage: str,
    status: str,
    payload: Optional[dict] = None,
    timestamp_utc: Optional[str] = None,
) -> dict:
    """
    Append one canonical audit event to the JSONL chain.

    Raises ValueError for forbidden or unknown event_type.

    Returns the complete event dict as written.
    """
    validate_event_type(event_type)

    prev_hash, prev_seq = _load_last(audit_path)

    event: dict = {
        "schema": "ph6.cram_audit.v1",
        "event_seq": prev_seq + 1,
        "event_type": event_type,
        "object_id": object_id,
        "authority_hash": authority_hash,
        "prev_event_hash": prev_hash,
        "timestamp_utc": timestamp_utc if timestamp_utc is not None else _utc_now(),
        "node_id": node_id,
        "stage": stage,
        "status": status,
    }

    if payload:
        event["payload"] = payload

    # event_hash excludes itself from preimage
    preimage = {k: v for k, v in event.items() if k != "event_hash"}
    event["event_hash"] = blake2b_256(canonical_json(preimage))

    audit_path.parent.mkdir(parents=True, exist_ok=True)
    line = canonical_json(event) + b"\n"

    with open(audit_path, "ab") as f:
        f.write(line)
        f.flush()
        os.fsync(f.fileno())

    return event


def validate_chain(audit_path: Path) -> tuple[bool, int, str]:
    """
    Walk the audit chain and verify event_hash and prev_event_hash linkage.
    Returns (is_valid, event_count, error_or_empty).
    """
    if not audit_path.exists():
        return True, 0, ""

    prev_hash = GENESIS_HASH
    count = 0

    try:
        with open(audit_path, "rb") as f:
            for raw in f:
                raw = raw.strip()
                if not raw:
                    continue

                event = json.loads(raw.decode("utf-8"))
                stored = event.get("event_hash", "")
                preimage = {k: v for k, v in event.items() if k != "event_hash"}
                computed = blake2b_256(canonical_json(preimage))

                if computed != stored:
                    return False, count, f"hash mismatch at seq {event.get('event_seq')}"

                if event.get("prev_event_hash") != prev_hash:
                    return False, count, f"chain break at seq {event.get('event_seq')}"

                prev_hash = stored
                count += 1

    except Exception as e:
        return False, count, str(e)

    return True, count, ""
