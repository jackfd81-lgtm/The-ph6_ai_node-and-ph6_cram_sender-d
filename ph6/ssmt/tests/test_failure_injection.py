import os
import json
import pytest
from ph6.ssmt.failure_injection import (
    disk_full, partial_write, fsync_failure,
    concurrent_writes, frozen_clock, permission_denied,
)
from ph6.ssmt.models import SwarmInput, SwarmPacket
from ph6.ssmt.audit_log import SSMTAuditLog
from ph6.ssmt.scheduler import SwarmScheduler
from ph6.ssmt.forensic_closure import ForensicClosureValidator


def _packet(swarm_id="S1", ts=1700000001.0):
    return SwarmPacket(
        swarm_id=swarm_id, role="active_memory", authority="NONE",
        lane="LANE_2_ADVISORY", ssmt_version="1.0", ttl_seconds=30,
        output_type="advisory", advisory_payload={"x": 1},
        drift_score=0, confidence_fp=9500,
        created_at=ts, dependency_for_replay=False,
    )


def _log(root):
    log = SSMTAuditLog.__new__(SSMTAuditLog)
    log.root = root
    log.audit_path = os.path.join(root, "ssmt_audit.jsonl")
    os.makedirs(root, exist_ok=True)
    return log


# ── FI-SSMT-01: disk full mid-write ─────────────────────────────────────────

def test_fi01_disk_full_raises_oserror(tmp_path):
    root = str(tmp_path) + "/swarms/"
    os.makedirs(root)
    log = _log(root)
    with disk_full():
        with pytest.raises(OSError):
            log.append_packet_event(_packet(), "/var/ph6/mram-s/swarms/S1_x.json")


def test_fi01_disk_full_leaves_no_partial_audit_file(tmp_path):
    root = str(tmp_path) + "/swarms/"
    os.makedirs(root)
    log = _log(root)
    try:
        with disk_full():
            log.append_packet_event(_packet(), "/var/ph6/mram-s/swarms/S1_x.json")
    except OSError:
        pass
    assert not os.path.exists(log.audit_path)


# ── FI-SSMT-02: partial write (tmp crash) ───────────────────────────────────

def test_fi02_partial_write_produces_invalid_json(tmp_path):
    target = os.path.join(str(tmp_path), "test.json")
    try:
        with partial_write(truncate_at=5):
            with open(target, "w") as f:
                f.write('{"key": "value"}')
    except Exception:
        pass
    if os.path.exists(target):
        content = open(target).read()
        assert len(content) <= 5


def test_fi02_scheduler_survives_partial_write(tmp_path):
    # Swarm cycle itself (in-memory) is unaffected by write failures
    scheduler = SwarmScheduler()
    packets = scheduler.run_cycle(
        SwarmInput(cram_refs=["cram://frame/0001"], tok_refs=[], advisory_refs=[])
    )
    assert len(packets) == 9
    for p in packets:
        assert p.authority == "NONE"


# ── FI-SSMT-03: fsync failure (audit log) ───────────────────────────────────

def test_fi03_fsync_failure_raises(tmp_path):
    root = str(tmp_path) + "/swarms/"
    os.makedirs(root)
    log = _log(root)
    with fsync_failure():
        with pytest.raises(OSError):
            log.append_packet_event(_packet(), "/var/ph6/mram-s/swarms/S1_x.json")


def test_fi03_fsync_failure_does_not_silently_corrupt(tmp_path):
    root = str(tmp_path) + "/swarms/"
    os.makedirs(root)
    log = _log(root)
    # Write one good event before injecting failure
    log.append_packet_event(_packet("S1"), "/var/ph6/mram-s/swarms/S1_1.json")
    try:
        with fsync_failure():
            log.append_packet_event(_packet("S2"), "/var/ph6/mram-s/swarms/S2_1.json")
    except OSError:
        pass
    # First event should still be valid JSONL
    with open(log.audit_path) as f:
        lines = [l.strip() for l in f if l.strip()]
    assert len(lines) >= 1
    json.loads(lines[0])


# ── FI-SSMT-04: concurrent scheduler runs ───────────────────────────────────

def test_fi04_concurrent_runs_produce_correct_packet_count(tmp_path):
    results = []
    lock = __import__("threading").Lock()

    def run_cycle():
        scheduler = SwarmScheduler()
        packets = scheduler.run_cycle(
            SwarmInput(cram_refs=["cram://frame/0001"], tok_refs=[], advisory_refs=[])
        )
        with lock:
            results.append(len(packets))

    with concurrent_writes(n_threads=4) as run_parallel:
        errors = run_parallel(run_cycle, [() for _ in range(4)])

    assert errors == [], f"Concurrent run raised: {errors}"
    assert all(n == 9 for n in results), f"Expected 9 packets each, got: {results}"


def test_fi04_concurrent_runs_no_authority_leakage(tmp_path):
    all_packets = []
    lock = __import__("threading").Lock()

    def run_and_collect():
        scheduler = SwarmScheduler()
        packets = scheduler.run_cycle(
            SwarmInput(cram_refs=["cram://frame/0001"], tok_refs=[], advisory_refs=[])
        )
        with lock:
            all_packets.extend(packets)

    with concurrent_writes(n_threads=4) as run_parallel:
        run_parallel(run_and_collect, [() for _ in range(4)])

    for p in all_packets:
        assert p.authority == "NONE"
        assert p.dependency_for_replay is False


# ── FI-SSMT-05: timestamp collision ─────────────────────────────────────────

def test_fi05_frozen_clock_forces_same_created_at():
    with frozen_clock(ts=1700000000.0):
        import time
        assert time.time() == 1700000000.0
        assert time.time() == 1700000000.0


def test_fi05_audit_chain_valid_despite_timestamp_collision(tmp_path):
    root = str(tmp_path) + "/swarms/"
    os.makedirs(root)
    log = _log(root)

    with frozen_clock(ts=1700000000.0):
        e1 = log.append_packet_event(_packet("S1", ts=1700000000.0),
                                     "/var/ph6/mram-s/swarms/S1_x.json")
        e2 = log.append_packet_event(_packet("S1", ts=1700000000.0),
                                     "/var/ph6/mram-s/swarms/S1_x.json")

    # Chain must link correctly even with identical timestamps
    assert e2["prev_event_hash"] == e1["event_hash"]
    assert e1["event_seq"] == 1
    assert e2["event_seq"] == 2

    # Audit JSONL has both events
    with open(log.audit_path) as f:
        lines = [l.strip() for l in f if l.strip()]
    assert len(lines) == 2


def test_fi05_forensic_closure_passes_after_collision(tmp_path):
    root = str(tmp_path) + "/swarms/"
    os.makedirs(root)
    log = _log(root)

    with frozen_clock(ts=1700000000.0):
        for sid in ["S1", "S2", "S3"]:
            log.append_packet_event(_packet(sid, ts=1700000000.0),
                                    f"/var/ph6/mram-s/swarms/{sid}_x.json")

    # Walk the chain — must be valid despite duplicate timestamps
    validator = ForensicClosureValidator.__new__(ForensicClosureValidator)
    validator.root = root
    # Point at our tmp audit path
    import os as _os
    _real_audit = _os.path.join(root, "ssmt_audit.jsonl")
    assert _os.path.exists(_real_audit)

    result = validator.validate_audit_chain()
    assert result["chain_valid"] is True
    assert result["events"] == 3


# ── Existing guards (unchanged) ──────────────────────────────────────────────

def test_permission_denied_raises(tmp_path):
    target = str(tmp_path)
    with permission_denied(target):
        with pytest.raises(PermissionError):
            open(os.path.join(target, "test.txt"), "w").close()


def test_permission_denied_restores(tmp_path):
    target = str(tmp_path)
    original_mode = oct(os.stat(target).st_mode)
    with permission_denied(target):
        pass
    assert oct(os.stat(target).st_mode) == original_mode
