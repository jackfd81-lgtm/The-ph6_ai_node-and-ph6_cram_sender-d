import os
import json
import pytest
from ph6.ssmt.failure_injection import (
    disk_full, permission_denied, partial_write, frozen_clock, fsync_failure
)
from ph6.ssmt.models import SwarmPacket
from ph6.ssmt.audit_log import SSMTAuditLog


def _packet():
    return SwarmPacket(
        swarm_id="S1", role="active_memory", authority="NONE",
        lane="LANE_2_ADVISORY", ssmt_version="1.0", ttl_seconds=30,
        output_type="advisory", advisory_payload={"x": 1},
        drift_score=0, confidence_fp=95,
        created_at=1700000000.0, dependency_for_replay=False,
    )


def _log(root):
    log = SSMTAuditLog.__new__(SSMTAuditLog)
    log.root = root
    log.audit_path = os.path.join(root, "ssmt_audit.jsonl")
    os.makedirs(root, exist_ok=True)
    return log


def test_disk_full_raises_oserror(tmp_path):
    root = str(tmp_path) + "/swarms/"
    os.makedirs(root)
    log = _log(root)
    with disk_full():
        with pytest.raises(OSError):
            log.append_packet_event(_packet(), "/var/ph6/mram-s/swarms/S1_x.json")


def test_disk_full_leaves_no_partial_file(tmp_path):
    root = str(tmp_path) + "/swarms/"
    os.makedirs(root)
    log = _log(root)
    try:
        with disk_full():
            log.append_packet_event(_packet(), "/var/ph6/mram-s/swarms/S1_x.json")
    except OSError:
        pass
    assert not os.path.exists(log.audit_path)


def test_frozen_clock_forces_collision():
    import time
    with frozen_clock(ts=1234567890.0):
        assert time.time() == 1234567890.0
        assert time.time() == 1234567890.0


def test_fsync_failure_raises(tmp_path):
    root = str(tmp_path) + "/swarms/"
    os.makedirs(root)
    log = _log(root)
    with fsync_failure():
        with pytest.raises(OSError):
            log.append_packet_event(_packet(), "/var/ph6/mram-s/swarms/S1_x.json")


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
