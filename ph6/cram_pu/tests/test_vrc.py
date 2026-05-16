"""
Tests for PH6-VRC-1.0 — Validator Replay Certification.

VRC-1.0 verifies replay consistency with the ingest receipt chain.
It does NOT declare production clearance.

Coverage:
  - empty store certifies (no evidence to contradict)
  - accepted frame with matching CRAM file and hash: PASS
  - accepted receipt with no CRAM file: FAIL (R5)
  - accepted receipt with wrong authority_hash: FAIL (R3)
  - CRAM chain break: FAIL (R4)
  - cert_hash seals the receipt
  - production_clearance is always False
  - OI-01, OI-03 always listed as open
"""

import json
import os
import tempfile
from pathlib import Path

import pytest

from ph6.cram_pu.ingest_receipt_logger import IngestReceiptLogger
from ph6.cram_pu.crash_replay import CRAMWriter
from ph6.cram_pu.vrc import certify


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_store() -> Path:
    td = Path(tempfile.mkdtemp())
    (td / "ingest_receipt_log.jsonl").touch()
    return td


def _write_cram_file(store: Path, frame_id: int, cram_hash: str, prev_hash: str) -> Path:
    """Write a minimal cram_*.json with controlled hashes."""
    import hashlib
    record = {
        "schema":         "ph6.cram_commit.v1",
        "frame_id":       frame_id,
        "payload_hash":   "x" * 64,
        "hash_algorithm": "BLAKE2b-256",
        "verdict":        "PASS",
        "authority":      "LANE_1",
        "prev_cram_hash": prev_hash,
        "timestamp_utc":  "2026-05-16T00:00:00Z",
    }
    # Use the provided cram_hash directly (override canonical computation for test isolation)
    record["cram_hash"] = cram_hash
    path = store / f"cram_{frame_id:010d}.json"
    path.write_text(json.dumps(record, sort_keys=True, separators=(",", ":")))
    return path


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_empty_store_certifies():
    """Empty store with no receipts and no CRAM files: PASS (no evidence to contradict)."""
    store = _make_store()
    result = certify(store)
    assert result["passed"] is True
    assert result["failure_count"] == 0


def test_production_clearance_always_false():
    """VRC never declares production clearance."""
    store = _make_store()
    result = certify(store)
    assert result["production_clearance"] is False


def test_stop_ship_gates_always_present():
    """OI-01 and OI-03 always listed as open stop-ship gates."""
    store = _make_store()
    result = certify(store)
    assert "OI-01" in result["open_stop_ship_gates"]
    assert "OI-03" in result["open_stop_ship_gates"]


def test_cert_hash_seals_receipt():
    """cert_hash is BLAKE2b-256 of canonical body excluding cert_hash."""
    import hashlib
    store = _make_store()
    result = certify(store)
    stored_hash = result.pop("cert_hash")
    canonical = json.dumps(result, sort_keys=True, ensure_ascii=False,
                           allow_nan=False, separators=(",", ":")).encode()
    expected = hashlib.blake2b(canonical, digest_size=32).hexdigest()
    assert stored_hash == expected


def test_accepted_frame_with_matching_cram_passes():
    """INGEST_ACCEPTED receipt with matching CRAM cram_hash passes Step B."""
    store = _make_store()
    logger = IngestReceiptLogger(store)

    cram_hash = "a" * 64
    logger.arrived(frame_id=1, payload_hash="b" * 64)
    logger.accepted(frame_id=1, cram_hash=cram_hash)

    # Write a CRAM file whose cram_hash matches the receipt authority_hash
    record = {
        "schema":         "ph6.cram_commit.v1",
        "frame_id":       1,
        "payload_hash":   "b" * 64,
        "hash_algorithm": "BLAKE2b-256",
        "verdict":        "PASS",
        "authority":      "LANE_1",
        "prev_cram_hash": "0" * 64,
        "timestamp_utc":  "2026-05-16T00:00:00Z",
    }
    # Compute the real cram_hash from body so it matches what VRC expects
    import hashlib
    canonical = json.dumps(record, sort_keys=True, ensure_ascii=False,
                           allow_nan=False, separators=(",", ":")).encode()
    computed_hash = hashlib.blake2b(canonical, digest_size=32).hexdigest()
    record["cram_hash"] = computed_hash

    # Update the receipt to use the computed hash
    log = store / "ingest_receipt_log.jsonl"
    lines = log.read_text().splitlines()
    for i, line in enumerate(lines):
        r = json.loads(line)
        if r.get("event_type") == "INGEST_ACCEPTED":
            r["authority_hash"] = computed_hash
            # Re-seal event_hash
            body = {k: v for k, v in r.items() if k != "event_hash"}
            canon = json.dumps(body, sort_keys=True, ensure_ascii=False,
                               allow_nan=False, separators=(",", ":")).encode()
            r["event_hash"] = hashlib.blake2b(canon, digest_size=32).hexdigest()
            lines[i] = json.dumps(r, sort_keys=True, ensure_ascii=False,
                                   allow_nan=False, separators=(",", ":"))
    log.write_text("\n".join(lines) + "\n")

    (store / "cram_0000000001.json").write_text(
        json.dumps(record, sort_keys=True, separators=(",", ":"))
    )

    result = certify(store)
    assert result["steps"]["B_accepted_frames_in_cram"] == 1
    assert result["steps"]["B_accepted_frames_missing"] == 0


def test_accepted_frame_without_cram_file_fails():
    """INGEST_ACCEPTED receipt with no CRAM file fails Step B (R5)."""
    store = _make_store()
    logger = IngestReceiptLogger(store)
    logger.accepted(frame_id=42, cram_hash="c" * 64)

    result = certify(store)
    assert result["passed"] is False
    classes = [f["failure_class"] for f in result["failures"]]
    assert "R5" in classes


def test_authority_hash_mismatch_fails():
    """INGEST_ACCEPTED receipt with wrong authority_hash fails Step B (R3)."""
    import hashlib
    store = _make_store()
    logger = IngestReceiptLogger(store)
    logger.accepted(frame_id=1, cram_hash="wrong" + "0" * 59)

    # Write a real CRAM file with a different cram_hash
    record = {
        "schema": "ph6.cram_commit.v1", "frame_id": 1,
        "payload_hash": "p" * 64, "hash_algorithm": "BLAKE2b-256",
        "verdict": "PASS", "authority": "LANE_1",
        "prev_cram_hash": "0" * 64, "timestamp_utc": "2026-05-16T00:00:00Z",
    }
    canonical = json.dumps(record, sort_keys=True, ensure_ascii=False,
                           allow_nan=False, separators=(",", ":")).encode()
    record["cram_hash"] = hashlib.blake2b(canonical, digest_size=32).hexdigest()
    (store / "cram_0000000001.json").write_text(
        json.dumps(record, sort_keys=True, separators=(",", ":"))
    )

    result = certify(store)
    assert result["passed"] is False
    classes = [f["failure_class"] for f in result["failures"]]
    assert "R3" in classes


def test_cert_schema_and_authority():
    """Receipt has correct schema and VERIFY_ONLY authority."""
    store = _make_store()
    result = certify(store)
    assert result["schema"] == "ph6.vrc_receipt.v1"
    assert result["authority"] == "VERIFY_ONLY"


def test_result_set_hash_deterministic():
    """result_set_hash is BLAKE2b of ordered authority_hashes — same input → same hash."""
    import hashlib
    store = _make_store()
    logger = IngestReceiptLogger(store)
    logger.accepted(frame_id=1, cram_hash="a" * 64)
    logger.accepted(frame_id=2, cram_hash="b" * 64)

    r1 = certify(store)
    r2 = certify(store)
    assert r1["result_set_hash"] == r2["result_set_hash"]
    assert r1["result_set_hash"] is not None


def test_receipt_chain_final_hash_present():
    """receipt_chain_final_hash is set when receipts exist."""
    store = _make_store()
    logger = IngestReceiptLogger(store)
    logger.arrived(frame_id=1, payload_hash="c" * 64)
    result = certify(store)
    assert result["receipt_chain_final_hash"] is not None


def test_receipt_chain_final_hash_none_when_empty():
    """receipt_chain_final_hash is None for empty store."""
    store = _make_store()
    result = certify(store)
    assert result["receipt_chain_final_hash"] is None


def test_advisory_field_in_cram_fails_step_d():
    """CRAM commit file with advisory field fails Step D (G5)."""
    import hashlib
    store = _make_store()

    # Write a CRAM file that has an advisory field
    record = {
        "schema":         "ph6.cram_commit.v1",
        "frame_id":       1,
        "payload_hash":   "d" * 64,
        "hash_algorithm": "BLAKE2b-256",
        "verdict":        "PASS",
        "authority":      "LANE_1",
        "prev_cram_hash": "0" * 64,
        "timestamp_utc":  "2026-05-16T00:00:00Z",
        "soso_advisory":  {"state": "STABLE"},  # advisory contamination
    }
    canonical = json.dumps(record, sort_keys=True, ensure_ascii=False,
                           allow_nan=False, separators=(",", ":")).encode()
    record["cram_hash"] = hashlib.blake2b(canonical, digest_size=32).hexdigest()
    (store / "cram_0000000001.json").write_text(
        json.dumps(record, sort_keys=True, separators=(",", ":"))
    )

    result = certify(store)
    assert result["passed"] is False
    classes = [f["failure_class"] for f in result["failures"]]
    assert "G5" in classes


def test_broken_receipt_chain_fails_step_a():
    """Tampered receipt chain fails Step A."""
    store = _make_store()
    logger = IngestReceiptLogger(store)
    logger.arrived(frame_id=1, payload_hash="e" * 64)
    logger.arrived(frame_id=2, payload_hash="f" * 64)

    # Tamper the second receipt's prev_event_hash
    log = store / "ingest_receipt_log.jsonl"
    lines = log.read_text().splitlines()
    r2 = json.loads(lines[1])
    r2["prev_event_hash"] = "0" * 64  # wrong
    lines[1] = json.dumps(r2, sort_keys=True, ensure_ascii=False,
                           allow_nan=False, separators=(",", ":"))
    log.write_text("\n".join(lines) + "\n")

    result = certify(store)
    assert result["passed"] is False
    assert result["steps"]["A_receipt_chain_intact"] is False


def test_open_evidence_gaps_always_listed():
    """open_evidence_gaps always includes payload-replay gap."""
    store = _make_store()
    result = certify(store)
    assert "verdict_metric_payload_replay" in result["open_evidence_gaps"]


def test_step_d_clean_store_passes():
    """Store with no advisory fields passes Step D."""
    store = _make_store()
    result = certify(store)
    assert result["steps"]["D_advisory_fields_absent"] is True


def test_missing_receipt_log_still_reported():
    """Store with no receipt log at all: receipt chain reports as broken (no log found)."""
    store = _make_store()
    (store / "ingest_receipt_log.jsonl").unlink()  # delete the log
    result = certify(store)
    # With no receipt log, Step A reports not intact
    assert result["steps"]["A_receipt_chain_intact"] is False


def test_duplicate_event_seq_in_receipt_log_fails_vrc():
    """Duplicate event_seq detected via receipt chain verifier — fails Step A."""
    store = _make_store()
    logger = IngestReceiptLogger(store)
    logger.arrived(frame_id=1, payload_hash="g" * 64)
    logger.arrived(frame_id=2, payload_hash="h" * 64)

    # Inject a duplicate seq in the second entry
    log = store / "ingest_receipt_log.jsonl"
    lines = log.read_text().splitlines()
    r2 = json.loads(lines[1])
    r2["event_seq"] = 1  # duplicate
    # Also re-seal body without updating event_hash (creates hash mismatch too)
    lines[1] = json.dumps(r2, sort_keys=True, ensure_ascii=False,
                           allow_nan=False, separators=(",", ":"))
    log.write_text("\n".join(lines) + "\n")

    result = certify(store)
    assert result["passed"] is False


def test_verdict_metric_payload_replay_always_in_open_gaps():
    """
    Verdict/metric payload-replay comparison is always named as an open gap.
    This ensures the boundary is explicit in every certification receipt.
    """
    store = _make_store()
    result = certify(store)
    assert "verdict_metric_payload_replay" in result["open_evidence_gaps"]
    assert result["production_clearance"] is False
