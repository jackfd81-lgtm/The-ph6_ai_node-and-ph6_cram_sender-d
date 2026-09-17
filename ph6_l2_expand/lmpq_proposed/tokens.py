"""
ph6_l2_expand.lmpq_proposed.tokens

Lane: 2
Authority: ZERO
Write domain: none (pure dataclasses/functions — persistence, if any, is
the caller's responsibility via ph6_l2_expand.mram_s_writer)
Status: PROPOSED — see PH6_SOURCE/DRAFT/PH6-LMPQ-001-PROPOSED-SPEC-v0.1.md

RLT / PLT / AHT. NONE of these are members of
ph6_l2_expand.schemas.TOKEN_TYPES or token_policy.ALLOWED_TOKEN_TYPES.
That set is locked to exactly {"RT", "VDT", "VLT"} by
ph6_l2_expand/tests/test_token_classes_locked.py and
ph6_l2_expand/tests/test_soso_tokens_not_lane1.py — this module must
never be wired into those constants.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from ph6_l2_expand.schemas import canonical_json

PROPOSED_SCHEMA = "ph6.lmpq_proposed.token.v1"

# Fixed namespace, distinct from ph6_l2_expand.token_types.PH6_TOKEN_NAMESPACE,
# so proposed-layer token ids can never collide with locked RT/VDT/VLT ids.
PH6_LMPQ_NAMESPACE = uuid.UUID("0c0ffee0-0000-4000-8000-0000000000aa")


def blake2b256_hex(obj: Any) -> str:
    return hashlib.blake2b(canonical_json(obj), digest_size=32).hexdigest()


def rlt_token_id(cram_ref_hash: str, drop_observed_at_ms: int) -> str:
    return str(uuid.uuid5(PH6_LMPQ_NAMESPACE, f"RLT|{cram_ref_hash}|{drop_observed_at_ms}"))


def plt_token_id(parent_token_id: str, linked_token_ids: List[str]) -> str:
    key = f"PLT|{parent_token_id}|{'|'.join(sorted(linked_token_ids))}"
    return str(uuid.uuid5(PH6_LMPQ_NAMESPACE, key))


def aht_token_id(source_token_id: str, event_time_ms: int) -> str:
    return str(uuid.uuid5(PH6_LMPQ_NAMESPACE, f"AHT|{source_token_id}|{event_time_ms}"))


# ---------------------------------------------------------------------------
# RLT — Reference Loss Token
# ---------------------------------------------------------------------------

@dataclass(frozen=True, kw_only=True)
class RLT:
    token_id: str
    cram_ref_hash: str
    drop_observed_at_ms: int
    parent_token_id: Optional[str] = None
    authority: str = "ZERO"
    advisory_only: bool = True
    replay_dependency: bool = False
    affects_pass_drop: bool = False
    affects_cram_commit: bool = False
    schema: str = PROPOSED_SCHEMA
    token_type: str = field(default="RLT", init=False)
    # Locked: DROP != DELETE. RLT can never assert the evidence is gone.
    evidence_deleted: bool = field(default=False, init=False)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def state_hash(self) -> str:
        return blake2b256_hex(self.to_dict())


def make_rlt(
    cram_ref_hash: str,
    drop_observed_at_ms: int,
    parent_token_id: Optional[str] = None,
) -> RLT:
    """
    Construct an RLT referencing an already-committed Lane-1 CRAM-R (DROP)
    event. Fails closed on missing evidence reference or missing event-time
    (no wall-clock default is ever substituted here).
    """
    if not cram_ref_hash:
        raise ValueError("RLT requires a non-empty cram_ref_hash (missing source evidence)")
    if not isinstance(drop_observed_at_ms, int) or drop_observed_at_ms <= 0:
        raise ValueError(
            "RLT requires an explicit positive drop_observed_at_ms event-time; "
            "wall-clock defaults are forbidden for this field"
        )
    return RLT(
        token_id=rlt_token_id(cram_ref_hash, drop_observed_at_ms),
        cram_ref_hash=cram_ref_hash,
        drop_observed_at_ms=drop_observed_at_ms,
        parent_token_id=parent_token_id,
    )


# ---------------------------------------------------------------------------
# PLT — Provenance Link Token
# ---------------------------------------------------------------------------

@dataclass(frozen=True, kw_only=True)
class PLT:
    token_id: str
    parent_token_id: str
    linked_token_ids: List[str]
    continuity_gap_ms: int
    authority: str = "ZERO"
    advisory_only: bool = True
    replay_dependency: bool = False
    schema: str = PROPOSED_SCHEMA
    token_type: str = field(default="PLT", init=False)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def state_hash(self) -> str:
        return blake2b256_hex(self.to_dict())


def make_plt(
    parent_token_id: str,
    linked_token_ids: List[str],
    token_map: Dict[str, Any],
    parent_event_time_ms: int,
    linked_event_times_ms: Dict[str, int],
) -> PLT:
    """
    Construct a PLT linking parent_token_id (typically an RLT, but any
    RT/VDT/VLT is accepted) forward to linked_token_ids. Fails closed if
    the parent is not present in the caller-supplied token_map (invalid
    parent token / broken provenance), or if no link targets are given.
    """
    if parent_token_id not in token_map:
        raise ValueError(
            f"invalid parent token: {parent_token_id!r} not found in supplied "
            f"token map (broken provenance)"
        )
    if not linked_token_ids:
        raise ValueError("PLT requires at least one linked_token_id (broken provenance)")

    missing = [t for t in linked_token_ids if t not in linked_event_times_ms]
    if missing:
        raise ValueError(f"missing event-time for linked tokens: {missing}")

    earliest_linked_ms = min(linked_event_times_ms[t] for t in linked_token_ids)
    continuity_gap_ms = earliest_linked_ms - parent_event_time_ms

    return PLT(
        token_id=plt_token_id(parent_token_id, linked_token_ids),
        parent_token_id=parent_token_id,
        linked_token_ids=sorted(linked_token_ids),
        continuity_gap_ms=continuity_gap_ms,
    )


# ---------------------------------------------------------------------------
# AHT — Archival Hydration Token
# ---------------------------------------------------------------------------

@dataclass(frozen=True, kw_only=True)
class AHT:
    token_id: str
    source_token_id: str
    source_event_type: Optional[str]
    event_time_ms: int
    reconstructed_at_ms: int
    reconstructed_state_hash: str
    authority: str = "ZERO"
    advisory_only: bool = True
    replay_dependency: bool = False
    schema: str = PROPOSED_SCHEMA
    token_type: str = field(default="AHT", init=False)
    # Locked: Replay != New Observation. Persistence != Truth.
    is_replay: bool = field(default=True, init=False)
    new_observation: bool = field(default=False, init=False)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def rehydrate_token_from_chain(audit_path: Path, source_token_id: str) -> Dict[str, Any]:
    """
    Deterministically replay a ph6/tok advisory audit chain
    (tok_advisory_audit.jsonl) and return the last known state recorded
    for source_token_id.

    This wraps the existing rehydration primitive
    (ph6.tok.reconstruct.validate_chain_integrity) rather than creating a
    second one. Raises ValueError if the chain fails hash-chain integrity
    (altered/tampered source evidence) or if source_token_id never
    appears in the chain (invalid rehydration reference / missing source
    evidence).
    """
    from ph6.tok.reconstruct import validate_chain_integrity

    audit_path = Path(audit_path)
    valid, _count, err = validate_chain_integrity(audit_path)
    if not valid:
        raise ValueError(f"cannot rehydrate: audit chain failed integrity validation: {err}")

    last_payload: Optional[Dict[str, Any]] = None
    last_event_type: Optional[str] = None
    last_event_time_ms: Optional[int] = None

    with open(audit_path, "rb") as fh:
        for raw_line in fh:
            raw_line = raw_line.strip()
            if not raw_line:
                continue
            event = json.loads(raw_line.decode("utf-8"))
            payload = event.get("payload", {})
            candidate_id = payload.get("token_id") or payload.get("vlt_token_id")
            if candidate_id != source_token_id:
                continue
            last_payload = payload
            last_event_type = event.get("event_type")
            last_event_time_ms = event.get("timestamp_ms")

    if last_payload is None:
        raise ValueError(
            f"invalid rehydration reference: token_id {source_token_id!r} "
            f"not found in audit chain {audit_path}"
        )

    return {
        "source_token_id": source_token_id,
        "last_event_type": last_event_type,
        "event_time_ms": last_event_time_ms,
        "payload": last_payload,
    }


def make_aht(audit_path: Path, source_token_id: str, reconstructed_at_ms: int) -> AHT:
    """
    Construct an AHT for source_token_id by replaying audit_path.

    reconstructed_at_ms is recorded but deliberately excluded from
    reconstructed_state_hash, so replaying the same chain for the same
    token at a different wall-clock time yields an identical hash.
    """
    rehydrated = rehydrate_token_from_chain(audit_path, source_token_id)

    hashable = {
        "source_token_id": rehydrated["source_token_id"],
        "last_event_type": rehydrated["last_event_type"],
        "event_time_ms": rehydrated["event_time_ms"],
        "payload": rehydrated["payload"],
    }
    reconstructed_state_hash = blake2b256_hex(hashable)

    return AHT(
        token_id=aht_token_id(source_token_id, rehydrated["event_time_ms"]),
        source_token_id=source_token_id,
        source_event_type=rehydrated["last_event_type"],
        event_time_ms=rehydrated["event_time_ms"],
        reconstructed_at_ms=reconstructed_at_ms,
        reconstructed_state_hash=reconstructed_state_hash,
    )
