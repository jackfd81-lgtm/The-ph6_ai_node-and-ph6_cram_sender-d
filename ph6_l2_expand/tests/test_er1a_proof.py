"""
ER-1A Proof Harness

Proves whether PH6 can reconstruct advisory topology continuity from
preserved advisory evidence alone, with no snapshot dependency.

Lane: 2  Authority: ZERO

Tests:
  1. test_evidence_chain_reconstructs_token_store
  2. test_topology_reconstruction_is_deterministic_across_invocations
  3. test_topology_hash_matches_after_cache_deletion
  4. test_corrupt_advisory_chain_rejected
  5. test_legacy_soso_lite_records_not_mixed
  6. test_no_cram_write_from_reconstruction
  7. test_no_pass_drop_verdict_write_from_reconstruction
  8. test_no_lane1_imports_from_topology_reconstruction
"""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path
from typing import List

import pytest

# ---------------------------------------------------------------------------
# Path setup (same pattern as conftest.py)
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

FIXED_T0 = 1_000_000_000_000  # ms — fixed for determinism
CRAM_REF_A = "cram_er1a_proof_abc123"
CRAM_REF_B = "cram_er1a_proof_def456"


def _build_tok_chain(base_dir: Path, cram_ref: str = CRAM_REF_A) -> Path:
    """
    Build a minimal valid tok advisory chain in base_dir/tokens/.
    Uses deterministic timestamps so the same inputs produce the same chain.
    Returns path to tok_advisory_audit.jsonl.
    """
    from ph6.tok.lifecycle import (
        VDT,
        AdvisoryAudit,
        TokenStore,
        DEFAULT_TOK_CONFIG,
    )

    tokens_dir = base_dir / "tokens"

    store = TokenStore(str(tokens_dir))

    for i in range(5):
        vdt = VDT(
            token_id=f"vdt_er1a_{cram_ref[-6:]}_{i:03d}",
            cram_ref_hash=cram_ref,
            timestamp_ms=FIXED_T0 + i * 100,
            last_updated_ms=FIXED_T0 + i * 100,
            object_class="vehicle",
            bbox=[10.0 + i, 20.0, 100.0, 60.0],
            confidence=0.75,
            support_count=1,
        )
        store.add_vdt(vdt)

    vlt = store.promote_to_vlt(
        [f"vdt_er1a_{cram_ref[-6:]}_{i:03d}" for i in range(5)],
        DEFAULT_TOK_CONFIG,
        event_time_ms=FIXED_T0 + 600,
    )
    assert vlt is not None, "promotion should succeed in test fixture"

    return tokens_dir / "tok_advisory_audit.jsonl"


# ---------------------------------------------------------------------------
# 1. Evidence chain reconstructs token store
# ---------------------------------------------------------------------------

def test_evidence_chain_reconstructs_token_store(tmp_path):
    """Chain can be validated and VLT observations extracted from it."""
    from ph6.tok.reconstruct import validate_chain_integrity, count_events_by_type
    from ph6_l2_expand.topology_reconstruct import replay_tok_chain, reconstruct_topology

    audit_path = _build_tok_chain(tmp_path)

    chain_valid, event_count, error = validate_chain_integrity(audit_path)
    assert chain_valid, f"chain integrity failed: {error}"
    assert event_count > 0

    by_type = count_events_by_type(audit_path)
    assert by_type.get("VDT_PROMOTED_TO_VLT", 0) >= 1

    valid, observations, errors = replay_tok_chain(audit_path)
    assert valid, f"replay failed: {errors}"
    assert len(observations) >= 1, "at least one VLT observation expected"

    token_map, topo_hash, metadata = reconstruct_topology(audit_path)
    assert len(token_map) > 0, "token_map must be non-empty after reconstruction"
    assert topo_hash and len(topo_hash) == 64, "expected 64-char hex BLAKE2b-256 hash"
    assert metadata["observation_count"] >= 1
    assert metadata["authority_level"] == "ZERO"
    assert metadata["advisory_only"] is True


# ---------------------------------------------------------------------------
# 2. Deterministic across invocations (two reads of the same chain)
# ---------------------------------------------------------------------------

def test_topology_reconstruction_is_deterministic_across_invocations(tmp_path):
    """Reading the same chain twice produces an identical topology hash."""
    from ph6_l2_expand.topology_reconstruct import reconstruct_topology

    audit_path = _build_tok_chain(tmp_path)

    _map1, hash1, _meta1 = reconstruct_topology(audit_path)
    _map2, hash2, _meta2 = reconstruct_topology(audit_path)

    assert hash1 == hash2, (
        f"topology hash differed across invocations:\n  run1={hash1}\n  run2={hash2}"
    )


# ---------------------------------------------------------------------------
# 3. Topology hash stable after cache deletion
# ---------------------------------------------------------------------------

def test_topology_hash_matches_after_cache_deletion(tmp_path):
    """Deleting the snapshot cache does not change the reconstructed topology hash."""
    from ph6_l2_expand.topology_reconstruct import reconstruct_topology

    audit_path = _build_tok_chain(tmp_path)
    tokens_dir = audit_path.parent

    _map1, hash1, _ = reconstruct_topology(audit_path)

    # Delete any cache-like files the tok system may have written.
    cache_candidates = [
        tokens_dir / "live_tokens.json",
        tokens_dir / "receipts" / "tok_rebuild_receipt.json",
    ]
    for candidate in cache_candidates:
        if candidate.exists():
            candidate.unlink()

    _map2, hash2, _ = reconstruct_topology(audit_path)

    assert hash1 == hash2, (
        f"topology hash changed after cache deletion:\n  before={hash1}\n  after={hash2}"
    )


# ---------------------------------------------------------------------------
# 4. Corrupt advisory chain is rejected
# ---------------------------------------------------------------------------

def test_corrupt_advisory_chain_rejected(tmp_path):
    """A byte-corrupted audit chain fails integrity checks and raises ValueError."""
    from ph6.tok.reconstruct import validate_chain_integrity
    from ph6_l2_expand.topology_reconstruct import reconstruct_topology

    audit_path = _build_tok_chain(tmp_path)

    # Confirm it passes before corruption.
    chain_valid_before, _, _ = validate_chain_integrity(audit_path)
    assert chain_valid_before

    # Corrupt a byte near the middle of the file.
    raw = bytearray(audit_path.read_bytes())
    mid = len(raw) // 2
    raw[mid] = (raw[mid] + 1) % 256
    audit_path.write_bytes(bytes(raw))

    chain_valid_after, _, chain_error = validate_chain_integrity(audit_path)
    assert not chain_valid_after, "corrupted chain should fail integrity check"

    with pytest.raises(ValueError, match="chain replay failed"):
        reconstruct_topology(audit_path)


# ---------------------------------------------------------------------------
# 5. Legacy soso_lite.v0.1 records are not mixed into topology
# ---------------------------------------------------------------------------

def test_legacy_soso_lite_records_not_mixed():
    """Events with schema ph6.soso_lite.v0.1 are rejected and never enter VLT set."""
    from ph6_l2_expand.topology_reconstruct import (
        LEGACY_SOSO_LITE_SCHEMA,
        VLT_PROMOTION_EVENT,
        _extract_vlt_observations_from_events,
    )

    legacy_event = {
        "schema": LEGACY_SOSO_LITE_SCHEMA,
        "event_type": VLT_PROMOTION_EVENT,
        "payload": {"vlt_token_id": "vlt_legacy_poisoned", "cram_ref_hash": "abc"},
    }
    real_event = {
        "schema": "ph6.tok.advisory_event.v1",
        "event_type": VLT_PROMOTION_EVENT,
        "payload": {"vlt_token_id": "vlt_real_valid", "cram_ref_hash": "def"},
    }

    events = [legacy_event, real_event]
    active_vlts, errors = _extract_vlt_observations_from_events(events)

    assert "vlt_legacy_poisoned" not in active_vlts, (
        "legacy soso_lite.v0.1 VLT must not enter topology"
    )
    assert "vlt_real_valid" in active_vlts, (
        "valid event VLT must be present"
    )
    assert any(LEGACY_SOSO_LITE_SCHEMA in e for e in errors), (
        "legacy event must be recorded as an error"
    )


# ---------------------------------------------------------------------------
# 6. No CRAM writes occur during reconstruction
# ---------------------------------------------------------------------------

def test_no_cram_write_from_reconstruction(tmp_path):
    """Reconstruction writes nothing to CRAM-0, CRAM-A, or CRAM-R paths."""
    from ph6_l2_expand.topology_reconstruct import reconstruct_topology

    audit_path = _build_tok_chain(tmp_path)
    reconstruct_topology(audit_path)

    # Walk every file created under tmp_path.
    forbidden_segments = {"cram-0", "cram-a", "cram-r"}
    for created in tmp_path.rglob("*"):
        parts_lower = {p.lower() for p in created.parts}
        overlap = parts_lower & forbidden_segments
        assert not overlap, (
            f"reconstruction wrote to forbidden CRAM path: {created}"
        )


# ---------------------------------------------------------------------------
# 7. No PASS/DROP verdict fields in reconstruction output
# ---------------------------------------------------------------------------

def test_no_pass_drop_verdict_write_from_reconstruction(tmp_path):
    """Reconstruction metadata and token map contain no PASS/DROP/verdict fields."""
    from ph6_l2_expand.topology_reconstruct import reconstruct_topology
    from ph6_l2_expand.topology_mapper import serialize_token_map

    audit_path = _build_tok_chain(tmp_path)
    token_map, topo_hash, metadata = reconstruct_topology(audit_path)

    forbidden_values = {"PASS", "DROP", "ACCEPT", "REJECT", "verdict"}
    forbidden_keys = {"verdict", "pass", "drop", "accept", "reject", "threshold"}

    def _check_dict(d: dict, label: str) -> List[str]:
        violations = []
        for k, v in d.items():
            if str(k).lower() in forbidden_keys:
                violations.append(f"{label}: forbidden key '{k}'")
            if isinstance(v, str) and v.upper() in forbidden_values:
                violations.append(f"{label}: forbidden value '{v}' at key '{k}'")
        return violations

    meta_violations = _check_dict(metadata, "metadata")
    assert not meta_violations, f"metadata violations: {meta_violations}"

    serialized = serialize_token_map(token_map)
    token_violations: List[str] = []
    for token_id, token_dict in serialized.items():
        token_violations.extend(_check_dict(token_dict, f"token[{token_id}]"))
        payload = token_dict.get("advisory_payload", {})
        token_violations.extend(_check_dict(payload, f"token[{token_id}].advisory_payload"))

    assert not token_violations, f"token violations: {token_violations}"

    # Topology hash must not be a known verdict token.
    assert topo_hash not in forbidden_values


# ---------------------------------------------------------------------------
# 8. No Lane-1 imports from topology_reconstruct
# ---------------------------------------------------------------------------

def test_no_lane1_imports_from_topology_reconstruction():
    """topology_reconstruct.py must not import from Lane-1 modules."""
    module_path = Path(__file__).resolve().parents[1] / "topology_reconstruct.py"
    assert module_path.exists(), f"module not found: {module_path}"

    source = module_path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    lane1_prefixes = (
        "ph6.cram_pu",
        "ph6_cert",
        "ph6.audit",
        "cram_pu",
    )

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
        f"topology_reconstruct.py contains Lane-1 imports:\n  " + "\n  ".join(violations)
    )
