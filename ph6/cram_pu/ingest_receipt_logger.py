"""
ph6.cram_pu.ingest_receipt_logger — CRAM Ingest Receipt Chain v1.0

Emits a chained ingest receipt for every Lane-1 ingest event.
Each receipt carries:
  event_seq        — monotonic per CRAM store (persisted in seq file)
  event_type       — INGEST_ARRIVED | INGEST_ACCEPTED | INGEST_DROPPED
  object_id        — canonical frame/object identifier
  event_hash       — BLAKE2b-256 of canonical body (excluding event_hash)
  prev_event_hash  — BLAKE2b-256 of previous receipt file (or genesis)
  authority_hash   — BLAKE2b-256 of the authoritative Lane-1 content
  timestamp_utc    — ISO 8601 UTC

Chain rules:
  - Genesis prev_event_hash = "0" * 64
  - event_seq monotonically increases; gaps are chain violations
  - event_hash computed last, over body excluding event_hash
  - authority_hash is the CRAM commit hash for ACCEPTED,
    or payload_hash for DROPPED / ARRIVED
  - No advisory fields in this log
  - No raw floats

Schema: ph6.ingest_receipt.v1
Authority: LANE_1
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path


GENESIS_HASH   = "0" * 64
EVENT_TYPES    = frozenset({"INGEST_ARRIVED", "INGEST_ACCEPTED", "INGEST_DROPPED"})
_RECEIPT_LOG   = "ingest_receipt_log.jsonl"
_SEQ_FILE      = "ingest_receipt_seq.txt"


def _blake2b(data: bytes) -> str:
    return hashlib.blake2b(data, digest_size=32).hexdigest()


def _canonical(obj) -> bytes:
    return json.dumps(
        obj, sort_keys=True, ensure_ascii=False,
        allow_nan=False, separators=(",", ":"),
    ).encode("utf-8")


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _append_fsync(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("ab") as f:
        f.write(data + b"\n")
        f.flush()
        os.fsync(f.fileno())


class IngestReceiptLogger:
    """
    Emits chained ingest receipts to <cram_store>/ingest_receipt_log.jsonl.
    One instance per CRAM store. Not thread-safe — caller must serialize.
    """

    def __init__(self, cram_store: Path):
        self._store    = cram_store
        self._log_path = cram_store / _RECEIPT_LOG
        self._seq_path = cram_store / _SEQ_FILE
        self._seq      = self._load_seq()

    # ── Sequence tracking ────────────────────────────────────────────────────

    def _load_seq(self) -> int:
        try:
            return int(self._seq_path.read_text().strip())
        except (FileNotFoundError, ValueError):
            return 0

    def _save_seq(self, seq: int) -> None:
        tmp = self._seq_path.with_suffix(".seq.tmp")
        tmp.write_text(str(seq))
        tmp.replace(self._seq_path)

    # ── Previous receipt hash ────────────────────────────────────────────────

    def _prev_hash(self) -> str:
        """BLAKE2b-256 of the last line in the receipt log, or genesis."""
        if not self._log_path.exists():
            return GENESIS_HASH
        try:
            last_line = b""
            with self._log_path.open("rb") as f:
                for line in f:
                    stripped = line.strip()
                    if stripped:
                        last_line = stripped
            if not last_line:
                return GENESIS_HASH
            return _blake2b(last_line)
        except OSError:
            return GENESIS_HASH

    # ── Receipt emission ─────────────────────────────────────────────────────

    def emit(
        self,
        event_type: str,
        object_id: str,
        authority_hash: str,
        *,
        timestamp_utc: str | None = None,
    ) -> dict:
        """
        Emit one ingest receipt. Returns the sealed receipt dict.

        Args:
            event_type:     "INGEST_ARRIVED" | "INGEST_ACCEPTED" | "INGEST_DROPPED"
            object_id:      Frame or object identifier (e.g. "frame_00000441")
            authority_hash: BLAKE2b-256 of the authoritative Lane-1 content.
                            For ACCEPTED: the cram_hash from the CRAM commit.
                            For DROPPED/ARRIVED: the payload_hash.
        """
        if event_type not in EVENT_TYPES:
            raise ValueError(f"Unknown event_type '{event_type}'. Must be one of {sorted(EVENT_TYPES)}")

        self._seq += 1
        seq = self._seq

        body: dict = {
            "schema":          "ph6.ingest_receipt.v1",
            "event_seq":       seq,
            "event_type":      event_type,
            "object_id":       object_id,
            "authority_hash":  authority_hash,
            "prev_event_hash": self._prev_hash(),
            "hash_algorithm":  "BLAKE2b-256",
            "authority":       "LANE_1",
            "timestamp_utc":   timestamp_utc or _utc_now(),
        }

        # event_hash seals the body (excluding itself — same as CRAM commit pattern)
        body_without_hash = {k: v for k, v in body.items() if k != "event_hash"}
        body["event_hash"] = _blake2b(_canonical(body_without_hash))

        raw_line = _canonical(body)
        _append_fsync(self._log_path, raw_line)
        self._save_seq(seq)
        return body

    # ── Convenience wrappers ─────────────────────────────────────────────────

    def arrived(self, frame_id: int, payload_hash: str, **kw) -> dict:
        return self.emit(
            "INGEST_ARRIVED",
            f"frame_{frame_id:010d}",
            payload_hash,
            **kw,
        )

    def accepted(self, frame_id: int, cram_hash: str, **kw) -> dict:
        return self.emit(
            "INGEST_ACCEPTED",
            f"frame_{frame_id:010d}",
            cram_hash,
            **kw,
        )

    def dropped(self, frame_id: int, payload_hash: str, **kw) -> dict:
        return self.emit(
            "INGEST_DROPPED",
            f"frame_{frame_id:010d}",
            payload_hash,
            **kw,
        )
