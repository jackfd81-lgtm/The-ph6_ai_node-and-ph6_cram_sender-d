from ph6.ssmt.hash_chain import (
    canonical_dumps, canon_hash, chain_event, HASH_LABEL
)
from ph6.ssmt.models import SwarmPacket
import time


def _sample_packet():
    return SwarmPacket(
        swarm_id="S1", role="active_memory", authority="NONE",
        lane="LANE_2_ADVISORY", ssmt_version="1.0", ttl_seconds=30,
        output_type="advisory", advisory_payload={"k": "v"},
        drift_score=0, confidence_fp=95,
        created_at=1700000000.0, dependency_for_replay=False,
    )


def test_canonical_dumps_is_deterministic():
    obj = {"z": 1, "a": 2, "m": 3}
    assert canonical_dumps(obj) == canonical_dumps(obj)
    assert '"a":2' in canonical_dumps(obj)


def test_canonical_dumps_sorts_keys():
    a = canonical_dumps({"z": 1, "a": 2})
    b = canonical_dumps({"a": 2, "z": 1})
    assert a == b


def test_canon_hash_is_64_hex_chars():
    h = canon_hash({"x": 1})
    assert len(h) == 64
    assert all(c in "0123456789abcdef" for c in h)


def test_canon_hash_dataclass():
    p = _sample_packet()
    h = canon_hash(p)
    assert len(h) == 64


def test_canon_hash_changes_on_mutation():
    h1 = canon_hash({"x": 1})
    h2 = canon_hash({"x": 2})
    assert h1 != h2


def test_chain_event_links_correctly():
    prev = "a" * 64
    event = {"event_seq": 1, "data": "hello"}
    chained = chain_event(event, prev)
    assert chained["prev_event_hash"] == prev
    assert len(chained["event_hash"]) == 64


def test_chain_event_hash_excludes_itself():
    prev = "b" * 64
    e1 = chain_event({"data": "x"}, prev)
    e2 = chain_event({"data": "x"}, prev)
    assert e1["event_hash"] == e2["event_hash"]


def test_chain_breaks_on_tamper():
    prev = "0" * 64
    chained = chain_event({"data": "original"}, prev)
    chained["data"] = "tampered"
    recomputed = canon_hash({k: v for k, v in chained.items() if k != "event_hash"})
    assert recomputed != chained["event_hash"]
