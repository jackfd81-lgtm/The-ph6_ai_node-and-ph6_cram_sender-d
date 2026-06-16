from ph6_l2_expand.token_policy import ALLOWED_TOKEN_TYPES, validate_token_dict
from ph6_l2_expand.token_types import make_rt, make_vdt, make_vlt


def test_only_rt_vdt_vlt_allowed():
    assert ALLOWED_TOKEN_TYPES == {"RT", "VDT", "VLT"}


def test_valid_rt_passes_validation():
    rt = make_rt("internal_000001", "motion_fraction")
    assert validate_token_dict(rt.to_dict()) == []


def test_valid_vdt_and_vlt_pass_validation():
    rt_a = make_rt("internal_000001", "motion_fraction")
    rt_b = make_rt("internal_000001", "rssi_event")
    vdt = make_vdt(rt_a.token_id, rt_b.token_id, "co-observed", cycle=1, decay_ttl=2)
    assert validate_token_dict(vdt.to_dict()) == []

    vlt = make_vlt(vdt, cycle=2)
    assert validate_token_dict(vlt.to_dict()) == []


def test_unknown_token_type_rejected():
    rt = make_rt("internal_000001", "motion_fraction")
    bad = rt.to_dict()
    bad["token_type"] = "PASS_TOKEN"
    errors = validate_token_dict(bad)
    assert errors
    assert any("token_type" in e for e in errors)
