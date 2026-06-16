"""
ph6_l2_expand.token_decay

Lane: 2
Authority: ZERO
Write domain: none (in-memory map mutation only)

Applies decay to Virtual Decay Tokens (VDT) that were not reinforced in
the current improvement cycle. Decay is advisory bookkeeping only — it
never touches CRAM-0/A/R, EvidencePacket, thresholds, or PASS/DROP.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

from ph6_l2_expand.token_types import TokenBase


def apply_decay(
    token_map: Dict[str, TokenBase],
    cycle: int,
    touched_this_cycle: List[str],
) -> Tuple[Dict[str, TokenBase], int, List[str]]:
    """
    Decrement decay_remaining for every VDT not touched this cycle.
    Remove VDT tokens whose decay_remaining drops to 0 or below.

    Returns (token_map, decayed_link_count, decay_notes).
    """
    decayed_count = 0
    decay_notes: List[str] = []
    touched = set(touched_this_cycle)

    for token_id in list(token_map.keys()):
        token = token_map[token_id]
        if token.token_type != "VDT":
            continue
        if token_id in touched:
            continue

        remaining = token.advisory_payload.get("decay_remaining", 0) - 1
        token.advisory_payload["decay_remaining"] = remaining
        decay_notes.append(f"decayed:{token_id}:remaining={remaining}")

        if remaining <= 0:
            del token_map[token_id]
            decayed_count += 1
            decay_notes.append(f"removed:{token_id}:cycle={cycle}")

    return token_map, decayed_count, decay_notes
