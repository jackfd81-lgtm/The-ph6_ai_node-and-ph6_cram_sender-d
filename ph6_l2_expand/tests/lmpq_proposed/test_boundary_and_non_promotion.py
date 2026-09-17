"""
Proves that adding ph6_l2_expand.lmpq_proposed did not touch, weaken, or
route around the two existing locked boundary tests:

  ph6_l2_expand/tests/test_token_classes_locked.py::test_only_rt_vdt_vlt_allowed
  ph6_l2_expand/tests/test_soso_tokens_not_lane1.py::test_token_types_are_exactly_rt_vdt_vlt

and that the Lane-1/Lane-2 boundary holds in both directions for the new
package.
"""

from pathlib import Path

from ph6_l2_expand.schemas import TOKEN_TYPES
from ph6_l2_expand.token_policy import ALLOWED_TOKEN_TYPES, validate_token_dict

REPO_ROOT = Path(__file__).resolve().parents[3]
LMPQ_DIR = REPO_ROOT / "ph6_l2_expand" / "lmpq_proposed"
CRAM_PU_DIR = REPO_ROOT / "ph6" / "cram_pu"


def test_authoritative_token_set_still_locked_to_rt_vdt_vlt():
    """Unchanged by this work — the same assertion the locked tests make."""
    assert ALLOWED_TOKEN_TYPES == {"RT", "VDT", "VLT"}
    assert set(TOKEN_TYPES) == {"RT", "VDT", "VLT"}


def test_rlt_plt_aht_are_not_promoted_into_allowed_token_types():
    assert "RLT" not in ALLOWED_TOKEN_TYPES
    assert "PLT" not in ALLOWED_TOKEN_TYPES
    assert "AHT" not in ALLOWED_TOKEN_TYPES


def test_locked_validator_rejects_proposed_token_types():
    """The existing, unmodified validator must reject RLT/PLT/AHT dicts —
    proving they carry no authority in the locked schema path."""
    from ph6_l2_expand.lmpq_proposed.tokens import make_rlt

    rlt = make_rlt("cram_ref_x", 1000)
    errors = validate_token_dict(rlt.to_dict())
    assert errors  # must be rejected: wrong schema AND wrong token_type
    assert any("token_type" in e for e in errors)


def test_lane2_to_lane1_leak_lmpq_proposed_absent_from_cram_pu_runtime():
    """Mirrors test_soso_tokens_not_lane1.py's static proof, extended to
    the new package name."""
    offenders = []
    for path in CRAM_PU_DIR.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        if "tests" in path.relative_to(CRAM_PU_DIR).parts:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "lmpq_proposed" in text:
            offenders.append(str(path))
    assert offenders == [], f"lmpq_proposed leaked into Lane-1 cram_pu runtime: {offenders}"


def test_lane1_to_lane2_leak_lmpq_proposed_does_not_import_cram_pu():
    """Lane-2 -> Lane-1 direction: the proposed package must not import
    the Lane-1 runtime package."""
    offenders = []
    for path in LMPQ_DIR.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "ph6.cram_pu" in text or "ph6_cert" in text:
            offenders.append(str(path))
    assert offenders == [], f"lmpq_proposed imports Lane-1 runtime: {offenders}"


def test_lmpq_proposed_tokens_carry_no_forbidden_authority_language():
    """Every proposed token dataclass, scanned via the existing
    boundary_guard, must classify OK."""
    from ph6_l2_expand.boundary_guard import classify
    from ph6_l2_expand.lmpq_proposed.tokens import make_aht, make_plt, make_rlt

    rlt = make_rlt("cram_ref_x", 1000)
    status, violations = classify(rlt.to_dict())
    assert status == "OK", violations

    plt = make_plt(rlt.token_id, ["t1"], {rlt.token_id: rlt}, 1000, {"t1": 2000})
    status, violations = classify(plt.to_dict())
    assert status == "OK", violations
