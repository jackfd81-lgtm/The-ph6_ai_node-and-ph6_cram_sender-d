import os
import json
import pytest
from ph6.ssmt.replay_receipt import ReplayReceiptWriter, ManifestWriter
from ph6.ssmt.models import SwarmPacket


def _packet(swarm_id="S1"):
    return SwarmPacket(
        swarm_id=swarm_id, role="test", authority="NONE",
        lane="LANE_2_ADVISORY", ssmt_version="1.0", ttl_seconds=30,
        output_type="advisory", advisory_payload={},
        drift_score=0, confidence_fp=90,
        created_at=1700000000.0, dependency_for_replay=False,
    )


def _make_root(tmp_path):
    root = str(tmp_path) + "/swarms/"
    os.makedirs(root, exist_ok=True)
    return root


def _writer(root):
    w = ReplayReceiptWriter.__new__(ReplayReceiptWriter)
    w.root = root
    return w


def test_receipt_boundary_enforced():
    with pytest.raises(RuntimeError, match="boundary"):
        ReplayReceiptWriter(root="/tmp/bad/")


def test_receipt_written_and_parseable(tmp_path):
    root = _make_root(tmp_path)
    writer = _writer(root)
    packets = [_packet("S1"), _packet("S2")]
    path = writer.write(packets, {"passed": True})
    assert os.path.exists(path)
    with open(path) as f:
        r = json.load(f)
    assert r["packets_validated"] == 2
    assert r["all_independent"] is True
    assert r["schema"] == "ph6.ssmt.replay_receipt.v1"


def test_receipt_hash_verifies(tmp_path):
    root = _make_root(tmp_path)
    writer = _writer(root)
    path = writer.write([_packet()], {"passed": True})
    assert writer.verify(path) is True


def test_tampered_receipt_fails_verify(tmp_path):
    root = _make_root(tmp_path)
    writer = _writer(root)
    path = writer.write([_packet()], {"passed": True})

    with open(path, "r") as f:
        data = json.load(f)
    data["packets_validated"] = 999
    with open(path, "w") as f:
        json.dump(data, f)

    assert writer.verify(path) is False


def test_manifest_written(tmp_path):
    root = _make_root(tmp_path)
    mw = ManifestWriter.__new__(ManifestWriter)
    mw.root = root
    path = mw.write("cycle-123", "/some/receipt.json", "/some/audit.jsonl", 9)
    assert os.path.exists(path)
    with open(path) as f:
        m = json.load(f)
    assert m["cycle_id"] == "cycle-123"
    assert m["packet_count"] == 9
    assert m["schema"] == "ph6.ssmt.manifest.v1"
