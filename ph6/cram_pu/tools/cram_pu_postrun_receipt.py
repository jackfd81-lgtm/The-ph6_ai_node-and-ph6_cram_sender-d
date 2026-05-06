"""
Phase 9 — CRAM-PU postrun closure receipt.
Reads all output artifacts, computes final pass/fail, writes postrun_receipt.json.
"""

import hashlib
import json
import os
import sys
import time
import uuid
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


def _canonical_bytes(obj: dict) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def _blake2b256(obj: dict) -> str:
    return hashlib.blake2b(_canonical_bytes(obj), digest_size=32).hexdigest()


def build_receipt(run_dir: Path, receipt_path: Path) -> dict:
    verdicts    = _read_jsonl(run_dir / "verdicts.jsonl")
    shedding    = _read_jsonl(run_dir / "shedding_log.jsonl")
    cram_files  = sorted((run_dir / "cram_commits").glob("cram_*.json")) \
                  if (run_dir / "cram_commits").exists() else []

    continuity_report = {}
    if (run_dir / "continuity_report.json").exists():
        continuity_report = json.loads((run_dir / "continuity_report.json").read_text())

    replay_report = {}
    if (run_dir / "replay_report.json").exists():
        replay_report = json.loads((run_dir / "replay_report.json").read_text())

    passes   = [v for v in verdicts if v.get("verdict") == "PASS"]
    drops    = [v for v in verdicts if v.get("verdict") == "DROP"]

    shed_ids = {s["packet_id"] for s in shedding}
    drop_ids = {v["packet_id"] for v in drops}

    # PASS silently dropped if any PASS verdict has no matching CRAM commit
    committed_pids = set()
    for cf in cram_files:
        with cf.open() as f:
            rec = json.load(f)
            committed_pids.add(rec["packet_id"])

    pass_silently_dropped = any(v["packet_id"] not in committed_pids for v in passes)

    # DROP shed without policy: any DROP not in shedding_log
    drop_shed_without_policy = any(pid not in shed_ids for pid in drop_ids)

    # SoSo influenced verdict: check no soso field that changes authority
    soso_influenced = False
    for v in verdicts:
        soso = v.get("soso_advisory", {})
        if soso.get("authority", "NONE") != "NONE":
            soso_influenced = True
            break

    runtime_wired = (
        continuity_report.get("ok", False)
        and replay_report.get("ok", False)
        and not pass_silently_dropped
        and not drop_shed_without_policy
        and not soso_influenced
        and replay_report.get("chain_valid", False)
    )

    receipt = {
        "schema":                   "ph6.cram_pu.receipt.v1",
        "receipt_id":               str(uuid.uuid4()),
        "runtime_wired":            runtime_wired,
        "packets_total":            len(verdicts),
        "packets_passed":           len(passes),
        "packets_dropped":          len(drops),
        "packets_shed":             len(shedding),
        "cram_commits":             len(cram_files),
        "replay_matches":           replay_report.get("replayed", 0),
        "chain_valid":              replay_report.get("chain_valid", False),
        "soso_influenced_verdict":  soso_influenced,
        "pass_silently_dropped":    pass_silently_dropped,
        "drop_shed_without_policy": drop_shed_without_policy,
        "rsync_blocked":            False,
        "continuity_ok":            continuity_report.get("ok", False),
        "replay_ok":                replay_report.get("ok", False),
        "timestamp":                time.time(),
    }
    receipt["receipt_hash"] = _blake2b256(
        {k: v for k, v in receipt.items() if k != "receipt_hash"}
    )

    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = receipt_path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(receipt, indent=2, sort_keys=True,
                               ensure_ascii=False, allow_nan=False))
    os.replace(str(tmp), str(receipt_path))

    return receipt


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir",  required=True)
    ap.add_argument("--receipt",  required=True)
    args = ap.parse_args()
    receipt = build_receipt(Path(args.run_dir), Path(args.receipt))
    wired = receipt["runtime_wired"]
    print(f"CRAM_PU_RUNTIME_WIRED = {'true' if wired else 'false'}")
    sys.exit(0 if wired else 1)
