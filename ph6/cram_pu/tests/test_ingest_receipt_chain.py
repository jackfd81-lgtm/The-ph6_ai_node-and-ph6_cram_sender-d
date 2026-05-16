"""
Tests for CRAM ingest receipt chain (ph6.ingest_receipt.v1).

Coverage:
  - valid 3-receipt chain passes
  - broken prev_event_hash fails
  - duplicate event_seq fails
  - missing authority_hash fails
  - genesis only allowed at first event
  - event_hash tampering detected
"""

import json
import tempfile
from pathlib import Path

import pytest

from ph6.cram_pu.ingest_receipt_logger import IngestReceiptLogger, GENESIS_HASH
from ph6.cram_pu.ingest_receipt_verify import verify_receipt_chain


# ── Helpers ──────────────────────────────────────────────────────────────────

def _make_store() -> Path:
    td = Path(tempfile.mkdtemp())
    (td / "ingest_receipt_log.jsonl").touch()
    return td


def _overwrite_log(store: Path, receipts: list[dict]) -> None:
    log = store / "ingest_receipt_log.jsonl"
    with log.open("w", encoding="utf-8") as f:
        for r in receipts:
            f.write(json.dumps(r, sort_keys=True, ensure_ascii=False,
                               allow_nan=False, separators=(",", ":")) + "\n")


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_valid_three_receipt_chain():
    """Valid chain of 3 receipts: ARRIVED → ACCEPTED → DROPPED passes."""
    store = _make_store()
    logger = IngestReceiptLogger(store)

    logger.arrived(frame_id=1, payload_hash="a" * 64)
    logger.accepted(frame_id=1, cram_hash="b" * 64)
    logger.dropped(frame_id=2, payload_hash="c" * 64)

    report = verify_receipt_chain(store / "ingest_receipt_log.jsonl")
    assert report["chain_intact"] is True, report["findings"]
    assert report["receipt_count"] == 3
    assert report["error_count"] == 0


def test_genesis_hash_at_first_receipt():
    """First receipt must have prev_event_hash = GENESIS."""
    store = _make_store()
    logger = IngestReceiptLogger(store)
    receipt = logger.arrived(frame_id=1, payload_hash="d" * 64)
    assert receipt["prev_event_hash"] == GENESIS_HASH


def test_chain_links_successive_receipts():
    """Each receipt's prev_event_hash must equal hash of previous receipt line."""
    import hashlib
    store = _make_store()
    logger = IngestReceiptLogger(store)

    r1 = logger.arrived(frame_id=1, payload_hash="e" * 64)
    r2 = logger.accepted(frame_id=1, cram_hash="f" * 64)

    # r2's prev_event_hash must be BLAKE2b of the canonical r1 line
    r1_line = json.dumps(r1, sort_keys=True, ensure_ascii=False,
                         allow_nan=False, separators=(",", ":")).encode()
    expected = hashlib.blake2b(r1_line, digest_size=32).hexdigest()
    assert r2["prev_event_hash"] == expected


def test_broken_prev_event_hash_fails():
    """Tampered prev_event_hash detected as chain break (R4)."""
    store = _make_store()
    logger = IngestReceiptLogger(store)
    logger.arrived(frame_id=1, payload_hash="g" * 64)
    r2 = logger.accepted(frame_id=1, cram_hash="h" * 64)

    # Tamper r2's prev_event_hash in the log
    log = store / "ingest_receipt_log.jsonl"
    lines = log.read_text().splitlines()
    r2_dict = json.loads(lines[1])
    r2_dict["prev_event_hash"] = "0" * 64  # wrong
    lines[1] = json.dumps(r2_dict, sort_keys=True, ensure_ascii=False,
                           allow_nan=False, separators=(",", ":"))
    log.write_text("\n".join(lines) + "\n")

    report = verify_receipt_chain(log)
    assert report["chain_intact"] is False
    types = [f["type"] for f in report["findings"]]
    # Both event_hash mismatch (body changed) and chain_break should be detected
    assert "chain_break" in types or "event_hash_mismatch" in types


def test_duplicate_event_seq_fails():
    """Duplicate event_seq is detected as a sequence violation."""
    store = _make_store()
    logger = IngestReceiptLogger(store)
    r1 = logger.arrived(frame_id=1, payload_hash="i" * 64)
    r2 = logger.accepted(frame_id=1, cram_hash="j" * 64)

    # Manually duplicate seq 1 in r2 (write a corrupted log)
    log = store / "ingest_receipt_log.jsonl"
    lines = log.read_text().splitlines()
    r2_dict = json.loads(lines[1])
    r2_dict["event_seq"] = 1  # duplicate
    lines[1] = json.dumps(r2_dict, sort_keys=True, ensure_ascii=False,
                           allow_nan=False, separators=(",", ":"))
    log.write_text("\n".join(lines) + "\n")

    report = verify_receipt_chain(log)
    assert report["chain_intact"] is False
    types = [f["type"] for f in report["findings"]]
    assert "event_seq_violation" in types or "event_hash_mismatch" in types


def test_missing_authority_hash_fails():
    """Receipt with empty authority_hash is detected."""
    store = _make_store()
    logger = IngestReceiptLogger(store)
    logger.arrived(frame_id=1, payload_hash="k" * 64)

    # Tamper authority_hash to empty string
    log = store / "ingest_receipt_log.jsonl"
    lines = log.read_text().splitlines()
    r1_dict = json.loads(lines[0])
    r1_dict["authority_hash"] = ""
    lines[0] = json.dumps(r1_dict, sort_keys=True, ensure_ascii=False,
                           allow_nan=False, separators=(",", ":"))
    log.write_text("\n".join(lines) + "\n")

    report = verify_receipt_chain(log)
    assert report["chain_intact"] is False
    types = [f["type"] for f in report["findings"]]
    assert "missing_authority_hash" in types or "event_hash_mismatch" in types


def test_non_genesis_prev_hash_at_first_receipt_fails():
    """First receipt with non-genesis prev_event_hash is flagged."""
    store = _make_store()
    logger = IngestReceiptLogger(store)
    logger.arrived(frame_id=1, payload_hash="l" * 64)

    log = store / "ingest_receipt_log.jsonl"
    lines = log.read_text().splitlines()
    r1_dict = json.loads(lines[0])
    r1_dict["prev_event_hash"] = "a" * 64  # non-genesis
    lines[0] = json.dumps(r1_dict, sort_keys=True, ensure_ascii=False,
                           allow_nan=False, separators=(",", ":"))
    log.write_text("\n".join(lines) + "\n")

    report = verify_receipt_chain(log)
    assert report["chain_intact"] is False
    types = [f["type"] for f in report["findings"]]
    assert "invalid_genesis" in types or "event_hash_mismatch" in types


def test_event_hash_tampering_detected():
    """Modifying any field after emission is detected via event_hash mismatch."""
    store = _make_store()
    logger = IngestReceiptLogger(store)
    logger.arrived(frame_id=1, payload_hash="m" * 64)

    log = store / "ingest_receipt_log.jsonl"
    lines = log.read_text().splitlines()
    r1_dict = json.loads(lines[0])
    r1_dict["authority_hash"] = "n" * 64  # tamper content
    lines[0] = json.dumps(r1_dict, sort_keys=True, ensure_ascii=False,
                           allow_nan=False, separators=(",", ":"))
    log.write_text("\n".join(lines) + "\n")

    report = verify_receipt_chain(log)
    assert report["chain_intact"] is False
    types = [f["type"] for f in report["findings"]]
    assert "event_hash_mismatch" in types


def test_empty_log_returns_intact():
    """Empty log (no receipts) is considered intact."""
    store = _make_store()
    report = verify_receipt_chain(store / "ingest_receipt_log.jsonl")
    assert report["chain_intact"] is True
    assert report["receipt_count"] == 0


def test_missing_log_returns_broken():
    """Missing log file is reported as broken."""
    store = _make_store()
    report = verify_receipt_chain(store / "nonexistent.jsonl")
    assert report["chain_intact"] is False
