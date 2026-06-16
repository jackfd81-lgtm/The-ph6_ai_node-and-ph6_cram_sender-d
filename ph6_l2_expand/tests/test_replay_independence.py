"""
Proves: replay works with ph6_l2_expand entirely absent.

Static proof: no file under ph6/cram_pu (the Lane-1 CRAM / replay / 4-pass
driver tree) imports or references ph6_l2_expand. If this holds, deleting
ph6_l2_expand entirely cannot break any cram_pu import or code path.
"""

from ph6_l2_expand.tests.conftest import PH6_DIR


def test_cram_pu_does_not_import_ph6_l2_expand():
    cram_pu_dir = PH6_DIR / "cram_pu"
    assert cram_pu_dir.exists()

    offenders = []
    for path in cram_pu_dir.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "ph6_l2_expand" in text:
            offenders.append(str(path))

    assert offenders == [], f"ph6_l2_expand referenced from Lane-1 cram_pu tree: {offenders}"
