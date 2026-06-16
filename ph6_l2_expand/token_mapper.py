"""
ph6_l2_expand.token_mapper

Lane: 2
Authority: ZERO
Write domain: none (in-memory map construction only)

Builds Reference Tokens (RT) from a read-only source object seed. The
source object is a plain dict that has already been adjudicated by
PSEUDO-A (CRAM-A) or rejected (CRAM-R); this module never writes back to
it and never inspects Lane-1 verdict fields.
"""

from __future__ import annotations

from typing import Any, Dict, List

from ph6_l2_expand.token_types import TokenBase, make_rt


def build_reference_tokens(source_object_id: str, source_object: Dict[str, Any]) -> Dict[str, TokenBase]:
    """
    Build one RT token per top-level field of source_object.

    Deterministic: same (source_object_id, source_object) always yields the
    same set of RT token ids.
    """
    tokens: Dict[str, TokenBase] = {}
    for field_name in sorted(source_object.keys()):
        rt = make_rt(source_object_id, field_name)
        tokens[rt.token_id] = rt
    return tokens


def observable_fields(source_object: Dict[str, Any]) -> List[str]:
    """Stable, sorted list of top-level field names in a source object."""
    return sorted(source_object.keys())
