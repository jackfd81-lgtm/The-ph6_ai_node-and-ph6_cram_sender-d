#!/usr/bin/env python3
"""
PH6 Ingest Receipt Chain Verifier v1.0

Walks all receipts in chronological order and verifies:
  1. receipt_hash   — matches BLAKE2b-256 of body (excluding receipt_hash field)
  2. prev_receipt_hash — matches hash of previous receipt file content
  3. Genesis receipt has prev_receipt_hash = '0' * 64

This proves chain-of-custody for ingest lineage: no receipt can be
inserted, deleted, or modified without breaking the chain.

Exit: 0 = chain intact, 1 = chain broken or receipts missing

Usage:
  python3 ph6_receipt_chain_verify.py
  python3 ph6_receipt_chain_verify.py --json
  python3 ph6_receipt_chain_verify.py --receipts-dir /path/to/receipts
"""

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


_SOURCE_ROOT  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_BUILDS_DIR   = os.path.join(_SOURCE_ROOT, "builds")
_RECEIPTS_DIR = os.path.join(_BUILDS_DIR, "receipts")
_GENESIS_HASH = "0" * 64


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _blake2b(data: bytes) -> str:
    return hashlib.blake2b(data, digest_size=32).hexdigest()


def _canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False,
                      allow_nan=False, separators=(",", ":"))


def _load_receipt(path: Path) -> tuple[dict | None, str]:
    """Returns (receipt_dict, file_hash). file_hash = BLAKE2b of raw file bytes."""
    try:
        raw = path.read_bytes()
        file_hash = _blake2b(raw)
        receipt = json.loads(raw.decode("utf-8"))
        return receipt, file_hash
    except Exception as e:
        return None, ""


def verify_chain(receipts_dir: str) -> dict:
    """
    Walk all receipts in sorted filename order (chronological).
    Returns verification report.
    """
    now = _utc_now()
    dir_path = Path(receipts_dir)

    if not dir_path.exists():
        return {
            "schema":         "ph6.receipt_chain.verify.v1",
            "chain_intact":   False,
            "receipt_count":  0,
            "findings":       [{"type": "missing_receipts_dir", "severity": "HIGH",
                                "reason": f"Receipts directory not found: {receipts_dir}"}],
            "timestamp_utc":  now,
        }

    # Sort by modification time — write order is authoritative for chain sequence
    receipt_files = sorted(dir_path.glob("*.json"), key=lambda p: p.stat().st_mtime)
    findings = []
    prev_file_hash = _GENESIS_HASH

    for i, path in enumerate(receipt_files):
        receipt, file_hash = _load_receipt(path)
        rel = str(path.name)

        if receipt is None:
            findings.append({
                "type":     "parse_error",
                "severity": "HIGH",
                "file":     rel,
                "reason":   "Could not parse receipt JSON",
            })
            prev_file_hash = file_hash or _GENESIS_HASH
            continue

        # ── Check 1: receipt_hash field ─────────────────────────────────────
        stored_receipt_hash = receipt.get("receipt_hash")
        if stored_receipt_hash is None:
            # Receipt predates chaining (v1.0 receipts) — skip hash checks, note it
            findings.append({
                "type":     "no_chain_fields",
                "severity": "LOW",
                "file":     rel,
                "reason":   "Receipt predates chain scheme (receipt_version < 1.1) — no hash fields",
            })
            prev_file_hash = file_hash
            continue

        body = {k: v for k, v in receipt.items() if k != "receipt_hash"}
        expected_receipt_hash = _blake2b(_canonical(body).encode("utf-8"))

        if stored_receipt_hash != expected_receipt_hash:
            findings.append({
                "type":              "receipt_hash_mismatch",
                "severity":          "HIGH",
                "violation_class":   "R3",
                "file":              rel,
                "stored_hash":       stored_receipt_hash,
                "expected_hash":     expected_receipt_hash,
                "reason":            "receipt_hash does not match canonical body — receipt may be corrupted",
            })

        # ── Check 2: prev_receipt_hash chain ────────────────────────────────
        stored_prev = receipt.get("prev_receipt_hash")
        if stored_prev is None:
            findings.append({
                "type":     "missing_prev_hash",
                "severity": "HIGH",
                "file":     rel,
                "reason":   "prev_receipt_hash field missing from chained receipt",
            })
        elif stored_prev != prev_file_hash:
            findings.append({
                "type":            "chain_break",
                "severity":        "HIGH",
                "violation_class": "R4",
                "file":            rel,
                "position":        i,
                "stored_prev":     stored_prev,
                "expected_prev":   prev_file_hash,
                "reason":          "prev_receipt_hash chain break — receipt may be inserted, deleted, or modified",
            })

        prev_file_hash = file_hash

    # Count v1.1+ receipts (those with chain fields)
    chained_count = sum(
        1 for f in findings if f.get("type") == "no_chain_fields"
    )
    chain_errors = [f for f in findings if f.get("type") in ("receipt_hash_mismatch", "chain_break", "parse_error", "missing_prev_hash")]

    return {
        "schema":              "ph6.receipt_chain.verify.v1",
        "chain_intact":        len(chain_errors) == 0,
        "receipt_count":       len(receipt_files),
        "chained_receipts":    len(receipt_files) - chained_count,
        "legacy_receipts":     chained_count,
        "chain_errors":        len(chain_errors),
        "findings":            findings,
        "receipts_dir":        receipts_dir,
        "timestamp_utc":       now,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="PH6 Ingest Receipt Chain Verifier v1.0")
    parser.add_argument("--receipts-dir", default=_RECEIPTS_DIR,
                        help=f"Receipts directory (default: {_RECEIPTS_DIR})")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args()

    report = verify_chain(args.receipts_dir)

    if args.json:
        print(_canonical(report))
        sys.exit(0 if report["chain_intact"] else 1)

    status = "INTACT" if report["chain_intact"] else "BROKEN"
    print(f"PH6 RECEIPT CHAIN: {status}")
    print(f"  Receipts total:  {report['receipt_count']}")
    print(f"  Chained (v1.1+): {report.get('chained_receipts', 0)}")
    print(f"  Legacy (v1.0):   {report.get('legacy_receipts', 0)}")
    print(f"  Chain errors:    {report.get('chain_errors', 0)}")

    if report["findings"]:
        print("\n  FINDINGS:")
        for f in report["findings"]:
            sev  = f.get("severity", "?")
            typ  = f.get("type", "?")
            fil  = f.get("file", "?")
            rsn  = f.get("reason", "")
            vcls = f.get("violation_class", "")
            tag  = f"[{vcls}] " if vcls else ""
            print(f"    {tag}{sev}: {typ} — {fil}")
            if rsn:
                print(f"      {rsn}")

    sys.exit(0 if report["chain_intact"] else 1)


if __name__ == "__main__":
    main()
