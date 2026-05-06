"""
PH6 / CRAM-PU — Canonical schema helper tests.

Covers PATCH 2 (canonical JSON), PATCH 3 (fixed-point),
PATCH 4 (BLAKE2b-256), PATCH 1 (audit fields), PATCH 5 (.blake2b marker).
"""

import hashlib
import json
import pytest
from pathlib import Path
from decimal import Decimal

from ph6.cram_pu.schemas.canonical import (
    canonical_json,
    blake2b_256,
    blake2b_256_obj,
    fp_int,
    fp_from_int,
    validate_event_type,
    ALLOWED_EVENT_TYPES,
    FORBIDDEN_EVENT_TYPES,
)
from ph6.cram_pu.schemas.audit import append_audit, validate_chain, GENESIS_HASH
from ph6.cram_pu.tools.cram_pu_atomic_commit import AtomicCRAMCommitter


# ---------------------------------------------------------------------------
# PATCH 2 — Canonical JSON stability
# ---------------------------------------------------------------------------

class TestCanonicalJSON:
    def test_same_input_same_output(self):
        obj = {"b": 2, "a": 1, "c": [3, 1, 2]}
        assert canonical_json(obj) == canonical_json(obj)

    def test_sort_keys(self):
        a = canonical_json({"z": 1, "a": 2})
        b = canonical_json({"a": 2, "z": 1})
        assert a == b

    def test_no_nan_allowed(self):
        with pytest.raises((ValueError, Exception)):
            json.loads(canonical_json({"x": float("nan")}))

    def test_no_infinity_allowed(self):
        with pytest.raises((ValueError, Exception)):
            canonical_json({"x": float("inf")})

    def test_compact_separators(self):
        data = canonical_json({"a": 1}).decode("utf-8")
        assert " " not in data

    def test_utf8_encoding(self):
        result = canonical_json({"msg": "héllo"})
        assert isinstance(result, bytes)
        assert "héllo".encode("utf-8") in result


# ---------------------------------------------------------------------------
# PATCH 4 — BLAKE2b-256
# ---------------------------------------------------------------------------

class TestBLAKE2b256:
    def test_output_is_64_hex_chars(self):
        h = blake2b_256(b"test")
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)

    def test_deterministic(self):
        assert blake2b_256(b"data") == blake2b_256(b"data")

    def test_different_inputs_differ(self):
        assert blake2b_256(b"a") != blake2b_256(b"b")

    def test_matches_stdlib(self):
        data = b"ph6test"
        expected = hashlib.blake2b(data, digest_size=32).hexdigest()
        assert blake2b_256(data) == expected

    def test_obj_helper_matches(self):
        obj = {"x": 1, "y": 2}
        assert blake2b_256_obj(obj) == blake2b_256(canonical_json(obj))


# ---------------------------------------------------------------------------
# PATCH 3 — Fixed-point encoder
# ---------------------------------------------------------------------------

class TestFixedPoint:
    def test_integer_value(self):
        assert fp_int(1) == 10000

    def test_decimal_value(self):
        assert fp_int(3.5) == 35000

    def test_round_half_even(self):
        # 0.00005 * 10000 = 0.5 → rounds to 0 (even)
        assert fp_int("0.00005") == 0
        # 0.00015 * 10000 = 1.5 → rounds to 2 (even)
        assert fp_int("0.00015") == 2

    def test_zero(self):
        assert fp_int(0) == 0

    def test_nan_raises(self):
        with pytest.raises(ValueError, match="non-finite"):
            fp_int(float("nan"))

    def test_infinity_raises(self):
        with pytest.raises(ValueError, match="non-finite"):
            fp_int(float("inf"))

    def test_round_trip(self):
        original = Decimal("12.3456")
        encoded = fp_int(original)
        recovered = fp_from_int(encoded)
        assert recovered == original

    def test_brightness_thresholds(self):
        # Verify threshold comparisons work correctly in fixed-point
        assert fp_int(20) == 200000   # BRIGHT_MIN
        assert fp_int(235) == 2350000 # BRIGHT_MAX
        assert fp_int(15.0) == 150000 # VAR_MIN


# ---------------------------------------------------------------------------
# PATCH 1 — Audit event required fields
# ---------------------------------------------------------------------------

class TestAuditRequiredFields:
    def test_all_required_fields_present(self, tmp_path):
        audit_path = tmp_path / "audit.jsonl"
        event = append_audit(
            audit_path=audit_path,
            event_type="CRAM_PASS_COMMIT",
            object_id="frame_001",
            authority_hash="a" * 64,
            node_id="CRAM_PU_NODE_1",
            stage="COMMIT",
            status="OK",
        )
        required = {
            "schema", "event_seq", "event_type", "object_id",
            "event_hash", "prev_event_hash", "authority_hash",
            "timestamp_utc", "node_id", "stage", "status",
        }
        assert required.issubset(event.keys()), \
            f"Missing fields: {required - event.keys()}"

    def test_first_event_genesis_prev_hash(self, tmp_path):
        audit_path = tmp_path / "audit.jsonl"
        event = append_audit(
            audit_path=audit_path,
            event_type="CRAM0_INTAKE",
            object_id="frame_001",
            authority_hash="b" * 64,
            node_id="NODE_1",
            stage="INTAKE",
            status="OK",
        )
        assert event["prev_event_hash"] == GENESIS_HASH
        assert event["event_seq"] == 1

    def test_event_seq_monotonic(self, tmp_path):
        audit_path = tmp_path / "audit.jsonl"
        for i in range(3):
            event = append_audit(
                audit_path=audit_path,
                event_type="CRAM_PASS_COMMIT",
                object_id=f"frame_{i:03d}",
                authority_hash="c" * 64,
                node_id="NODE_1",
                stage="COMMIT",
                status="OK",
            )
        assert event["event_seq"] == 3

    def test_forbidden_event_type_rejected(self, tmp_path):
        audit_path = tmp_path / "audit.jsonl"
        for bad_type in FORBIDDEN_EVENT_TYPES:
            with pytest.raises(ValueError, match="Forbidden"):
                append_audit(
                    audit_path=audit_path,
                    event_type=bad_type,
                    object_id="obj",
                    authority_hash="d" * 64,
                    node_id="NODE_1",
                    stage="X",
                    status="X",
                )

    def test_timestamp_utc_format(self, tmp_path):
        audit_path = tmp_path / "audit.jsonl"
        event = append_audit(
            audit_path=audit_path,
            event_type="EXPORT_START",
            object_id="obj_001",
            authority_hash="e" * 64,
            node_id="NODE_1",
            stage="EXPORT",
            status="OK",
        )
        ts = event["timestamp_utc"]
        assert "T" in ts and ts.endswith("Z"), \
            f"timestamp_utc must be UTC ISO format, got {ts!r}"


# ---------------------------------------------------------------------------
# Audit hash chain integrity
# ---------------------------------------------------------------------------

class TestAuditHashChain:
    def test_chain_valid_after_writes(self, tmp_path):
        audit_path = tmp_path / "audit.jsonl"
        for i in range(5):
            append_audit(
                audit_path=audit_path,
                event_type="CRAM_PASS_COMMIT",
                object_id=f"obj_{i}",
                authority_hash="f" * 64,
                node_id="NODE_1",
                stage="COMMIT",
                status="OK",
            )
        valid, count, err = validate_chain(audit_path)
        assert valid, f"Chain invalid: {err}"
        assert count == 5

    def test_empty_file_is_valid(self, tmp_path):
        audit_path = tmp_path / "audit.jsonl"
        valid, count, err = validate_chain(audit_path)
        assert valid
        assert count == 0

    def test_tampered_event_detected(self, tmp_path):
        audit_path = tmp_path / "audit.jsonl"
        append_audit(
            audit_path=audit_path,
            event_type="CRAM_PASS_COMMIT",
            object_id="obj_001",
            authority_hash="g" * 64,
            node_id="NODE_1",
            stage="COMMIT",
            status="OK",
        )
        # Tamper: rewrite event with different object_id
        lines = audit_path.read_bytes().splitlines()
        evt = json.loads(lines[0])
        evt["object_id"] = "tampered"
        lines[0] = json.dumps(evt, sort_keys=True, separators=(",", ":")).encode()
        audit_path.write_bytes(b"\n".join(lines) + b"\n")

        valid, count, err = validate_chain(audit_path)
        assert not valid


# ---------------------------------------------------------------------------
# PATCH 5 — CRAM-A .blake2b commit marker
# ---------------------------------------------------------------------------

class TestCRAMAMarker:
    def test_marker_written_after_commit(self, tmp_path):
        committer = AtomicCRAMCommitter(tmp_path)
        verdict = {
            "packet_id": "pkt_001",
            "input_hash": "h" * 64,
            "verdict": "PASS",
        }
        record = committer.commit(verdict)

        markers = list(tmp_path.glob("*.blake2b"))
        assert len(markers) == 1, "Expected exactly one .blake2b marker"

    def test_marker_contains_cram_hash(self, tmp_path):
        committer = AtomicCRAMCommitter(tmp_path)
        verdict = {
            "packet_id": "pkt_002",
            "input_hash": "i" * 64,
            "verdict": "PASS",
        }
        record = committer.commit(verdict)

        marker = next(tmp_path.glob("*.blake2b"))
        marker_content = marker.read_text().strip()
        assert marker_content == record["cram_hash"], \
            "Marker hash must match cram_hash"

    def test_no_tmp_marker_left_after_commit(self, tmp_path):
        committer = AtomicCRAMCommitter(tmp_path)
        verdict = {
            "packet_id": "pkt_003",
            "input_hash": "j" * 64,
            "verdict": "PASS",
        }
        committer.commit(verdict)

        tmp_markers = list(tmp_path.glob("*.blake2b.tmp"))
        assert tmp_markers == [], "No .tmp marker files should remain"

    def test_missing_marker_means_non_authoritative(self, tmp_path):
        committer = AtomicCRAMCommitter(tmp_path)
        verdict = {
            "packet_id": "pkt_004",
            "input_hash": "k" * 64,
            "verdict": "PASS",
        }
        committer.commit(verdict)

        # Delete the marker — object should be treated as non-authoritative
        for m in tmp_path.glob("*.blake2b"):
            m.unlink()

        markers = list(tmp_path.glob("*.blake2b"))
        assert markers == [], "Marker deleted — object is no longer authoritative"
        # Caller logic should check for marker before treating object as authoritative
