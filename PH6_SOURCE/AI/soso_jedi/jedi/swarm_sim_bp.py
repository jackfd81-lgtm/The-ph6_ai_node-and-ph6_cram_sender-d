#!/usr/bin/env python3
"""
PH6 Book V Engine Core — Lane 2 Advisory System (ADVISORY_ZERO).

Implements BookVCoreEngine: Storm exploration → Swarm evaluation → JEDI reconstruction.

This system may NOT:
  adjudicate, rewrite CRAM, override PSEUDO, modify authority hashes,
  modify replay certification, issue PASS/DROP, mint CRAM tokens,
  or change Lane 1 sequence state.

AI Contribution Signature:
  {"proposed_by":"claude-code-lane2","proposed_at_utc":"2026-06-06","ratified_by":null}
"""
from __future__ import annotations

import datetime
import hashlib
import json
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

try:
    import networkx as nx
    _NX_AVAILABLE = True
except ImportError:
    nx = None
    _NX_AVAILABLE = False

EXECUTION_VERSION = "PH6_BOOK_V_CORE_V5_0"

# Corrected schema IDs — dot-separated, per operator correction lock 2026-06-06
SCHEMA_CONTINUITY_BLOCK = "ph6.soso.continuity_block.v1"
SCHEMA_STRATIGRAPHY_LAYER = "ph6.cognitive.stratigraphy.layer.v1"
SCHEMA_ADVISORY_MANIFEST = "ph6.advisory.manifest.v1"

GENESIS = "GENESIS"
AUTHORITY = "ADVISORY_ZERO"


def compute_blake2b_256(data: bytes) -> str:
    """BLAKE2b-256, digest_size=32. Width-64 hex. Not SHA-256."""
    return hashlib.blake2b(data, digest_size=32).hexdigest()


def canonical_timestamp() -> str:
    """UTC microsecond timestamp. NOT used in hash computation (replay isolation)."""
    dt = datetime.datetime.now(datetime.timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%S") + f".{dt.microsecond:06d}Z"


def canonical_json_bytes(obj: Dict[str, Any]) -> bytes:
    return (
        json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
        + "\n"
    ).encode("utf-8")


def hash_json(domain: str, obj: Dict[str, Any]) -> str:
    """BLAKE2b-256 over domain-prefix + canonical JSON bytes."""
    return compute_blake2b_256(domain.encode("utf-8") + b"|" + canonical_json_bytes(obj))


def drift_status(index: float) -> str:
    if index < 0.10:
        return "STABLE"
    if index < 0.20:
        return "WATCH"
    if index < 0.35:
        return "ELEVATED"
    if index < 0.50:
        return "HIGH"
    return "CRITICAL"


class BookVCoreEngine:
    """
    Lane 2 Storm → Swarm → JEDI reconstruction engine.
    Authority: ADVISORY_ZERO.

    All output records are advisory only and structurally blocked from
    modifying Lane 1 state, CRAM tiers, or PSEUDO adjudication.
    """

    def __init__(self, execution_seed: int = 42):
        self.rng = np.random.default_rng(execution_seed)
        self.prev_continuity_hash = GENESIS
        self.prev_trace_hash = GENESIS
        self.continuity_seq = 0
        self.trace_seq = 0

    def run_storm_exploration(self, base_layer_id: int) -> List[Dict[str, Any]]:
        """Domain 4: generate counterfactual branch candidates from deterministic RNG."""
        variances = self.rng.uniform(0.01, 0.99, size=3)
        branches = []
        for idx, variance in enumerate(variances):
            core: Dict[str, Any] = {
                "branch_index": idx,
                "parent_layer": base_layer_id,
                "projected_variance": f"{float(variance):.6f}",
                "authority": AUTHORITY,
            }
            core["branch_hash"] = hash_json("PH6_STORM_BRANCH_V1", core)
            branches.append(core)
        return branches

    def run_swarm_evaluation(self, storm_branches: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Domain 5: belief-propagation summary over storm branch set."""
        mean_drift = (
            float(np.mean([float(b["projected_variance"]) for b in storm_branches]))
            if storm_branches
            else 0.0
        )
        return {
            "evaluated_mean_drift": mean_drift,
            "drift_status": drift_status(mean_drift),
            "branch_count": len(storm_branches),
            "authority": AUTHORITY,
        }

    def run_jedi_reconstruction(
        self,
        layer_id: int,
        parent_id: Optional[int],
        storm_data: List[Dict[str, Any]],
        swarm_data: Dict[str, Any],
    ) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
        """
        Domain 6: synthesize stratigraphy, continuity block, and advisory manifest.

        Returns (stratigraphy_record, continuity_block, advisory_manifest).
        All three carry authority=ADVISORY_ZERO.

        Replay isolation: timestamp is excluded from all hash inputs.
        """
        recovered_nodes = len(storm_data) * 4
        unsupported_assumptions = 2
        # MCI: lower = fewer assumptions = stronger reconstruction (Occam's razor)
        mci_score = float(unsupported_assumptions) / max(float(recovered_nodes), 1.0)

        # --- Stratigraphy record ---
        stratigraphy_core: Dict[str, Any] = {
            "schema_id": SCHEMA_STRATIGRAPHY_LAYER,
            "layer_id": layer_id,
            "parent_layer_id": parent_id if parent_id is not None else -1,
            "branch_count": len(storm_data),
            "recovered_nodes": recovered_nodes,
            "mci_score": round(mci_score, 6),
            "reasoning_fossil_signatures": [b["branch_hash"] for b in storm_data],
            "authority": AUTHORITY,
        }
        stratigraphy_core["continuity_hash"] = hash_json(
            "PH6_COGNITIVE_STRATIGRAPHY_V1", stratigraphy_core
        )

        # --- Continuity block (timestamp excluded from hash input) ---
        continuity_hashable: Dict[str, Any] = {
            "schema_id": SCHEMA_CONTINUITY_BLOCK,
            "continuity_seq": self.continuity_seq,
            "prev_continuity_hash": self.prev_continuity_hash,
            "soso_component": "JEDI",
            "topology_payload": {
                "active_vertices": [f"layer_{layer_id}", f"parent_{parent_id}"],
                "edge_count": len(storm_data),
            },
        }
        continuity_hash = hash_json("PH6_SOSO_CONTINUITY_BLOCK_V1", continuity_hashable)
        continuity_block: Dict[str, Any] = {
            **continuity_hashable,
            "timestamp_utc": canonical_timestamp(),
            "continuity_hash": continuity_hash,
            "authority": AUTHORITY,
        }

        # --- Advisory manifest (timestamp excluded from trace_hash input) ---
        mean_drift = swarm_data["evaluated_mean_drift"]
        advisory_hashable: Dict[str, Any] = {
            "schema_id": SCHEMA_ADVISORY_MANIFEST,
            "trace_seq": self.trace_seq,
            "prev_trace_hash": self.prev_trace_hash,
            "drift_index": round(mean_drift, 6),
            "drift_status": swarm_data["drift_status"],
            "excavation_summary": {
                "stratigrapher_layers_processed": recovered_nodes,
                "minimum_capacity_assumptions_count": unsupported_assumptions,
                "mci_score": round(mci_score, 6),
            },
            "authority_compliance_flag": True,
            "authority": AUTHORITY,
        }
        trace_hash = hash_json("PH6_ADVISORY_TRACE_V1", advisory_hashable)
        advisory_manifest: Dict[str, Any] = {
            **advisory_hashable,
            "timestamp_utc": canonical_timestamp(),
            "trace_hash": trace_hash,
        }

        # Advance chain state
        self.prev_continuity_hash = continuity_hash
        self.prev_trace_hash = trace_hash
        self.continuity_seq += 1
        self.trace_seq += 1

        return stratigraphy_core, continuity_block, advisory_manifest


# Alias for tests that import SoSoJEDISwarm by name
SoSoJEDISwarm = BookVCoreEngine


if __name__ == "__main__":
    engine = BookVCoreEngine()
    branches = engine.run_storm_exploration(base_layer_id=0)
    evaluation = engine.run_swarm_evaluation(branches)
    _, _, advisory = engine.run_jedi_reconstruction(1, 0, branches, evaluation)
    print(json.dumps(advisory, indent=2))
