"""
ph6_l2_expand.lmpq_proposed.soso_jedi_adapter

Lane: 2
Authority: ADVISORY_ZERO (unchanged from PH6_SOURCE/AI/soso_jedi — this
adapter does not raise or alter its authority level)
Write domain: none
Status: PROPOSED — see PH6_SOURCE/DRAFT/PH6-LMPQ-001-PROPOSED-SPEC-v0.1.md §7

Adapter for single-token provenance lookup against the existing,
UNMODIFIED PH6_SOURCE.AI.soso_jedi.jedi.swarm_sim_bp.BookVCoreEngine.
BookVCoreEngine performs continuity/stratigraphy reconstruction over an
abstract layer/branch model, not single-token lookup — this adapter
derives a deterministic per-token seed and layer id so a given token_id
always reproduces the same Storm/Swarm/JEDI output, without touching
CRAM, PSEUDO, or issuing any verdict.
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path
from typing import Any, Dict


def _seed_for_token(token_id: str) -> int:
    digest = hashlib.blake2b(token_id.encode("utf-8"), digest_size=32).hexdigest()
    return int(digest[:8], 16) % (2**31 - 1)


def _layer_id_for_token(token_id: str) -> int:
    digest = hashlib.blake2b(token_id.encode("utf-8"), digest_size=8).hexdigest()
    return int(digest, 16) % 1_000_000


def _import_book_v_core_engine():
    repo_root = Path(__file__).resolve().parents[2]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    from PH6_SOURCE.AI.soso_jedi.jedi.swarm_sim_bp import BookVCoreEngine

    return BookVCoreEngine


def lookup_token_provenance(token_id: str) -> Dict[str, Any]:
    """
    Run one deterministic Storm -> Swarm -> JEDI pass anchored on
    token_id and return its stratigraphy/continuity/advisory output,
    tagged with the source token id. Same token_id always reproduces the
    same seed, layer id, and (timestamp aside) the same hashes, since
    BookVCoreEngine itself excludes wall-clock time from its hash inputs.
    """
    if not token_id:
        raise ValueError("lookup_token_provenance requires a non-empty token_id")

    BookVCoreEngine = _import_book_v_core_engine()

    seed = _seed_for_token(token_id)
    layer_id = _layer_id_for_token(token_id)

    engine = BookVCoreEngine(execution_seed=seed)
    branches = engine.run_storm_exploration(base_layer_id=layer_id)
    evaluation = engine.run_swarm_evaluation(branches)
    stratigraphy, continuity_block, advisory_manifest = engine.run_jedi_reconstruction(
        layer_id, None, branches, evaluation
    )

    return {
        "schema": "ph6.lmpq_proposed.soso_jedi_lookup.v1",
        "authority": "ADVISORY_ZERO",
        "source_token_id": token_id,
        "stratigraphy": stratigraphy,
        "continuity_block": continuity_block,
        "advisory_manifest": advisory_manifest,
    }
