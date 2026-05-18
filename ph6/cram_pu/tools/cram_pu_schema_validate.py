#!/usr/bin/env python3
"""
CRAM-PU schema validator.
Validates departure/arrival/verdict/commit/shedding records
against ph6 protocol field requirements without external deps.

Called from cram_pu_live.py after each run.
Returns a list of error strings; empty list = PASS.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import List

HEX64 = re.compile(r"^[0-9a-f]{64}$")


# ---------------------------------------------------------------------------
# Per-record validators
# ---------------------------------------------------------------------------

def _check_departure(rec: dict, idx: int) -> List[str]:
    errs = []
    pfx  = f"departure[{idx}]"
    if rec.get("schema") != "ph6.raw_departure.v1":
        errs.append(f"{pfx} schema mismatch: {rec.get('schema')!r}")
    if not isinstance(rec.get("frame_id"), int):
        errs.append(f"{pfx} frame_id missing or not int")
    ph = rec.get("payload_hash", "")
    if not HEX64.match(ph):
        errs.append(f"{pfx} payload_hash not 64-hex: {ph!r}")
    if rec.get("hash_algorithm") != "BLAKE2b-256":
        errs.append(f"{pfx} hash_algorithm must be 'BLAKE2b-256', got {rec.get('hash_algorithm')!r}")
    if rec.get("authority") != "NONE":
        errs.append(f"{pfx} authority must be NONE, got {rec.get('authority')!r}")
    return errs


def _check_arrival(rec: dict, idx: int) -> List[str]:
    errs = []
    pfx  = f"arrival[{idx}]"
    if rec.get("schema") != "ph6.raw_arrival.v1":
        errs.append(f"{pfx} schema mismatch: {rec.get('schema')!r}")
    if not isinstance(rec.get("frame_id"), int):
        errs.append(f"{pfx} frame_id missing or not int")
    ph = rec.get("payload_hash", "")
    if not HEX64.match(ph):
        errs.append(f"{pfx} payload_hash not 64-hex: {ph!r}")
    if rec.get("hash_algorithm") != "BLAKE2b-256":
        errs.append(f"{pfx} hash_algorithm must be 'BLAKE2b-256', got {rec.get('hash_algorithm')!r}")
    if rec.get("transfer_status") not in ("OK", "HASH_MISMATCH"):
        errs.append(f"{pfx} invalid transfer_status: {rec.get('transfer_status')!r}")
    if rec.get("authority") != "LANE_1":
        errs.append(f"{pfx} authority must be LANE_1, got {rec.get('authority')!r}")
    return errs


def _check_verdict(rec: dict, idx: int) -> List[str]:
    errs = []
    pfx  = f"verdict[{idx}]"
    if rec.get("schema") not in ("ph6.pseudo_verdict.v1", "ph6.pseudo_verdict.v2",
                                  "ph6.pseudo_verdict.camera.v1"):
        errs.append(f"{pfx} schema mismatch: {rec.get('schema')!r}")
    if not isinstance(rec.get("frame_id"), int):
        errs.append(f"{pfx} frame_id missing or not int")
    if rec.get("verdict") not in ("PASS", "DROP"):
        errs.append(f"{pfx} verdict must be PASS or DROP, got {rec.get('verdict')!r}")
    if rec.get("authority") != "LANE_1":
        errs.append(f"{pfx} authority must be LANE_1, got {rec.get('authority')!r}")
    if rec.get("hash_algorithm") != "BLAKE2b-256":
        errs.append(f"{pfx} hash_algorithm must be 'BLAKE2b-256', got {rec.get('hash_algorithm')!r}")
    soso = rec.get("soso_advisory", {})
    if soso.get("authority") != "NONE":
        errs.append(f"{pfx} soso_advisory.authority must be NONE — authority leakage detected")
    ih = rec.get("input_hash", "")
    if not HEX64.match(ih):
        errs.append(f"{pfx} input_hash not 64-hex: {ih!r}")
    return errs


def _check_commit(rec: dict, path: str) -> List[str]:
    errs = []
    pfx  = f"commit[{path}]"
    if rec.get("schema") != "ph6.cram_commit.v1":
        errs.append(f"{pfx} schema mismatch: {rec.get('schema')!r}")
    if not isinstance(rec.get("frame_id"), int):
        errs.append(f"{pfx} frame_id missing or not int")
    if rec.get("verdict") != "PASS":
        errs.append(f"{pfx} verdict must be PASS, got {rec.get('verdict')!r}")
    if rec.get("authority") != "LANE_1":
        errs.append(f"{pfx} authority must be LANE_1, got {rec.get('authority')!r}")
    if rec.get("hash_algorithm") != "BLAKE2b-256":
        errs.append(f"{pfx} hash_algorithm must be 'BLAKE2b-256', got {rec.get('hash_algorithm')!r}")
    for field in ("cram_hash", "prev_cram_hash", "payload_hash"):
        v = rec.get(field, "")
        if not HEX64.match(v):
            errs.append(f"{pfx} {field} not 64-hex: {v!r}")
    return errs


def _check_shedding(rec: dict, idx: int) -> List[str]:
    errs = []
    pfx  = f"shedding[{idx}]"
    if rec.get("schema") != "ph6.drop_shedding.v1":
        errs.append(f"{pfx} schema mismatch: {rec.get('schema')!r}")
    if not isinstance(rec.get("frame_id"), int):
        errs.append(f"{pfx} frame_id missing or not int")
    if not rec.get("policy_ref"):
        errs.append(f"{pfx} policy_ref missing or empty")
    if rec.get("authority") != "LANE_1":
        errs.append(f"{pfx} authority must be LANE_1, got {rec.get('authority')!r}")
    return errs


# ---------------------------------------------------------------------------
# Run-dir validator (called from cram_pu_live.py)
# ---------------------------------------------------------------------------

def _read_jsonl(path: Path) -> List[dict]:
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            out.append(json.loads(line))
    return out


def validate_run_dir(paths) -> List[str]:
    """Validate all log records in a CRAMPaths layout. Returns list of errors."""
    errs: List[str] = []

    for i, rec in enumerate(_read_jsonl(paths.departure_log)):
        errs.extend(_check_departure(rec, i))

    for i, rec in enumerate(_read_jsonl(paths.arrival_log)):
        errs.extend(_check_arrival(rec, i))

    for i, rec in enumerate(_read_jsonl(paths.verdict_log)):
        errs.extend(_check_verdict(rec, i))

    for p in sorted(paths.cram_store.glob("cram_*.json")):
        with p.open("r", encoding="utf-8") as f:
            rec = json.load(f)
        errs.extend(_check_commit(rec, p.name))

    for i, rec in enumerate(_read_jsonl(paths.shedding_log)):
        errs.extend(_check_shedding(rec, i))

    return errs


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse, sys
    from ph6.cram_pu.crash_replay import CRAMPaths
    HERE = Path(__file__).resolve()
    sys.path.insert(0, str(HERE.parent.parent.parent.parent))

    ap = argparse.ArgumentParser()
    ap.add_argument("--cram-store", required=True, type=Path)
    ap.add_argument("--mram-s",     required=True, type=Path)
    args = ap.parse_args()

    paths = CRAMPaths(cram_store=args.cram_store, mram_s=args.mram_s)
    errs  = validate_run_dir(paths)
    if errs:
        for e in errs:
            print(f"ERROR: {e}")
        sys.exit(1)
    print("SCHEMA_VALID=True")
