import pytest

from ph6_l2_expand.lmpq_proposed.life_cram_bcv2 import BCV2_SCHEMA, build_bcv2, write_bcv2


def test_valid_bcv2_bundle():
    bundle = build_bcv2(
        experience_id="exp_test",
        cram_refs=["cram_a", "cram_b"],
        token_ids=["tok_2", "tok_1"],
        token_types_present=["VLT", "RT"],
        event_window_start_ms=1000,
        event_window_end_ms=2000,
    )
    assert bundle["schema"] == BCV2_SCHEMA
    assert bundle["authority"] == "ZERO"
    assert bundle["advisory_only"] is True
    # sorted deterministically regardless of input order
    assert bundle["token_ids"] == ["tok_1", "tok_2"]
    assert bundle["token_types_present"] == ["RT", "VLT"]
    assert bundle["constraints"]["may_issue_verdict"] is False


def test_bcv2_deterministic_id():
    a = build_bcv2("exp", ["c1"], ["t1"], ["RT"], 0, 100)
    b = build_bcv2("exp", ["c1"], ["t1"], ["RT"], 0, 999)  # window differs, id inputs don't
    assert a["bcv_id"] == b["bcv_id"]


def test_bcv2_rejects_missing_experience_id():
    with pytest.raises(ValueError, match="experience_id"):
        build_bcv2("", ["c1"], ["t1"], ["RT"], 0, 100)


def test_bcv2_rejects_missing_cram_refs():
    with pytest.raises(ValueError, match="missing source evidence"):
        build_bcv2("exp", [], ["t1"], ["RT"], 0, 100)


def test_bcv2_rejects_inverted_event_window():
    with pytest.raises(ValueError, match="event_window"):
        build_bcv2("exp", ["c1"], ["t1"], ["RT"], 5000, 1000)


def test_bcv2_write_and_quarantine(tmp_path):
    bundle = build_bcv2("exp", ["c1"], ["t1"], ["RT"], 0, 100)
    path, status, violations = write_bcv2(tmp_path, bundle)
    assert status == "WRITTEN"
    assert path.exists()

    bad_bundle = dict(bundle)
    bad_bundle["verdict"] = "PASS"
    path2, status2, violations2 = write_bcv2(tmp_path, bad_bundle)
    assert status2 == "QUARANTINED"
    assert violations2
