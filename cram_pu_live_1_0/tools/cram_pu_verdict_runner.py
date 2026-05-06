#!/usr/bin/env python3
import argparse
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
from ph6_common import read_jsonl, append_jsonl, file_hash, blake2b256_bytes, now_utc

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

def soso_advisory(metrics):
    return {
        "schema": "ph6.soso.advisory.v1",
        "authority": "NONE",
        "comment": "advisory-only",
        "pattern_hint": "active" if metrics["entropy_proxy"] > 8 else "quiet"
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arrival-log", required=True)
    ap.add_argument("--verdict-log", required=True)
    args = ap.parse_args()
    arrivals = read_jsonl(args.arrival_log)
    for pkt in arrivals:
        path = Path(pkt["payload_path"])
        payload_hash = file_hash(path)
        metrics = pseudo_metrics(path)
        verdict = pseudo_verdict(metrics)
        soso = soso_advisory(metrics)
        record = {
            "schema": "ph6.cram_pu.verdict.v1",
            "packet_id": pkt["packet_id"],
            "arrival_seq": pkt["arrival_seq"],
            "timestamp": now_utc(),
            "input_hash": payload_hash,
            "lane1_authority": "PSEUDO",
            "verdict": verdict,
            "pseudo_metrics": metrics,
            "soso": soso,
            "authority_leakage": soso.get("authority") != "NONE",
            "verdict_basis_hash": blake2b256_bytes(
                f'{payload_hash}|{metrics}|PSEUDO'.encode("utf-8")
            )
        }
        append_jsonl(args.verdict_log, record)
    print(f"verdicts={len(arrivals)}")

if __name__ == "__main__":
    main()
