from ph6_l2_expand.experimental import mock_ai_client
from ph6_l2_expand.schemas import ADVISORY_AUTHORITY_LEVEL, MOCK_AI_ADVISORY_SCHEMA


def test_mock_ai_runs_with_no_network_and_no_ollama(sample_source_object):
    advisory = mock_ai_client.generate("internal_000001", sample_source_object, cycle=1, token_map_before_dict={})

    assert advisory["schema"] == MOCK_AI_ADVISORY_SCHEMA
    assert advisory["mode"] == "MOCK_OFFLINE_AI"
    assert advisory["authority_level"] == ADVISORY_AUTHORITY_LEVEL
    assert advisory["improvement_cycle"] == 1

    metrics = advisory["improvement_metrics"]
    for key in ("rt_count", "vdt_count", "vlt_count", "stable_link_count", "decayed_link_count", "topology_density"):
        assert key in metrics


def test_mock_ai_observations_cover_all_fields(sample_source_object):
    advisory = mock_ai_client.generate("internal_000001", sample_source_object, cycle=1, token_map_before_dict={})
    observed_fields = {o.split("'")[1] for o in advisory["observations"]}
    assert observed_fields == set(sample_source_object.keys())
