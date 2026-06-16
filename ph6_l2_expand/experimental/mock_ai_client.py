"""
ph6_l2_expand.experimental.mock_ai_client

Lane: 2
Authority: ZERO
Write domain: none (returns a dict; mram_s_writer performs the write)

Deterministic, rule-based, fully offline mock AI advisory node.

Mode: MOCK_OFFLINE_AI
  - no internet
  - no Ollama required
  - same input -> same output (deterministic)
  - never emits authority, never issues PASS/DROP, never mutates Lane 1

This is the DEFAULT advisory node. ph6_l2_expand.experimental.deepseek_client
is an optional, experimental, real-model replacement that follows the same
output schema and the same boundary rules.
"""

from __future__ import annotations

from typing import Any, Dict, List

from ph6_l2_expand.schemas import MOCK_AI_ADVISORY_SCHEMA, ADVISORY_AUTHORITY_LEVEL
from ph6_l2_expand.token_mapper import observable_fields
from ph6_l2_expand.token_promotion import DEFAULT_PROMOTION_THRESHOLD
from ph6_l2_expand.token_types import rt_token_id, vdt_token_id
from ph6_l2_expand.topology_mapper import apply_cycle, deserialize_token_map, serialize_token_map
from ph6_l2_expand.virtual_token_mapper import DEFAULT_DECAY_TTL

MODE = "MOCK_OFFLINE_AI"


def _candidate_links(source_object_id: str, fields: List[str]) -> List[Dict[str, str]]:
    """Deterministic chain of co-observation links between consecutive fields."""
    links = []
    rt_ids = {f: rt_token_id(source_object_id, f) for f in fields}
    for a, b in zip(fields, fields[1:]):
        links.append({"from": rt_ids[a], "to": rt_ids[b], "relation": "co-observed"})
    return links


def generate(
    source_object_id: str,
    source_object: Dict[str, Any],
    cycle: int,
    token_map_before_dict: Dict[str, Any],
    decay_ttl: int = DEFAULT_DECAY_TTL,
    promotion_threshold: int = DEFAULT_PROMOTION_THRESHOLD,
) -> Dict[str, Any]:
    """
    Produce one ph6_mock_ai_advisory_v1 record for a single improvement cycle.

    Deterministic for fixed (source_object_id, source_object, cycle,
    token_map_before_dict).
    """
    fields = observable_fields(source_object)
    candidate_links = _candidate_links(source_object_id, fields)

    token_map = deserialize_token_map(token_map_before_dict)
    token_map_before = serialize_token_map(token_map)

    candidate_vdt_ids = {
        vdt_token_id(link["from"], link["to"], link["relation"]) for link in candidate_links
    }

    stability_notes: List[str] = []
    decay_notes: List[str] = []
    for token_id, token in token_map.items():
        if token.token_type == "VLT":
            stability_notes.append(f"stable:{token_id}")
        elif token.token_type == "VDT" and token_id in candidate_vdt_ids:
            stability_notes.append(f"reinforced:{token_id}")
        elif token.token_type == "VDT":
            decay_notes.append(f"not_reinforced:{token_id}")

    token_map, metrics, cycle_decay_notes, promoted = apply_cycle(
        token_map,
        source_object_id,
        source_object,
        candidate_links,
        cycle,
        decay_ttl=decay_ttl,
        promotion_threshold=promotion_threshold,
    )
    decay_notes.extend(cycle_decay_notes)
    stability_notes.extend(f"promoted:{tid}" for tid in promoted)

    token_map_after = serialize_token_map(token_map)

    return {
        "schema": MOCK_AI_ADVISORY_SCHEMA,
        "mode": MODE,
        "authority_level": ADVISORY_AUTHORITY_LEVEL,
        "source_object_id": source_object_id,
        "observations": [f"observed field '{f}'" for f in fields],
        "candidate_links": candidate_links,
        "decay_notes": decay_notes,
        "stability_notes": stability_notes,
        "boundary_warnings": [],
        "improvement_cycle": cycle,
        "token_map_before": token_map_before,
        "token_map_after": token_map_after,
        "improvement_metrics": metrics,
    }
