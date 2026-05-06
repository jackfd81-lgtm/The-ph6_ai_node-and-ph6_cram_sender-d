"""
TOK-1.0 boundary validation tests.
Lane-2 / MRAM-S / Authority ZERO enforcement.
"""

from pathlib import Path


FORBIDDEN_TERMS = [
    "issue_pass",
    "issue_drop",
    "set_pass",
    "set_drop",
    "modify_pseudo",
    "write_cram",
    "block_rsync",
    "replay_authority",
]

FORBIDDEN_PATHS = [
    "/var/ph6/cram-0",
    "/var/ph6/cram-a",
    "/var/ph6/cram-r",
    "/var/ph6/export",
    "/var/ph6/audit",
]


def test_tok_forbidden_terms_absent():
    root = Path(__file__).parent.parent
    for path in root.rglob("*.py"):
        if path.parent.name == "tests":
            continue
        text = path.read_text(encoding="utf-8")
        for term in FORBIDDEN_TERMS:
            assert term not in text, f"Forbidden term '{term}' found in {path}"


def test_tok_forbidden_paths_absent():
    root = Path(__file__).parent.parent
    for path in root.rglob("*.py"):
        if path.parent.name == "tests":
            continue
        text = path.read_text(encoding="utf-8")
        for forbidden in FORBIDDEN_PATHS:
            assert forbidden not in text, f"Forbidden path '{forbidden}' found in {path}"


def test_tok_declares_authority_zero():
    lifecycle = (Path(__file__).parent.parent / "lifecycle.py").read_text(encoding="utf-8")
    assert 'authority: str = "ZERO"' in lifecycle
    assert '"authority": "ZERO"' in lifecycle
    assert '"advisory_only": True' in lifecycle
