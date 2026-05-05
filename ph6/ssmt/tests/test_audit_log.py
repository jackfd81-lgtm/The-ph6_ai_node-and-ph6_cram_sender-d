import os
import json
import pytest
from ph6.ssmt.audit_log import SSMTAuditLog, GENESIS_HASH
from ph6.ssmt.hash_chain import canon_hash
from ph6.ssmt.models import SwarmPacket


def _packet(swarm_id="S1", ts=1700000001.0):
    return SwarmPacket(
        swarm_id=swarm_id, role="active_memory", authority="NONE",
        lane="LANE_2_ADVISORY", ssmt_version="1.0", ttl_seconds=30,
        output_type="advisory", advisory_payload={"k": "v"},
        drift_score=0, confidence_fp=95,
        created_at=ts, dependency_for_replay=False,
    )


def test_audit_boundary_enforced():
    with pytest.raises(RuntimeError, match="boundary"):
        SSMTAuditLog(root="/tmp/bad_path/")


def test_first_event_links_to_genesis(tmp_path):
    root = str(tmp_path) + "/swarms/"
    log = SSMTAuditLog.__new__(SSMTAuditLog)
    log.root = root
    log.audit_path = os.path.join(root, "ssmt_audit.jsonl")
    os.makedirs(root, exist_ok=True)

    event = log.append_packet_event(_packet(), "/var/ph6/mram-s/swarms/S1_x.json")
    assert event["prev_event_hash"] == GENESIS_HASH
    assert event["event_seq"] == 1


def test_second_event_chains_to_first(tmp_path):
    root = str(tmp_path) + "/swarms/"
    log = SSMTAuditLog.__new__(SSMTAuditLog)
    log.root = root
    log.audit_path = os.path.join(root, "ssmt_audit.jsonl")
    os.makedirs(root, exist_ok=True)

    e1 = log.append_packet_event(_packet("S1"), "/var/ph6/mram-s/swarms/S1_1.json")
    e2 = log.append_packet_event(_packet("S2"), "/var/ph6/mram-s/swarms/S2_1.json")
    assert e2["prev_event_hash"] == e1["event_hash"]
    assert e2["event_seq"] == 2


def test_event_authority_is_none(tmp_path):
    root = str(tmp_path) + "/swarms/"
    log = SSMTAuditLog.__new__(SSMTAuditLog)
    log.root = root
    log.audit_path = os.path.join(root, "ssmt_audit.jsonl")
    os.makedirs(root, exist_ok=True)

    event = log.append_packet_event(_packet(), "/var/ph6/mram-s/swarms/S1_x.json")
    assert event["authority"] == "NONE"
    assert event["lane"] == "LANE_2_ADVISORY"
    assert event["dependency_for_replay"] is False


def test_audit_file_is_valid_jsonl(tmp_path):
    root = str(tmp_path) + "/swarms/"
    log = SSMTAuditLog.__new__(SSMTAuditLog)
    log.root = root
    log.audit_path = os.path.join(root, "ssmt_audit.jsonl")
    os.makedirs(root, exist_ok=True)

    for i in range(3):
        log.append_packet_event(_packet(f"S{i+1}"), f"/var/ph6/mram-s/swarms/S{i+1}_x.json")

    with open(log.audit_path) as f:
        lines = [l.strip() for l in f if l.strip()]
    assert len(lines) == 3
    for line in lines:
        json.loads(line)
