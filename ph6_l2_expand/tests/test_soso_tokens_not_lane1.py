"""
FINAL RULE: SoSo and tokens are never Lane 1.

Static proof: ph6_l2_expand is never referenced from the Lane-1 cram_pu
*runtime* tree (cram_pu/tests is excluded -- it already contains its own
pre-existing advisory-isolation proofs that legitimately use the
ph6.soso_token.v1 / VDT vocabulary as test fixture data, which is the
opposite of coupling: those tests check that such packets stay confined
to MRAM-S).
"""

from ph6_l2_expand.schemas import SOSO_TOKEN_SCHEMA, TOKEN_TYPES
from ph6_l2_expand.tests.conftest import PH6_DIR

FORBIDDEN_STRINGS = [SOSO_TOKEN_SCHEMA, "ph6_l2_expand"]


def test_soso_token_concepts_absent_from_cram_pu_runtime():
    cram_pu_dir = PH6_DIR / "cram_pu"
    offenders = []

    for path in cram_pu_dir.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        if "tests" in path.relative_to(cram_pu_dir).parts:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for needle in FORBIDDEN_STRINGS:
            if needle in text:
                offenders.append((str(path), needle))

    assert offenders == [], f"SoSo/token concepts leaked into Lane-1 cram_pu runtime: {offenders}"


def test_token_types_are_exactly_rt_vdt_vlt():
    assert set(TOKEN_TYPES) == {"RT", "VDT", "VLT"}
