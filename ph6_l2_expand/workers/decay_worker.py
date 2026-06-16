"""
ph6_l2_expand.workers.decay_worker

Lane: 2
Authority: ZERO
Write domain: none (in-memory)

Standalone wrapper around token_decay for applying a decay pass to an
already-serialized token map (e.g. loaded from a prior MRAM-S advisory
record).
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from ph6_l2_expand.token_decay import apply_decay
from ph6_l2_expand.topology_mapper import deserialize_token_map, serialize_token_map


def run_decay(
    token_map_dict: Dict[str, Any],
    cycle: int,
    touched_this_cycle: List[str],
) -> Tuple[Dict[str, Any], int, List[str]]:
    token_map = deserialize_token_map(token_map_dict)
    token_map, decayed_count, decay_notes = apply_decay(token_map, cycle, touched_this_cycle)
    return serialize_token_map(token_map), decayed_count, decay_notes
