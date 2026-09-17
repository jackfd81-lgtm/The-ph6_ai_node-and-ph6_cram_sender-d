import pytest

from ph6_l2_expand.lmpq_proposed.tokens import make_plt, make_rlt


def test_valid_plt_construction():
    rlt = make_rlt("cram_ref_x", 5000)
    plt = make_plt(
        parent_token_id=rlt.token_id,
        linked_token_ids=["vlt_resumed_1"],
        token_map={rlt.token_id: rlt},
        parent_event_time_ms=5000,
        linked_event_times_ms={"vlt_resumed_1": 8000},
    )
    assert plt.token_type == "PLT"
    assert plt.parent_token_id == rlt.token_id
    assert plt.linked_token_ids == ["vlt_resumed_1"]
    assert plt.continuity_gap_ms == 3000
    assert plt.authority == "ZERO"


def test_plt_deterministic_identity():
    rlt = make_rlt("cram_ref_x", 5000)
    token_map = {rlt.token_id: rlt}
    a = make_plt(rlt.token_id, ["t1"], token_map, 5000, {"t1": 6000})
    b = make_plt(rlt.token_id, ["t1"], token_map, 5000, {"t1": 6000})
    assert a.token_id == b.token_id
    assert a.state_hash() == b.state_hash()


def test_plt_rejects_invalid_parent_token():
    with pytest.raises(ValueError, match="invalid parent token"):
        make_plt(
            parent_token_id="does_not_exist",
            linked_token_ids=["t1"],
            token_map={},
            parent_event_time_ms=0,
            linked_event_times_ms={"t1": 1000},
        )


def test_plt_rejects_empty_link_list():
    rlt = make_rlt("cram_ref_x", 5000)
    with pytest.raises(ValueError, match="broken provenance"):
        make_plt(
            parent_token_id=rlt.token_id,
            linked_token_ids=[],
            token_map={rlt.token_id: rlt},
            parent_event_time_ms=5000,
            linked_event_times_ms={},
        )


def test_plt_rejects_missing_event_time_for_linked_token():
    rlt = make_rlt("cram_ref_x", 5000)
    with pytest.raises(ValueError, match="missing event-time"):
        make_plt(
            parent_token_id=rlt.token_id,
            linked_token_ids=["t1", "t2"],
            token_map={rlt.token_id: rlt},
            parent_event_time_ms=5000,
            linked_event_times_ms={"t1": 6000},  # t2 missing
        )


def test_plt_no_forbidden_vocabulary():
    from ph6_l2_expand.boundary_guard import classify

    rlt = make_rlt("cram_ref_x", 5000)
    plt = make_plt(rlt.token_id, ["t1"], {rlt.token_id: rlt}, 5000, {"t1": 6000})
    status, violations = classify(plt.to_dict())
    assert status == "OK", violations
