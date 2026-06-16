"""
ph6_l2_expand.experimental.advisory_improvement_tracker

Lane: 2
Authority: ZERO
Write domain: MRAM-S only (via ph6_l2_expand.mram_s_writer)

Runs N advisory improvement cycles for a single source object, writing one
MRAM-S advisory record per cycle. "Improvement" means only:
  - more stable advisory links
  - better continuity grouping
  - clearer decay/stability classification
  - repeatable token topology
  - improved MRAM-S-only hypothesis maps

It never means model self-modification, threshold/authority/PASS-DROP
changes, EvidencePacket mutation, CRAM mutation, or replay-dependency
changes. Each cycle's record is independently boundary-checked by
mram_s_writer before it is accepted.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from ph6_l2_expand.experimental import mock_ai_client
from ph6_l2_expand.mram_s_writer import write_advisory
from ph6_l2_expand.schemas import ADVISORY_AUTHORITY_LEVEL, MRAM_S_ADVISORY_SCHEMA
from ph6_l2_expand.token_promotion import DEFAULT_PROMOTION_THRESHOLD
from ph6_l2_expand.virtual_token_mapper import DEFAULT_DECAY_TTL

MOCK_OFFLINE_AI = "mock-offline-ai"
OLLAMA_LOCAL = "ollama-local"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_advisory_record(source_object_id: str, analysis_type: str, advisory: Dict[str, Any], model_info: str = None) -> Dict[str, Any]:
    record = {
        "schema": MRAM_S_ADVISORY_SCHEMA,
        "advisory_id": str(uuid.uuid4()),
        "source_object_id": source_object_id,
        "analysis_type": analysis_type,
        "created_at": _utc_now_iso(),
        "authority_level": ADVISORY_AUTHORITY_LEVEL,
        "isolation_confirmed": True,
        "refs": [source_object_id],
        "advisory_data": advisory,
    }
    if model_info is not None:
        record["model_info"] = model_info
    return record


def run_cycles(
    source_object_id: str,
    source_object: Dict[str, Any],
    out_dir: Path,
    cycles: int,
    mode: str = MOCK_OFFLINE_AI,
    decay_ttl: int = DEFAULT_DECAY_TTL,
    promotion_threshold: int = DEFAULT_PROMOTION_THRESHOLD,
) -> List[Dict[str, Any]]:
    """
    Run `cycles` advisory improvement cycles, writing one MRAM-S advisory
    record per cycle. Returns a list of per-cycle result dicts:
      {"cycle": int, "path": str, "status": "WRITTEN"|"QUARANTINED",
       "metrics": {...}}
    """
    token_map: Dict[str, Any] = {}
    results: List[Dict[str, Any]] = []

    for cycle in range(1, cycles + 1):
        if mode == MOCK_OFFLINE_AI:
            advisory = mock_ai_client.generate(
                source_object_id, source_object, cycle, token_map,
                decay_ttl=decay_ttl, promotion_threshold=promotion_threshold,
            )
            analysis_type = "MOCK_AI"
            model_info = "mock-offline-ai:deterministic-rule-based"
        elif mode == OLLAMA_LOCAL:
            from ph6_l2_expand.experimental import deepseek_client

            advisory = deepseek_client.generate(
                source_object_id, source_object, cycle, token_map,
                decay_ttl=decay_ttl, promotion_threshold=promotion_threshold,
            )
            analysis_type = "DEEPSEEK"
            model_info = advisory.get("model_info", "deepseek-r1:1.5b")
        else:
            raise ValueError(f"unknown mode: {mode!r}")

        token_map = advisory.get("token_map_after", token_map)

        record = build_advisory_record(source_object_id, analysis_type, advisory, model_info)
        filename = f"advisory_{source_object_id}_cycle{cycle:04d}.json"
        path, status, violations = write_advisory(Path(out_dir), filename, record)

        results.append({
            "cycle": cycle,
            "path": str(path),
            "status": status,
            "violations": violations,
            "metrics": advisory.get("improvement_metrics", {}),
        })

    return results
