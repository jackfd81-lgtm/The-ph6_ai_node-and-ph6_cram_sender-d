"""
ph6_l2_expand.token_topology

Lane: 2
Authority: ZERO
Write domain: none (pure computation)

Computes advisory topology metrics from a token map. These metrics
describe MRAM-S token topology only — they are never thresholds, never
confidence-as-authority, and never feed back into Lane 1.
"""

from __future__ import annotations

from typing import Dict

from ph6_l2_expand.token_types import TokenBase

STABLE_SUPPORT_MIN = 2


def compute_metrics(token_map: Dict[str, TokenBase], decayed_link_count: int = 0) -> Dict[str, object]:
    rt_count = sum(1 for t in token_map.values() if t.token_type == "RT")
    vdt_count = sum(1 for t in token_map.values() if t.token_type == "VDT")
    vlt_count = sum(1 for t in token_map.values() if t.token_type == "VLT")

    stable_link_count = vlt_count + sum(
        1
        for t in token_map.values()
        if t.token_type == "VDT" and t.advisory_payload.get("support_count", 0) >= STABLE_SUPPORT_MIN
    )

    possible_pairs = max(1, rt_count * (rt_count - 1) // 2)
    topology_density = stable_link_count / possible_pairs

    return {
        "rt_count": rt_count,
        "vdt_count": vdt_count,
        "vlt_count": vlt_count,
        "stable_link_count": stable_link_count,
        "decayed_link_count": decayed_link_count,
        "topology_density": f"{topology_density:.4f}",
    }
