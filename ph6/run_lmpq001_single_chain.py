#!/usr/bin/env python3
"""
ph6.run_lmpq001_single_chain

Runs the LMPQ-001 PM-01..PM-05 single-chain bench (ph6.lmpq001_single_chain_bench)
once, into a persistent output directory, and writes:

  result_summary.json     -- full ChainStepResult trace + missing components
  result_summary.sha256   -- sidecar hash of result_summary.json (compat only;
                              this is a bench report, not CRAM authority, so
                              no .blake2b marker is written here)

This script performs no CRAM writes of its own, issues no PASS/DROP, and
does not touch any authority file. It only calls run_single_chain() (which
does the real CRAM/tok/SoSo work inside its own bench_root) and serializes
the resulting report.

Usage: python3 ph6/run_lmpq001_single_chain.py <output_dir>
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from ph6.lmpq001_single_chain_bench import run_single_chain


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: run_lmpq001_single_chain.py <output_dir>", file=sys.stderr)
        return 2

    out_dir = Path(argv[1])
    out_dir.mkdir(parents=True, exist_ok=True)

    bench_root = out_dir / "bench_root"
    report = run_single_chain(bench_root)
    payload = report.to_dict()

    summary_path = out_dir / "result_summary.json"
    data = json.dumps(payload, indent=2, sort_keys=True, default=str).encode("utf-8")
    summary_path.write_bytes(data)

    digest = hashlib.sha256(data).hexdigest()
    (out_dir / "result_summary.sha256").write_text(digest + "\n")

    print(f"wrote {summary_path} (sha256={digest})")
    for step in report.steps:
        print(f"  [{step.status:>18}] {step.step}  ({step.component})")

    any_fail = any(s.status not in ("PASS_PENDING_REVIEW",) for s in report.steps)
    return 1 if any_fail else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
