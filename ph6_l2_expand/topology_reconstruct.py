"""
ph6_l2_expand.topology_reconstruct

ER-1A bridge: ph6/tok advisory lifecycle chain → ph6_l2_expand topology.

Lane: 2
Authority: ZERO
Write domain: none (pure computation — no I/O performed here)

Reads a ph6/tok tok_advisory_audit.jsonl chain, extracts VLT observations,
translates each observation into a topology source object, and runs
apply_cycle() to produce an advisory token_map with a deterministic
BLAKE2b-256 topology hash.

STRICT BOUNDARIES:
- No Lane-1 imports (no ph6.cram_pu, no ph6_cert)
- No CRAM-0/A/R reads or writes
- No PASS/DROP verdict fields
- No MRAM-S writes (caller is responsible for any persistence)
- Events with schema "ph6.soso_lite.v0.1" are rejected and logged as errors
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ph6_l2_expand.schemas import canonical_json
from ph6_l2_expand.token_types import TokenBase
from ph6_l2_expand.topology_mapper import apply_cycle, serialize_token_map

LEGACY_SOSO_LITE_SCHEMA = "ph6.soso_lite.v0.1"

VLT_PROMOTION_EVENT = "VDT_PROMOTED_TO_VLT"
VLT_PRUNE_EVENT = "VLT_PRUNED"


# ---------------------------------------------------------------------------
# Chain replay (pure extraction)
# ---------------------------------------------------------------------------

def _extract_vlt_observations_from_events(
    events: List[Dict[str, Any]],
) -> Tuple[Dict[str, Dict[str, Any]], List[str]]:
    """
    Extract the active VLT set from a pre-parsed list of audit events.

    Returns (active_vlts, errors) where active_vlts maps vlt_token_id →
    promotion payload, and errors collects rejected/filtered events.

    Legacy soso_lite.v0.1 events are rejected and recorded in errors.
    VLT_PRUNED events remove previously promoted VLTs from the active set.
    """
    active_vlts: Dict[str, Dict[str, Any]] = {}
    errors: List[str] = []

    for idx, event in enumerate(events):
        if event.get("schema") == LEGACY_SOSO_LITE_SCHEMA:
            errors.append(
                f"event[{idx}]: rejected legacy schema {LEGACY_SOSO_LITE_SCHEMA}"
                f" (event_type={event.get('event_type', 'unknown')})"
            )
            continue

        event_type = event.get("event_type", "")
        payload = event.get("payload", {})

        if event_type == VLT_PROMOTION_EVENT:
            vlt_id = payload.get("vlt_token_id", "")
            if vlt_id:
                active_vlts[vlt_id] = payload

        elif event_type == VLT_PRUNE_EVENT:
            vlt_id = payload.get("token_id", "")
            active_vlts.pop(vlt_id, None)

    return active_vlts, errors


def replay_tok_chain(
    audit_path: Path,
) -> Tuple[bool, List[Dict[str, Any]], List[str]]:
    """
    Validate a tok advisory audit chain and extract active VLT observations.

    Step 1: run ph6.tok.reconstruct.validate_chain_integrity (hash chain check).
    Step 2: walk events, filter legacy records, track VLT promotions/prunings.

    Returns (chain_valid, vlt_observations_list, errors).
    Raises nothing — errors are collected and returned.
    """
    from ph6.tok.reconstruct import validate_chain_integrity

    if not audit_path.exists():
        return False, [], [f"audit file not found: {audit_path}"]

    chain_valid, _event_count, chain_error = validate_chain_integrity(audit_path)
    if not chain_valid:
        return False, [], [f"chain integrity failure: {chain_error}"]

    events: List[Dict[str, Any]] = []
    parse_errors: List[str] = []

    with open(audit_path, "rb") as fh:
        for raw_line in fh:
            raw_line = raw_line.strip()
            if not raw_line:
                continue
            try:
                events.append(json.loads(raw_line.decode("utf-8")))
            except Exception as exc:
                parse_errors.append(f"json parse error: {exc}")

    active_vlts, extract_errors = _extract_vlt_observations_from_events(events)
    all_errors = parse_errors + extract_errors

    return True, list(active_vlts.values()), all_errors


# ---------------------------------------------------------------------------
# Translation helpers
# ---------------------------------------------------------------------------

def vlt_observation_to_source(
    observation: Dict[str, Any],
) -> Tuple[str, Dict[str, Any]]:
    """
    Translate a VLT promotion payload into a (source_object_id, source_object)
    pair for build_reference_tokens() in topology_mapper.

    Only topology-safe, non-forbidden field names are exposed in source_object.
    """
    vlt_id = observation.get("vlt_token_id", "unknown_vlt")
    cram_ref = observation.get("cram_ref_hash", "unknown_cram_ref")
    source_object = {
        "cram_ref": cram_ref[:16],
        "vlt_prefix": vlt_id[:16],
    }
    return vlt_id, source_object


def build_candidate_links_from_observations(
    observations: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Generate advisory candidate links from VLT observations.

    VLTs sharing the same cram_ref_hash are linked (co-observed in the same
    CRAM frame context). These are hypothetical links only — Authority ZERO,
    never fed to Lane-1.
    """
    by_cram: Dict[str, List[str]] = {}
    for obs in observations:
        cram_ref = obs.get("cram_ref_hash", "")
        vlt_id = obs.get("vlt_token_id", "")
        if cram_ref and vlt_id:
            by_cram.setdefault(cram_ref, []).append(vlt_id)

    links: List[Dict[str, Any]] = []
    for _cram, vlt_ids in sorted(by_cram.items()):
        sorted_ids = sorted(vlt_ids)
        for i in range(len(sorted_ids)):
            for j in range(i + 1, len(sorted_ids)):
                links.append({
                    "from": sorted_ids[i],
                    "to": sorted_ids[j],
                    "relation": "co_observed",
                })
    return links


# ---------------------------------------------------------------------------
# Canonical hash
# ---------------------------------------------------------------------------

def canonical_topology_hash(token_map: Dict[str, TokenBase]) -> str:
    """
    Deterministic BLAKE2b-256 hash of the advisory token map.

    Tokens are serialized with sorted keys then canonicalized.
    Stable across Python restarts and across machines given the same map.
    """
    serialized = serialize_token_map(token_map)
    data = canonical_json(serialized)
    return hashlib.blake2b(data, digest_size=32).hexdigest()


# ---------------------------------------------------------------------------
# Full reconstruction pipeline
# ---------------------------------------------------------------------------

def reconstruct_topology(
    audit_path: Path,
    cycle: int = 1,
) -> Tuple[Dict[str, TokenBase], str, Dict[str, Any]]:
    """
    Full ER-1A reconstruction pipeline.

    Reads tok advisory audit chain → extracts VLT observations →
    translates each VLT to topology source objects + candidate links →
    applies advisory cycles → returns (token_map, topology_hash, metadata).

    Raises ValueError if chain integrity fails (chain_valid=False).
    """
    chain_valid, observations, errors = replay_tok_chain(audit_path)
    if not chain_valid:
        raise ValueError(f"chain replay failed: {errors}")

    token_map: Dict[str, TokenBase] = {}

    # Per-VLT cycle: build RT tokens and any intra-VLT links.
    for obs in observations:
        source_object_id, source_object = vlt_observation_to_source(obs)
        token_map, _metrics, _decay_notes, _promoted = apply_cycle(
            token_map,
            source_object_id=source_object_id,
            source_object=source_object,
            candidate_links=[],
            cycle=cycle,
        )

    # Cross-VLT candidate links (co_observed within same cram_ref).
    cross_links = build_candidate_links_from_observations(observations)
    if cross_links:
        token_map, _metrics, _decay_notes, _promoted = apply_cycle(
            token_map,
            source_object_id="er1a_cross_link",
            source_object={"link_pass": "cross"},
            candidate_links=cross_links,
            cycle=cycle + 1,
        )

    topo_hash = canonical_topology_hash(token_map)

    metadata: Dict[str, Any] = {
        "schema": "ph6.er1a.topology_reconstruct.v1",
        "authority_level": "ZERO",
        "advisory_only": True,
        "chain_errors": errors,
        "observation_count": len(observations),
        "token_count": len(token_map),
        "topology_hash": topo_hash,
    }
    return token_map, topo_hash, metadata
