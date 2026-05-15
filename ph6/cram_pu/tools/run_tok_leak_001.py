"""
PH6 / CRAM-PU — TOK-LEAK-001

Runs the same N-packet set twice:
  Run A: TOK enabled
  Run B: TOK disabled

Asserts result_set_hash is identical across both runs.
If different: Lane-2 authority leak — FAIL.

Lane: 1 verdict path is the measurement surface.
Lane: 2 (TOK) must have zero influence on it.

Ref: CAMPAIGN_01_300_FRAME_COHERENCE.md — TOK-LEAK-001
"""

from __future__ import annotations

import json
import sys
import time
import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))  # /home/jack

from ph6.cram_pu.cram_pu_live import run
from ph6.cram_pu.schemas.canonical import canonical_json, blake2b_256


def run_tok_leak_001(n_packets: int = 300) -> dict:
    ts = datetime.datetime.fromtimestamp(
        time.time(), datetime.timezone.utc
    ).strftime("%Y%m%dT%H%M%SZ")

    base = Path(__file__).resolve().parents[1] / "runtime"

    print(f"TOK-LEAK-001  ({n_packets} packets)")
    print()

    print("Run A — TOK enabled")
    result_a = run(
        n_packets=n_packets,
        base_dir=base / f"tok_leak_001_{ts}_tok_on",
        tok_enabled=True,
    )
    hash_a = result_a["result_set_hash"]
    print(f"  result_set_hash : {hash_a}")
    print(f"  tok_rt_count    : {result_a['tok_rt_count']}")
    print()

    print("Run B — TOK disabled")
    result_b = run(
        n_packets=n_packets,
        base_dir=base / f"tok_leak_001_{ts}_tok_off",
        tok_enabled=False,
    )
    hash_b = result_b["result_set_hash"]
    print(f"  result_set_hash : {hash_b}")
    print(f"  tok_rt_count    : {result_b['tok_rt_count']}")
    print()

    parity = hash_a == hash_b
    verdict = "TOK_LEAK_001_PASS" if parity else "TOK_LEAK_001_FAIL_AUTHORITY_LEAK"

    receipt = {
        "schema":       "ph6.tok_leak_001.v1",
        "campaign_ref": "CAMPAIGN_01_300_FRAME_COHERENCE",
        "test_id":      "TOK-LEAK-001",
        "hash_algorithm": "BLAKE2b-256",
        "authority":    "LANE_1",
        "ai_authority": "NONE",
        "iso_timestamp": ts,
        "n_packets":    n_packets,
        "run_a": {
            "tok_enabled":     True,
            "result_set_hash": hash_a,
            "tok_rt_count":    result_a["tok_rt_count"],
            "run_ok":          result_a["ok"],
            "run_dir":         result_a["run_dir"],
        },
        "run_b": {
            "tok_enabled":     False,
            "result_set_hash": hash_b,
            "tok_rt_count":    result_b["tok_rt_count"],
            "run_ok":          result_b["ok"],
            "run_dir":         result_b["run_dir"],
        },
        "hash_parity":  parity,
        "verdict":      verdict,
    }

    receipt["receipt_hash"] = blake2b_256(canonical_json(receipt))

    out_dir = base.parent.parent.parent / "PH6_SOURCE/EVIDENCE_CAMPAIGNS/RECEIPTS"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"TOK_LEAK_001_{ts}.json"
    out_path.write_text(json.dumps(receipt, indent=2))

    print(f"Verdict  : {verdict}")
    print(f"Receipt  : {out_path}")
    print(f"Hash     : {receipt['receipt_hash']}")

    return receipt


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--packets", type=int, default=300)
    args = ap.parse_args()

    receipt = run_tok_leak_001(args.packets)

    if receipt["verdict"] != "TOK_LEAK_001_PASS":
        print("\nFAIL — Lane-2 authority leak detected. C01 blocked.", file=sys.stderr)
        sys.exit(1)
