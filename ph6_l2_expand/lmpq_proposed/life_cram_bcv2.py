"""
ph6_l2_expand.lmpq_proposed.life_cram_bcv2

Lane: 2
Authority: ZERO
Write domain: MRAM-S only, via ph6_l2_expand.mram_s_writer (no direct
filesystem I/O in this module)
Status: PROPOSED — see PH6_SOURCE/DRAFT/PH6-LMPQ-001-PROPOSED-SPEC-v0.1.md §6

"BCV2" (Bounded Campaign Vector, schema v2): a deterministic,
hash-addressable bundle summarizing one Life-CRAM "experience" for the
LMPQ-001 four-experience bench. Does not duplicate Life CRAM itself
(ph6/cram_pu/tools/life_cram_lcc_01_live_camera.py) — it packages
references to tokens/evidence already produced elsewhere.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ph6_l2_expand.schemas import canonical_json
from ph6_l2_expand.lmpq_proposed.tokens import blake2b256_hex

BCV2_SCHEMA = "ph6.lmpq.life_cram_bcv2.v1"


def build_bcv2(
    experience_id: str,
    cram_refs: List[str],
    token_ids: List[str],
    token_types_present: List[str],
    event_window_start_ms: int,
    event_window_end_ms: int,
    topology_hash: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Build a deterministic BCV2 bundle. Fails closed on missing evidence
    references or an inverted event window.
    """
    if not experience_id:
        raise ValueError("BCV2 requires a non-empty experience_id")
    if not cram_refs:
        raise ValueError("BCV2 requires at least one cram_ref (missing source evidence)")
    if not token_ids:
        raise ValueError("BCV2 requires at least one token_id")
    if event_window_end_ms < event_window_start_ms:
        raise ValueError("BCV2 event_window end precedes start")

    sorted_cram_refs = sorted(cram_refs)
    sorted_token_ids = sorted(token_ids)
    sorted_types = sorted(set(token_types_present))

    seed = {
        "experience_id": experience_id,
        "cram_refs": sorted_cram_refs,
        "token_ids": sorted_token_ids,
    }
    bcv_id = blake2b256_hex(seed)

    return {
        "schema": BCV2_SCHEMA,
        "authority": "ZERO",
        "advisory_only": True,
        "bcv_id": bcv_id,
        "experience_id": experience_id,
        "cram_refs": sorted_cram_refs,
        "token_ids": sorted_token_ids,
        "token_types_present": sorted_types,
        "topology_hash": topology_hash,
        "event_window": {"start_ms": event_window_start_ms, "end_ms": event_window_end_ms},
        "constraints": {
            "may_write_cram": False,
            "may_modify_evidence": False,
            "may_affect_pseudo": False,
            "may_issue_verdict": False,
            "may_block_rsync": False,
        },
    }


def write_bcv2(out_dir: Path, bundle: Dict[str, Any]) -> Tuple[Path, str, list]:
    """Persist a BCV2 bundle via the existing MRAM-S atomic writer."""
    from ph6_l2_expand.mram_s_writer import write_advisory

    filename = f"bcv2_{bundle['bcv_id']}.json"
    return write_advisory(out_dir, filename, bundle)
