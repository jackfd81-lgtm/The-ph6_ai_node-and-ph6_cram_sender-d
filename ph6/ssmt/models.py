from dataclasses import dataclass, field
from typing import Any, Dict, List
import time


@dataclass(frozen=True)
class SwarmInput:
    cram_refs: List[str]
    tok_refs: List[str]
    advisory_refs: List[str]


@dataclass
class SwarmPacket:
    swarm_id: str
    role: str
    authority: str
    lane: str
    ssmt_version: str
    ttl_seconds: int
    output_type: str
    advisory_payload: Dict[str, Any]
    drift_score: int
    confidence_fp: int
    created_at: float = field(default_factory=time.time)
    dependency_for_replay: bool = False
