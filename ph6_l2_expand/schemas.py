"""
ph6_l2_expand.schemas

Lane: 2
Authority: ZERO
Write domain: MRAM-S only (this module performs no writes itself)

Canonical JSON helpers and schema name/version constants shared by every
module in ph6_l2_expand. Pure functions only — no I/O, no Lane-1 imports.
"""

from __future__ import annotations

import json
from typing import Any


# ---------------------------------------------------------------------------
# Schema identifiers (locked)
# ---------------------------------------------------------------------------

SOSO_TOKEN_SCHEMA = "ph6.soso_token.v1"
MRAM_S_ADVISORY_SCHEMA = "ph6_mram_s_advisory_v1"
MOCK_AI_ADVISORY_SCHEMA = "ph6_mock_ai_advisory_v1"

TOKEN_AUTHORITY = "MRAM-S_ONLY"
ADVISORY_AUTHORITY_LEVEL = "ZERO"

ANALYSIS_TYPES = ("SOSO", "TOKEN", "MOCK_AI", "DEEPSEEK")

TOKEN_TYPES = ("RT", "VDT", "VLT")


def canonical_json(obj: Any) -> bytes:
    """
    PH6-style canonical JSON:
    - sorted keys
    - UTF-8
    - no NaN / Infinity
    - compact separators
    """
    return json.dumps(
        obj,
        sort_keys=True,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")


def canonical_json_str(obj: Any) -> str:
    return canonical_json(obj).decode("utf-8")
