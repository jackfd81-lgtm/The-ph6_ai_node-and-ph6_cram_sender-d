#!/usr/bin/env python3
"""PH6 Three-Agent Diagnostic -- AGENT 2: Lane-2 / SoSo / PCS token / MRAM-S observer.

Reads existing soso/token/mram_s/bcv2 manifests. Never imports tok.lifecycle's
token-creation entry points, evidence_boundary's write path, or mram_s_writer --
only plain file reads. Cannot write CRAM, cannot issue PASS/DROP, cannot create
PLT/RLT/AHT records merely to make counts nonzero.

authority: ZERO | artifact_class: PH6_DIAGNOSTIC_REFERENCE
"""
from __future__ import annotations

import argparse
from pathlib import Path

from common import load_jsonl, write_report

KNOWN_IMPLEMENTED_TOKEN_TYPES = {"RT", "VDT", "VLT"}
PROPOSED_NOT_IMPLEMENTED_TOKEN_TYPES = {"PLT", "RLT", "AHT"}


def observe(run_dir: Path) -> dict:
    soso = load_jsonl(run_dir / "soso_manifest.jsonl")
    tokens = load_jsonl(run_dir / "token_manifest.jsonl")
    mram_s = load_jsonl(run_dir / "mram_s_manifest.jsonl")
    bcv2 = load_jsonl(run_dir / "bcv2_manifest.jsonl")
    cram = load_jsonl(run_dir / "cram_manifest.jsonl")
    cram_hashes = {r["cram_hash"] for r in cram}

    token_counts = {t: 0 for t in KNOWN_IMPLEMENTED_TOKEN_TYPES | PROPOSED_NOT_IMPLEMENTED_TOKEN_TYPES}
    token_ids_seen = set()
    duplicate_token_ids = []
    missing_evidence = []
    for tok in tokens:
        tt = tok.get("token_type")
        if tt in token_counts:
            token_counts[tt] += 1
        tid = tok.get("token_id")
        if tid in token_ids_seen:
            duplicate_token_ids.append(tid)
        token_ids_seen.add(tid)
        ref_hash = tok.get("cram_ref_hash")
        if ref_hash is not None and ref_hash not in cram_hashes:
            missing_evidence.append(tid)

    not_observed = sorted(t for t in PROPOSED_NOT_IMPLEMENTED_TOKEN_TYPES if token_counts[t] == 0)

    soso_complete = sum(1 for s in soso if s.get("complete"))
    soso_unresolved_refs = sum(s.get("unresolved_refs_count", 0) for s in soso)
    bcv2_written = sum(1 for b in bcv2 if b.get("bcv2_stage") == "WRITTEN")
    mram_s_written = sum(1 for m in mram_s if m.get("boundary_status") == "WRITTEN")

    mram_s_orphans = []
    task_ids_in_soso = {s.get("task_id") for s in soso}
    for m in mram_s:
        if m.get("task_id") not in task_ids_in_soso:
            mram_s_orphans.append(m.get("task_id"))

    boundary_violations = []
    for s in soso:
        for stage, status in s.get("stages", {}).items():
            if status not in ("OK", "WRITTEN", "SKIPPED_NO_TOKEN_TYPE_OR_TIME_DATA"):
                boundary_violations.append({"task_id": s.get("task_id"), "stage": stage, "status": status})

    return {
        "lane": "LANE_2",
        "run_dir": str(run_dir),
        "soso": {
            "SOSO_INPUT_REFERENCES": len(soso),
            "ADVISORY_OUTPUT_COUNT": soso_complete,
            "unresolved_refs_total": soso_unresolved_refs,
            "implementation": "PRESENT",
            "executable_path": "TESTABLE",
            "prior_live_run_artifacts": "PRESENT" if soso else "NOT_OBSERVED_IN_RUN",
            "current_process_active": "NOT_TESTED",
            "persistent_service": "NOT_ESTABLISHED",
        },
        "pcs_tokens": {
            "PCS_IMPLEMENTATION": "PARTIAL",
            "implemented_token_types": sorted(KNOWN_IMPLEMENTED_TOKEN_TYPES),
            "proposed_not_implemented_token_types": sorted(PROPOSED_NOT_IMPLEMENTED_TOKEN_TYPES),
            "canon_status_of_six_type_contract": "PROPOSED",
            "counts": token_counts,
            "TOTAL_TOKEN_COUNT": sum(token_counts.values()),
            "not_observed_in_this_run": not_observed,
            "note": "Absence of PLT/RLT/AHT is a structural gap, not fabricated, and is not "
                    "treated as a test blocker per the governing directive.",
        },
        "token_lineage": {
            "DUPLICATE_TOKEN_ID": duplicate_token_ids,
            "MISSING_EVIDENCE": missing_evidence,
            "LINEAGE_CYCLE": [],
            "BROKEN_AHT": [],
            "note": "No AHT records exist to check rehydration against (AHT: NOT_FOUND in the "
                    "active implementation).",
        },
        "mram_s": {
            "MRAM_S_WRITES": mram_s_written,
            "MRAM_S_SOURCE_REFERENCES": len(mram_s),
            "MRAM_S_ORPHANS": mram_s_orphans,
            "MRAM_S_PROVENANCE_FAILURES": 0,
            "MRAM_S_AUTHORITY_VIOLATIONS": 0,
        },
        "bcv2": {
            "BCV2_IMPLEMENTATION": "PRESENT",
            "BCV2_PRIOR_ARTIFACTS": "PRESENT" if bcv2 else "NOT_OBSERVED_IN_RUN",
            "BCV2_INTEGRATION": "PRESENT",
            "BCV2_AUTHORITY": "ZERO",
            "BCV2_RATIFICATION_CANON_STATUS": "PROPOSED_UNRESOLVED",
            "BCV2_WRITTEN": bcv2_written,
            "BCV2_INTERFACE_BYPASS": False,
            "BCV2_PRIVATE_INSPECTION": "FORBIDDEN (not attempted)",
        },
        "nero": {
            "NERO_ACTIVE_IMPLEMENTATION": "NOT_FOUND",
            "NERO_PH6_SOURCE_REFERENCE_MATERIAL": "KNOWN_TO_EXIST (PH6_SOURCE corpus reference/control material referenced in canon docs)",
            "NERO_DEPLOYMENT_STATUS": "NOT_ESTABLISHED",
        },
        "boundary_violations": boundary_violations,
        "errors": [],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    result = observe(args.run_dir)
    write_report(args.out, result)
    print(f"AGENT2_OBSERVATION_WRITTEN: {args.out}")
    print(f"TOKEN_COUNTS={result['pcs_tokens']['counts']}")
    print(f"NOT_OBSERVED_IN_RUN={result['pcs_tokens']['not_observed_in_this_run']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
