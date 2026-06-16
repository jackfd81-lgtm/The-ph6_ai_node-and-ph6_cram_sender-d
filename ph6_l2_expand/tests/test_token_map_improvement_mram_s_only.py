import json

from ph6_l2_expand.experimental.advisory_improvement_tracker import MOCK_OFFLINE_AI, run_cycles
from ph6_l2_expand.token_policy import validate_token_dict
from ph6_l2_expand.workers.comparison_worker import compare


def _load(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_every_token_in_improved_map_validates(mram_s_dir, sample_source_object):
    results = run_cycles("internal_000001", sample_source_object, mram_s_dir, cycles=5, mode=MOCK_OFFLINE_AI)

    final = _load(results[-1]["path"])
    token_map = final["advisory_data"]["token_map_after"]

    assert token_map  # non-empty
    for token_id, token in token_map.items():
        errors = validate_token_dict(token)
        assert errors == [], (token_id, errors)
        assert token["token_type"] in {"RT", "VDT", "VLT"}


def test_compare_maps_reports_topology_growth(mram_s_dir, sample_source_object):
    results = run_cycles("internal_000001", sample_source_object, mram_s_dir, cycles=3, mode=MOCK_OFFLINE_AI)

    diff = compare(results[0]["path"], results[-1]["path"])

    assert "metric_deltas" in diff
    assert "added_tokens" in diff
    assert "promoted_tokens" in diff


def test_promotion_occurs_after_enough_cycles(mram_s_dir, sample_source_object):
    # promotion threshold defaults to 3; run enough cycles for a VLT to appear
    results = run_cycles("internal_000001", sample_source_object, mram_s_dir, cycles=6, mode=MOCK_OFFLINE_AI)

    final = _load(results[-1]["path"])
    token_map = final["advisory_data"]["token_map_after"]
    vlt_count = sum(1 for t in token_map.values() if t["token_type"] == "VLT")
    assert vlt_count >= 1
