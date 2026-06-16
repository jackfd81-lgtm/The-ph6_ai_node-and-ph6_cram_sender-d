"""
Proves: ph6_l2_expand cannot self-modify Lane-1 authority state.

Static proof: no module under ph6_l2_expand (excluding tests) *imports*
the Lane-1 symbols PSEUDO_M, PSEUDO_A, evaluate_frame, CRAM_A, CRAM_R,
CRAM_0, or EvidencePacket. (Some of these names appear as plain strings
elsewhere -- e.g. boundary_guard's forbidden-word list and
reference_worker's field-stripping list -- which is the *opposite* of
coupling: those modules name the symbols only to keep them out.)
"""

import re

from ph6_l2_expand.tests.conftest import iter_l2_source_files

FORBIDDEN_SYMBOLS = [
    "PSEUDO_M",
    "PSEUDO_A",
    "evaluate_frame",
    "CRAM_A",
    "CRAM_R",
    "CRAM_0",
    "EvidencePacket",
]

_IMPORT_LINE = re.compile(r"^\s*(import|from)\s+\S+", re.MULTILINE)


def test_no_l2_module_imports_lane1_symbols():
    offenders = []
    for path in iter_l2_source_files():
        for line in path.read_text(encoding="utf-8").splitlines():
            if not _IMPORT_LINE.match(line):
                continue
            for symbol in FORBIDDEN_SYMBOLS:
                if symbol in line:
                    offenders.append((str(path), line.strip()))

    assert offenders == [], f"Lane-1 authority symbols imported in ph6_l2_expand: {offenders}"
