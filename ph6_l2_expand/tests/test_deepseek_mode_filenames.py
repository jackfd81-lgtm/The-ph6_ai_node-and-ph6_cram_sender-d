import json

from ph6_l2_expand import cli


def test_mock_offline_and_ollama_local_write_distinct_files(monkeypatch, mram_s_dir, source_object_path):
    from ph6_l2_expand.experimental import deepseek_client

    def fake_unreachable(*args, **kwargs):
        return deepseek_client._skipped_offline("internal_000001", 1, {}, "offline test")

    monkeypatch.setattr(deepseek_client, "generate", fake_unreachable)

    cli.main(["deepseek", "--source", str(source_object_path), "--out", str(mram_s_dir), "--mode", "mock-offline-ai"])
    cli.main(["deepseek", "--source", str(source_object_path), "--out", str(mram_s_dir), "--mode", "ollama-local"])

    mock_path = mram_s_dir / "deepseek_mock_offline_ai_internal_000001.json"
    ollama_path = mram_s_dir / "deepseek_ollama_local_internal_000001.json"

    assert mock_path.exists()
    assert ollama_path.exists()

    mock_record = json.loads(mock_path.read_text())["advisory_data"]
    ollama_record = json.loads(ollama_path.read_text())["advisory_data"]

    assert mock_record["mode"] == "MOCK_OFFLINE_AI"
    assert mock_record["token_map_after"]

    assert ollama_record["status"] == "SKIPPED_DEEPSEEK_OFFLINE"
    assert ollama_record["token_map_after"] == {}
