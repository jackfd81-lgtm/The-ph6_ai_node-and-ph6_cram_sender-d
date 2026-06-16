"""
ph6_l2_expand.token_policy

Lane: 2
Authority: ZERO
Write domain: none (pure validation)

Locks the token class set to RT / VDT / VLT and the analysis_type set to
SOSO / TOKEN / MOCK_AI / DEEPSEEK. Validates token dicts before they are
written to MRAM-S. Contains no Lane-1 imports and performs no I/O.
"""

from __future__ import annotations

from typing import Any, Dict, List

from ph6_l2_expand.schemas import (
    ANALYSIS_TYPES,
    SOSO_TOKEN_SCHEMA,
    TOKEN_AUTHORITY,
    TOKEN_TYPES,
)

ALLOWED_TOKEN_TYPES = set(TOKEN_TYPES)
ALLOWED_ANALYSIS_TYPES = set(ANALYSIS_TYPES)

REQUIRED_TOKEN_FIELDS = {
    "schema",
    "token_id",
    "token_type",
    "refs",
    "created_at",
    "authority",
    "advisory_payload",
}


def validate_token_dict(token: Dict[str, Any]) -> List[str]:
    """Return a list of validation errors. Empty list == valid."""
    errors: List[str] = []

    missing = REQUIRED_TOKEN_FIELDS - set(token.keys())
    if missing:
        errors.append(f"token missing required fields: {sorted(missing)}")

    if token.get("schema") != SOSO_TOKEN_SCHEMA:
        errors.append(f"token.schema must be {SOSO_TOKEN_SCHEMA!r}, got {token.get('schema')!r}")

    token_type = token.get("token_type")
    if token_type not in ALLOWED_TOKEN_TYPES:
        errors.append(
            f"token_type must be one of {sorted(ALLOWED_TOKEN_TYPES)}, got {token_type!r}"
        )

    if token.get("authority") != TOKEN_AUTHORITY:
        errors.append(f"token.authority must be {TOKEN_AUTHORITY!r}, got {token.get('authority')!r}")

    if not isinstance(token.get("refs"), list) or not token.get("refs"):
        errors.append("token.refs must be a non-empty list")

    if not isinstance(token.get("advisory_payload"), dict):
        errors.append("token.advisory_payload must be a dict")

    return errors


def validate_analysis_type(analysis_type: str) -> List[str]:
    if analysis_type not in ALLOWED_ANALYSIS_TYPES:
        return [f"analysis_type must be one of {sorted(ALLOWED_ANALYSIS_TYPES)}, got {analysis_type!r}"]
    return []
