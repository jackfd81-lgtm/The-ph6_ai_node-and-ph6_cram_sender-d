#!/usr/bin/env python3
import argparse
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
from ph6_common import read_jsonl, read_json, write_json, canon_hash

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--departure-log", required=True)
    ap.add_argument("--arrival-log", required=True)
    ap.add_argument("--continuity-report", required=True)
    ap.add_argument("--verdict-log", required=True)
    ap.add_argument("--commit-log", required=True)
    ap.add_argument("--shedding-report", required=True)
    ap.add_argument("--replay-report", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    dep = read_jsonl(args.departure_log)
    arr = read_jsonl(args.arrival_log)
    verdicts = read_jsonl(args.verdict_log)
    commits = read_jsonl(args.commit_log)
    continuity = read_json(args.continuity_report)
    shedding = read_json(args.shedding_report)
    replay = read_json(args.replay_report)
    authority_leakage = any(v.get("authority_leakage") for v in verdicts)
    pass_shed_count = shedding["pass_shed_count"]
    drop_shed_without_policy_count = shedding["drop_shed_without_policy_count"]
    passed = (
        continuity["passed"] and
        replay["passed"] and
        shedding["passed"] and
        not authority_leakage and
        len(dep) == len(arr) == len(verdicts) == len(commits) and
        len(dep) > 0
    )
    receipt = {
        "schema": "ph6.cram_pu.receipt.v1",
        "milestone": "CRAM-PU-LIVE-1.0",
        "cram_pu_live_1_0_pass": passed,
        "departure_count": len(dep),
        "arrival_count": len(arr),
        "verdict_count": len(verdicts),
        "commit_count": len(commits),
        "continuity_passed": continuity["passed"],
        "replay_match": replay["replay_match"],
        "commit_chain_valid": replay["commit_chain_valid"],
        "authority_leakage": authority_leakage,
        "pass_shed_count": pass_shed_count,
        "drop_shed_without_policy_count": drop_shed_without_policy_count
    }
    receipt["receipt_hash"] = canon_hash(receipt)
    write_json(args.out, receipt)
    print(f"CRAM_PU_LIVE_1_0_PASS={passed}")

if __name__ == "__main__":
    main()
