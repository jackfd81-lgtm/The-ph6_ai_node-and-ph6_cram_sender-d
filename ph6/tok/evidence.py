"""
TOK-1.0 CRAM Evidence Integrity Check (read-only) + Loss/Rehydration
Orchestration

Lane: 2
Authority: ZERO
Write domain: MRAM-S only (via TokenStore, never here directly)
Read domain: caller-supplied CRAM commit directory (inspection only)

This module never writes a CRAM commit, never issues PASS/DROP, and never
adjudicates. It performs a read-only integrity check against a
previously-committed CRAM-PU PASS record (see ph6.cram_pu.crash_replay.
CRAMWriter for the commit format this checks against) and, on failure,
drives the RLT/PLT/AHT token-loss response protocol documented in
PH6_SOURCE/GOVERNANCE/PH6_LIVING_MEMORY_TOKEN_RETENTION_POLICY.md section 4.

DROP != DELETE: a DROP frame never had a CRAM commit in the first place and
is therefore never a candidate for loss detection here. Only a frame that
was previously PASS-committed (and therefore has an RT token referencing
it) can produce an RLT.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from ph6.tok.lifecycle import (
    AHT,
    PLT,
    RLT,
    RT,
    TokenStore,
    make_aht,
    make_plt,
    make_rlt,
    now_ms,
    rehydrated_rt_token_id,
)


def _canonical_bytes(obj) -> bytes:
    return json.dumps(
        obj,
        sort_keys=True,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")


def _blake2b256_hex(data: bytes) -> str:
    return hashlib.blake2b(data, digest_size=32).hexdigest()


def _normalize_hash(h: str) -> str:
    return h.replace("blake2b256:", "") if isinstance(h, str) else h


@dataclass(frozen=True)
class EvidenceStatus:
    intact: bool
    frame_id: int
    reason: str
    checked_cram_hash: Optional[str] = None
    checked_payload_hash: Optional[str] = None


def check_cram_commit_intact(
    cram_store_dir: Path, frame_id: int, expected_payload_hash: str
) -> EvidenceStatus:
    """
    Read-only integrity check for a previously-committed CRAM PASS record.

    Verifies, in order:
      1. the commit JSON file exists and is readable
      2. its recomputed cram_hash matches the stored cram_hash
      3. its durable `.blake2b` marker exists and matches
      4. the payload file exists
      5. the payload's content hash matches the expected payload hash
      6. the commit record's own payload_hash field matches too

    Never writes anything. Never adjudicates PASS/DROP.
    """
    cram_store_dir = Path(cram_store_dir)
    record_path = cram_store_dir / f"cram_{frame_id:010d}.json"
    marker_path = cram_store_dir / f"cram_{frame_id:010d}.json.blake2b"
    payload_path = cram_store_dir / "payloads" / f"frame_{frame_id:010d}.bin"

    if not record_path.exists():
        return EvidenceStatus(False, frame_id, "cram_record_missing")

    try:
        record = json.loads(record_path.read_text(encoding="utf-8"))
    except Exception:
        return EvidenceStatus(False, frame_id, "cram_record_unreadable")

    stored_hash = record.get("cram_hash", "")
    body = {k: v for k, v in record.items() if k != "cram_hash"}
    recomputed_hash = _blake2b256_hex(_canonical_bytes(body))

    if recomputed_hash != stored_hash:
        return EvidenceStatus(False, frame_id, "cram_hash_mismatch", checked_cram_hash=recomputed_hash)

    if not marker_path.exists():
        return EvidenceStatus(False, frame_id, "durable_marker_missing", checked_cram_hash=stored_hash)

    marker_value = marker_path.read_text(encoding="utf-8").strip()
    if marker_value != stored_hash:
        return EvidenceStatus(False, frame_id, "durable_marker_mismatch", checked_cram_hash=stored_hash)

    if not payload_path.exists():
        return EvidenceStatus(False, frame_id, "payload_missing", checked_cram_hash=stored_hash)

    payload_hex = _blake2b256_hex(payload_path.read_bytes())
    expected_hex = _normalize_hash(expected_payload_hash)

    if payload_hex != expected_hex:
        return EvidenceStatus(
            False, frame_id, "payload_hash_mismatch",
            checked_cram_hash=stored_hash, checked_payload_hash=payload_hex,
        )

    record_payload_hash = _normalize_hash(record.get("payload_hash", ""))
    if record_payload_hash != expected_hex:
        return EvidenceStatus(
            False, frame_id, "record_payload_hash_mismatch", checked_cram_hash=stored_hash,
        )

    return EvidenceStatus(
        True, frame_id, "intact", checked_cram_hash=stored_hash, checked_payload_hash=payload_hex,
    )


def detect_rt_loss(
    store: TokenStore,
    rt: RT,
    cram_store_dir: Path,
    frame_id: int,
    event_time_ms: Optional[int] = None,
) -> Optional[RLT]:
    """
    Run the read-only evidence check for `rt` and, if its CRAM evidence is
    no longer intact, create the RLT + AHT pair (token-loss response
    protocol steps 1-3) and record them via the store.

    Returns the created RLT, or None if the evidence is still intact.
    """
    status = check_cram_commit_intact(cram_store_dir, frame_id, rt.cram_ref_hash)
    if status.intact:
        return None

    now = event_time_ms if event_time_ms is not None else now_ms()

    aht = make_aht(rt, frame_id, now)
    rlt = make_rlt(rt, frame_id, status.reason, aht.token_id, now)

    store.add_rlt(rlt, aht, event_time_ms=now)
    return rlt


def predict_rt_risk(
    store: TokenStore,
    rt: RT,
    frame_id: int,
    risk_reason: str,
    risk_score: float,
    event_time_ms: Optional[int] = None,
) -> PLT:
    """
    Record a PLT for an RT flagged at risk by an explicit external signal
    (e.g. storage pressure, pending hash re-verification). The signal is
    always caller-supplied — this function never infers risk on its own,
    which would make PLT creation non-deterministic and unauditable.
    """
    now = event_time_ms if event_time_ms is not None else now_ms()
    plt = make_plt(rt, frame_id, risk_reason, risk_score, now)
    store.add_plt(plt, event_time_ms=now)
    return plt


def attempt_rehydration(
    store: TokenStore,
    aht: AHT,
    cram_store_dir: Path,
    frame_id: int,
    expected_payload_hash: str,
    event_time_ms: Optional[int] = None,
) -> Optional[RT]:
    """
    Attempt to rebuild an RT from preserved CRAM evidence via an AHT
    anchor (token-loss response protocol steps 6-8).

    Rehydration is valid only when the source CRAM evidence is intact and
    hash-verified. It never alters evidence content and never changes a
    PSEUDO verdict — it only reconstructs an advisory reference token.

    Returns the new RT on success, or None if the evidence is still
    unavailable (in which case the AHT is marked FAILED and remains for a
    future attempt; the RLT continues to mark the gap).
    """
    status = check_cram_commit_intact(cram_store_dir, frame_id, expected_payload_hash)
    now = event_time_ms if event_time_ms is not None else now_ms()

    if not status.intact:
        store.mark_aht_rehydration_failed(aht.token_id, status.reason, event_time_ms=now)
        return None

    new_rt = RT(
        token_id=rehydrated_rt_token_id(aht.token_id, frame_id, expected_payload_hash),
        cram_ref_hash=expected_payload_hash,
        timestamp_ms=now,
        object_class=aht.metadata.get("object_class", ""),
        bbox=list(aht.metadata.get("bbox", [])),
        confidence=float(aht.metadata.get("confidence", 0.0)),
        metadata={
            "rehydrated_from_aht": aht.token_id,
            "rehydrated_from_lost_token": aht.anchor_for_token_id,
            "provenance": "REHYDRATION",
        },
    )

    store.rehydrate_aht_to_rt(aht.token_id, new_rt, event_time_ms=now)
    return new_rt
