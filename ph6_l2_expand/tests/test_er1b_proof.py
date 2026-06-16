"""
ER-1B Proof Harness

Proves that VLT spatial/object fields emitted in VDT_PROMOTED_TO_VLT audit
events are recoverable from the advisory chain and produce semantically richer
deterministic topology nodes.

Lane: 2  Authority: ZERO
No mean_confidence used or emitted.
Temporal fields (first_seen_ms, last_seen_ms) emitted to chain but excluded
from topology source_object per ER-1B temporal policy.

Tests:
  1.  test_er1b_spatial_payload_preserved_in_audit_chain
  2.  test_multi_vlt_chain_reconstructs_spatial_fields
  3.  test_er1b_topology_hash_stable_across_invocations
  4.  test_er1b_spatial_source_objects_richer_than_er1a
  5.  test_er1b_legacy_chain_degrades_gracefully
  6.  test_er1b_distinct_object_classes_produce_distinct_rt_tokens
  7.  test_er1b_malformed_spatial_metadata_rejected_or_deterministically_degraded
  8.  test_no_cram_write
  9.  test_no_lane1_imports
"""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# ---------------------------------------------------------------------------
# Fixed constants for determinism
# ---------------------------------------------------------------------------

FIXED_T0 = 2_000_000_000_000  # ms — distinct from ER-1A T0

_OBJECTS = [
    # (object_class, cram_ref_hash, base_bbox, centroid)
    ("vehicle",  "cram_er1b_ref_vehicle_aaa", [10.0,  20.0, 100.0, 60.0],  [60.0,  50.0]),
    ("person",   "cram_er1b_ref_person__bbb", [180.0, 100.0, 40.0,  80.0], [200.0, 140.0]),
    ("bicycle",  "cram_er1b_ref_bicycle_ccc", [320.0, 160.0, 60.0,  80.0], [350.0, 200.0]),
]


def _build_er1b_tok_chain(base_dir: Path) -> Path:
    """
    Build a tok advisory chain with 3 VLT promotions (vehicle, person, bicycle),
    each with distinct spatial fields. Returns path to tok_advisory_audit.jsonl.

    All VDTs use fixed timestamps so the chain is deterministic.
    """
    from ph6.tok.lifecycle import VDT, TokenStore, DEFAULT_TOK_CONFIG

    tokens_dir = base_dir / "tokens"
    store = TokenStore(str(tokens_dir))

    for obj_class, cram_ref, base_bbox, _centroid in _OBJECTS:
        vdt_ids = []
        for i in range(5):
            t = FIXED_T0 + i * 100
            bbox = [base_bbox[0] + i * 0.2, base_bbox[1], base_bbox[2], base_bbox[3]]
            vdt = VDT(
                token_id=f"vdt_er1b_{obj_class}_{i:03d}",
                cram_ref_hash=cram_ref,
                timestamp_ms=t,
                last_updated_ms=t,
                object_class=obj_class,
                bbox=bbox,
                confidence=0.75,
                support_count=1,
            )
            store.add_vdt(vdt)
            vdt_ids.append(vdt.token_id)

        vlt = store.promote_to_vlt(
            vdt_ids,
            DEFAULT_TOK_CONFIG,
            event_time_ms=FIXED_T0 + 600,
        )
        assert vlt is not None, f"promotion failed for {obj_class}"

    return tokens_dir / "tok_advisory_audit.jsonl"


def _build_legacy_chain(base_dir: Path) -> Path:
    """
    Build a minimal chain with VDT_PROMOTED_TO_VLT events that do NOT contain
    spatial fields — simulates pre-ER-1B audit chains.
    """
    from ph6.tok.lifecycle import AdvisoryAudit

    audit_path = base_dir / "tok_advisory_audit.jsonl"
    audit = AdvisoryAudit(audit_path)
    audit.emit("VDT_PROMOTED_TO_VLT", {
        "vlt_token_id": "vlt_legacy_001",
        "source_vdt_ids": ["vdt_leg_0", "vdt_leg_1"],
        "cram_ref_hash": "cram_legacy_aabbccdd1122",
        "token_state_hash": "fake_state_hash_aaa",
        "config_hash": "fake_config_hash_aaa",
        # no spatial fields
    })
    return audit_path


def _build_malformed_spatial_chain(base_dir: Path) -> Path:
    """
    Build a chain where VDT_PROMOTED_TO_VLT events contain malformed spatial fields.
    Reconstruction should degrade gracefully (no exception, malformed fields excluded).
    """
    from ph6.tok.lifecycle import AdvisoryAudit

    audit_path = base_dir / "tok_advisory_audit.jsonl"
    audit = AdvisoryAudit(audit_path)
    audit.emit("VDT_PROMOTED_TO_VLT", {
        "vlt_token_id": "vlt_malformed_001",
        "source_vdt_ids": ["vdt_m_0"],
        "cram_ref_hash": "cram_malformed_xyz_9900",
        "token_state_hash": "fake_state_hash_bbb",
        "config_hash": "fake_config_hash_bbb",
        "object_class": "",           # empty string — invalid
        "centroid": [1.0],            # only 1 element — invalid
        "bbox": [-1.0, 0.0, -5.0, 10.0],  # negative w — invalid
        "support_count": -3,          # negative — invalid
        "first_seen_ms": 2000,
        "last_seen_ms": 1000,         # last < first — invalid temporal order
    })
    return audit_path


# ---------------------------------------------------------------------------
# 1. Spatial payload preserved in audit chain
# ---------------------------------------------------------------------------

def test_er1b_spatial_payload_preserved_in_audit_chain(tmp_path):
    """
    VDT_PROMOTED_TO_VLT events emitted after ER-1B patch contain spatial fields
    and do NOT contain mean_confidence.
    """
    audit_path = _build_er1b_tok_chain(tmp_path)

    with open(audit_path, "rb") as fh:
        events = [json.loads(line) for line in fh if line.strip()]

    promotion_events = [
        e for e in events if e.get("event_type") == "VDT_PROMOTED_TO_VLT"
    ]
    assert len(promotion_events) == 3, f"expected 3 promotion events, got {len(promotion_events)}"

    required_spatial = {"object_class", "centroid", "bbox", "support_count",
                        "first_seen_ms", "last_seen_ms"}
    forbidden_fields = {"mean_confidence"}

    for ev in promotion_events:
        payload = ev.get("payload", {})
        missing = required_spatial - set(payload.keys())
        assert not missing, f"promotion event missing spatial fields: {missing}\npayload={payload}"

        present_forbidden = forbidden_fields & set(payload.keys())
        assert not present_forbidden, (
            f"promotion event contains forbidden field(s): {present_forbidden}"
        )

    # Confirm object classes match expected objects
    emitted_classes = {ev["payload"]["object_class"] for ev in promotion_events}
    assert emitted_classes == {"vehicle", "person", "bicycle"}


# ---------------------------------------------------------------------------
# 2. Multi-VLT chain reconstructs spatial fields
# ---------------------------------------------------------------------------

def test_multi_vlt_chain_reconstructs_spatial_fields(tmp_path):
    """
    Reconstructing a 3-VLT ER-1B chain produces source_objects with spatial fields
    (object_class, centroid_x, centroid_y, bbox_x, bbox_y, bbox_w, bbox_h, support_count).
    """
    from ph6_l2_expand.topology_reconstruct import replay_tok_chain, vlt_observation_to_source

    audit_path = _build_er1b_tok_chain(tmp_path)
    valid, observations, errors = replay_tok_chain(audit_path)

    assert valid, f"replay failed: {errors}"
    assert len(observations) == 3, f"expected 3 VLT observations, got {len(observations)}"

    expected_spatial_keys = {
        "object_class", "centroid_x", "centroid_y",
        "bbox_x", "bbox_y", "bbox_w", "bbox_h", "support_count",
    }

    for obs in observations:
        _vlt_id, source_obj = vlt_observation_to_source(obs)
        present_spatial = expected_spatial_keys & set(source_obj.keys())
        assert present_spatial == expected_spatial_keys, (
            f"source_object missing spatial keys: {expected_spatial_keys - present_spatial}\n"
            f"source_object keys: {set(source_obj.keys())}"
        )
        # Temporal fields must NOT be in source_object
        assert "first_seen_ms" not in source_obj
        assert "last_seen_ms" not in source_obj
        # mean_confidence must NOT be present
        assert "mean_confidence" not in source_obj


# ---------------------------------------------------------------------------
# 3. Topology hash stable across invocations
# ---------------------------------------------------------------------------

def test_er1b_topology_hash_stable_across_invocations(tmp_path):
    """Reconstructing the same ER-1B chain twice yields identical topology hashes."""
    from ph6_l2_expand.topology_reconstruct import reconstruct_topology

    audit_path = _build_er1b_tok_chain(tmp_path)

    _map1, hash1, _meta1 = reconstruct_topology(audit_path)
    _map2, hash2, _meta2 = reconstruct_topology(audit_path)

    assert hash1 == hash2, (
        f"ER-1B topology hash differed across invocations:\n  run1={hash1}\n  run2={hash2}"
    )
    assert len(hash1) == 64, "expected 64-char hex BLAKE2b-256 hash"
    assert _meta1["observation_count"] == 3


# ---------------------------------------------------------------------------
# 4. ER-1B source_objects richer than ER-1A
# ---------------------------------------------------------------------------

def test_er1b_spatial_source_objects_richer_than_er1a(tmp_path):
    """
    ER-1B chains (with spatial fields) produce source_objects with more fields
    than legacy chains (without spatial fields).
    """
    from ph6_l2_expand.topology_reconstruct import replay_tok_chain, vlt_observation_to_source

    er1b_path = _build_er1b_tok_chain(tmp_path / "er1b")
    legacy_path = _build_legacy_chain(tmp_path / "legacy")

    _, er1b_obs, _ = replay_tok_chain(er1b_path)
    _, legacy_obs, _ = replay_tok_chain(legacy_path)

    assert er1b_obs, "ER-1B chain must have observations"
    assert legacy_obs, "legacy chain must have observations"

    _, er1b_src = vlt_observation_to_source(er1b_obs[0])
    _, legacy_src = vlt_observation_to_source(legacy_obs[0])

    assert len(er1b_src) > len(legacy_src), (
        f"ER-1B source_object ({len(er1b_src)} fields) should be richer than "
        f"legacy ({len(legacy_src)} fields)"
    )
    assert len(er1b_src) >= 5, f"ER-1B source_object expected >=5 fields, got {len(er1b_src)}"
    assert len(legacy_src) == 2, f"legacy source_object expected 2 fields, got {len(legacy_src)}"


# ---------------------------------------------------------------------------
# 5. Legacy chain degrades gracefully
# ---------------------------------------------------------------------------

def test_er1b_legacy_chain_degrades_gracefully(tmp_path):
    """
    Events without spatial fields produce a 2-field source_object (cram_ref_hash,
    vlt_prefix) without raising exceptions.
    """
    from ph6_l2_expand.topology_reconstruct import (
        replay_tok_chain, vlt_observation_to_source, reconstruct_topology,
    )

    audit_path = _build_legacy_chain(tmp_path)
    valid, observations, errors = replay_tok_chain(audit_path)

    assert valid, f"legacy chain replay failed: {errors}"
    assert len(observations) == 1

    _vlt_id, source_obj = vlt_observation_to_source(observations[0])
    assert set(source_obj.keys()) == {"cram_ref_hash", "vlt_prefix"}, (
        f"legacy source_object should have exactly 2 fields, got: {set(source_obj.keys())}"
    )

    # Full reconstruction must not raise
    token_map, topo_hash, metadata = reconstruct_topology(audit_path)
    assert token_map
    assert len(topo_hash) == 64
    assert metadata["authority_level"] == "ZERO"


# ---------------------------------------------------------------------------
# 6. Distinct object classes produce distinct RT token sets
# ---------------------------------------------------------------------------

def test_er1b_distinct_object_classes_produce_distinct_rt_tokens(tmp_path):
    """
    Distinct VLTs (vehicle, person, bicycle) produce disjoint RT token sets.
    Each VLT's RT tokens carry the object_class field, confirming spatial info
    enters the topology node structure.
    """
    from ph6_l2_expand.topology_reconstruct import replay_tok_chain, vlt_observation_to_source
    from ph6_l2_expand.token_mapper import build_reference_tokens

    audit_path = _build_er1b_tok_chain(tmp_path)
    _, observations, _ = replay_tok_chain(audit_path)
    assert len(observations) == 3

    rt_sets: List[set] = []
    for obs in observations:
        vlt_id, source_obj = vlt_observation_to_source(obs)
        assert "object_class" in source_obj, "spatial VLT must have object_class in source_obj"
        rts = build_reference_tokens(vlt_id, source_obj)
        rt_sets.append(set(rts.keys()))

    # All 3 RT sets must be pairwise disjoint
    for i in range(len(rt_sets)):
        for j in range(i + 1, len(rt_sets)):
            overlap = rt_sets[i] & rt_sets[j]
            assert not overlap, (
                f"RT token sets for observations {i} and {j} overlap: {overlap}"
            )

    # Each set must include an RT for the object_class field
    for i, obs in enumerate(observations):
        _, source_obj = vlt_observation_to_source(obs)
        assert "object_class" in source_obj
        field_names = {
            tok.advisory_payload.get("field") for tok in
            build_reference_tokens(obs.get("vlt_token_id", ""), source_obj).values()
        }
        assert "object_class" in field_names, (
            f"observation {i}: no RT with field='object_class' found"
        )


# ---------------------------------------------------------------------------
# 7. Malformed spatial metadata rejected / deterministically degraded
# ---------------------------------------------------------------------------

def test_er1b_malformed_spatial_metadata_rejected_or_deterministically_degraded(tmp_path):
    """
    Events with malformed spatial metadata (empty object_class, 1-element centroid,
    negative bbox dimensions, negative support_count, inverted temporal order) do not
    raise exceptions. Invalid fields are excluded; valid base fields remain.
    """
    from ph6_l2_expand.topology_reconstruct import (
        replay_tok_chain, vlt_observation_to_source, reconstruct_topology,
        _validate_er1b_spatial,
    )

    audit_path = _build_malformed_spatial_chain(tmp_path)
    valid, observations, _errors = replay_tok_chain(audit_path)

    assert valid, "malformed spatial chain must still have valid hash chain"
    assert len(observations) == 1

    obs = observations[0]
    spatial_fields, notes = _validate_er1b_spatial(obs)

    # All malformed fields must have been noted and excluded
    assert "object_class" not in spatial_fields, "empty object_class must be excluded"
    assert "centroid_x" not in spatial_fields, "1-element centroid must be excluded"
    assert "centroid_y" not in spatial_fields
    assert "bbox_x" not in spatial_fields, "negative-w bbox must be excluded"
    assert "support_count" not in spatial_fields, "negative support_count must be excluded"

    # Notes must record each rejection
    assert any("object_class" in n for n in notes), f"no note for object_class: {notes}"
    assert any("centroid" in n for n in notes), f"no note for centroid: {notes}"
    assert any("bbox" in n for n in notes), f"no note for bbox: {notes}"
    assert any("support_count" in n for n in notes), f"no note for support_count: {notes}"
    assert any("temporal" in n for n in notes), f"no note for temporal: {notes}"

    # Full reconstruction must not raise; produces minimal source_object
    _vlt_id, source_obj = vlt_observation_to_source(obs)
    assert set(source_obj.keys()) == {"cram_ref_hash", "vlt_prefix"}, (
        f"malformed event should produce 2-field source_object, got: {set(source_obj.keys())}"
    )

    token_map, topo_hash, metadata = reconstruct_topology(audit_path)
    assert token_map
    assert len(topo_hash) == 64


# ---------------------------------------------------------------------------
# 8. No CRAM writes occur during reconstruction
# ---------------------------------------------------------------------------

def test_no_cram_write(tmp_path):
    """Reconstruction from ER-1B chain writes nothing to CRAM-0, CRAM-A, or CRAM-R."""
    from ph6_l2_expand.topology_reconstruct import reconstruct_topology

    audit_path = _build_er1b_tok_chain(tmp_path)
    reconstruct_topology(audit_path)

    forbidden_segments = {"cram-0", "cram-a", "cram-r"}
    for created in tmp_path.rglob("*"):
        parts_lower = {p.lower() for p in created.parts}
        assert not (parts_lower & forbidden_segments), (
            f"reconstruction wrote to forbidden CRAM path: {created}"
        )


# ---------------------------------------------------------------------------
# 9. No Lane-1 imports from topology_reconstruct
# ---------------------------------------------------------------------------

def test_no_lane1_imports():
    """topology_reconstruct.py must not import from Lane-1 modules."""
    module_path = Path(__file__).resolve().parents[1] / "topology_reconstruct.py"
    assert module_path.exists()

    source = module_path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    lane1_prefixes = ("ph6.cram_pu", "ph6_cert", "ph6.audit", "cram_pu")
    violations: List[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                for prefix in lane1_prefixes:
                    if alias.name.startswith(prefix):
                        violations.append(f"import {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for prefix in lane1_prefixes:
                if module.startswith(prefix):
                    violations.append(f"from {module} import ...")

    assert not violations, (
        "topology_reconstruct.py contains Lane-1 imports:\n  " + "\n  ".join(violations)
    )
