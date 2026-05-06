#!/usr/bin/env python3
import argparse
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
from ph6_common import read_jsonl, read_json, write_json, file_hash

def pseudo_metrics(path: Path):
    data = path.read_bytes()
    if not data:
        return {"entropy_proxy": 0, "laplacian_proxy": 0, "motion_proxy": 0}
    unique = len(set(data))
    transitions = sum(1 for a,b in zip(data, data[1:]) if a != b)
    avg = sum(data) // len(data)
    return {"entropy_proxy": unique, "laplacian_proxy": transitions, "motion_proxy": avg}

def pseudo_verdict(metrics):
    score = metrics["entropy_proxy"] + metrics["laplacian_proxy"]
    return "PASS" if score >= 16 else "DROP"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arrival-log", required=True)
    ap.add_argument("--verdict-log", required=True)
    ap.add_argument("--commit-log", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    arrivals = {x["packet_id"]: x for x in read_jsonl(args.arrival_log)}
    verdicts = {x["packet_id"]: x for x in read_jsonl(args.verdict_log)}
    commit_events = read_jsonl(args.commit_log)
    mismatches = []
    checked = 0
    for packet_id, original in verdicts.items():
        path = Path(arrivals[packet_id]["payload_path"])
        replay_hash = file_hash(path)
        replay_metrics = pseudo_metrics(path)
        replay_verdict = pseudo_verdict(replay_metrics)
        if replay_hash != original["input_hash"]:
            mismatches.append({"packet_id": packet_id, "reason": "input_hash_mismatch"})
        if replay_metrics != original["pseudo_metrics"]:
            mismatches.append({"packet_id": packet_id, "reason": "metrics_mismatch"})
        if replay_verdict != original["verdict"]:
            mismatches.append({"packet_id": packet_id, "reason": "verdict_mismatch"})
        checked += 1
    chain_valid = True
    prev = "GENESIS"
    for ev in commit_events:
        commit = read_json(ev["commit_path"])
        if commit["prev_commit_hash"] != prev:
            chain_valid = False
        if commit["commit_hash"] != ev["commit_hash"]:
            chain_valid = False
        prev = commit["commit_hash"]
    report = {
        "schema": "ph6.cram_pu.replay_report.v1",
        "checked": checked,
        "mismatches": mismatches,
        "replay_match": not mismatches,
        "commit_chain_valid": chain_valid,
        "passed": not mismatches and chain_valid
    }
    write_json(args.out, report)
    print(f"replay_passed={report['passed']}")

if __name__ == "__main__":
    main()
