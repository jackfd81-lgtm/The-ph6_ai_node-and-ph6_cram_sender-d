#!/usr/bin/env python3
import argparse
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
from ph6_common import read_jsonl, append_jsonl, write_json

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--verdict-log", required=True)
    ap.add_argument("--policy", required=False)
    ap.add_argument("--shedding-log", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    policy_present = bool(args.policy and Path(args.policy).exists())
    pass_shed_count = 0
    drop_shed_without_policy_count = 0
    drop_shed_count = 0
    for v in read_jsonl(args.verdict_log):
        if v["verdict"] == "PASS":
            continue
        if v["verdict"] == "DROP":
            if not policy_present:
                drop_shed_without_policy_count += 1
                continue
            drop_shed_count += 1
            append_jsonl(args.shedding_log, {
                "schema": "ph6.cram_pu.shedding_event.v1",
                "packet_id": v["packet_id"],
                "verdict": "DROP",
                "policy_id": "DROP_SHED_POLICY_TEST_1",
                "reason": "explicit test shedding policy present",
                "authority": "PSEUDO",
                "pass_shed": False
            })
    report = {
        "schema": "ph6.cram_pu.shedding_report.v1",
        "policy_present": policy_present,
        "pass_shed_count": pass_shed_count,
        "drop_shed_count": drop_shed_count,
        "drop_shed_without_policy_count": drop_shed_without_policy_count,
        "passed": pass_shed_count == 0 and drop_shed_without_policy_count == 0
    }
    write_json(args.out, report)
    print(f"shedding_passed={report['passed']}")

if __name__ == "__main__":
    main()
