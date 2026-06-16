"""
ph6_l2_expand.workers.comparison_worker

Lane: 2
Authority: ZERO
Write domain: none (read-only comparison)

Compares two MRAM-S advisory records (e.g. before/after an improvement
cycle) and reports token-map deltas and metric deltas. Purely advisory —
the comparison result is itself only ever written to MRAM-S.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


def _load(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _token_map(payload: Dict[str, Any]) -> Dict[str, Any]:
    data = payload.get("advisory_data", {})
    return data.get("token_map_after") or data.get("token_map", {})


def _metrics(payload: Dict[str, Any]) -> Dict[str, Any]:
    data = payload.get("advisory_data", {})
    return data.get("improvement_metrics") or data.get("metrics", {})


def compare(before_path: str, after_path: str) -> Dict[str, Any]:
    before = _load(before_path)
    after = _load(after_path)

    before_map = _token_map(before)
    after_map = _token_map(after)

    before_ids = set(before_map.keys())
    after_ids = set(after_map.keys())

    added = sorted(after_ids - before_ids)
    removed = sorted(before_ids - after_ids)

    promoted = sorted(
        tid for tid in added
        if after_map.get(tid, {}).get("token_type") == "VLT"
    )

    before_metrics = _metrics(before)
    after_metrics = _metrics(after)

    metric_deltas: Dict[str, Any] = {}
    for key in sorted(set(before_metrics) | set(after_metrics)):
        b = before_metrics.get(key)
        a = after_metrics.get(key)
        try:
            metric_deltas[key] = float(a) - float(b)
        except (TypeError, ValueError):
            metric_deltas[key] = {"before": b, "after": a}

    return {
        "before_path": str(Path(before_path)),
        "after_path": str(Path(after_path)),
        "added_tokens": added,
        "removed_tokens": removed,
        "promoted_tokens": promoted,
        "metric_deltas": metric_deltas,
    }
