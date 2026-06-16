"""
ph6_l2_expand.audit_guard

Lane: 2
Authority: ZERO
Write domain: none (read-only audit of MRAM-S output)

Walks an MRAM-S output directory and confirms:
  - every accepted (non-quarantine) JSON file passes boundary_guard
  - every file under quarantine/ is correctly marked DRIFT_FAIL
  - no forbidden authority language has leaked into accepted output

This module never writes and never touches CRAM-0/A/R.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from ph6_l2_expand.boundary_guard import classify


def audit_directory(root: Path) -> Dict[str, Any]:
    root = Path(root)
    scanned = 0
    quarantined = 0
    violations: List[str] = []

    if not root.exists():
        return {"status": "OK", "scanned": 0, "quarantined": 0, "violations": []}

    for path in sorted(root.rglob("*.json")):
        scanned += 1
        try:
            with open(path, "r", encoding="utf-8") as f:
                payload = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            violations.append(f"{path}: unreadable ({exc})")
            continue

        in_quarantine = "quarantine" in path.relative_to(root).parts

        if in_quarantine:
            quarantined += 1
            if not (isinstance(payload, dict) and payload.get("DRIFT_FAIL") is True):
                violations.append(f"{path}: quarantined file missing DRIFT_FAIL marker")
            continue

        status, file_violations = classify(payload)
        if status != "OK":
            violations.append(f"{path}: accepted output failed boundary_guard: {file_violations}")

    overall = "OK" if not violations else "DRIFT_FAIL"
    return {
        "status": overall,
        "scanned": scanned,
        "quarantined": quarantined,
        "violations": violations,
    }
