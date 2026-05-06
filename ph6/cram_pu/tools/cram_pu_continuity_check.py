"""
Phase 4 — CRAM-PU continuity verifier.
Reads departure_log.jsonl + arrival_log.jsonl.
Verifies: all departures arrived, hashes match, no gaps, no duplicates.
Writes continuity_report.json.
"""

import json
import os
import sys
import time
from pathlib import Path


def _read_jsonl(path: Path) -> list:
    if not path.exists():
        return []
    records = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def run_continuity_check(departure_log: Path, arrival_log: Path,
                         report_path: Path) -> dict:
    departures = _read_jsonl(departure_log)
    arrivals   = _read_jsonl(arrival_log)

    dep_by_id  = {d["packet_id"]: d for d in departures}
    arr_by_id  = {a["packet_id"]: a for a in arrivals}

    # Duplicate detection
    dep_ids    = [d["packet_id"] for d in departures]
    arr_ids    = [a["packet_id"] for a in arrivals]
    dup_deps   = [pid for pid in dep_ids if dep_ids.count(pid) > 1]
    dup_arrs   = [pid for pid in arr_ids if arr_ids.count(pid) > 1]

    # Sequence gap detection (departure_seq must be 1..N with no gaps)
    dep_seqs   = sorted(d["departure_seq"] for d in departures)
    seq_gaps   = [dep_seqs[i] for i in range(1, len(dep_seqs))
                  if dep_seqs[i] != dep_seqs[i-1] + 1]

    # Pairing
    matched          = []
    orphan_departures = []
    orphan_arrivals   = []
    hash_mismatches   = []

    all_ids = set(dep_by_id) | set(arr_by_id)
    for pid in sorted(all_ids):
        dep = dep_by_id.get(pid)
        arr = arr_by_id.get(pid)
        if dep and not arr:
            orphan_departures.append(pid)
        elif arr and not dep:
            orphan_arrivals.append(pid)
        else:
            if dep["payload_hash"] != arr["received_hash"]:
                hash_mismatches.append({
                    "packet_id":   pid,
                    "dep_hash":    dep["payload_hash"],
                    "arr_hash":    arr["received_hash"],
                })
            else:
                matched.append(pid)

    ok = (
        len(orphan_departures) == 0
        and len(orphan_arrivals) == 0
        and len(hash_mismatches) == 0
        and len(seq_gaps) == 0
        and len(dup_deps) == 0
        and len(dup_arrs) == 0
    )

    report = {
        "schema":             "ph6.continuity_report.v1",
        "timestamp":          time.time(),
        "ok":                 ok,
        "matched":            len(matched),
        "orphan_departures":  orphan_departures,
        "orphan_arrivals":    orphan_arrivals,
        "hash_mismatches":    hash_mismatches,
        "sequence_gaps":      seq_gaps,
        "duplicate_dep_ids":  list(set(dup_deps)),
        "duplicate_arr_ids":  list(set(dup_arrs)),
    }

    report_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = report_path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(report, indent=2, sort_keys=True,
                               ensure_ascii=False, allow_nan=False))
    os.replace(str(tmp), str(report_path))

    return report


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--departure-log",  required=True)
    ap.add_argument("--arrival-log",    required=True)
    ap.add_argument("--report",         required=True)
    args = ap.parse_args()
    report = run_continuity_check(
        Path(args.departure_log),
        Path(args.arrival_log),
        Path(args.report),
    )
    status = "PASS" if report["ok"] else "FAIL"
    print(f"CONTINUITY: {status}  matched={report['matched']}  "
          f"orphan_dep={len(report['orphan_departures'])}  "
          f"orphan_arr={len(report['orphan_arrivals'])}  "
          f"hash_mismatch={len(report['hash_mismatches'])}")
    sys.exit(0 if report["ok"] else 1)
