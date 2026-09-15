"""
PH6 Evidence Access Boundary.

The single, narrow, read-only interface through which a Lane-2 (advisory) consumer
may observe Lane-1 authoritative CRAM-A evidence. It has no write, commit, delete,
rename, or verdict-issuing capability of any kind — those methods do not exist on
this class, rather than existing and being denied at runtime.

This module reuses the CRAM store layout (`CRAMPaths`) and the canonical BLAKE2b-256
hashing (`blake2b256`) defined in `ph6.cram_pu.crash_replay` — the same module that
implements `CRAMWriter`'s atomic-commit and `.blake2b`-marker-last contract (Finding
A). This boundary does not reinterpret or relax that contract; a record is only ever
reported FOUND if it passes the identical hash-and-marker checks `CRAMWriter`/
`check_cram_integrity()` already enforce.

Reference: PH6_SOURCE/DEPLOYMENT/PH6_EVIDENCE_ACCESS_BOUNDARY_PROPOSAL.md
Authority: NONE (this boundary observes Lane-1 authority; it does not hold any)
Lane: 1-adjacent read surface, exposed for Lane-2 consumption
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

from ph6.cram_pu.crash_replay import CRAMPaths, blake2b256


class EvidenceStatus(Enum):
    FOUND = "FOUND"
    NOT_FOUND = "NOT_FOUND"
    INVALID = "INVALID"
    CONFLICT = "CONFLICT"


@dataclass(frozen=True)
class EvidenceView:
    status: EvidenceStatus
    frame_id: Optional[int] = None
    record: Optional[Dict[str, Any]] = None
    cram_hash: Optional[str] = None
    prev_cram_hash: Optional[str] = None
    marker_present: Optional[bool] = None
    marker_matches: Optional[bool] = None


def _is_valid_frame_id(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


class PH6EvidenceAccessBoundary:
    """
    Read-only accessor over a Lane-1 CRAM store. Exposes exactly three operations:
    get_evidence, get_evidence_range, verify_integrity. No other public method
    exists on this class.
    """

    _MAX_RANGE = 500

    def __init__(self, paths: CRAMPaths):
        self._paths = paths

    def get_evidence(self, frame_id: int) -> EvidenceView:
        if not _is_valid_frame_id(frame_id):
            return EvidenceView(status=EvidenceStatus.INVALID, frame_id=None)

        path = self._paths.cram_store / f"cram_{frame_id:010d}.json"
        if not path.exists():
            return EvidenceView(status=EvidenceStatus.NOT_FOUND, frame_id=frame_id)

        try:
            with path.open("r", encoding="utf-8") as f:
                rec = json.load(f)
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            return EvidenceView(status=EvidenceStatus.INVALID, frame_id=frame_id)

        stored_hash = rec.get("cram_hash", "")
        body = {k: v for k, v in rec.items() if k != "cram_hash"}
        recomputed = blake2b256(body)
        if recomputed != stored_hash:
            return EvidenceView(
                status=EvidenceStatus.CONFLICT,
                frame_id=frame_id,
                record=rec,
                cram_hash=stored_hash,
                prev_cram_hash=rec.get("prev_cram_hash"),
            )

        marker_path = path.parent / (path.name + ".blake2b")
        marker_present = marker_path.exists()
        marker_matches = False
        if marker_present:
            try:
                marker_matches = marker_path.read_text(encoding="utf-8").strip() == stored_hash
            except OSError:
                marker_matches = False

        if not marker_present or not marker_matches:
            return EvidenceView(
                status=EvidenceStatus.CONFLICT,
                frame_id=frame_id,
                record=rec,
                cram_hash=stored_hash,
                prev_cram_hash=rec.get("prev_cram_hash"),
                marker_present=marker_present,
                marker_matches=marker_matches,
            )

        return EvidenceView(
            status=EvidenceStatus.FOUND,
            frame_id=frame_id,
            record=rec,
            cram_hash=stored_hash,
            prev_cram_hash=rec.get("prev_cram_hash"),
            marker_present=True,
            marker_matches=True,
        )

    def get_evidence_range(
        self,
        start_frame_id: int,
        end_frame_id: int,
        max_count: int = 500,
    ) -> List[EvidenceView]:
        if (
            not _is_valid_frame_id(start_frame_id)
            or not _is_valid_frame_id(end_frame_id)
            or end_frame_id < start_frame_id
        ):
            return [EvidenceView(status=EvidenceStatus.INVALID, frame_id=None)]

        hard_cap = min(max_count, self._MAX_RANGE) if max_count > 0 else 0
        last_frame_id = min(end_frame_id, start_frame_id + hard_cap - 1) if hard_cap > 0 else start_frame_id - 1
        return [self.get_evidence(fid) for fid in range(start_frame_id, last_frame_id + 1)]

    def verify_integrity(self, frame_id: int) -> EvidenceView:
        return self.get_evidence(frame_id)
