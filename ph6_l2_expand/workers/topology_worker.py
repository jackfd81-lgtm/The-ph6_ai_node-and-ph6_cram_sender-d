"""
ph6_l2_expand.workers.topology_worker

Lane: 2
Authority: ZERO
Write domain: none (in-memory)

Computes advisory topology metrics for an already-serialized token map.
"""

from __future__ import annotations

from typing import Any, Dict

from ph6_l2_expand.token_topology import compute_metrics
from ph6_l2_expand.topology_mapper import deserialize_token_map


def metrics(token_map_dict: Dict[str, Any], decayed_link_count: int = 0) -> Dict[str, object]:
    token_map = deserialize_token_map(token_map_dict)
    return compute_metrics(token_map, decayed_link_count=decayed_link_count)
