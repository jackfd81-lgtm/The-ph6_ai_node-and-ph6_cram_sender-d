import json

from ph6_l2_expand.boundary_guard import classify
from ph6_l2_expand.experimental import mock_ai_client
from ph6_l2_expand.workers import reference_worker


def test_reference_worker_strips_lane1_only_fields(tmp_path):
    raw = {
        "object_id": "internal_000001",
        "motion_fraction": 0.42,
        "verdict": "PASS",
        "threshold": 0.5,
        "evidence_packet": {"hash": "deadbeef"},
        "authority_chain": "abc",
        "replay_dependency": "xyz",
    }
    p = tmp_path / "obj.json"
    p.write_text(json.dumps(raw), encoding="utf-8")

    object_id, source_object = reference_worker.load_source(str(p))

    assert object_id == "internal_000001"
    assert "verdict" not in source_object
    assert "threshold" not in source_object
    assert "evidence_packet" not in source_object
    assert "authority_chain" not in source_object
    assert "replay_dependency" not in source_object
    assert "motion_fraction" in source_object


def test_token_map_never_contains_evidence_packet(sample_source_object):
    advisory = mock_ai_client.generate("internal_000001", sample_source_object, cycle=3, token_map_before_dict={})

    status, violations = classify(advisory)
    assert status == "OK", violations

    for token in advisory["token_map_after"].values():
        assert "evidence_packet" not in {k.lower() for k in token.keys()}
        assert "evidencepacket" not in {k.lower() for k in token.keys()}
        # refs are plain id strings, never nested authority objects
        for ref in token["refs"]:
            assert isinstance(ref, str)
