from ph6_l2_expand.boundary_guard import classify
from ph6_l2_expand.experimental import deepseek_client, mock_ai_client
from ph6_l2_expand.experimental.advisory_improvement_tracker import build_advisory_record
from ph6_l2_expand.mram_s_writer import write_advisory


def test_mock_ai_output_contains_no_verdicts(sample_source_object):
    advisory = mock_ai_client.generate("internal_000001", sample_source_object, cycle=1, token_map_before_dict={})
    assert classify(advisory)[0] == "OK"


def test_offline_deepseek_output_contains_no_verdicts(sample_source_object):
    advisory = deepseek_client.generate(
        "internal_000001", sample_source_object, cycle=1, token_map_before_dict={},
        endpoint="http://127.0.0.1:1/api/generate", timeout_s=1,
    )
    assert advisory["status"] == "SKIPPED_DEEPSEEK_OFFLINE"
    assert classify(advisory)[0] == "OK"


def test_advisory_containing_verdict_is_quarantined_not_accepted(mram_s_dir, sample_source_object):
    advisory = mock_ai_client.generate("internal_000001", sample_source_object, cycle=1, token_map_before_dict={})
    advisory["observations"].append("the operator should PASS this object")

    record = build_advisory_record("internal_000001", "MOCK_AI", advisory)
    path, status, violations = write_advisory(mram_s_dir, "tainted.json", record)

    assert status == "QUARANTINED"
    assert violations
    assert "quarantine" in path.parts

    # Accepted output directory must not contain the tainted record.
    accepted = list((mram_s_dir).glob("tainted.json"))
    assert accepted == []
