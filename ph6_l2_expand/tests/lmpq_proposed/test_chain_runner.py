from ph6_l2_expand.lmpq_proposed.chain_runner import run_lmpq_chain


def test_full_chain_completes_all_stages(tmp_path):
    result = run_lmpq_chain(tmp_path / "mram-s")

    assert result["complete"] is True
    expected_stages = {
        "RT_VDT_VLT_normal_path",
        "RLT_construction",
        "PLT_construction",
        "AHT_rehydration",
        "soso_jedi_lookup",
        "bcv2_bundle_write",
    }
    assert set(result["stages"].keys()) == expected_stages
    assert all(v in ("OK", "WRITTEN") for v in result["stages"].values())

    assert result["vlt_token_id"]
    assert result["rlt_token_id"]
    assert result["plt_token_id"]
    assert result["aht_token_id"]
    assert result["bcv2_violations"] == []


def test_chain_is_deterministic_across_independent_runs(tmp_path):
    r1 = run_lmpq_chain(tmp_path / "run1")
    r2 = run_lmpq_chain(tmp_path / "run2")

    assert r1["vlt_token_id"] == r2["vlt_token_id"]
    assert r1["rlt_token_id"] == r2["rlt_token_id"]
    assert r1["plt_token_id"] == r2["plt_token_id"]
    assert r1["aht_token_id"] == r2["aht_token_id"]
    assert r1["bcv2_bundle_id"] == r2["bcv2_bundle_id"]
    assert r1["soso_jedi_continuity_hash"] == r2["soso_jedi_continuity_hash"]


def test_chain_bundle_is_readable_json(tmp_path):
    import json

    result = run_lmpq_chain(tmp_path / "mram-s")
    payload = json.loads(open(result["bcv2_bundle_path"], "rb").read().decode("utf-8"))
    assert payload["bcv_id"] == result["bcv2_bundle_id"]
    assert payload["authority"] == "ZERO"
