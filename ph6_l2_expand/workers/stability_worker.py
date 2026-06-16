"""
ph6_l2_expand.workers.stability_worker

Lane: 2
Authority: ZERO
Write domain: none (in-memory)

Classifies each token in a token map as "stable" or "unstable" advisory
topology, and applies VDT -> VLT promotion for stable tokens. These labels
describe MRAM-S token topology only and are never PASS/DROP verdicts.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from ph6_l2_expand.token_promotion import DEFAULT_PROMOTION_THRESHOLD, promote_stable_vdts
from ph6_l2_expand.token_topology import STABLE_SUPPORT_MIN
from ph6_l2_expand.topology_mapper import deserialize_token_map, serialize_token_map


def classify_stability(token_map_dict: Dict[str, Any]) -> Dict[str, str]:
    """Return {token_id: "stable"|"unstable"} for every token."""
    labels: Dict[str, str] = {}
    for token_id, token in token_map_dict.items():
        if token["token_type"] == "VLT":
            labels[token_id] = "stable"
        elif token["token_type"] == "VDT":
            support = token.get("advisory_payload", {}).get("support_count", 0)
            labels[token_id] = "stable" if support >= STABLE_SUPPORT_MIN else "unstable"
        else:
            labels[token_id] = "unstable"
    return labels


def run_promotion(
    token_map_dict: Dict[str, Any],
    cycle: int,
    promotion_threshold: int = DEFAULT_PROMOTION_THRESHOLD,
) -> Tuple[Dict[str, Any], List[str]]:
    token_map = deserialize_token_map(token_map_dict)
    token_map, promoted = promote_stable_vdts(token_map, cycle, promotion_threshold)
    return serialize_token_map(token_map), promoted
