"""
ph6_l2_expand.topology_mapper

Lane: 2
Authority: ZERO
Write domain: none (orchestration over in-memory token maps)

Top-level orchestration for a single advisory improvement cycle:
  1. ensure RT tokens exist for the source object
  2. apply candidate links as VDT tokens (create or reinforce)
  3. decay VDT tokens not reinforced this cycle
  4. promote stable VDT tokens to VLT
  5. compute topology metrics

This module never reads or writes CRAM-0/A/R, EvidencePacket, thresholds,
or PASS/DROP state. It operates entirely on in-memory token maps that are
later serialized by mram_s_writer.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from ph6_l2_expand.token_decay import apply_decay
from ph6_l2_expand.token_mapper import build_reference_tokens
from ph6_l2_expand.token_promotion import DEFAULT_PROMOTION_THRESHOLD, promote_stable_vdts
from ph6_l2_expand.token_topology import compute_metrics
from ph6_l2_expand.token_types import TokenBase
from ph6_l2_expand.virtual_token_mapper import DEFAULT_DECAY_TTL, apply_candidate_links


def serialize_token_map(token_map: Dict[str, TokenBase]) -> Dict[str, Any]:
    return {tid: tok.to_dict() for tid, tok in token_map.items()}


def deserialize_token_map(d: Dict[str, Any]) -> Dict[str, TokenBase]:
    return {tid: TokenBase.from_dict(tok) for tid, tok in d.items()}


def apply_cycle(
    token_map: Dict[str, TokenBase],
    source_object_id: str,
    source_object: Dict[str, Any],
    candidate_links: List[Dict[str, Any]],
    cycle: int,
    decay_ttl: int = DEFAULT_DECAY_TTL,
    promotion_threshold: int = DEFAULT_PROMOTION_THRESHOLD,
) -> Tuple[Dict[str, TokenBase], Dict[str, object], List[str], List[str]]:
    """
    Run one advisory improvement cycle in place on token_map.

    Returns (token_map, metrics, decay_notes, promoted_vlt_ids).
    """
    # 1. ensure RT tokens exist (idempotent, deterministic ids)
    for token_id, rt in build_reference_tokens(source_object_id, source_object).items():
        token_map.setdefault(token_id, rt)

    # 2. apply candidate links -> VDT create/reinforce
    token_map, touched = apply_candidate_links(token_map, candidate_links, cycle, decay_ttl)

    # 3. decay untouched VDTs
    token_map, decayed_count, decay_notes = apply_decay(token_map, cycle, touched)

    # 4. promote stable VDTs to VLT
    token_map, promoted = promote_stable_vdts(token_map, cycle, promotion_threshold)

    # 5. metrics
    metrics = compute_metrics(token_map, decayed_link_count=decayed_count)

    return token_map, metrics, decay_notes, promoted
