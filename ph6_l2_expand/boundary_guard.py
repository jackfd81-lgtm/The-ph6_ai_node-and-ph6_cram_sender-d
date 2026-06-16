"""
ph6_l2_expand.boundary_guard

Lane: 2
Authority: ZERO
Write domain: none (pure scan, no I/O)

Scans any advisory payload (token dicts, MRAM-S advisory records, mock AI
or DeepSeek output) for forbidden authority language before it is allowed
into accepted MRAM-S output. Any hit is classified DRIFT_FAIL and the
whole payload must be quarantined — never sanitized in place.
"""

from __future__ import annotations

import re
from typing import Any, List, Tuple

# Whole-word, case-insensitive. These are Lane-1 verdict / authority tokens
# and must never appear anywhere in Lane-2 advisory output.
FORBIDDEN_WORDS = (
    "PASS",
    "DROP",
    "ACCEPT",
    "REJECT",
    "PROMOTE",
    "verdict",
    "threshold",
)

# Substring, case-insensitive. Phrases that indicate Lane-1 authority
# coupling or evidence mutation.
FORBIDDEN_PHRASES = (
    "evidencepacket",
    "authority over lane 1",
    "modify cram",
    "modify pseudo",
    "modify replay",
    "modify gate",
)

# Dict keys that are never permitted in Lane-2 advisory output, regardless
# of value.
FORBIDDEN_FIELD_NAMES = {
    "verdict",
    "pass",
    "drop",
    "accept",
    "reject",
    "promote",
    "threshold",
    "evidencepacket",
    "confidence",
    "probability",
}

_WORD_RES = [re.compile(rf"\b{re.escape(w)}\b", re.IGNORECASE) for w in FORBIDDEN_WORDS]


def _scan_string(value: str, path: str, violations: List[str]) -> None:
    for regex, word in zip(_WORD_RES, FORBIDDEN_WORDS):
        if regex.search(value):
            violations.append(f"forbidden word '{word}' found in value at {path}")

    lowered = value.lower()
    for phrase in FORBIDDEN_PHRASES:
        if phrase in lowered:
            violations.append(f"forbidden phrase '{phrase}' found in value at {path}")


def _scan(obj: Any, path: str, violations: List[str]) -> None:
    if isinstance(obj, dict):
        for key, value in obj.items():
            key_lower = str(key).lower()
            if key_lower in FORBIDDEN_FIELD_NAMES:
                violations.append(f"forbidden field name '{key}' at {path}.{key}")
            _scan_string(str(key), f"{path}.{key}<key>", violations)
            _scan(value, f"{path}.{key}", violations)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            _scan(item, f"{path}[{i}]", violations)
    elif isinstance(obj, str):
        _scan_string(obj, path, violations)


def scan(obj: Any) -> List[str]:
    """Return a list of human-readable violation descriptions (empty == clean)."""
    violations: List[str] = []
    _scan(obj, "$", violations)
    return violations


def classify(obj: Any) -> Tuple[str, List[str]]:
    """Return ("OK", []) or ("DRIFT_FAIL", [violations])."""
    violations = scan(obj)
    if violations:
        return "DRIFT_FAIL", violations
    return "OK", []
