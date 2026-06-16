"""
ph6_l2_expand.token_types

Lane: 2
Authority: ZERO
Write domain: MRAM-S only (no I/O performed here)

Locked token classes:
  RT  = Reference Token
  VLT = Virtual Longevity Token
  VDT = Virtual Decay Token

No other token classes are permitted (enforced by token_policy).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List

from ph6_l2_expand.schemas import SOSO_TOKEN_SCHEMA, TOKEN_AUTHORITY, TOKEN_TYPES

# Fixed namespace so token ids are deterministic and reproducible across runs.
PH6_TOKEN_NAMESPACE = uuid.UUID("0c0ffee0-0000-4000-8000-000000000001")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def rt_token_id(source_object_id: str, field_name: str) -> str:
    """Deterministic RT token id for a (source_object_id, field) pair."""
    return str(uuid.uuid5(PH6_TOKEN_NAMESPACE, f"RT|{source_object_id}|{field_name}"))


def vdt_token_id(from_token_id: str, to_token_id: str, relation: str) -> str:
    """Deterministic VDT token id for a candidate link."""
    return str(uuid.uuid5(PH6_TOKEN_NAMESPACE, f"VDT|{from_token_id}|{to_token_id}|{relation}"))


def vlt_token_id(source_vdt_token_id: str) -> str:
    """Deterministic VLT token id for a promoted VDT."""
    return str(uuid.uuid5(PH6_TOKEN_NAMESPACE, f"VLT|{source_vdt_token_id}"))


@dataclass
class TokenBase:
    token_id: str
    token_type: str
    refs: List[str]
    created_at: str
    advisory_payload: Dict[str, Any] = field(default_factory=dict)
    schema: str = SOSO_TOKEN_SCHEMA
    authority: str = TOKEN_AUTHORITY

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "TokenBase":
        return TokenBase(
            token_id=d["token_id"],
            token_type=d["token_type"],
            refs=list(d["refs"]),
            created_at=d["created_at"],
            advisory_payload=dict(d.get("advisory_payload", {})),
            schema=d.get("schema", SOSO_TOKEN_SCHEMA),
            authority=d.get("authority", TOKEN_AUTHORITY),
        )


def make_rt(source_object_id: str, field_name: str, created_at: str = None) -> TokenBase:
    return TokenBase(
        token_id=rt_token_id(source_object_id, field_name),
        token_type="RT",
        refs=[source_object_id],
        created_at=created_at or utc_now_iso(),
        advisory_payload={"field": field_name, "source_object_id": source_object_id},
    )


def make_vdt(
    from_token_id: str,
    to_token_id: str,
    relation: str,
    cycle: int,
    decay_ttl: int,
    created_at: str = None,
) -> TokenBase:
    return TokenBase(
        token_id=vdt_token_id(from_token_id, to_token_id, relation),
        token_type="VDT",
        refs=[from_token_id, to_token_id],
        created_at=created_at or utc_now_iso(),
        advisory_payload={
            "relation": relation,
            "support_count": 1,
            "first_seen_cycle": cycle,
            "last_seen_cycle": cycle,
            "decay_remaining": decay_ttl,
        },
    )


def make_vlt(vdt: TokenBase, cycle: int, created_at: str = None) -> TokenBase:
    return TokenBase(
        token_id=vlt_token_id(vdt.token_id),
        token_type="VLT",
        refs=list(vdt.refs),
        created_at=created_at or utc_now_iso(),
        advisory_payload={
            "relation": vdt.advisory_payload.get("relation"),
            "support_count": vdt.advisory_payload.get("support_count", 1),
            "first_seen_cycle": vdt.advisory_payload.get("first_seen_cycle", cycle),
            "last_seen_cycle": cycle,
            "promoted_from": vdt.token_id,
        },
    )


assert set(TOKEN_TYPES) == {"RT", "VDT", "VLT"}
