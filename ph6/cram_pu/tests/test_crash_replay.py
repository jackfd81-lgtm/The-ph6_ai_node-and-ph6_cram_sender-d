"""
Tests for CRAM-PU crash/replay validation.

Proves all six invariants from PH6-ARCH-CRAM-PU-v1.1:
  1. No torn authoritative final files
  2. No silent PASS loss
  3. DROP shedding is policy-bound and logged
  4. Advisory shedding never affects Lane-1
  5. CRAM history is replay-consistent
  6. RSYNC export is never blocked
"""

import json
import os
import time
import pytest
from pathlib import Path

from ph6.cram_pu.crash_replay import (
    CRAMPaths,
    CRAMWriter,
    SheddingLogger,
    CrashReplayValidator,
    blake2b256,
    check_torn_files,
    check_continuity,
    check_pass_loss,
    check_drop_shedding,
    check_advisory_isolation,
    check_cram_integrity,
    check_rsync_health,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def store(tmp_path):
    cram = tmp_path / "cram-0"
    mram = tmp_path / "mram-s" / "swarms"
    cram.mkdir(parents=True)
    mram.mkdir(parents=True)
    return CRAMPaths(cram_store=cram, mram_s=mram)


def _write_jsonl(path: Path, records: list):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, sort_keys=True, separators=(",", ":"),
                               allow_nan=False, ensure_ascii=False))
            f.write("\n")


def _departure(frame_id: int, payload_hash: str) -> dict:
    return {
        "schema": "ph6.raw_departure.v1",
        "source_node": "RAW_PI5",
        "dest_node": "CRAM_PU",
        "frame_id": frame_id,
        "payload_hash": payload_hash,
        "payload_bytes": 921600,
        "authority": "NONE",
        "timestamp_utc": "2026-05-05T00:00:00Z",
    }


def _arrival(frame_id: int, payload_hash: str, hash_match: bool = True) -> dict:
    return {
        "schema": "ph6.raw_arrival.v1",
        "source_node": "RAW_PI5",
        "receiver_node": "CRAM_PU",
        "frame_id": frame_id,
        "payload_hash": payload_hash,
        "hash_match": hash_match,
        "authority": "LANE_1_RECEIVER",
    }


def _verdict(frame_id: int, verdict: str) -> dict:
    return {
        "schema": "ph6.pseudo_verdict.v1",
        "frame_id": frame_id,
        "verdict": verdict,
        "metrics": {"entropy": 3.1, "laplacian_var": 80.0, "motion_fraction": 0.02},
        "reasons": [],
        "authority": "LANE_1",
    }


# ---------------------------------------------------------------------------
# 1. Torn files
# ---------------------------------------------------------------------------

class TestTornFiles:
    def test_clean_store_passes(self, store):
        result = check_torn_files(store)
        assert result.ok
        assert result.torn == []

    def test_tmp_file_detected(self, store):
        (store.cram_store / "cram_0000000001.json.tmp").write_text("{}")
        result = check_torn_files(store)
        assert not result.ok
        assert len(result.torn) == 1

    def test_multiple_tmp_files_all_reported(self, store):
        for i in range(3):
            (store.cram_store / f"cram_{i:010d}.json.tmp").write_text("{}")
        result = check_torn_files(store)
        assert len(result.torn) == 3

    def test_final_file_not_flagged(self, store):
        (store.cram_store / "cram_0000000001.json").write_text("{}")
        result = check_torn_files(store)
        assert result.ok


# ---------------------------------------------------------------------------
# 2. Transfer continuity
# ---------------------------------------------------------------------------

class TestContinuity:
    def test_matched_pair_passes(self, store):
        h = "blake2b256:" + "a" * 64
        _write_jsonl(store.departure_log, [_departure(1, h)])
        _write_jsonl(store.arrival_log, [_arrival(1, h)])
        result = check_continuity(store)
        assert result.ok
        assert result.matched == 1

    def test_orphan_departure_detected(self, store):
        h = "blake2b256:" + "b" * 64
        _write_jsonl(store.departure_log, [_departure(1, h)])
        _write_jsonl(store.arrival_log, [])
        result = check_continuity(store)
        assert not result.ok
        assert len(result.orphan_departures) == 1

    def test_orphan_arrival_detected(self, store):
        h = "blake2b256:" + "c" * 64
        _write_jsonl(store.departure_log, [])
        _write_jsonl(store.arrival_log, [_arrival(1, h)])
        result = check_continuity(store)
        assert not result.ok
        assert len(result.orphan_arrivals) == 1

    def test_hash_mismatch_detected(self, store):
        h1 = "blake2b256:" + "d" * 64
        h2 = "blake2b256:" + "e" * 64
        _write_jsonl(store.departure_log, [_departure(1, h1)])
        _write_jsonl(store.arrival_log, [_arrival(1, h2)])
        result = check_continuity(store)
        assert not result.ok
        assert len(result.hash_mismatches) == 1

    def test_empty_logs_pass(self, store):
        result = check_continuity(store)
        assert result.ok
        assert result.matched == 0

    def test_multiple_frames_all_matched(self, store):
        deps = [_departure(i, f"h{i:064d}") for i in range(5)]
        arrs = [_arrival(i, f"h{i:064d}") for i in range(5)]
        _write_jsonl(store.departure_log, deps)
        _write_jsonl(store.arrival_log, arrs)
        result = check_continuity(store)
        assert result.ok
        assert result.matched == 5


# ---------------------------------------------------------------------------
# 3. Silent PASS loss
# ---------------------------------------------------------------------------

class TestPassLoss:
    def test_pass_with_cram_commit_passes(self, store):
        writer = CRAMWriter(store.cram_store)
        h = "x" * 64
        writer.commit(1, h, _verdict(1, "PASS"))
        _write_jsonl(store.verdict_log, [_verdict(1, "PASS")])
        result = check_pass_loss(store)
        assert result.ok
        assert result.pass_verdicts == 1
        assert result.cram_commits == 1

    def test_pass_without_cram_commit_detected(self, store):
        _write_jsonl(store.verdict_log, [_verdict(1, "PASS")])
        result = check_pass_loss(store)
        assert not result.ok
        assert 1 in result.silent_losses

    def test_drop_verdict_not_required_in_cram(self, store):
        _write_jsonl(store.verdict_log, [_verdict(1, "DROP")])
        result = check_pass_loss(store)
        assert result.ok
        assert result.pass_verdicts == 0

    def test_multiple_passes_all_must_commit(self, store):
        writer = CRAMWriter(store.cram_store)
        for fid in range(1, 4):
            writer.commit(fid, "h" * 64, _verdict(fid, "PASS"))
        verdicts = [_verdict(fid, "PASS") for fid in range(1, 5)]  # 4 verdicts, 3 commits
        _write_jsonl(store.verdict_log, verdicts)
        result = check_pass_loss(store)
        assert not result.ok
        assert 4 in result.silent_losses


# ---------------------------------------------------------------------------
# 4. DROP shedding audit
# ---------------------------------------------------------------------------

class TestDropShedding:
    def test_logged_drop_passes(self, store):
        _write_jsonl(store.verdict_log, [_verdict(1, "DROP")])
        logger = SheddingLogger(store)
        logger.log(1, policy_ref="PH6-DROP-POLICY-v1", reason="below entropy threshold")
        result = check_drop_shedding(store)
        assert result.ok
        assert result.total_drops == 1
        assert result.logged_drops == 1

    def test_unlogged_drop_detected(self, store):
        _write_jsonl(store.verdict_log, [_verdict(1, "DROP")])
        result = check_drop_shedding(store)
        assert not result.ok
        assert 1 in result.unlogged_drops

    def test_pass_not_checked_in_shedding(self, store):
        _write_jsonl(store.verdict_log, [_verdict(1, "PASS")])
        result = check_drop_shedding(store)
        assert result.ok
        assert result.total_drops == 0

    def test_mixed_verdicts_drop_must_be_logged(self, store):
        verdicts = [_verdict(1, "PASS"), _verdict(2, "DROP"), _verdict(3, "DROP")]
        _write_jsonl(store.verdict_log, verdicts)
        logger = SheddingLogger(store)
        logger.log(2, policy_ref="PH6-DROP-POLICY-v1", reason="blur too low")
        # frame 3 DROP not logged
        result = check_drop_shedding(store)
        assert not result.ok
        assert 3 in result.unlogged_drops
        assert 2 not in result.unlogged_drops


# ---------------------------------------------------------------------------
# 5. Advisory isolation
# ---------------------------------------------------------------------------

class TestAdvisoryIsolation:
    def test_clean_advisory_packets_pass(self, store):
        packet = {
            "schema": "ph6.soso_token.v1",
            "frame_id": 1,
            "token_type": "VDT",
            "authority": "NONE",
            "store": "MRAM-S",
        }
        (store.mram_s / "S1_123.json").write_text(
            json.dumps(packet, sort_keys=True, separators=(",", ":"))
        )
        result = check_advisory_isolation(store)
        assert result.ok

    def test_advisory_packet_referencing_cram_store_detected(self, store):
        packet = {
            "schema": "ph6.soso_token.v1",
            "debug_path": str(store.cram_store),  # forbidden: Lane-1 path in advisory
            "authority": "NONE",
        }
        (store.mram_s / "S2_456.json").write_text(
            json.dumps(packet, sort_keys=True, separators=(",", ":"))
        )
        result = check_advisory_isolation(store)
        assert not result.ok
        assert len(result.lane1_paths_touched_by_advisory) == 1

    def test_empty_mram_s_passes(self, store):
        result = check_advisory_isolation(store)
        assert result.ok


# ---------------------------------------------------------------------------
# 6. CRAM integrity (hash + chain)
# ---------------------------------------------------------------------------

class TestCRAMIntegrity:
    def test_empty_store_passes(self, store):
        result = check_cram_integrity(store)
        assert result.ok
        assert result.total_files == 0

    def test_valid_chain_passes(self, store):
        writer = CRAMWriter(store.cram_store)
        for fid in range(1, 4):
            writer.commit(fid, "h" * 64, _verdict(fid, "PASS"))
        result = check_cram_integrity(store)
        assert result.ok
        assert result.total_files == 3

    def test_tampered_file_detected(self, store):
        writer = CRAMWriter(store.cram_store)
        writer.commit(1, "h" * 64, _verdict(1, "PASS"))
        cram_file = next(store.cram_store.glob("cram_*.json"))
        rec = json.loads(cram_file.read_text())
        rec["payload_hash"] = "tampered"
        cram_file.write_text(json.dumps(rec, sort_keys=True, separators=(",", ":")))
        result = check_cram_integrity(store)
        assert not result.ok
        assert len(result.hash_failures) == 1

    def test_broken_prev_hash_chain_detected(self, store):
        writer = CRAMWriter(store.cram_store)
        writer.commit(1, "h" * 64, _verdict(1, "PASS"))
        writer.commit(2, "h" * 64, _verdict(2, "PASS"))
        second_file = sorted(store.cram_store.glob("cram_*.json"))[1]
        rec = json.loads(second_file.read_text())
        # Break the chain: set prev_cram_hash to something wrong
        rec["prev_cram_hash"] = "0" * 64
        rec["cram_hash"] = blake2b256({k: v for k, v in rec.items() if k != "cram_hash"})
        second_file.write_text(json.dumps(rec, sort_keys=True, separators=(",", ":")))
        result = check_cram_integrity(store)
        assert not result.ok
        assert len(result.prev_hash_mismatches) >= 1


# ---------------------------------------------------------------------------
# 7. RSYNC health
# ---------------------------------------------------------------------------

class TestRSYNCHealth:
    def test_no_queue_file_passes(self, store):
        result = check_rsync_health(store)
        assert result.ok

    def test_queue_with_no_blocked_entry_passes(self, store):
        entry = {"schema": "ph6.rsync_queue.v1", "frame_id": 1, "status": "QUEUED"}
        _write_jsonl(store.rsync_queue, [entry])
        result = check_rsync_health(store)
        assert result.ok

    def test_blocked_entry_detected(self, store):
        entry = {
            "schema": "ph6.rsync_queue.v1",
            "frame_id": 1,
            "blocked_by": "PSEUDO_backpressure",
        }
        _write_jsonl(store.rsync_queue, [entry])
        result = check_rsync_health(store)
        assert not result.ok
        assert result.blocked
        assert "PSEUDO" in result.reason


# ---------------------------------------------------------------------------
# 8. CRAMWriter contract
# ---------------------------------------------------------------------------

class TestCRAMWriter:
    def test_atomic_write_no_tmp_left(self, store):
        writer = CRAMWriter(store.cram_store)
        writer.commit(1, "h" * 64, _verdict(1, "PASS"))
        tmp_files = list(store.cram_store.glob("*.tmp"))
        assert tmp_files == []

    def test_drop_verdict_rejected(self, store):
        writer = CRAMWriter(store.cram_store)
        with pytest.raises(ValueError, match="Only PASS"):
            writer.commit(1, "h" * 64, _verdict(1, "DROP"))

    def test_chain_links_correctly(self, store):
        writer = CRAMWriter(store.cram_store)
        r1 = writer.commit(1, "h" * 64, _verdict(1, "PASS"))
        r2 = writer.commit(2, "h" * 64, _verdict(2, "PASS"))
        assert r2["prev_cram_hash"] == r1["cram_hash"]

    def test_genesis_prev_hash(self, store):
        writer = CRAMWriter(store.cram_store)
        r1 = writer.commit(1, "h" * 64, _verdict(1, "PASS"))
        assert r1["prev_cram_hash"] == "0" * 64


# ---------------------------------------------------------------------------
# 9. Full validator
# ---------------------------------------------------------------------------

class TestCrashReplayValidator:
    def test_clean_system_passes(self, store):
        h = "a" * 64
        _write_jsonl(store.departure_log, [_departure(1, h)])
        _write_jsonl(store.arrival_log, [_arrival(1, h)])
        _write_jsonl(store.verdict_log, [_verdict(1, "PASS")])
        writer = CRAMWriter(store.cram_store)
        writer.commit(1, h, _verdict(1, "PASS"))
        report = CrashReplayValidator(store).run()
        assert report.verdict == "PASS"

    def test_torn_file_causes_fail(self, store):
        (store.cram_store / "cram_0000000001.json.tmp").write_text("{}")
        report = CrashReplayValidator(store).run()
        assert report.verdict == "FAIL"

    def test_silent_pass_loss_causes_fail(self, store):
        _write_jsonl(store.verdict_log, [_verdict(1, "PASS")])
        # No CRAM commit
        report = CrashReplayValidator(store).run()
        assert report.verdict == "FAIL"

    def test_unlogged_drop_causes_fail(self, store):
        _write_jsonl(store.verdict_log, [_verdict(1, "DROP")])
        # No shedding log entry
        report = CrashReplayValidator(store).run()
        assert report.verdict == "FAIL"

    def test_summary_contains_all_checks(self, store):
        report = CrashReplayValidator(store).run()
        summary = report.summary()
        assert "[1]" in summary
        assert "[2]" in summary
        assert "[3]" in summary
        assert "[4]" in summary
        assert "[5]" in summary
        assert "[6]" in summary
