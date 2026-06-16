"""
ph6_l2_expand.token_promotion

Lane: 2
Authority: ZERO
Write domain: none (in-memory map mutation only)

Promotes a Virtual Decay Token (VDT) to a Virtual Longevity Token (VLT)
once it has been reinforced often enough to be considered a stable
advisory link. Promotion is an MRAM-S-only topology change — it never
creates a verdict, never touches thresholds, and never affects Lane 1.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

from ph6_l2_expand.token_types import TokenBase, make_vlt

DEFAULT_PROMOTION_THRESHOLD = 3


def promote_stable_vdts(
    token_map: Dict[str, TokenBase],
    cycle: int,
    promotion_threshold: int = DEFAULT_PROMOTION_THRESHOLD,
) -> Tuple[Dict[str, TokenBase], List[str]]:
    """
    Promote any VDT whose support_count has reached promotion_threshold
    into a VLT. The originating VDT is removed (its history is carried
    into the VLT's advisory_payload via "promoted_from").

    Returns (token_map, promoted_token_ids) where promoted_token_ids are
    the new VLT token ids.
    """
    promoted: List[str] = []

    for token_id in list(token_map.keys()):
        token = token_map[token_id]
        if token.token_type != "VDT":
            continue
        if token.advisory_payload.get("support_count", 0) < promotion_threshold:
            continue

        vlt = make_vlt(token, cycle)
        token_map[vlt.token_id] = vlt
        del token_map[token_id]
        promoted.append(vlt.token_id)

    return token_map, promoted
