#!/usr/bin/env python3
"""
PH6 Replay Comparator

Reads pseudo_measurements.jsonl and recomputes summary digest.
Verifies counts and hash chain stability.

Read-only. Does not modify evidence.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, List


def _blake2b256_hex(data: bytes) -> str:
    return hashlib.blake2b(data, digest_size=32).hexdigest()


def _load_jsonl(path: Path) -> List[Dict[str, Any]]:
    records = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def compute_chain_digest(measurements: List[Dict[str, Any]]) -> str:
    """BLAKE2b-256 of all measurement_hash_blake2b256 values concatenated in order."""
    chain = "".join(
        m.get("measurement_hash_blake2b256", "") for m in measurements
    ).encode("utf-8")
    return _blake2b256_hex(chain)


def compute_summary_digest(
    total: int, passed: int, dropped: int, chain_digest: str
) -> str:
    payload = json.dumps(
        {
            "chain": chain_digest,
            "dropped": dropped,
            "passed": passed,
            "total": total,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return _blake2b256_hex(payload)


def run_compare(run_dir: Path) -> Dict[str, Any]:
    meas_path    = run_dir / "pseudo_measurements.jsonl"
    verdict_path = run_dir / "pseudo_verdicts.jsonl"
    digest_path  = run_dir / "replay_digest.json"

    measurements = _load_jsonl(meas_path)
    verdicts     = _load_jsonl(verdict_path)

    total   = len(measurements)
    passed  = sum(1 for v in verdicts if v.get("verdict") == "PASS")
    dropped = sum(1 for v in verdicts if v.get("verdict") == "DROP")

    chain_digest   = compute_chain_digest(measurements)
    summary_digest = compute_summary_digest(total, passed, dropped, chain_digest)

    stored: Dict[str, Any] = {}
    if digest_path.exists():
        with digest_path.open("r", encoding="utf-8") as f:
            stored = json.load(f)

    stored_digest = stored.get("summary_digest", "NOT_FOUND")
    if stored_digest == "NOT_FOUND":
        match = None
        status = "NO_STORED_DIGEST"
    else:
        match = (stored_digest == summary_digest)
        status = "MATCH" if match else "MISMATCH"

    return {
        "run_dir": str(run_dir),
        "total_records": total,
        "total_verdicts": len(verdicts),
        "pass_count": passed,
        "drop_count": dropped,
        "chain_digest": chain_digest,
        "summary_digest": summary_digest,
        "stored_digest": stored_digest,
        "digest_match": match,
        "replay_status": status,
    }


def main(argv: List[str]) -> int:
    if len(argv) < 2:
        print("Usage: replay_compare.py <run_dir>")
        return 1

    run_dir = Path(argv[1])
    if not run_dir.exists():
        print(f"ERROR: {run_dir} does not exist")
        return 1

    result = run_compare(run_dir)
    print(json.dumps(result, indent=2, sort_keys=True))

    if result["replay_status"] in ("MATCH", "NO_STORED_DIGEST"):
        print(f"\nReplay status: {result['replay_status']}")
        return 0
    else:
        print(f"\nReplay status: {result['replay_status']} — DIGEST MISMATCH")
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
