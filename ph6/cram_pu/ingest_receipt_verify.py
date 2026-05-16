"""
ph6.cram_pu.ingest_receipt_verify — CRAM Ingest Receipt Chain Verifier v1.0

Walks ingest_receipt_log.jsonl and verifies:
  1. event_seq  — monotonically increasing, no gaps, no duplicates
  2. event_hash — matches BLAKE2b-256 of body (excluding event_hash)
  3. prev_event_hash — matches hash of previous receipt line (or genesis)
  4. authority_hash — present and non-empty
  5. genesis — first receipt prev_event_hash == "0" * 64

Exit: 0 = chain intact, 1 = chain broken
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


GENESIS_HASH = "0" * 64


def _blake2b(data: bytes) -> str:
    return hashlib.blake2b(data, digest_size=32).hexdigest()


def _canonical(obj: Any) -> bytes:
    return json.dumps(
        obj, sort_keys=True, ensure_ascii=False,
        allow_nan=False, separators=(",", ":"),
    ).encode("utf-8")


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def verify_receipt_chain(log_path: Path) -> dict:
    """
    Verify the ingest receipt chain at log_path.
    Returns a structured report dict.
    """
    now = _utc_now()
    findings: list[dict] = []

    if not log_path.exists():
        return {
            "schema":        "ph6.ingest_receipt_verify.v1",
            "chain_intact":  False,
            "receipt_count": 0,
            "findings":      [{"type": "log_missing", "severity": "HIGH",
                               "reason": f"Receipt log not found: {log_path}"}],
            "log_path":      str(log_path),
            "timestamp_utc": now,
        }

    lines: list[bytes] = []
    with log_path.open("rb") as f:
        for raw in f:
            stripped = raw.strip()
            if stripped:
                lines.append(stripped)

    prev_line_hash  = GENESIS_HASH
    expected_seq    = 1
    seen_seqs: set[int] = set()

    for i, raw_line in enumerate(lines):
        try:
            receipt = json.loads(raw_line.decode("utf-8"))
        except Exception as e:
            findings.append({
                "type":     "parse_error",
                "severity": "HIGH",
                "line":     i + 1,
                "reason":   str(e),
            })
            prev_line_hash = _blake2b(raw_line)
            expected_seq += 1
            continue

        seq     = receipt.get("event_seq")
        obj_id  = receipt.get("object_id", "?")
        stored_event_hash   = receipt.get("event_hash")
        stored_prev_hash    = receipt.get("prev_event_hash")
        authority_hash      = receipt.get("authority_hash")

        # ── Check 1: event_seq monotonicity and uniqueness ───────────────────
        if seq is None:
            findings.append({
                "type": "missing_event_seq", "severity": "HIGH",
                "line": i + 1, "object_id": obj_id,
                "reason": "event_seq field missing",
            })
        elif seq != expected_seq:
            findings.append({
                "type": "event_seq_violation", "severity": "HIGH",
                "violation_class": "D1",
                "line": i + 1, "object_id": obj_id,
                "expected_seq": expected_seq, "actual_seq": seq,
                "reason": "event_seq out of order or duplicate" if seq in seen_seqs else "event_seq gap or jump",
            })
        else:
            seen_seqs.add(seq)

        # ── Check 2: event_hash integrity ────────────────────────────────────
        if stored_event_hash is None:
            findings.append({
                "type": "missing_event_hash", "severity": "HIGH",
                "line": i + 1, "object_id": obj_id,
                "reason": "event_hash field missing",
            })
        else:
            body_without_hash = {k: v for k, v in receipt.items() if k != "event_hash"}
            expected_event_hash = _blake2b(_canonical(body_without_hash))
            if stored_event_hash != expected_event_hash:
                findings.append({
                    "type": "event_hash_mismatch", "severity": "HIGH",
                    "violation_class": "R3",
                    "line": i + 1, "object_id": obj_id,
                    "stored":   stored_event_hash,
                    "expected": expected_event_hash,
                    "reason": "event_hash does not match canonical body — receipt may be corrupted",
                })

        # ── Check 3: prev_event_hash chain ───────────────────────────────────
        if stored_prev_hash is None:
            findings.append({
                "type": "missing_prev_event_hash", "severity": "HIGH",
                "line": i + 1, "object_id": obj_id,
                "reason": "prev_event_hash field missing",
            })
        elif i == 0 and stored_prev_hash != GENESIS_HASH:
            findings.append({
                "type": "invalid_genesis", "severity": "HIGH",
                "violation_class": "R4",
                "line": i + 1, "object_id": obj_id,
                "stored_prev": stored_prev_hash,
                "reason": "First receipt must have prev_event_hash = GENESIS ('0' * 64)",
            })
        elif stored_prev_hash != prev_line_hash:
            findings.append({
                "type": "chain_break", "severity": "HIGH",
                "violation_class": "R4",
                "line": i + 1, "object_id": obj_id,
                "stored_prev":   stored_prev_hash,
                "expected_prev": prev_line_hash,
                "reason": "prev_event_hash chain break — receipt may be inserted, deleted, or modified",
            })

        # ── Check 4: authority_hash present ──────────────────────────────────
        if not authority_hash:
            findings.append({
                "type": "missing_authority_hash", "severity": "HIGH",
                "line": i + 1, "object_id": obj_id,
                "reason": "authority_hash missing or empty",
            })

        prev_line_hash = _blake2b(raw_line)
        expected_seq   = (seq or expected_seq) + 1

    chain_errors = [f for f in findings
                    if f.get("severity") in ("HIGH", "CRITICAL")]

    return {
        "schema":         "ph6.ingest_receipt_verify.v1",
        "chain_intact":   len(chain_errors) == 0,
        "receipt_count":  len(lines),
        "error_count":    len(chain_errors),
        "findings":       findings,
        "log_path":       str(log_path),
        "timestamp_utc":  now,
    }
