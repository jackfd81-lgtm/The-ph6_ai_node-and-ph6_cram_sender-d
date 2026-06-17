"""
ER-1E Real Multi-VLT Artifact Campaign Proof

Verifies the committed ER-1E artifact campaign:
  PH6_SOURCE/ARTIFACTS/ER1E_REAL_MULTIVLT_20260617/

Note on topology hash: token_types.make_rt/make_vdt/make_vlt use utc_now_iso()
for created_at (1-second wall-clock granularity). Topology hashes are stable
within a Python session (all token creations in a test complete within 1s),
but differ across sessions. Tests assert within-session hash equality; they do
NOT compare against the manifest's generation-time topology_hash value.

Lane: 2  Authority: ZERO
Prerequisites: ER-1A, ER-1B, ER-1D-LITE

Tests:
   1. test_er1e_artifacts_exist
   2. test_er1e_manifest_sha256_matches_artifacts
   3. test_er1e_audit_chain_valid
   4. test_er1e_reconstruction_deterministic
   5. test_er1e_reconstruction_from_isolated_audit_copy
   6. test_er1e_all_required_spatial_fields_survive_replay
   7. test_er1e_multi_cycle_temporal_fields_survive_replay
   8. test_er1e_corrupt_chain_rejected
   9. test_er1e_no_mrams_mutation
  10. test_er1e_no_cram_verdict_writes
  11. test_er1e_no_snapshot_cache
  12. test_er1e_no_lane1_imports
"""

from __future__ import annotations

import ast
import hashlib
import json
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_WORKTREE_ROOT = Path(__file__).resolve().parents[2]
_ARTIFACT_DIR = _WORKTREE_ROOT / "PH6_SOURCE" / "ARTIFACTS" / "ER1E_REAL_MULTIVLT_20260617"

EXPECTED_OBJECT_CLASSES = frozenset(["bicycle", "doorway", "person", "sign", "vehicle"])
EXPECTED_NUM_CYCLES = 3
EXPECTED_NUM_OBJECTS = 5
EXPECTED_VLT_COUNT = 15  # 5 objects × 3 cycles
REQUIRED_SPATIAL_IN_PAYLOAD = {
    "object_class", "centroid", "bbox", "support_count",
    "first_seen_ms", "last_seen_ms",
}
LANE1_PREFIXES = ("ph6.cram_pu", "ph6_cert", "ph6.audit", "cram_pu")


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_manifest() -> Dict[str, Any]:
    return json.loads((_ARTIFACT_DIR / "manifest.json").read_bytes())


# ---------------------------------------------------------------------------
# 1. Artifacts exist
# ---------------------------------------------------------------------------

def test_er1e_artifacts_exist():
    """All 4 committed artifact files must exist at the expected path."""
    assert _ARTIFACT_DIR.is_dir(), f"artifact dir not found: {_ARTIFACT_DIR}"
    for name in (
        "source_observations.jsonl",
        "tok_advisory_audit.jsonl",
        "reconstruction_report.json",
        "manifest.json",
    ):
        p = _ARTIFACT_DIR / name
        assert p.exists(), f"artifact not found: {p}"
        assert p.stat().st_size > 0, f"artifact is empty: {p}"


# ---------------------------------------------------------------------------
# 2. Manifest sha256 hashes match artifact file contents
# ---------------------------------------------------------------------------

def test_er1e_manifest_sha256_matches_artifacts():
    """
    sha256 of each artifact file must match the value stored in manifest.json.
    """
    manifest = _load_manifest()
    sha256s = manifest["file_sha256"]

    for fname, expected_sha in sha256s.items():
        path = _ARTIFACT_DIR / fname
        assert path.exists(), f"artifact listed in manifest not found: {path}"
        actual = _sha256_file(path)
        assert actual == expected_sha, (
            f"sha256 mismatch for {fname}:\n"
            f"  manifest: {expected_sha}\n"
            f"  actual:   {actual}"
        )

    # Manifest must record the required artifact files
    required_keys = {
        "source_observations.jsonl",
        "tok_advisory_audit.jsonl",
        "reconstruction_report.json",
    }
    assert required_keys.issubset(set(sha256s.keys())), (
        f"manifest missing sha256 entries: {required_keys - set(sha256s.keys())}"
    )


# ---------------------------------------------------------------------------
# 3. Audit chain valid
# ---------------------------------------------------------------------------

def test_er1e_audit_chain_valid():
    """The committed tok_advisory_audit.jsonl must pass hash chain integrity."""
    from ph6.tok.reconstruct import validate_chain_integrity, count_events_by_type

    audit_path = _ARTIFACT_DIR / "tok_advisory_audit.jsonl"
    chain_valid, event_count, error = validate_chain_integrity(audit_path)
    assert chain_valid, f"chain integrity failed: {error}"
    assert event_count > 0

    by_type = count_events_by_type(audit_path)
    assert by_type.get("VDT_PROMOTED_TO_VLT", 0) == EXPECTED_VLT_COUNT, (
        f"expected {EXPECTED_VLT_COUNT} promotions, got {by_type.get('VDT_PROMOTED_TO_VLT', 0)}"
    )


# ---------------------------------------------------------------------------
# 4. Reconstruction deterministic within session
# ---------------------------------------------------------------------------

def test_er1e_reconstruction_deterministic():
    """
    Two calls to reconstruct_topology on the same artifact produce identical
    topology hashes, observation counts, and object classes (within-session).

    Note: the topology hash is NOT compared to manifest['topology_hash'] because
    token created_at timestamps have 1-second wall-clock granularity; the hash
    differs between Python sessions but is stable within one session.
    """
    from ph6_l2_expand.topology_reconstruct import reconstruct_topology, replay_tok_chain

    audit_path = _ARTIFACT_DIR / "tok_advisory_audit.jsonl"
    manifest = _load_manifest()

    map1, hash1, meta1 = reconstruct_topology(audit_path)
    map2, hash2, meta2 = reconstruct_topology(audit_path)

    assert hash1 == hash2, (
        f"topology hash diverged across calls:\n  call1={hash1}\n  call2={hash2}"
    )
    assert len(hash1) == 64, "expected 64-char BLAKE2b-256 hex topology hash"
    assert meta1["observation_count"] == meta2["observation_count"]
    assert meta1["observation_count"] == EXPECTED_VLT_COUNT
    assert meta1["token_count"] == meta2["token_count"]
    assert meta1["authority_level"] == "ZERO"
    assert meta1["advisory_only"] is True

    # Object classes from replay must match expected set
    _, observations, _ = replay_tok_chain(audit_path)
    found_classes = frozenset(o.get("object_class") for o in observations)
    assert found_classes == EXPECTED_OBJECT_CLASSES, (
        f"object classes mismatch: found={found_classes} expected={EXPECTED_OBJECT_CLASSES}"
    )

    # Manifest metadata fields must be internally consistent
    assert manifest["vlt_count"] == EXPECTED_VLT_COUNT
    assert manifest["observation_count"] == EXPECTED_VLT_COUNT
    assert frozenset(manifest["object_classes"]) == EXPECTED_OBJECT_CLASSES
    assert manifest["snapshot_cache"] is False
    assert manifest["live_mram_s_mutation"] is False
    assert manifest["lane1_imports"] is False


# ---------------------------------------------------------------------------
# 5. Reconstruction from isolated audit copy
# ---------------------------------------------------------------------------

def test_er1e_reconstruction_from_isolated_audit_copy(tmp_path):
    """
    Copying tok_advisory_audit.jsonl to an isolated tmp_path and reconstructing
    from it gives the same topology hash as reconstructing from the original.
    Proves reconstruction depends only on the evidence chain, not its location.
    """
    from ph6_l2_expand.topology_reconstruct import reconstruct_topology

    original_audit = _ARTIFACT_DIR / "tok_advisory_audit.jsonl"
    isolated_copy = tmp_path / "tok_advisory_audit.jsonl"
    shutil.copy2(original_audit, isolated_copy)

    _, hash_original, meta_orig = reconstruct_topology(original_audit)
    _, hash_isolated, meta_iso = reconstruct_topology(isolated_copy)

    assert hash_original == hash_isolated, (
        f"hash differed between original and isolated copy:\n"
        f"  original: {hash_original}\n  isolated: {hash_isolated}"
    )
    assert meta_orig["observation_count"] == meta_iso["observation_count"]


# ---------------------------------------------------------------------------
# 6. Required spatial fields survive replay
# ---------------------------------------------------------------------------

def test_er1e_all_required_spatial_fields_survive_replay():
    """
    All VDT_PROMOTED_TO_VLT events in the artifact chain contain the required
    ER-1B spatial fields. mean_confidence must be absent from all payloads.
    """
    audit_path = _ARTIFACT_DIR / "tok_advisory_audit.jsonl"

    with open(audit_path, "rb") as fh:
        events = [json.loads(line) for line in fh if line.strip()]

    promotion_events = [e for e in events if e.get("event_type") == "VDT_PROMOTED_TO_VLT"]
    assert len(promotion_events) == EXPECTED_VLT_COUNT, (
        f"expected {EXPECTED_VLT_COUNT} promotion events, got {len(promotion_events)}"
    )

    for ev in promotion_events:
        payload = ev["payload"]
        missing = REQUIRED_SPATIAL_IN_PAYLOAD - set(payload.keys())
        assert not missing, (
            f"promotion payload missing fields: {missing}\n"
            f"  object_class={payload.get('object_class')!r}"
        )
        assert "mean_confidence" not in payload, (
            f"promotion payload contains forbidden 'mean_confidence'"
        )

    # All 5 object classes must appear across promotions
    found = frozenset(e["payload"]["object_class"] for e in promotion_events)
    assert found == EXPECTED_OBJECT_CLASSES


# ---------------------------------------------------------------------------
# 7. Multi-cycle temporal fields survive replay
# ---------------------------------------------------------------------------

def test_er1e_multi_cycle_temporal_fields_survive_replay():
    """
    Each object class must appear in exactly 3 observation cycles with distinct
    first_seen_ms values, proving topology is not single-frame only.
    """
    from ph6_l2_expand.topology_reconstruct import replay_tok_chain

    audit_path = _ARTIFACT_DIR / "tok_advisory_audit.jsonl"
    _, observations, errors = replay_tok_chain(audit_path)

    assert not errors, f"unexpected replay errors: {errors}"
    assert len(observations) == EXPECTED_VLT_COUNT

    by_class: Dict[str, List[int]] = {}
    for obs in observations:
        oc = obs.get("object_class", "")
        tsms = obs.get("first_seen_ms")
        assert isinstance(tsms, int), f"first_seen_ms missing or non-int for {oc!r}"
        by_class.setdefault(oc, []).append(tsms)

    assert frozenset(by_class.keys()) == EXPECTED_OBJECT_CLASSES

    for oc, timestamps in by_class.items():
        assert len(timestamps) == EXPECTED_NUM_CYCLES, (
            f"{oc!r}: expected {EXPECTED_NUM_CYCLES} cycles, got {len(timestamps)}"
        )
        # All timestamps must be distinct (different cycles)
        assert len(set(timestamps)) == EXPECTED_NUM_CYCLES, (
            f"{oc!r}: first_seen_ms values are not distinct across cycles: {timestamps}"
        )
        # last_seen_ms must be >= first_seen_ms (validated by ER-1B spatial validator)
        for obs in observations:
            if obs.get("object_class") == oc:
                assert obs["last_seen_ms"] >= obs["first_seen_ms"], (
                    f"{oc!r}: last_seen_ms < first_seen_ms"
                )


# ---------------------------------------------------------------------------
# 8. Corrupt chain rejected
# ---------------------------------------------------------------------------

def test_er1e_corrupt_chain_rejected(tmp_path):
    """
    Byte-corrupting a copy of tok_advisory_audit.jsonl causes chain validation
    to fail and reconstruct_topology to raise ValueError.
    Uses a tmp_path copy to protect the committed artifact.
    """
    from ph6.tok.reconstruct import validate_chain_integrity
    from ph6_l2_expand.topology_reconstruct import reconstruct_topology

    original = _ARTIFACT_DIR / "tok_advisory_audit.jsonl"
    corrupted = tmp_path / "tok_advisory_audit.jsonl"
    shutil.copy2(original, corrupted)

    valid_before, _, _ = validate_chain_integrity(corrupted)
    assert valid_before, "copy should be valid before corruption"

    raw = bytearray(corrupted.read_bytes())
    mid = len(raw) // 2
    raw[mid] = (raw[mid] + 1) % 256
    corrupted.write_bytes(bytes(raw))

    valid_after, _, _ = validate_chain_integrity(corrupted)
    assert not valid_after, "corrupted chain must fail integrity check"

    with pytest.raises(ValueError, match="chain replay failed"):
        reconstruct_topology(corrupted)


# ---------------------------------------------------------------------------
# 9. No /var/ph6/mram-s mutation
# ---------------------------------------------------------------------------

def test_er1e_no_mrams_mutation():
    """
    Running reconstruction from the artifact audit chain does not create
    or mutate /var/ph6/mram-s.
    """
    from ph6_l2_expand.topology_reconstruct import reconstruct_topology

    mrams = Path("/var/ph6/mram-s")
    existed_before = mrams.exists()
    mtime_before = mrams.stat().st_mtime if existed_before else None

    audit_path = _ARTIFACT_DIR / "tok_advisory_audit.jsonl"
    reconstruct_topology(audit_path)

    if not existed_before:
        assert not mrams.exists(), "/var/ph6/mram-s must not be created by reconstruction"
    else:
        mtime_after = mrams.stat().st_mtime
        assert mtime_before == mtime_after, "/var/ph6/mram-s mtime changed during reconstruction"


# ---------------------------------------------------------------------------
# 10. No CRAM / verdict writes
# ---------------------------------------------------------------------------

def test_er1e_no_cram_verdict_writes(tmp_path):
    """
    Reconstruction from a tmp_path copy of the audit chain writes no files
    to CRAM-0, CRAM-A, CRAM-R, PASS, DROP, or verdict paths.
    """
    from ph6_l2_expand.topology_reconstruct import reconstruct_topology

    audit_copy = tmp_path / "tok_advisory_audit.jsonl"
    shutil.copy2(_ARTIFACT_DIR / "tok_advisory_audit.jsonl", audit_copy)

    reconstruct_topology(audit_copy)

    forbidden_segments = {"cram-0", "cram-a", "cram-r"}
    forbidden_stems = {"pass", "drop", "verdict"}

    for created in tmp_path.rglob("*"):
        parts_lower = {p.lower() for p in created.parts}
        overlap = parts_lower & forbidden_segments
        assert not overlap, f"reconstruction wrote to forbidden CRAM path: {created}"

        if created.is_file():
            assert created.stem.lower() not in forbidden_stems, (
                f"reconstruction created forbidden verdict file: {created}"
            )


# ---------------------------------------------------------------------------
# 11. No snapshot cache
# ---------------------------------------------------------------------------

def test_er1e_no_snapshot_cache(tmp_path):
    """
    Reconstruction creates no snapshot or cache files.
    """
    from ph6_l2_expand.topology_reconstruct import reconstruct_topology

    audit_copy = tmp_path / "tok_advisory_audit.jsonl"
    shutil.copy2(_ARTIFACT_DIR / "tok_advisory_audit.jsonl", audit_copy)

    reconstruct_topology(audit_copy)

    for created in tmp_path.rglob("*"):
        if created.is_file():
            name_lower = created.name.lower()
            for sub in ("snapshot", "cache"):
                assert sub not in name_lower, (
                    f"reconstruction created forbidden file (contains '{sub}'): {created}"
                )


# ---------------------------------------------------------------------------
# 12. No Lane-1 imports
# ---------------------------------------------------------------------------

def test_er1e_no_lane1_imports():
    """
    This test file, er1e_campaign.py, and topology_reconstruct.py must not
    import from Lane-1 modules.
    """
    files_to_check = [
        Path(__file__),
        _WORKTREE_ROOT / "ph6_l2_expand" / "er1e_campaign.py",
        _WORKTREE_ROOT / "ph6_l2_expand" / "topology_reconstruct.py",
    ]

    violations: List[str] = []
    for path in files_to_check:
        assert path.exists(), f"file not found: {path}"
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
