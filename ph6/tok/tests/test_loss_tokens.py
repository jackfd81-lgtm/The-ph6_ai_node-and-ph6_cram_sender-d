"""
TOK-1.0 RLT / PLT / AHT lifecycle tests.

Covers:
  - positive paths: valid RLT, valid PLT, valid AHT, successful rehydration
  - negative paths: intact evidence produces no loss token, malformed token
    rejection, invalid parent linkage, altered/missing evidence detection,
    failed rehydration, replay-is-not-a-new-observation enforcement
  - determinism: identical inputs (including identical event_time_ms)
    produce byte-identical token ids and state hashes on repeated runs
  - boundary: Authority ZERO invariants hold for every new token class
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from ph6.cram_pu.crash_replay import CRAMWriter
from ph6.tok.evidence import (
    attempt_rehydration,
    check_cram_commit_intact,
    detect_rt_loss,
    predict_rt_risk,
)
from ph6.tok.lifecycle import (
    AHT,
    PLT,
    RLT,
    RT,
    TokenStore,
    make_aht,
    make_plt,
    make_rlt,
)
from ph6.tok.validators import validate_aht, validate_plt, validate_rlt


def _blake2b_hex(data: bytes) -> str:
    return hashlib.blake2b(data, digest_size=32).hexdigest()


def _commit_pass_frame(cram_store: Path, frame_id: int, payload: bytes) -> str:
    """Write a real CRAM PASS commit + durable marker + payload, using the
    actual Lane-1 CRAMWriter, so evidence checks run against the genuine
    on-disk format rather than a hand-rolled fixture."""
    payload_hash = _blake2b_hex(payload)
    writer = CRAMWriter(cram_store)
    verdict_record = {"verdict": "PASS", "frame_id": frame_id}
    writer.commit(frame_id, payload_hash, verdict_record)

    payloads_dir = cram_store / "payloads"
    payloads_dir.mkdir(parents=True, exist_ok=True)
    (payloads_dir / f"frame_{frame_id:010d}.bin").write_bytes(payload)
    return payload_hash


def _make_rt(frame_id: int, payload_hash: str) -> RT:
    return RT(
        token_id=f"rt_test_{frame_id}",
        cram_ref_hash=payload_hash,
        timestamp_ms=1_700_000_000_000 + frame_id,
        object_class="test_object",
        bbox=[1.0, 2.0, 3.0, 4.0],
        confidence=0.9,
    )


# ---------------------------------------------------------------------------
# Positive paths
# ---------------------------------------------------------------------------

def test_intact_evidence_produces_no_loss_token(tmp_path):
    cram_store = tmp_path / "cram_store"
    payload_hash = _commit_pass_frame(cram_store, 1, b"frame-one-bytes")
    rt = _make_rt(1, payload_hash)
    store = TokenStore(str(tmp_path / "mram-s" / "tokens"))

    status = check_cram_commit_intact(cram_store, 1, payload_hash)
    assert status.intact

    rlt = detect_rt_loss(store, rt, cram_store, frame_id=1, event_time_ms=1000)
    assert rlt is None
    assert store.rlt_store == {}
    assert store.aht_store == {}


def test_valid_rlt_and_aht_created_on_missing_cram_record(tmp_path):
    cram_store = tmp_path / "cram_store"
    payload_hash = _commit_pass_frame(cram_store, 2, b"frame-two-bytes")
    rt = _make_rt(2, payload_hash)
    store = TokenStore(str(tmp_path / "mram-s" / "tokens"))

    # Simulate loss: delete the durable CRAM commit record.
    (cram_store / "cram_0000000002.json").unlink()

    rlt = detect_rt_loss(store, rt, cram_store, frame_id=2, event_time_ms=2000)

    assert rlt is not None
    assert validate_rlt(rlt) is None
    assert rlt.lost_token_id == rt.token_id
    assert rlt.detection_reason == "cram_record_missing"
    assert rlt.token_id in store.rlt_store

    aht = store.aht_store[rlt.aht_token_id]
    assert validate_aht(aht) is None
    assert aht.anchor_for_token_id == rt.token_id
    assert aht.rehydration_status == "PENDING"


def test_valid_plt_for_at_risk_rt(tmp_path):
    cram_store = tmp_path / "cram_store"
    payload_hash = _commit_pass_frame(cram_store, 3, b"frame-three-bytes")
    rt = _make_rt(3, payload_hash)
    store = TokenStore(str(tmp_path / "mram-s" / "tokens"))

    plt = predict_rt_risk(
        store, rt, frame_id=3,
        risk_reason="storage_pressure", risk_score=0.72,
        event_time_ms=3000,
    )

    assert validate_plt(plt) is None
    assert plt.at_risk_token_id == rt.token_id
    assert plt.risk_score == 0.72
    assert plt.token_id in store.plt_store


def test_successful_rehydration_produces_new_rt_with_rehydration_provenance(tmp_path):
    cram_store = tmp_path / "cram_store"
    payload_hash = _commit_pass_frame(cram_store, 4, b"frame-four-bytes")
    rt = _make_rt(4, payload_hash)
    store = TokenStore(str(tmp_path / "mram-s" / "tokens"))

    # Simulate loss, then "recover" the commit record before rehydrating.
    commit_path = cram_store / "cram_0000000004.json"
    saved = commit_path.read_text(encoding="utf-8")
    commit_path.unlink()

    rlt = detect_rt_loss(store, rt, cram_store, frame_id=4, event_time_ms=4000)
    assert rlt is not None
    aht = store.aht_store[rlt.aht_token_id]

    commit_path.write_text(saved, encoding="utf-8")

    new_rt = attempt_rehydration(
        store, aht, cram_store, frame_id=4,
        expected_payload_hash=payload_hash, event_time_ms=4500,
    )

    assert new_rt is not None
    assert new_rt.metadata["provenance"] == "REHYDRATION"
    assert new_rt.metadata["rehydrated_from_lost_token"] == rt.token_id
    assert new_rt.token_id != rt.token_id  # never reuses the lost identity

    updated_aht = store.aht_store[aht.token_id]
    assert updated_aht.rehydration_status == "SUCCEEDED"
    assert updated_aht.rehydrated_to_token_id == new_rt.token_id

    # Original RT and RLT are untouched — loss is recorded, never erased.
    assert rt.token_id == "rt_test_4"
    assert rlt.token_id in store.rlt_store


# ---------------------------------------------------------------------------
# Negative paths
# ---------------------------------------------------------------------------

def test_hash_corrupted_payload_detected_as_loss(tmp_path):
    cram_store = tmp_path / "cram_store"
    payload_hash = _commit_pass_frame(cram_store, 5, b"frame-five-bytes")
    rt = _make_rt(5, payload_hash)
    store = TokenStore(str(tmp_path / "mram-s" / "tokens"))

    # Corrupt the payload bytes without touching the commit record.
    payload_path = cram_store / "payloads" / "frame_0000000005.bin"
    payload_path.write_bytes(b"TAMPERED-BYTES")

    rlt = detect_rt_loss(store, rt, cram_store, frame_id=5, event_time_ms=5000)
    assert rlt is not None
    assert rlt.detection_reason == "payload_hash_mismatch"


def test_missing_payload_file_detected_as_loss(tmp_path):
    cram_store = tmp_path / "cram_store"
    payload_hash = _commit_pass_frame(cram_store, 6, b"frame-six-bytes")
    rt = _make_rt(6, payload_hash)
    store = TokenStore(str(tmp_path / "mram-s" / "tokens"))

    (cram_store / "payloads" / "frame_0000000006.bin").unlink()

    rlt = detect_rt_loss(store, rt, cram_store, frame_id=6, event_time_ms=6000)
    assert rlt is not None
    assert rlt.detection_reason == "payload_missing"


def test_tampered_cram_hash_detected_as_loss(tmp_path):
    cram_store = tmp_path / "cram_store"
    payload_hash = _commit_pass_frame(cram_store, 7, b"frame-seven-bytes")
    rt = _make_rt(7, payload_hash)
    store = TokenStore(str(tmp_path / "mram-s" / "tokens"))

    commit_path = cram_store / "cram_0000000007.json"
    record = json.loads(commit_path.read_text(encoding="utf-8"))
    record["frame_id"] = 999999  # mutate body without recomputing cram_hash
    commit_path.write_text(json.dumps(record), encoding="utf-8")

    rlt = detect_rt_loss(store, rt, cram_store, frame_id=7, event_time_ms=7000)
    assert rlt is not None
    assert rlt.detection_reason == "cram_hash_mismatch"


def test_failed_rehydration_leaves_aht_pending_gap_marked_failed(tmp_path):
    cram_store = tmp_path / "cram_store"
    payload_hash = _commit_pass_frame(cram_store, 8, b"frame-eight-bytes")
    rt = _make_rt(8, payload_hash)
    store = TokenStore(str(tmp_path / "mram-s" / "tokens"))

    (cram_store / "cram_0000000008.json").unlink()
    rlt = detect_rt_loss(store, rt, cram_store, frame_id=8, event_time_ms=8000)
    aht = store.aht_store[rlt.aht_token_id]

    # Evidence is still gone — rehydration must fail, not fabricate an RT.
    result = attempt_rehydration(
        store, aht, cram_store, frame_id=8,
        expected_payload_hash=payload_hash, event_time_ms=8500,
    )

    assert result is None
    assert store.aht_store[aht.token_id].rehydration_status == "FAILED"
    # The RLT still marks the gap — nothing was silently resolved.
    assert rlt.token_id in store.rlt_store


def test_malformed_rlt_missing_detection_reason_rejected():
    rlt = RLT(
        token_id="rlt_bad", cram_ref_hash="a" * 64, timestamp_ms=1,
        lost_token_id="rt_x", frame_id=1, detection_reason="", aht_token_id="aht_x",
    )
    assert rlt.is_invalid()
    err = validate_rlt(rlt)
    assert err is not None and "detection_reason" in err


def test_malformed_plt_out_of_range_risk_score_rejected():
    plt = PLT(
        token_id="plt_bad", cram_ref_hash="a" * 64, timestamp_ms=1,
        at_risk_token_id="rt_x", frame_id=1, risk_reason="x", risk_score=5.0,
    )
    assert plt.is_invalid()
    err = validate_plt(plt)
    assert err is not None and "risk_score" in err


def test_invalid_aht_rehydration_status_rejected():
    aht = AHT(
        token_id="aht_bad", cram_ref_hash="a" * 64, timestamp_ms=1,
        anchor_for_token_id="rt_x", frame_id=1, rehydration_status="MAYBE",
    )
    assert aht.is_invalid()
    err = validate_aht(aht)
    assert err is not None and "rehydration_status" in err


def test_rlt_with_mismatched_aht_parent_linkage_rejected(tmp_path):
    store = TokenStore(str(tmp_path / "mram-s" / "tokens"))
    rlt = make_rlt(
        _make_rt(9, "a" * 64), frame_id=9, detection_reason="cram_record_missing",
        aht_id="aht_does_not_match", event_time_ms=9000,
    )
    aht = make_aht(_make_rt(10, "b" * 64), frame_id=10, event_time_ms=9000)  # different lost token

    with pytest.raises(ValueError, match="anchor_for_token_id must match"):
        store.add_rlt(rlt, aht, event_time_ms=9000)


def test_rehydrated_rt_must_declare_rehydration_provenance(tmp_path):
    cram_store = tmp_path / "cram_store"
    payload_hash = _commit_pass_frame(cram_store, 11, b"frame-eleven-bytes")
    rt = _make_rt(11, payload_hash)
    store = TokenStore(str(tmp_path / "mram-s" / "tokens"))

    (cram_store / "cram_0000000011.json").unlink()
    rlt = detect_rt_loss(store, rt, cram_store, frame_id=11, event_time_ms=11000)
    aht = store.aht_store[rlt.aht_token_id]

    bogus_rt = RT(
        token_id="rt_bogus", cram_ref_hash=payload_hash, timestamp_ms=11500,
        metadata={"provenance": "OBSERVATION"},  # replay masquerading as new observation
    )
    with pytest.raises(ValueError, match="REHYDRATION"):
        store.rehydrate_aht_to_rt(aht.token_id, bogus_rt, event_time_ms=11500)


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------

def test_rlt_aht_identity_and_state_hash_are_deterministic(tmp_path):
    cram_store = tmp_path / "cram_store"
    payload_hash = _commit_pass_frame(cram_store, 12, b"frame-twelve-bytes")
    rt = _make_rt(12, payload_hash)

    store_a = TokenStore(str(tmp_path / "run_a" / "tokens"))
    store_b = TokenStore(str(tmp_path / "run_b" / "tokens"))

    (cram_store / "cram_0000000012.json").unlink()

    rlt_a = detect_rt_loss(store_a, rt, cram_store, frame_id=12, event_time_ms=42_000)
    rlt_b = detect_rt_loss(store_b, rt, cram_store, frame_id=12, event_time_ms=42_000)

    assert rlt_a.token_id == rlt_b.token_id
    assert rlt_a.state_hash() == rlt_b.state_hash()

    aht_a = store_a.aht_store[rlt_a.aht_token_id]
    aht_b = store_b.aht_store[rlt_b.aht_token_id]
    assert aht_a.token_id == aht_b.token_id
    assert aht_a.state_hash() == aht_b.state_hash()


def test_plt_identity_deterministic_from_explicit_inputs():
    rt = _make_rt(13, "c" * 64)
    plt_1 = make_plt(rt, frame_id=13, risk_reason="storage_pressure", risk_score=0.5, event_time_ms=1)
    plt_2 = make_plt(rt, frame_id=13, risk_reason="storage_pressure", risk_score=0.5, event_time_ms=1)
    assert plt_1.token_id == plt_2.token_id
    assert plt_1.state_hash() == plt_2.state_hash()


# ---------------------------------------------------------------------------
# Boundary / Authority ZERO invariants
# ---------------------------------------------------------------------------

def test_new_token_classes_declare_authority_zero_and_advisory_only():
    rt = _make_rt(14, "d" * 64)
    rlt = make_rlt(rt, frame_id=14, detection_reason="cram_record_missing", aht_id="aht_x", event_time_ms=1)
    aht = make_aht(rt, frame_id=14, event_time_ms=1)
    plt = make_plt(rt, frame_id=14, risk_reason="x", risk_score=0.1, event_time_ms=1)

    for token in (rlt, aht, plt):
        assert token.authority == "ZERO"
        assert token.advisory_only is True
