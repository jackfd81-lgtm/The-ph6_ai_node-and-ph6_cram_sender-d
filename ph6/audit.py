"""
ph6.audit — Lane-2 Advisory Audit Module

Lane:      2 (Advisory / Experimental)
Authority: ZERO — cannot issue PASS/DROP, cannot block Lane 1
Schema:    ph6.audit_event.v1

Callers: sensor tests, SoSo, TOK, SSMT, and any Lane-2 observer.
Do NOT use this module from Lane-1 (deterministic authority) code.
Lane-1 audit is at ph6.cram_pu.schemas.audit.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

AUDIT_PATH = Path("/var/ph6/audit/audit.jsonl")
ZERO_HASH  = "0" * 64   # Lane-2 authority_hash sentinel — authority is always NONE


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _blake2b(data: bytes) -> str:
    return hashlib.blake2b(data, digest_size=32).hexdigest()


def _canonical_json(obj: dict) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def _tail_read(path: Path) -> tuple[str, int]:
    """Return (last_event_hash, last_seq) via O(1) tail scan."""
    if not path.exists():
        return ZERO_HASH, 0

    BLOCK = 4096
    with open(path, "rb") as f:
        f.seek(0, 2)
        size = f.tell()
        if size == 0:
            return ZERO_HASH, 0
        pos = max(0, size - BLOCK)
        f.seek(pos)
        tail = f.read()

    lines = [ln for ln in tail.split(b"\n") if ln.strip()]
    if not lines:
        return ZERO_HASH, 0

    try:
        last = json.loads(lines[-1].decode("utf-8"))
        return last.get("event_hash", ZERO_HASH), last.get("event_seq", 0)
    except Exception:
        return ZERO_HASH, 0


def make_lane2_event(event_type: str, object_id: str, **kwargs: Any) -> dict:
    """
    Build a Lane-2 advisory event dict.
    authority_hash is always ZERO_HASH — Lane 2 carries zero authority.
    Pass additional fields as keyword arguments (e.g. reason=, frames=, fps=).
    """
    event: dict = {
        "schema":         "ph6.audit_event.v1",
        "event_type":     event_type,
        "object_id":      object_id,
        "authority_hash": ZERO_HASH,
        "authority":      "NONE",
        "lane":           2,
        "ts":             _utc_now(),
    }
    event.update(kwargs)
    return event


def append_audit(event: dict, path: Path = AUDIT_PATH) -> dict:
    """
    Append a Lane-2 audit event to the JSONL chain.

    Injects event_seq, prev_event_hash, and event_hash deterministically.
    Uses fsync + atomic append to guard against crash corruption.
    Returns the event as written.
    """
    prev_hash, prev_seq = _tail_read(path)

    event = dict(event)
    event["event_seq"]       = prev_seq + 1
    event["prev_event_hash"] = prev_hash

    preimage = {k: v for k, v in event.items() if k != "event_hash"}
    event["event_hash"] = _blake2b(_canonical_json(preimage))

    path.parent.mkdir(parents=True, exist_ok=True)
    line = _canonical_json(event) + b"\n"

    with open(path, "ab") as f:
        f.write(line)
        f.flush()
        os.fsync(f.fileno())

    return event
