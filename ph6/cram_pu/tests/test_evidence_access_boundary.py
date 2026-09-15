"""
Tests for the PH6 Evidence Access Boundary (Lane-2 -> Lane-1 read boundary).

Maps directly to the operator-ratified scenarios in
PH6_SOURCE/DEPLOYMENT/PH6_EVIDENCE_ACCESS_BOUNDARY_PROPOSAL.md:

  valid evidence        -> FOUND
  missing evidence       -> NOT_FOUND
  tampered evidence      -> CONFLICT
  missing marker         -> CONFLICT
  arbitrary path/type    -> INVALID (denied before any Path is touched)
  write/commit/delete    -> impossible (no such method exists on the class)
  verdict-shaped field   -> absent from EvidenceView entirely
  CRAM/MRAM-S filenames  -> provably non-colliding (explicit cross-lane contract)
"""

import json
import pytest
from pathlib import Path

from ph6.cram_pu.crash_replay import CRAMPaths, CRAMWriter, blake2b256
from ph6.cram_pu.evidence_boundary import (
    PH6EvidenceAccessBoundary,
    EvidenceStatus,
    EvidenceView,
)
from ph6.ssmt.constants import SWARM_IDS


@pytest.fixture
def store(tmp_path):
    cram = tmp_path / "cram-0"
    mram = tmp_path / "mram-s" / "swarms"
    cram.mkdir(parents=True)
    mram.mkdir(parents=True)
    return CRAMPaths(cram_store=cram, mram_s=mram)


@pytest.fixture
def boundary(store):
    return PH6EvidenceAccessBoundary(store)


def _verdict(frame_id: int, verdict: str = "PASS") -> dict:
    return {
        "schema": "ph6.pseudo_verdict.v1",
        "frame_id": frame_id,
        "verdict": verdict,
        "metrics": {"entropy": 3.1, "laplacian_var": 80.0, "motion_fraction": 0.02},
        "reasons": [],
        "authority": "LANE_1",
    }


# ---------------------------------------------------------------------------
# Interface-shape tests: denial by omission, not by runtime check
# ---------------------------------------------------------------------------

class TestBoundaryInterfaceShape:
    def test_boundary_only_exposes_three_read_methods(self):
        public_methods = {
            name
            for name in dir(PH6EvidenceAccessBoundary)
            if not name.startswith("_") and callable(getattr(PH6EvidenceAccessBoundary, name))
        }
        assert public_methods == {"get_evidence", "get_evidence_range", "verify_integrity"}

    def test_boundary_has_no_write_capability(self):
        forbidden = (
            "write", "commit", "delete", "rename", "overwrite", "promote",
            "approve", "reject", "certify", "override", "pass_", "drop",
        )
        for name in forbidden:
            assert not hasattr(PH6EvidenceAccessBoundary, name)

    def test_evidence_view_has_no_verdict_shaped_field(self):
        forbidden_fields = {
            "verdict", "pass", "drop", "result", "final", "block",
            "override", "approve", "reject", "certify",
        }
        actual_fields = set(EvidenceView.__dataclass_fields__.keys())
        assert forbidden_fields & actual_fields == set()


# ---------------------------------------------------------------------------
# get_evidence: positive and negative cases
# ---------------------------------------------------------------------------

class TestGetEvidence:
    def test_returns_found_for_valid_record(self, store, boundary):
        writer = CRAMWriter(store.cram_store)
        committed = writer.commit(1, "h" * 64, _verdict(1))

        view = boundary.get_evidence(1)

        assert view.status is EvidenceStatus.FOUND
        assert view.frame_id == 1
        assert view.record == committed
        assert view.cram_hash == committed["cram_hash"]
        assert view.marker_present is True
        assert view.marker_matches is True

    def test_returns_not_found_for_missing_frame(self, store, boundary):
        view = boundary.get_evidence(999)
        assert view.status is EvidenceStatus.NOT_FOUND
        assert view.record is None

    def test_detects_tampered_hash_as_conflict(self, store, boundary):
        writer = CRAMWriter(store.cram_store)
        writer.commit(1, "h" * 64, _verdict(1))
        cram_file = next(store.cram_store.glob("cram_*.json"))
        rec = json.loads(cram_file.read_text())
        rec["payload_hash"] = "tampered"
        cram_file.write_text(json.dumps(rec, sort_keys=True, separators=(",", ":")))

        view = boundary.get_evidence(1)

        assert view.status is EvidenceStatus.CONFLICT

    def test_detects_missing_marker_as_conflict(self, store, boundary):
        writer = CRAMWriter(store.cram_store)
        writer.commit(1, "h" * 64, _verdict(1))
        marker = next(store.cram_store.glob("cram_*.json.blake2b"))
        marker.unlink()

        view = boundary.get_evidence(1)

        assert view.status is EvidenceStatus.CONFLICT
        assert view.marker_present is False

    def test_detects_mismatched_marker_as_conflict(self, store, boundary):
        writer = CRAMWriter(store.cram_store)
        writer.commit(1, "h" * 64, _verdict(1))
        marker = next(store.cram_store.glob("cram_*.json.blake2b"))
        marker.write_text("f" * 64 + "\n", encoding="utf-8")

        view = boundary.get_evidence(1)

        assert view.status is EvidenceStatus.CONFLICT
        assert view.marker_present is True
        assert view.marker_matches is False

    @pytest.mark.parametrize("bad_frame_id", ["../../etc/passwd", "1", 3.5, True, -1, None])
    def test_rejects_non_int_or_negative_frame_id_without_touching_filesystem(
        self, store, boundary, bad_frame_id
    ):
        view = boundary.get_evidence(bad_frame_id)
        assert view.status is EvidenceStatus.INVALID
        assert view.frame_id is None
        # No traversal occurred: the store directory must remain exactly as created.
        assert list(store.cram_store.iterdir()) == []

    def test_malformed_json_is_invalid_not_a_crash(self, store, boundary):
        (store.cram_store / "cram_0000000002.json").write_text("{not valid json")
        view = boundary.get_evidence(2)
        assert view.status is EvidenceStatus.INVALID


# ---------------------------------------------------------------------------
# get_evidence_range: bounded, never a raw directory walk
# ---------------------------------------------------------------------------

class TestGetEvidenceRange:
    def test_range_matches_committed_frames(self, store, boundary):
        writer = CRAMWriter(store.cram_store)
        for fid in range(1, 4):
            writer.commit(fid, "h" * 64, _verdict(fid))

        views = boundary.get_evidence_range(1, 3)

        assert [v.status for v in views] == [EvidenceStatus.FOUND] * 3
        assert [v.frame_id for v in views] == [1, 2, 3]

    def test_range_is_capped_at_hard_maximum_regardless_of_request_size(self, store, boundary):
        views = boundary.get_evidence_range(1, 10_000, max_count=1_000_000)
        assert len(views) == 500

    def test_range_default_max_count_is_500(self, store, boundary):
        views = boundary.get_evidence_range(1, 10_000)
        assert len(views) == 500

    def test_range_rejects_end_before_start(self, store, boundary):
        views = boundary.get_evidence_range(10, 1)
        assert len(views) == 1
        assert views[0].status is EvidenceStatus.INVALID

    def test_range_rejects_non_int_bounds(self, store, boundary):
        views = boundary.get_evidence_range("0", 5)
        assert len(views) == 1
        assert views[0].status is EvidenceStatus.INVALID


# ---------------------------------------------------------------------------
# verify_integrity: same semantics as get_evidence, not a second interpretation
# ---------------------------------------------------------------------------

class TestVerifyIntegrity:
    def test_verify_integrity_matches_get_evidence(self, store, boundary):
        writer = CRAMWriter(store.cram_store)
        writer.commit(1, "h" * 64, _verdict(1))

        assert boundary.verify_integrity(1) == boundary.get_evidence(1)

    def test_verify_integrity_reports_conflict_on_tamper(self, store, boundary):
        writer = CRAMWriter(store.cram_store)
        writer.commit(1, "h" * 64, _verdict(1))
        marker = next(store.cram_store.glob("cram_*.json.blake2b"))
        marker.unlink()

        assert boundary.verify_integrity(1).status is EvidenceStatus.CONFLICT


# ---------------------------------------------------------------------------
# Explicit cross-lane filename-collision impossibility (closes the
# "emergent, not explicit" gap named in SOSO_AGENT_DISCOVERY_REPORT.md §14)
# ---------------------------------------------------------------------------

class TestCrossLaneFilenameDisjointness:
    def test_cram_and_mram_s_swarm_filenames_never_collide(self):
        import re

        cram_pattern = re.compile(r"^cram_\d{10}\.json$")
        swarm_prefixes = tuple(f"{swarm_id}_" for swarm_id in SWARM_IDS)

        # No swarm-packet filename (S{id}_{timestamp}.json, per
        # ssmt/audit_writer.py) can ever match the CRAM record pattern.
        for swarm_id in SWARM_IDS:
            sample = f"{swarm_id}_1234567890.json"
            assert not cram_pattern.match(sample)

        # No CRAM filename can start with a swarm-id prefix, and no swarm-id
        # prefix can start with the CRAM literal prefix.
        assert not any("cram_0000000001.json".startswith(p) for p in swarm_prefixes)
        assert not any(p.startswith("cram_") for p in swarm_prefixes)
