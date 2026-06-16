"""
ph6_l2_expand.workers.reference_worker

Lane: 2
Authority: ZERO
Write domain: none (read-only load)

Loads a read-only reference seed for a CRAM-A or CRAM-R object. The seed
is a plain JSON file: PSEUDO-A has already adjudicated the underlying
object, and this worker only reads the post-adjudication reference data
that Lane 1 has chosen to expose. It never writes back to the source file
and never inspects verdict/threshold fields even if present in the file
(those are stripped before tokens are built).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Tuple

# Top-level fields from a CRAM-A/R reference object that are explicitly
# Lane-1 authority data and must never be turned into tokens.
LANE1_ONLY_FIELDS = {
    "verdict",
    "pass",
    "drop",
    "threshold",
    "evidence_packet",
    "evidencepacket",
    "authority_chain",
    "replay_dependency",
}


def load_source(path: str) -> Tuple[str, Dict[str, Any]]:
    """
    Load a read-only CRAM-A/R reference object.

    Returns (source_object_id, source_object) where source_object contains
    only non-Lane-1 fields suitable for advisory token mapping.
    """
    p = Path(path)
    with open(p, "r", encoding="utf-8") as f:
        raw = json.load(f)

    if not isinstance(raw, dict):
        raise ValueError(f"source object must be a JSON object, got {type(raw).__name__}")

    object_id = str(raw.get("object_id") or p.stem)

    source_object = {
        k: v for k, v in raw.items()
        if k.lower() not in LANE1_ONLY_FIELDS and k != "object_id"
    }

    return object_id, source_object


def build_tokens(path: str):
    """Convenience: load a source object and build its RT tokens."""
    from ph6_l2_expand.token_mapper import build_reference_tokens

    object_id, source_object = load_source(path)
    return object_id, source_object, build_reference_tokens(object_id, source_object)
