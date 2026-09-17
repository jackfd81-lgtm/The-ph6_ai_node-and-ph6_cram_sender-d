import pytest

from ph6_l2_expand.lmpq_proposed.soso_jedi_adapter import lookup_token_provenance


def test_lookup_returns_advisory_zero_output():
    result = lookup_token_provenance("vlt_example_token_id")
    assert result["authority"] == "ADVISORY_ZERO"
    assert result["source_token_id"] == "vlt_example_token_id"
    assert "continuity_block" in result
    assert "advisory_manifest" in result
    assert result["continuity_block"]["authority"] == "ADVISORY_ZERO"


def test_lookup_is_deterministic_for_same_token():
    a = lookup_token_provenance("vlt_same_token")
    b = lookup_token_provenance("vlt_same_token")
    assert a["continuity_block"]["continuity_hash"] == b["continuity_block"]["continuity_hash"]
    assert a["advisory_manifest"]["trace_hash"] == b["advisory_manifest"]["trace_hash"]


def test_lookup_differs_for_different_tokens():
    a = lookup_token_provenance("vlt_token_a")
    b = lookup_token_provenance("vlt_token_b")
    assert a["continuity_block"]["continuity_hash"] != b["continuity_block"]["continuity_hash"]


def test_lookup_rejects_empty_token_id():
    with pytest.raises(ValueError):
        lookup_token_provenance("")


def test_lookup_never_issues_pass_drop_verdict():
    from ph6_l2_expand.boundary_guard import classify

    result = lookup_token_provenance("vlt_boundary_check")
    for key in ("stratigraphy", "continuity_block", "advisory_manifest"):
        status, violations = classify(result[key])
        assert status == "OK", (key, violations)
