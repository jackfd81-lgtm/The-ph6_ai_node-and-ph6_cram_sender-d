"""
Proves: ph6_l2_expand has no reverse path into Lane-1 authority code.

Static proof: no module under ph6_l2_expand (excluding tests) imports from
ph6.cram_pu, ph6.ph6_cert, ph6.audit, or any other Lane-1 authority module.
Lane 2 may only *read* a pre-adjudicated reference object passed in as a
plain dict/JSON file (workers/reference_worker.py) — it never imports
Lane-1 code to do so.
"""

import re

from ph6_l2_expand.tests.conftest import iter_l2_source_files

FORBIDDEN_IMPORT_PATTERNS = [
    re.compile(r"\bimport\s+ph6\.cram_pu"),
    re.compile(r"\bfrom\s+ph6\.cram_pu"),
    re.compile(r"\bimport\s+ph6\.ph6_cert"),
    re.compile(r"\bfrom\s+ph6\.ph6_cert"),
    re.compile(r"\bimport\s+ph6\.audit\b"),
    re.compile(r"\bfrom\s+ph6\.audit\b"),
]


def test_no_l2_module_imports_lane1_authority_code():
    offenders = []
    for path in iter_l2_source_files():
        text = path.read_text(encoding="utf-8")
        for pattern in FORBIDDEN_IMPORT_PATTERNS:
            if pattern.search(text):
                offenders.append((str(path), pattern.pattern))

    assert offenders == [], f"ph6_l2_expand modules importing Lane-1 code: {offenders}"
