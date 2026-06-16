"""
ph6_l2_expand.virtual_token_mapper

Lane: 2
Authority: ZERO
Write domain: none (in-memory map construction only)

Turns advisory "candidate links" (produced by the mock AI or DeepSeek
advisory node) into Virtual Decay Tokens (VDT). A candidate link is a
hypothesis about a relationship between two RT/VLT tokens — it is never
treated as fact and never carries verdict/threshold language.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from ph6_l2_expand.token_types import TokenBase, make_vdt, vdt_token_id

DEFAULT_DECAY_TTL = 2


def apply_candidate_links(
    token_map: Dict[str, TokenBase],
    candidate_links: List[Dict[str, Any]],
    cycle: int,
    decay_ttl: int = DEFAULT_DECAY_TTL,
) -> Tuple[Dict[str, TokenBase], List[str]]:
    """
    Apply candidate links for this cycle.

    For each link {"from": <token_id>, "to": <token_id>, "relation": <str>}:
      - if a matching VDT already exists, reinforce it (support_count += 1,
        last_seen_cycle = cycle, decay_remaining reset to decay_ttl)
      - otherwise create a new VDT with support_count = 1

    Returns the updated token_map and the list of VDT token_ids that were
    touched (reinforced or created) this cycle.
    """
    touched: List[str] = []

    for link in candidate_links:
        from_id = link["from"]
        to_id = link["to"]
        relation = link.get("relation", "related")

        vid = vdt_token_id(from_id, to_id, relation)
        existing = token_map.get(vid)

        if existing is not None and existing.token_type == "VDT":
            existing.advisory_payload["support_count"] = existing.advisory_payload.get("support_count", 1) + 1
            existing.advisory_payload["last_seen_cycle"] = cycle
            existing.advisory_payload["decay_remaining"] = decay_ttl
        else:
            vdt = make_vdt(from_id, to_id, relation, cycle, decay_ttl)
            token_map[vid] = vdt

        touched.append(vid)

    return token_map, touched
