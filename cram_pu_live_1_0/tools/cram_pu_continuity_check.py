#!/usr/bin/env python3
import argparse
from collections import Counter
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
from ph6_common import read_jsonl, write_json

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--departure-log", required=True)
    ap.add_argument("--arrival-log", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    dep = read_jsonl(args.departure_log)
    arr = read_jsonl(args.arrival_log)
    dep_by_id = {p["packet_id"]: p for p in dep}
    arr_by_id = {p["packet_id"]: p for p in arr}
    duplicate_departures = [k for k,v in Counter(p["packet_id"] for p in dep).items() if v > 1]
    duplicate_arrivals = [k for k,v in Counter(p["packet_id"] for p in arr).items() if v > 1]
    missing_arrivals = sorted(set(dep_by_id) - set(arr_by_id))
    orphan_arrivals = sorted(set(arr_by_id) - set(dep_by_id))
    hash_mismatches = [pid for pid in sorted(set(dep_by_id) & set(arr_by_id))
                       if dep_by_id[pid]["payload_hash"] != arr_by_id[pid]["received_hash"]]
    seqs = sorted(p["departure_seq"] for p in dep)
    sequence_gap = seqs != list(range(1, len(seqs)+1))
    passed = (not duplicate_departures and not duplicate_arrivals and
              not missing_arrivals and not orphan_arrivals and
              not hash_mismatches and not sequence_gap)
    report = {
        "schema": "ph6.cram_pu.continuity_report.v1",
        "passed": passed,
        "departure_count": len(dep),
        "arrival_count": len(arr),
        "duplicate_departures": duplicate_departures,
        "duplicate_arrivals": duplicate_arrivals,
        "missing_arrivals": missing_arrivals,
        "orphan_arrivals": orphan_arrivals,
        "hash_mismatches": hash_mismatches,
        "sequence_gap": sequence_gap,
        "departure_sequences": seqs
    }
    write_json(args.out, report)
    print(f"continuity_passed={passed}")

if __name__ == "__main__":
    main()
