#!/usr/bin/env python3
import argparse
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
from ph6_common import read_jsonl, atomic_write_json, append_jsonl, canon_hash, now_utc

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--verdict-log", required=True)
    ap.add_argument("--commit-dir", required=True)
    ap.add_argument("--commit-log", required=True)
    args = ap.parse_args()
    commit_dir = Path(args.commit_dir)
    commit_dir.mkdir(parents=True, exist_ok=True)
    prev_commit_hash = "GENESIS"
    count = 0
    for verdict in read_jsonl(args.verdict_log):
        commit = {
            "schema": "ph6.cram_pu.commit.v1",
            "packet_id": verdict["packet_id"],
            "timestamp": now_utc(),
            "input_hash": verdict["input_hash"],
            "lane1_authority": verdict["lane1_authority"],
            "verdict": verdict["verdict"],
            "pseudo_metrics": verdict["pseudo_metrics"],
            "soso_authority": verdict["soso"]["authority"],
            "prev_commit_hash": prev_commit_hash
        }
        commit["commit_hash"] = canon_hash(commit)
        final_path = commit_dir / f'{verdict["packet_id"]}.commit.json'
        atomic_write_json(final_path, commit)
        event = {
            "schema": "ph6.cram_pu.commit_event.v1",
            "packet_id": verdict["packet_id"],
            "commit_path": str(final_path),
            "commit_hash": commit["commit_hash"],
            "prev_commit_hash": prev_commit_hash,
            "atomic_contract": "write_tmp_fsync_rename_fsync_parent"
        }
        append_jsonl(args.commit_log, event)
        prev_commit_hash = commit["commit_hash"]
        count += 1
    print(f"commits={count}")

if __name__ == "__main__":
    main()
