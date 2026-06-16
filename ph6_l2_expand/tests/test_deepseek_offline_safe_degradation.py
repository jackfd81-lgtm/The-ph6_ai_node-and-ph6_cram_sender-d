from pathlib import Path

from ph6_l2_expand.experimental import deepseek_client
from ph6_l2_expand.experimental.advisory_improvement_tracker import OLLAMA_LOCAL, run_cycles
from ph6_l2_expand.schemas import MOCK_AI_ADVISORY_SCHEMA


def test_unreachable_endpoint_returns_skipped(sample_source_object):
    advisory = deepseek_client.generate(
        "internal_000001", sample_source_object, cycle=1, token_map_before_dict={},
        endpoint="http://127.0.0.1:1/api/generate", timeout_s=1,
    )

    assert advisory["status"] == "SKIPPED_DEEPSEEK_OFFLINE"
    assert advisory["schema"] == MOCK_AI_ADVISORY_SCHEMA
    assert advisory["authority_level"] == "ZERO"
    assert advisory["candidate_links"] == []
    assert advisory["token_map_after"] == advisory["token_map_before"]


def test_unparseable_model_output_does_not_raise(monkeypatch, sample_source_object):
    monkeypatch.setattr(deepseek_client, "_call_ollama", lambda *a, **k: "not json at all")

    advisory = deepseek_client.generate("internal_000001", sample_source_object, cycle=1, token_map_before_dict={})

    assert advisory["observations"] == ["UNPARSEABLE_MODEL_OUTPUT"]
    assert advisory["candidate_links"] == []
    assert "boundary_warnings" in advisory


def test_run_cycles_ollama_local_does_not_block_on_skip(monkeypatch, mram_s_dir, sample_source_object):
    def fake_generate(source_object_id, source_object, cycle, token_map_before_dict, **kwargs):
        return deepseek_client._skipped_offline(source_object_id, cycle, token_map_before_dict, "offline test")

    monkeypatch.setattr(deepseek_client, "generate", fake_generate)

    results = run_cycles("internal_000001", sample_source_object, mram_s_dir, cycles=2, mode=OLLAMA_LOCAL)

    assert len(results) == 2
    for r in results:
        assert r["status"] == "WRITTEN"
        assert Path(r["path"]).exists()
