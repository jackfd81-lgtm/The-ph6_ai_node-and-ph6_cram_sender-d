import pytest

from ph6.hw_hooks.pico_advisory import (
    PRESENCE_STATUS_VALUES,
    build_presence_record,
    classify_presence,
    intake_sample,
)

NOW = "2026-06-08T11:00:00Z"


def test_classify_presence_pure_and_advisory_only():
    assert classify_presence(None) == "UNKNOWN"
    assert classify_presence([]) == "NOT_PRESENT"
    assert classify_presence(["/dev/ttyACM0"]) == "PRESENT"
    for paths in (None, [], ["/dev/ttyACM0"]):
        assert classify_presence(paths) in PRESENCE_STATUS_VALUES


def test_presence_record_is_read_only_and_advisory():
    rec = build_presence_record("pico-01", ["/dev/ttyACM0"], NOW)
    assert rec["authority"] == "ZERO"
    assert rec["non_authoritative"] is True
    assert rec["status"] == "PRESENT"
    assert rec["candidate_paths"] == ["/dev/ttyACM0"]
    assert "verdict" not in rec


def test_presence_record_does_not_alias_caller_list():
    paths = ["/dev/ttyACM0"]
    rec = build_presence_record("pico-01", paths, NOW)
    paths.append("/dev/ttyACM1")
    assert rec["candidate_paths"] == ["/dev/ttyACM0"]


def test_intake_sample_tags_advisory_and_preserves_data():
    sample = {"temperature_c": 21.4, "humidity_pct": 38.0}
    rec = intake_sample("pico-01", sample, NOW)
    assert rec["authority"] == "ZERO"
    assert rec["non_authoritative"] is True
    assert rec["source"] == "external_microcontroller_test_node"
    assert rec["sample"] == sample
    assert "verdict" not in rec


def test_intake_sample_rejects_verdict_shaped_keys():
    with pytest.raises(ValueError):
        intake_sample("pico-01", {"verdict": "PASS"}, NOW)
    with pytest.raises(ValueError):
        intake_sample("pico-01", {"pass": True}, NOW)


def test_intake_sample_rejects_verdict_token_values():
    with pytest.raises(ValueError):
        intake_sample("pico-01", {"status": "PASS"}, NOW)
    with pytest.raises(ValueError):
        intake_sample("pico-01", {"status": "DROP"}, NOW)
