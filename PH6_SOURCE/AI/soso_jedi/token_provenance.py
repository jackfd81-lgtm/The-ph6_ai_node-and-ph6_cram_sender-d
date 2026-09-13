#!/usr/bin/env python3
"""
PH6 Book V — Single-Token Provenance Adapter (ADVISORY_ZERO).

Bridges token-lineage records produced by the Lane-2 TOK subsystem
(ph6.tok) into a SoSo/JEDI advisory provenance report, without SoSo-JEDI
needing to understand TOK's internal dataclasses or on-disk storage
format, and without TOK needing to know anything about SoSo-JEDI.

Why an adapter, and not a BookVCoreEngine rewrite:

BookVCoreEngine's public surface (run_storm_exploration /
run_swarm_evaluation / run_jedi_reconstruction) answers a different
question — "what does layered stratigraphy across storm branches look
like" — not "what is the provenance chain for one specific token."
Bending that layer/branch model to answer a single-token lookup would
distort its meaning. Instead this module accepts a plain-dict token
lineage (the same shape TokenBase.to_dict() / ph6.tok.lifecycle token
records already produce) and reconstructs a provenance trace using the
same deterministic hashing discipline BookVCoreEngine already uses.

This module performs NO I/O, reads no CRAM or MRAM-S paths itself, and
issues no PASS/DROP. It is a pure function over caller-supplied data —
the caller (e.g. a TOK TokenStore) is responsible for gathering the
records to hand it. It must never adjudicate CRAM evidence.

AI Contribution Signature:
  {"proposed_by":"claude-code-lane2","proposed_at_utc":"2026-09-13","ratified_by":null}
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
from jedi.swarm_sim_bp import AUTHORITY, hash_json  # noqa: E402

SCHEMA_TOKEN_PROVENANCE = "ph6.soso_jedi.token_provenance.v1"

# Parent-link field names this adapter knows how to follow, across the
# token shapes ph6.tok.lifecycle produces. Checked in order; the first
# match wins. Falls back to the same keys nested under "metadata" for
# tokens (e.g. a rehydrated RT) that record lineage there instead.
_PARENT_LINK_FIELDS = (
    "lost_token_id",           # RLT -> the RT it marks as lost
    "anchor_for_token_id",     # AHT -> the RT it anchors
    "at_risk_token_id",        # PLT -> the RT it warns about
    "rehydrated_from_aht",     # rehydrated RT -> the AHT it was rebuilt from
                                # (the version edge is AHT -> RT per doctrine;
                                # "rehydrated_from_lost_token" on the same
                                # record is informational lineage, not a
                                # separate traversal edge, so it is
                                # deliberately not listed here)
    "promoted_from",           # VLT -> the VDT(s) it was promoted from
)


def _parent_of(record: Dict[str, Any]) -> Optional[str]:
    """Best-effort single-parent extraction. Returns None at a chain root.

    Never guesses: only follows fields this adapter explicitly recognizes.
    An unrecognized token shape with no matching field is treated as a
    root, not as a broken link — a genuinely broken link is a *present*
    field pointing at a token_id absent from the supplied records, which
    build_token_provenance() rejects rather than silently drops.
    """
    for key in _PARENT_LINK_FIELDS:
        val = record.get(key)
        if val is None:
            val = record.get("metadata", {}).get(key)
        if isinstance(val, list):
            val = val[0] if val else None
        if val:
            return val
    return None


def build_token_provenance(
    token_id: str,
    token_records: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Walk `token_records` backward from `token_id` to its lineage root and
    produce an advisory provenance trace.

    `token_records` is a list of plain dicts — the output of
    TokenBase.to_dict() (or equivalent) from ph6.tok.lifecycle. This
    function performs no lookups beyond that list: it never reads CRAM,
    MRAM-S, or any filesystem path itself.

    Determinism / replay isolation: `trace_hash` is computed only from the
    token identities, types, and CRAM reference hashes in the chain — it
    never includes a wall-clock timestamp, so calling this twice with the
    same `token_records` always yields the same `trace_hash`, matching the
    replay-isolation discipline the rest of Book V already follows.

    Raises ValueError when:
      - `token_id` is not present in `token_records`
      - a parent link points at a token_id absent from `token_records`
        (broken provenance is reported, never silently truncated)
      - the lineage contains a cycle
    """
    by_id = {r["token_id"]: r for r in token_records if "token_id" in r}
    if token_id not in by_id:
        raise ValueError(f"token_id not found in supplied records: {token_id!r}")

    chain: List[Dict[str, Any]] = []
    seen = set()
    current: Optional[str] = token_id

    while current is not None:
        if current in seen:
            raise ValueError(f"cycle detected in token lineage at {current!r}")
        seen.add(current)

        record = by_id.get(current)
        if record is None:
            raise ValueError(
                f"broken provenance: parent token_id {current!r} not present in supplied records"
            )

        chain.append(record)
        current = _parent_of(record)

    chain_hashable = [
        {
            "token_id": r.get("token_id"),
            "token_type": r.get("token_type"),
            "cram_ref_hash": r.get("cram_ref_hash"),
        }
        for r in chain
    ]

    hashable_core: Dict[str, Any] = {
        "schema_id": SCHEMA_TOKEN_PROVENANCE,
        "queried_token_id": token_id,
        "chain": chain_hashable,
        "chain_length": len(chain),
        "root_token_type": chain[-1].get("token_type"),
        "authority": AUTHORITY,
        "authority_status": "SECONDARY_DERIVED_EVIDENCE_ONLY",
        "may_replace_primary_evidence": False,
    }
    trace_hash = hash_json("PH6_SOSO_JEDI_TOKEN_PROVENANCE_V1", hashable_core)

    return {**hashable_core, "trace_hash": trace_hash}
