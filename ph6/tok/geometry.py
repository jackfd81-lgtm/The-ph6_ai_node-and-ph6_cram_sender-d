"""
TOK-1.0 Spatial Geometry Helpers

Lane: 2
Authority: ZERO
Write domain: none (pure computation)

Canonical bbox format: [x, y, w, h]
"""

from __future__ import annotations

from typing import List


def bbox_iou(a: List[float], b: List[float]) -> float:
    """Intersection over Union for [x, y, w, h] bboxes."""
    if len(a) != 4 or len(b) != 4:
        return 0.0

    ax1, ay1, aw, ah = a
    bx1, by1, bw, bh = b

    ax2, ay2 = ax1 + aw, ay1 + ah
    bx2, by2 = bx1 + bw, by1 + bh

    inter_w = max(0.0, min(ax2, bx2) - max(ax1, bx1))
    inter_h = max(0.0, min(ay2, by2) - max(ay1, by1))
    inter_area = inter_w * inter_h

    area_a = max(0.0, aw) * max(0.0, ah)
    area_b = max(0.0, bw) * max(0.0, bh)
    denom = area_a + area_b - inter_area

    if denom <= 0:
        return 0.0

    return inter_area / denom


def meets_spatial_consistency(vdts: list, iou_min: float) -> bool:
    """Return True if all VDTs are spatially consistent with the first."""
    if len(vdts) < 2:
        return True

    base = vdts[0].bbox
    return all(bbox_iou(base, v.bbox) >= iou_min for v in vdts[1:])


def compute_centroid(bboxes: List[List[float]]) -> List[float]:
    """Return [cx, cy] centroid of a list of [x, y, w, h] bboxes."""
    centers = [
        [x + w / 2.0, y + h / 2.0]
        for b in bboxes
        if len(b) == 4
        for x, y, w, h in [b]
    ]

    if not centers:
        return [0.0, 0.0]

    cx = sum(c[0] for c in centers) / len(centers)
    cy = sum(c[1] for c in centers) / len(centers)
    return [round(cx, 6), round(cy, 6)]


def bbox_area(b: List[float]) -> float:
    if len(b) != 4:
        return 0.0
    _, _, w, h = b
    return max(0.0, w) * max(0.0, h)


def bbox_is_valid(b: List[float]) -> bool:
    """Return True if bbox has positive area and valid format."""
    if len(b) != 4:
        return False
    _, _, w, h = b
    return w > 0 and h > 0
