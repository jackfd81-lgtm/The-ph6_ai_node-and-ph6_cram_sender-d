"""
PH6 / CRAM-PU — Closure patch verification tests.

Covers:
  C-1: Fixed-point metric field names in verdict and replay paths.
  C-2: SSMT audit_log required fields.
  C-3: timestamp_utc in authority records.
  C-4: CRAMWriter atomic .blake2b marker.
"""

import json
import os
import pytest
from pathlib import Path
from datetime import datetime

from ph6.cram_pu.crash_replay import CRAMWriter, blake2b256
from ph6.ssmt.audit_log import SSMTAuditLog
from ph6.ssmt.models import SwarmPacket


# ---------------------------------------------------------------------------
# C-1: Fixed-point field names
# ---------------------------------------------------------------------------

class TestFixedPointFieldNames:
    """Verify the canonical fixed-point field names used by verdict paths."""

    def test_canonical_fp_fields_defined(self):
        from ph6.cram_pu.schemas.canonical import fp_int
        assert fp_int(20) == 200000
        assert fp_int(235) == 2350000
        assert fp_int(15.0) == 150000
        assert fp_int(0.40) == 4000

    def test_fp_fields_are_integers(self):
        from ph6.cram_pu.schemas.canonical import fp_int
        assert isinstance(fp_int(128.5), int)

    def test_verdict_runner_imports_fp_int(self):
        # Proves verdict_runner can import fp_int without error
        # (cv2 may not be installed in test env — skip if unavailable)
        pytest.importorskip("cv2", reason="cv2 not available in test env")
        from ph6.cram_pu.tools.cram_pu_verdict_runner import (
            _FP_BRIGHT_MIN, _FP_BRIGHT_MAX, _FP_LAP_MIN, _FP_MOTION_MAX
        )
        assert _FP_BRIGHT_MIN == 200000
        assert _FP_BRIGHT_MAX == 2350000
        assert _FP_LAP_MIN == 150000
        assert _FP_MOTION_MAX == 4000

    def test_replay_verify_imports_fp_int(self):
        pytest.importorskip("cv2", reason="cv2 not available in test env")
        from ph6.cram_pu.tools.cram_pu_replay_verify import (
            _FP_BRIGHT_MIN, _FP_BRIGHT_MAX, _FP_LAP_MIN, _FP_MOTION_MAX
        )
        assert _FP_BRIGHT_MIN == 200000
        assert _FP_BRIGHT_MAX == 2350000

    def test_old_float_field_names_absent_from_verdict_runner(self):
        """Forbid old float field names in the OpenCV verdict runner source."""
        path = Path("ph6/cram_pu/tools/cram_pu_verdict_runner.py")
        text = path.read_text(encoding="utf-8")
        for old_field in ('"mean_brightness"', '"laplacian_var"', '"motion_fraction"'):
            # Allow the field name to appear as part of a dict key only if
            # it's in a comment or the PSEUDO_METRICS definition with _fp suffix.
            # Fail if the plain (non _fp) field appears as a JSON key being set.
            assert old_field + ":" not in text, \
                f"Old float field {old_field} found as JSON key in {path}"

    def test_old_float_field_names_absent_from_replay_verify(self):
        path = Path("ph6/cram_pu/tools/cram_pu_replay_verify.py")
        text = path.read_text(encoding="utf-8")
        for old_field in ('"mean_brightness":', '"laplacian_var":', '"motion_fraction":'):
            assert old_field not in text, \
                f"Old float field {old_field} found as JSON key in {path}"


# ---------------------------------------------------------------------------
# C-3: timestamp_utc in authority records
# ---------------------------------------------------------------------------

class TestTimestampUTC:
    def test_cram_writer_record_has_timestamp_utc(self, tmp_path):
        writer = CRAMWriter(tmp_path)
        verdict = {"verdict": "PASS", "frame_id": 1}
        record = writer.commit(1, "h" * 64, verdict)
        assert "timestamp_utc" in record, "CRAM commit record must have timestamp_utc"
        assert "timestamp" not in record, "Raw float timestamp must not appear in CRAM commit"

    def test_cram_writer_timestamp_utc_is_iso_format(self, tmp_path):
        writer = CRAMWriter(tmp_path)
        verdict = {"verdict": "PASS", "frame_id": 1}
        record = writer.commit(1, "h" * 64, verdict)
        ts = record["timestamp_utc"]
        assert "T" in ts and ts.endswith("Z"), \
            f"timestamp_utc must be ISO UTC, got {ts!r}"
        # Verify parseable
        datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ")

    def test_ssmt_audit_has_timestamp_utc(self, tmp_path):
        root = str(tmp_path / "swarms") + "/"
        log = SSMTAuditLog.__new__(SSMTAuditLog)
        log.root = root
        log.audit_path = os.path.join(root, "ssmt_audit.jsonl")
        os.makedirs(root, exist_ok=True)

        packet = SwarmPacket(
            swarm_id="S1", role="active_memory", authority="NONE",
            lane="LANE_2_ADVISORY", ssmt_version="1.0", ttl_seconds=30,
            output_type="advisory", advisory_payload={"k": "v"},
            drift_score=0, confidence_fp=95,
            created_at=1700000001.0, dependency_for_replay=False,
        )
        event = log.append_packet_event(packet, "/var/ph6/mram-s/swarms/S1_x.json")
        assert "timestamp_utc" in event, "SSMT audit event must have timestamp_utc"
        ts = event["timestamp_utc"]
        assert "T" in ts and ts.endswith("Z")


# ---------------------------------------------------------------------------
# C-2: SSMT audit required fields
# ---------------------------------------------------------------------------

class TestSSMTAuditRequiredFields:
    REQUIRED_FIELDS = {
        "schema", "event_seq", "event_type", "object_id",
        "event_hash", "prev_event_hash",
        "authority_hash", "node_id", "stage", "status", "timestamp_utc",
    }

    def _make_log(self, tmp_path):
        root = str(tmp_path / "swarms") + "/"
        log = SSMTAuditLog.__new__(SSMTAuditLog)
        log.root = root
        log.audit_path = os.path.join(root, "ssmt_audit.jsonl")
        os.makedirs(root, exist_ok=True)
        return log

    def _packet(self):
        return SwarmPacket(
            swarm_id="S1", role="active_memory", authority="NONE",
            lane="LANE_2_ADVISORY", ssmt_version="1.0", ttl_seconds=30,
            output_type="advisory", advisory_payload={"k": "v"},
            drift_score=0, confidence_fp=95,
            created_at=1700000001.0, dependency_for_replay=False,
        )

    def test_all_required_fields_present(self, tmp_path):
        log = self._make_log(tmp_path)
        event = log.append_packet_event(
            self._packet(), "/var/ph6/mram-s/swarms/S1_x.json"
        )
        missing = self.REQUIRED_FIELDS - event.keys()
        assert not missing, f"SSMT audit event missing required fields: {missing}"

    def test_authority_hash_is_hex64(self, tmp_path):
        log = self._make_log(tmp_path)
        event = log.append_packet_event(
            self._packet(), "/var/ph6/mram-s/swarms/S1_x.json"
        )
        h = event["authority_hash"]
        assert len(h) == 64 and all(c in "0123456789abcdef" for c in h)

    def test_node_id_present(self, tmp_path):
        log = self._make_log(tmp_path)
        event = log.append_packet_event(
            self._packet(), "/var/ph6/mram-s/swarms/S1_x.json"
        )
        assert event["node_id"] == "S1"

    def test_stage_and_status(self, tmp_path):
        log = self._make_log(tmp_path)
        event = log.append_packet_event(
            self._packet(), "/var/ph6/mram-s/swarms/S1_x.json"
        )
        assert event["stage"] == "PACKET_WRITE"
        assert event["status"] == "OK"


# ---------------------------------------------------------------------------
# C-4: CRAMWriter atomic .blake2b marker
# ---------------------------------------------------------------------------

class TestCRAMWriterMarker:
    def test_marker_written_after_commit(self, tmp_path):
        writer = CRAMWriter(tmp_path)
        verdict = {"verdict": "PASS", "frame_id": 1}
        writer.commit(1, "h" * 64, verdict)
        markers = list(tmp_path.glob("*.blake2b"))
        assert len(markers) == 1, "CRAMWriter must write .blake2b marker"

    def test_marker_contains_cram_hash(self, tmp_path):
        writer = CRAMWriter(tmp_path)
        verdict = {"verdict": "PASS", "frame_id": 1}
        record = writer.commit(1, "h" * 64, verdict)
        marker = next(tmp_path.glob("*.blake2b"))
        assert marker.read_text().strip() == record["cram_hash"]

    def test_no_tmp_files_remain(self, tmp_path):
        writer = CRAMWriter(tmp_path)
        verdict = {"verdict": "PASS", "frame_id": 1}
        writer.commit(1, "h" * 64, verdict)
        assert list(tmp_path.glob("*.tmp")) == []
        assert list(tmp_path.glob("*.blake2b.tmp")) == []

    def test_multiple_commits_each_have_marker(self, tmp_path):
        writer = CRAMWriter(tmp_path)
        for i in range(1, 4):
            writer.commit(i, "h" * 64, {"verdict": "PASS", "frame_id": i})
        markers = list(tmp_path.glob("*.blake2b"))
        commits = list(tmp_path.glob("cram_*.json"))
        assert len(markers) == len(commits) == 3

    def test_marker_hash_matches_cram_hash_on_disk(self, tmp_path):
        import json as _json
        writer = CRAMWriter(tmp_path)
        verdict = {"verdict": "PASS", "frame_id": 1}
        writer.commit(1, "h" * 64, verdict)
        cram_file = next(tmp_path.glob("cram_*.json"))
        marker_file = Path(str(cram_file) + ".blake2b")
        record = _json.loads(cram_file.read_text())
        stored_marker_hash = marker_file.read_text().strip()
        assert stored_marker_hash == record["cram_hash"]
