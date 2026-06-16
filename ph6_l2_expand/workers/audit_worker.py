"""
ph6_l2_expand.workers.audit_worker

Lane: 2
Authority: ZERO
Write domain: none (read-only audit)

Thin wrapper around audit_guard for the `cli.py audit` command.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from ph6_l2_expand.audit_guard import audit_directory


def run_audit(out_dir: str) -> Dict[str, Any]:
    return audit_directory(Path(out_dir))
