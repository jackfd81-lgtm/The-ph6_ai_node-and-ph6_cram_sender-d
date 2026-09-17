import pytest

from ph6_l2_expand.lmpq_proposed.tokens import make_rlt


def test_valid_rlt_construction():
    rlt = make_rlt(
        cram_ref_hash="cram_ref_dropped_001",
        drop_observed_at_ms=1_000_000,
        parent_token_id="vlt_abc123",
    )
    assert rlt.token_type == "RLT"
    assert rlt.cram_ref_hash == "cram_ref_dropped_001"
    assert rlt.evidence_deleted is False  # DROP != DELETE, locked
    assert rlt.authority == "ZERO"
    assert rlt.advisory_only is True
    assert rlt.affects_pass_drop is False
    assert rlt.affects_cram_commit is False


def test_rlt_deterministic_identity():
    a = make_rlt("cram_ref_x", 5000)
    b = make_rlt("cram_ref_x", 5000)
    assert a.token_id == b.token_id
    assert a.state_hash() == b.state_hash()


def test_rlt_different_evidence_different_identity():
    a = make_rlt("cram_ref_x", 5000)
    b = make_rlt("cram_ref_y", 5000)
    assert a.token_id != b.token_id


def test_rlt_evidence_deleted_cannot_be_set_true():
    rlt = make_rlt("cram_ref_x", 5000)
    with pytest.raises(Exception):
        # frozen dataclass with init=False field: constructor rejects it outright
        type(rlt)(
            token_id=rlt.token_id,
            cram_ref_hash=rlt.cram_ref_hash,
            drop_observed_at_ms=rlt.drop_observed_at_ms,
            evidence_deleted=True,
        )


def test_rlt_rejects_missing_source_evidence():
    with pytest.raises(ValueError, match="missing source evidence"):
        make_rlt("", 5000)


def test_rlt_rejects_missing_event_time():
    with pytest.raises(ValueError, match="event-time"):
        make_rlt("cram_ref_x", 0)


def test_rlt_rejects_negative_event_time():
    with pytest.raises(ValueError):
        make_rlt("cram_ref_x", -1)


def test_rlt_no_forbidden_vocabulary():
    from ph6_l2_expand.boundary_guard import classify

    rlt = make_rlt("cram_ref_x", 5000)
    status, violations = classify(rlt.to_dict())
    assert status == "OK", violations
