"""
ER-1D-LITE Proof Harness — Isolated Live-Style Replay Proof

Proves that advisory evidence generated through the real token lifecycle path
(TokenStore + add_vdt + promote_to_vlt) can be preserved in an isolated
temporary advisory audit chain, reconstructed into topology across separate
invocations, and made to reject corruption — without writing Lane-1, CRAM,
PASS/DROP, verdicts, snapshot cache, or live /var/ph6/mram-s.

Lane: 2  Authority: ZERO
Prerequisites: ER-1A (test_er1a_proof.py), ER-1B (test_er1b_proof.py)
ER-1C: deferred
No snapshot cache introduced.
No live MRAM-S mutation.

Tests:
  1. test_er1d_lite_chain_generated_via_real_lifecycle
  2. test_er1d_lite_first_reconstruction
  3. test_er1d_lite_dual_reconstruction_deterministic
  4. test_er1d_lite_reconstruction_after_cache_deletion
  5. test_er1d_lite_corrupt_chain_rejected
  6. test_er1d_lite_no_mrams_mutation
  7. test_er1d_lite_no_cram_verdict_writes
  8. test_er1d_lite_no_lane1_imports
"""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

FIXED_T0 = 3_000_000_000_000  # ms — distinct from ER-1A (1T) and ER-1B (2T)

_ER1D_OBJECTS = [
    # (object_class, cram_ref_hash, base_bbox)
    ("vehicle", "cram_er1d_ref_vehicle_aaa", [10.0,  20.0, 100.0, 60.0]),
    ("person",  "cram_er1d_ref_person__bbb", [180.0, 100.0, 40.0,  80.0]),
    ("bicycle", "cram_er1d_ref_bicycle_ccc", [320.0, 160.0, 60.0,  80.0]),
]

REQUIRED_SPATIAL_IN_PAYLOAD = {
    "object_class", "centroid", "bbox", "support_count",
    "first_seen_ms", "last_seen_ms",
}

REQUIRED_SPATIAL_IN_SOURCE = {
    "object_class", "centroid_x", "centroid_y",
    "bbox_x", "bbox_y", "bbox_w", "bbox_h", "support_count",
}

FORBIDDEN_IN_PAYLOAD = {"mean_confidence"}
FORBIDDEN_IN_SOURCE = {"mean_confidence", "first_seen_ms", "last_seen_ms"}

LANE1_PREFIXES = ("ph6.cram_pu", "ph6_cert", "ph6.audit", "cram_pu")


# ---------------------------------------------------------------------------
# Chain builder — real lifecycle path
# ---------------------------------------------------------------------------

def _build_er1d_tok_chain(base_dir: Path) -> Path:
    """
    Generate advisory evidence via the real token lifecycle path.

    Creates 3 VLT promotions (vehicle, person, bicycle) each with 5 VDTs.
    All timestamps are fixed for determinism.
    TokenStore writes to base_dir/tokens/ (never to /var/ph6/mram-s).
    Returns path to tok_advisory_audit.jsonl.
    """
    from ph6.tok.lifecycle import VDT, TokenStore, DEFAULT_TOK_CONFIG

    tokens_dir = base_dir / "tokens"
    store = TokenStore(str(tokens_dir))

    for obj_class, cram_ref, base_bbox in _ER1D_OBJECTS:
        vdt_ids: List[str] = []
        for i in range(5):
            t = FIXED_T0 + i * 100
            bbox = [base_bbox[0] + i * 0.2, base_bbox[1], base_bbox[2], base_bbox[3]]
            vdt = VDT(
                token_id=f"vdt_er1d_{obj_class}_{i:03d}",
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
        assert vlt is not None, f"VLT promotion failed for object_class={obj_class!r}"

    return tokens_dir / "tok_advisory_audit.jsonl"


def _reconstruct_fresh(
    audit_path: Path,
) -> Tuple[Dict[str, Any], str, Dict[str, Any]]:
    """
    Independent reconstruction invocation — no shared state with caller.

    Each call reads the advisory audit chain from disk and reconstructs
    topology from scratch. Equivalent to a fresh session load.
    """
    from ph6_l2_expand.topology_reconstruct import reconstruct_topology
    return reconstruct_topology(audit_path)


# ---------------------------------------------------------------------------
# 1. Chain generated via real lifecycle
# ---------------------------------------------------------------------------

def test_er1d_lite_chain_generated_via_real_lifecycle(tmp_path):
    """
    The real token lifecycle path (TokenStore + add_vdt + promote_to_vlt)
    produces a valid advisory audit chain with:
    - 3 VDT_PROMOTED_TO_VLT events (vehicle, person, bicycle)
    - Required ER-1B spatial fields in each promotion payload
    - No mean_confidence in any promotion payload
    """
    audit_path = _build_er1d_tok_chain(tmp_path)
    assert audit_path.exists(), "lifecycle did not create audit chain"

    from ph6.tok.reconstruct import validate_chain_integrity, count_events_by_type

    chain_valid, event_count, error = validate_chain_integrity(audit_path)
    assert chain_valid, f"chain integrity failed: {error}"
    assert event_count > 0, "audit chain is empty"

    by_type = count_events_by_type(audit_path)
    assert by_type.get("VDT_PROMOTED_TO_VLT", 0) == 3, (
        f"expected 3 promotions, got {by_type.get('VDT_PROMOTED_TO_VLT', 0)}"
    )

    with open(audit_path, "rb") as fh:
        events = [json.loads(line) for line in fh if line.strip()]

    promotion_events = [e for e in events if e.get("event_type") == "VDT_PROMOTED_TO_VLT"]
    assert len(promotion_events) == 3

    for ev in promotion_events:
        payload = ev["payload"]
        missing = REQUIRED_SPATIAL_IN_PAYLOAD - set(payload.keys())
        assert not missing, (
            f"promotion payload missing spatial fields: {missing}\n"
            f"object_class={payload.get('object_class')!r}"
        )
        present_forbidden = FORBIDDEN_IN_PAYLOAD & set(payload.keys())
        assert not present_forbidden, (
            f"promotion payload contains forbidden field(s): {present_forbidden}"
        )

    emitted_classes = {ev["payload"]["object_class"] for ev in promotion_events}
    assert emitted_classes == {"vehicle", "person", "bicycle"}


# ---------------------------------------------------------------------------
# 2. First reconstruction
# ---------------------------------------------------------------------------

def test_er1d_lite_first_reconstruction(tmp_path):
    """
    First reconstruction from isolated advisory evidence:
    - Valid topology hash (64-char BLAKE2b-256 hex)
    - 3 VLT observations
    - Each source_object contains full ER-1B spatial fields
    - No mean_confidence, first_seen_ms, or last_seen_ms in source_objects
    - authority_level=ZERO, advisory_only=True
    """
    from ph6_l2_expand.topology_reconstruct import replay_tok_chain, vlt_observation_to_source

    audit_path = _build_er1d_tok_chain(tmp_path)

    chain_valid, observations, errors = replay_tok_chain(audit_path)
    assert chain_valid, f"replay failed: {errors}"
    assert len(observations) == 3, f"expected 3 VLT observations, got {len(observations)}"

    for obs in observations:
        _, src = vlt_observation_to_source(obs)
        present = REQUIRED_SPATIAL_IN_SOURCE & set(src.keys())
        assert present == REQUIRED_SPATIAL_IN_SOURCE, (
            f"source_object missing spatial keys: {REQUIRED_SPATIAL_IN_SOURCE - present}\n"
            f"source_object keys: {set(src.keys())}"
        )
        forbidden_present = FORBIDDEN_IN_SOURCE & set(src.keys())
        assert not forbidden_present, (
            f"source_object contains forbidden field(s): {forbidden_present}"
        )

    token_map, topo_hash, metadata = _reconstruct_fresh(audit_path)
    assert len(topo_hash) == 64, "expected 64-char hex BLAKE2b-256 topology hash"
    assert len(token_map) > 0, "token_map must be non-empty after reconstruction"
    assert metadata["observation_count"] == 3
    assert metadata["authority_level"] == "ZERO"
    assert metadata["advisory_only"] is True


# ---------------------------------------------------------------------------
# 3. Dual reconstruction — deterministic across separate invocations
# ---------------------------------------------------------------------------

def test_er1d_lite_dual_reconstruction_deterministic(tmp_path):
    """
    Reconstructing from the same isolated advisory chain in two separate
    function call paths produces identical:
    - topology hash
    - source object count
    - object classes
    - spatial field sets
    - stable topology result (token map size)
    """
    from ph6_l2_expand.topology_reconstruct import replay_tok_chain, vlt_observation_to_source

    audit_path = _build_er1d_tok_chain(tmp_path)

    # First reconstruction path
    map1, hash1, meta1 = _reconstruct_fresh(audit_path)
    _, obs1, _ = replay_tok_chain(audit_path)
    classes1 = frozenset(o.get("object_class") for o in obs1)
    src1 = sorted(str(sorted(vlt_observation_to_source(o)[1].items())) for o in obs1)

    # Second reconstruction path — independent call, no shared state
    map2, hash2, meta2 = _reconstruct_fresh(audit_path)
    _, obs2, _ = replay_tok_chain(audit_path)
    classes2 = frozenset(o.get("object_class") for o in obs2)
    src2 = sorted(str(sorted(vlt_observation_to_source(o)[1].items())) for o in obs2)

    assert hash1 == hash2, (
        f"topology hash diverged across invocations:\n  run1={hash1}\n  run2={hash2}"
    )
    assert meta1["observation_count"] == meta2["observation_count"], (
        "observation count differed"
    )
    assert len(map1) == len(map2), "token map size differed"
    assert classes1 == classes2, f"object classes differed: {classes1} vs {classes2}"
    assert src1 == src2, "source objects differed across invocations"


# ---------------------------------------------------------------------------
# 4. Reconstruction after cache deletion
# ---------------------------------------------------------------------------

def test_er1d_lite_reconstruction_after_cache_deletion(tmp_path):
    """
    Deleting derived output files (live materialization, receipts) does not
    change the reconstructed topology hash. Reconstruction succeeds from
    the advisory evidence chain alone.
    """
    audit_path = _build_er1d_tok_chain(tmp_path)
    tokens_dir = audit_path.parent

    _, hash_before, _ = _reconstruct_fresh(audit_path)

    cache_candidates = [
        tokens_dir / "live_tokens.json",
        tokens_dir / "receipts" / "tok_rebuild_receipt.json",
    ]
    for candidate in cache_candidates:
        if candidate.exists():
            candidate.unlink()

    _, hash_after, _ = _reconstruct_fresh(audit_path)

    assert hash_before == hash_after, (
        f"topology hash changed after cache deletion:\n"
        f"  before={hash_before}\n  after={hash_after}"
    )


# ---------------------------------------------------------------------------
# 5. Corrupt chain is rejected
# ---------------------------------------------------------------------------

def test_er1d_lite_corrupt_chain_rejected(tmp_path):
    """
    Byte-corrupting the advisory audit chain causes chain validation to fail
    and reconstruct_topology to raise ValueError.
    """
    from ph6.tok.reconstruct import validate_chain_integrity

    audit_path = _build_er1d_tok_chain(tmp_path)

    valid_before, _, _ = validate_chain_integrity(audit_path)
    assert valid_before, "chain must be valid before corruption"

    raw = bytearray(audit_path.read_bytes())
    mid = len(raw) // 2
    raw[mid] = (raw[mid] + 1) % 256
    audit_path.write_bytes(bytes(raw))

    valid_after, _, _ = validate_chain_integrity(audit_path)
    assert not valid_after, "corrupted chain must fail integrity check"

    with pytest.raises(ValueError, match="chain replay failed"):
        _reconstruct_fresh(audit_path)


# ---------------------------------------------------------------------------
# 6. No /var/ph6/mram-s mutation
# ---------------------------------------------------------------------------

def test_er1d_lite_no_mrams_mutation(tmp_path):
    """
    Running the full ER-1D-LITE lifecycle (build chain + reconstruct) does
    not create or mutate /var/ph6/mram-s. All writes stay under tmp_path.
    """
    mrams = Path("/var/ph6/mram-s")
    existed_before = mrams.exists()
    mtime_before = mrams.stat().st_mtime if existed_before else None

    audit_path = _build_er1d_tok_chain(tmp_path)
    _reconstruct_fresh(audit_path)

    if not existed_before:
        assert not mrams.exists(), "/var/ph6/mram-s must not be created by ER-1D-LITE"
    else:
        mtime_after = mrams.stat().st_mtime
        assert mtime_before == mtime_after, (
            "/var/ph6/mram-s mtime changed — ER-1D-LITE must not mutate live MRAM-S"
        )


# ---------------------------------------------------------------------------
# 7. No CRAM / PASS / DROP / verdict writes
# ---------------------------------------------------------------------------

def test_er1d_lite_no_cram_verdict_writes(tmp_path):
    """
    No files are written to CRAM-0, CRAM-A, CRAM-R, PASS, DROP, or verdict
    paths during ER-1D-LITE lifecycle and reconstruction.
    No snapshot cache files are created.
    """
    audit_path = _build_er1d_tok_chain(tmp_path)
    _reconstruct_fresh(audit_path)

    forbidden_path_segments = {"cram-0", "cram-a", "cram-r"}
    forbidden_file_stems = {"pass", "drop", "verdict"}
    forbidden_name_substrings = {"snapshot", "cache"}

    for created in tmp_path.rglob("*"):
        parts_lower = {p.lower() for p in created.parts}
        overlap = parts_lower & forbidden_path_segments
        assert not overlap, f"ER-1D-LITE wrote to forbidden CRAM path: {created}"

        if created.is_file():
            stem = created.stem.lower()
            name = created.name.lower()
            assert stem not in forbidden_file_stems, (
                f"ER-1D-LITE created forbidden verdict file: {created}"
            )
            for sub in forbidden_name_substrings:
                assert sub not in name, (
                    f"ER-1D-LITE created forbidden file (contains '{sub}'): {created}"
                )


# ---------------------------------------------------------------------------
# 8. No Lane-1 imports
# ---------------------------------------------------------------------------

def test_er1d_lite_no_lane1_imports():
    """
    This test file and topology_reconstruct.py must not import from
    Lane-1 modules (ph6.cram_pu, ph6_cert, ph6.audit, cram_pu).
    """
    files_to_check = [
        Path(__file__),
        Path(__file__).resolve().parents[1] / "topology_reconstruct.py",
    ]

    violations: List[str] = []
    for path in files_to_check:
        assert path.exists(), f"expected file not found: {path}"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    for prefix in LANE1_PREFIXES:
                        if alias.name.startswith(prefix):
                            violations.append(f"{path.name}: import {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for prefix in LANE1_PREFIXES:
                    if module.startswith(prefix):
                        violations.append(f"{path.name}: from {module} import ...")

    assert not violations, (
        "Lane-1 imports found:\n  " + "\n  ".join(violations)
    )
