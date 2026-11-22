#!/usr/bin/env python3
"""PH6 Three-Agent Diagnostic -- AGENT 3: whole-system / cross-lane observer.

Independently re-examines the same underlying records Agent 1/Agent 2 read
(never merely summarizes their output), correlates them by native identifier,
and checks for reverse-authority flow. Read-only; writes only its own report.

authority: NONE | artifact_class: PH6_DIAGNOSTIC_REFERENCE
"""
from __future__ import annotations

import argparse
from pathlib import Path

from common import load_jsonl, write_report


def observe(run_dir: Path) -> dict:
    capture = load_jsonl(run_dir / "capture_manifest.jsonl")
    cram = load_jsonl(run_dir / "cram_manifest.jsonl")
    tokens = load_jsonl(run_dir / "token_manifest.jsonl")
    soso = load_jsonl(run_dir / "soso_manifest.jsonl")
    mram_s = load_jsonl(run_dir / "mram_s_manifest.jsonl")
    bcv2 = load_jsonl(run_dir / "bcv2_manifest.jsonl")
    negative_path = load_jsonl(run_dir / "negative_path_results.jsonl")

    cram_by_frame = {r["frame_id"]: r for r in cram}
    capture_by_frame = {c["frame_id"]: c for c in capture}
    # NOTE: token.cram_ref_hash is keyed against capture_manifest's input_hash (the raw-input
    # identity RT genesis tokens reference), NOT cram_manifest's cram_hash (the post-commit CRAM
    # record hash) -- these are two distinct native-ID domains that happen to share a naming
    # collision-prone prefix ("hash"). An earlier version of this observer joined on the wrong
    # one and reported 0 complete chains; fixed by joining on the correct native identifier.
    token_by_input_hash = {}
    for t in tokens:
        token_by_input_hash.setdefault(t.get("cram_ref_hash"), []).append(t)

    complete_chains = 0
    partial_chains = 0
    broken_chains = 0
    orphaned_lane1 = []
    orphaned_lane2_task_ids = set()

    frame_to_batch = {}
    for s in soso:
        for fid in range(s.get("frame_id_first", 0), s.get("frame_id_last", -1) + 1):
            frame_to_batch[fid] = s.get("task_id")

    for frame_id, cram_rec in cram_by_frame.items():
        input_hash = capture_by_frame.get(frame_id, {}).get("input_hash")
        toks = token_by_input_hash.get(input_hash, [])
        batch = frame_to_batch.get(frame_id)
        has_soso = batch is not None
        has_mram_s = any(m.get("task_id") == batch for m in mram_s) if batch else False
        stages = [len([1]), bool(toks), has_soso, has_mram_s]
        n_present = sum(1 for x in stages if x)
        if n_present == 4:
            complete_chains += 1
        elif n_present == 1:
            broken_chains += 1
            orphaned_lane1.append(frame_id)
        else:
            partial_chains += 1

    soso_task_ids = {s.get("task_id") for s in soso}
    mram_s_task_ids = {m.get("task_id") for m in mram_s}
    orphaned_lane2 = sorted(mram_s_task_ids - soso_task_ids)

    # reverse-authority check: scan the run's own negative-path test log for anything
    # that indicates a reverse-flow attempt was tried and what happened to it.
    reverse_flow_evidence = [n for n in negative_path if any(
        kw in (n.get("test", "") + n.get("message", "")).lower()
        for kw in ("forged", "lane2", "cram_a_pass_write", "unauthorized_destination"))]
    reverse_flow_all_rejected = all(n.get("rejected", n.get("classification") == "DRIFT_FAIL")
                                     for n in reverse_flow_evidence) if reverse_flow_evidence else None

    return {
        "lane": "WHOLE_SYSTEM",
        "run_dir": str(run_dir),
        "end_to_end_correlation": {
            "END_TO_END_CORRELATIONS": len(cram_by_frame),
            "COMPLETE_CHAINS": complete_chains,
            "PARTIAL_CHAINS": partial_chains,
            "BROKEN_CHAINS": broken_chains,
            "ORPHANED_LANE1_RECORDS": orphaned_lane1,
            "ORPHANED_LANE2_RECORDS": orphaned_lane2,
        },
        "ordering_causality": {
            "expected_order": "REALITY -> PSEUDO -> CRAM -> reference -> SoSo -> token continuity -> MRAM-S advisory output",
            "REVERSE_AUTHORITY_VIOLATIONS": [] if reverse_flow_all_rejected or reverse_flow_all_rejected is None else reverse_flow_evidence,
            "reverse_flow_attempts_found_in_existing_negative_tests": len(reverse_flow_evidence),
            "reverse_flow_attempts_all_rejected": reverse_flow_all_rejected,
        },
        "resource_interference": {
            "note": "Not measured in this dry-run pass (no live process to sample); this "
                    "observer supports raw-metric collection (latency count/mean/median/p95/"
                    "p99/max, CPU/mem/I/O/temp) once attached to a live run. No threshold is "
                    "invented here.",
            "LANE1_STARVATION_CLASSIFICATION": "DEFERRED_TO_REVIEW",
        },
        "cross_agent_reconciliation": {
            "note": "Cross-checked directly against cram_manifest.jsonl/token_manifest.jsonl/"
                    "soso_manifest.jsonl/mram_s_manifest.jsonl independently, not by reading "
                    "Agent 1/Agent 2's output files.",
            "lane1_evidence_ids_referenced_by_lane2_all_exist": len(
                [t for t in tokens if t.get("cram_ref_hash") not in
                 {c["input_hash"] for c in capture}]
            ) == 0,
        },
        "protected_path_write_capability": "NONE (structurally -- this module performs no writes "
                                            "outside its own --out report path)",
        "errors": [],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    result = observe(args.run_dir)
    write_report(args.out, result)
    print(f"AGENT3_OBSERVATION_WRITTEN: {args.out}")
    print(f"COMPLETE_CHAINS={result['end_to_end_correlation']['COMPLETE_CHAINS']} "
          f"BROKEN_CHAINS={result['end_to_end_correlation']['BROKEN_CHAINS']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
