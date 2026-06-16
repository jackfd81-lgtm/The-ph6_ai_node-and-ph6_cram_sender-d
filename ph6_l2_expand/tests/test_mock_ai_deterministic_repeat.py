import json

from ph6_l2_expand.experimental import mock_ai_client


def test_same_input_produces_identical_output(sample_source_object):
    a = mock_ai_client.generate("internal_000001", sample_source_object, cycle=1, token_map_before_dict={})
    b = mock_ai_client.generate("internal_000001", sample_source_object, cycle=1, token_map_before_dict={})

    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def test_repeated_cycles_with_same_state_are_deterministic(sample_source_object):
    token_map = {}
    advisory_1 = mock_ai_client.generate("internal_000001", sample_source_object, cycle=3, token_map_before_dict=token_map)
    advisory_2 = mock_ai_client.generate("internal_000001", sample_source_object, cycle=3, token_map_before_dict=token_map)

    assert json.dumps(advisory_1, sort_keys=True) == json.dumps(advisory_2, sort_keys=True)
