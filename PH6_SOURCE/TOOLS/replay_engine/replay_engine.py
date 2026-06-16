#!/usr/bin/env python3
"""
PH6 Replay Engine — defines 8 replay classes, validates replay certification records.
PROPOSED artifact. Ratified_by: null.
Run with --self-test to validate all 8 classes.
"""

import hashlib
import json
import sys
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum

PROPOSED_BY = "claude-code-lane2"


class ReplayClass(Enum):
    REPLAY_FRAME              = "REPLAY_FRAME"
    REPLAY_AUDIO              = "REPLAY_AUDIO"
    REPLAY_SENSOR_PACKET      = "REPLAY_SENSOR_PACKET"
    REPLAY_MEASUREMENT        = "REPLAY_MEASUREMENT"
    REPLAY_VERDICT            = "REPLAY_VERDICT"
    REPLAY_HASH               = "REPLAY_HASH"
    REPLAY_EXPORT             = "REPLAY_EXPORT"
    REPLAY_AI_DERIVATIVE_REF  = "REPLAY_AI_DERIVATIVE_REFERENCE"


class CertificationStatus(Enum):
    CERTIFIED  = "CERTIFIED"
    FAILED     = "FAILED"
    PENDING    = "PENDING"
    DEGRADED   = "DEGRADED"


@dataclass
class ReplayResult:
    replay_class: ReplayClass
    original_evidence_id: str
    original_verdict_id: str
    same_evidence: bool = False
    same_config: bool = False
    same_code_hash: bool = False
    same_thresholds: bool = False
    same_normalization: bool = False
    metrics_match: bool = False
    verdict_match: bool = False
    hash_match: bool = False
    original_hash: str = ""
    replay_hash: str = ""
    delta_summary: str = ""
    gap_register_entry_id: Optional[str] = None

    @property
    def certification_status(self) -> CertificationStatus:
        required = [
            self.same_evidence, self.same_config, self.same_code_hash,
            self.same_thresholds, self.metrics_match, self.verdict_match,
            self.hash_match
        ]
        if all(required):
            return CertificationStatus.CERTIFIED
        if self.same_evidence and self.hash_match:
            return CertificationStatus.DEGRADED
        return CertificationStatus.FAILED

    def to_record(self) -> dict:
        ts = datetime.now(timezone.utc).isoformat()
        h = hashlib.blake2b(digest_size=32)
        h.update(self.original_evidence_id.encode())
        h.update(self.replay_hash.encode())
        h.update(ts.encode())
        return {
            "schema_id": "ph6.replay.certification_record.v1",
            "replay_id": h.hexdigest()[:16],
            "original_evidence_id": self.original_evidence_id,
            "original_verdict_id": self.original_verdict_id,
            "replay_class": self.replay_class.value,
            "same_evidence": self.same_evidence,
            "same_config": self.same_config,
            "same_code_hash": self.same_code_hash,
            "same_thresholds": self.same_thresholds,
            "same_normalization": self.same_normalization,
            "metrics_match": self.metrics_match,
            "verdict_match": self.verdict_match,
            "hash_match": self.hash_match,
            "certification_status": self.certification_status.value,
            "replayed_at_utc": ts,
            "original_hash": self.original_hash,
            "replay_hash": self.replay_hash,
            "delta_summary": self.delta_summary,
            "gap_register_entry_id": self.gap_register_entry_id,
            "operator_review_status": "PENDING",
            "proposed_by": PROPOSED_BY,
            "ratified_by": None,
        }


def self_test() -> int:
    print("REPLAY ENGINE SELF-TEST")
    failures = []

    for cls in ReplayClass:
        r = ReplayResult(
            replay_class=cls,
            original_evidence_id=f"ev_{cls.name.lower()}",
            original_verdict_id=f"v_{cls.name.lower()}",
            same_evidence=True,
            same_config=True,
            same_code_hash=True,
            same_thresholds=True,
            same_normalization=True,
            metrics_match=True,
            verdict_match=True,
            hash_match=True,
            original_hash="abc123",
            replay_hash="abc123",
            delta_summary="",
        )
        assert r.certification_status == CertificationStatus.CERTIFIED, \
            f"CERTIFIED check failed for {cls.name}"
        rec = r.to_record()
        assert rec["schema_id"] == "ph6.replay.certification_record.v1"
        assert rec["certification_status"] == "CERTIFIED"
        assert rec["operator_review_status"] == "PENDING"
        assert rec["ratified_by"] is None
        print(f"  PASS  {cls.name}")

    # FAILED path
    r_fail = ReplayResult(
        replay_class=ReplayClass.REPLAY_HASH,
        original_evidence_id="ev_fail",
        original_verdict_id="v_fail",
        same_evidence=True,
        hash_match=False,
        original_hash="abc",
        replay_hash="def",
        delta_summary="hash mismatch",
    )
    assert r_fail.certification_status == CertificationStatus.FAILED
    print(f"  PASS  FAILED_PATH")

    # DEGRADED path
    r_deg = ReplayResult(
        replay_class=ReplayClass.REPLAY_HASH,
        original_evidence_id="ev_deg",
        original_verdict_id="v_deg",
        same_evidence=True,
        hash_match=True,
        metrics_match=False,
        original_hash="abc",
        replay_hash="abc",
    )
    assert r_deg.certification_status == CertificationStatus.DEGRADED
    print(f"  PASS  DEGRADED_PATH")

    total = len(list(ReplayClass)) + 2
    print(f"\nRESULT: {total}/{total} PASS — all replay classes verified")
    return 0


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        sys.exit(self_test())
    print("PH6 Replay Engine loaded. Use --self-test to run self-test.")
