"""
Phase 7 — CRAM-PU DROP shedding policy enforcer.
DROP packets may only be shed with an explicit policy_id and reason.
Every shed event is logged to shedding_log.jsonl before discard.
PASS packets must never be passed to this module.
"""

import json
import os
import sys
import time
from pathlib import Path

DEFAULT_POLICY_ID = "PH6-DROP-POLICY-v1"


def _append_jsonl(path: Path, record: dict) -> None:
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, sort_keys=True, separators=(",", ":"),
                           ensure_ascii=False, allow_nan=False))
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())


class SheddingPolicyEnforcer:
    def __init__(self, shedding_log: Path, policy_id: str = DEFAULT_POLICY_ID):
        self.shedding_log = shedding_log
        self.shedding_log.parent.mkdir(parents=True, exist_ok=True)
        self.policy_id = policy_id
        self._seq = 0

    def shed(self, verdict: dict) -> dict:
        if verdict["verdict"] == "PASS":
            raise ValueError(
                f"SheddingPolicyEnforcer.shed: PASS packets must never be shed. "
                f"packet_id={verdict['packet_id']!r}"
            )
        if verdict["verdict"] != "DROP":
            raise ValueError(f"Expected DROP, got {verdict['verdict']!r}")

        self._seq += 1
        reasons = verdict.get("reasons", [])
        reason_str = "; ".join(reasons) if reasons else "DROP_verdict_no_specific_reason"

        record = {
            "schema":    "ph6.drop_shedding.v1",
            "packet_id": verdict["packet_id"],
            "policy_id": self.policy_id,
            "reason":    reason_str,
            "shed_seq":  self._seq,
            "authority": "LANE_1",
            "timestamp": time.time(),
        }
        _append_jsonl(self.shedding_log, record)
        return record


def shed_drop_verdicts(verdicts: list, shedding_log: Path,
                       policy_id: str = DEFAULT_POLICY_ID) -> list:
    enforcer = SheddingPolicyEnforcer(shedding_log, policy_id)
    shed_records = []
    for v in verdicts:
        if v["verdict"] == "DROP":
            shed_records.append(enforcer.shed(v))
        elif v["verdict"] == "PASS":
            pass  # PASS never shed — not an error, just skip
    return shed_records


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--verdict-log",   required=True)
    ap.add_argument("--shedding-log",  required=True)
    ap.add_argument("--policy-id",     default=DEFAULT_POLICY_ID)
    args = ap.parse_args()
    with Path(args.verdict_log).open() as f:
        verdicts = [json.loads(l) for l in f if l.strip()]
    shed = shed_drop_verdicts(verdicts, Path(args.shedding_log), args.policy_id)
    print(f"SHED: {len(shed)} DROP packets logged under policy {args.policy_id!r}")
