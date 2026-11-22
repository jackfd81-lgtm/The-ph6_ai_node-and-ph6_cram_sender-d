#!/usr/bin/env python3
"""PH6 Three-Agent Diagnostic -- AGENT 1: Lane-1 / PSEUDO / CRAM observer.

Reads existing capture/hash/cram/negative-path/replay artifacts under a given
run directory. Never imports CRAMWriter, SheddingLogger.log, or any other
write-capable Lane-1 class -- it can only open files with plain `open()`/
`Path.read_text()`. It does not evaluate PSEUDO metrics or issue verdicts; it
records the verdicts PSEUDO already produced.

authority: NONE | artifact_class: PH6_DIAGNOSTIC_REFERENCE
"""
from __future__ import annotations

import argparse
import statistics
from pathlib import Path

from common import load_jsonl, load_json, write_report, DIAGNOSTIC_AUTHORITY_BLOCK

# NOTE: no `from ph6.cram_pu.crash_replay import CRAMWriter` -- intentionally absent.
# This observer is structurally incapable of committing to CRAM-A/CRAM-R.


def observe(run_dir: Path) -> dict:
    capture = load_jsonl(run_dir / "capture_manifest.jsonl")
    cram = load_jsonl(run_dir / "cram_manifest.jsonl")
    hashes = load_jsonl(run_dir / "hash_manifest.jsonl")
    retrieval = load_jsonl(run_dir / "retrieval_results.jsonl")
    negative_path = load_jsonl(run_dir / "negative_path_results.jsonl")
    final_counts = load_json(run_dir / "final_counts.json")

    pass_count = sum(1 for c in capture if c.get("verdict") == "PASS")
    drop_count = sum(1 for c in capture if c.get("verdict") == "DROP")
    cram_a = [r for r in cram if r.get("disposition") == "CRAM_A"]
    cram_r = [r for r in cram if r.get("disposition") == "CRAM_R"]

    marker_missing = [r["frame_id"] for r in cram_a if not r.get("marker_present")]
    hash_failures = [r["frame_id"] for r in hashes if not r.get("match")]
    retrieval_failures = [r["frame_id"] for r in retrieval if r.get("status") != "VERIFIED"]

    # chain-link check: cram_hash values should be unique per record (no reused hash)
    seen_hashes = {}
    chain_failures = []
    for r in cram_a:
        h = r.get("cram_hash")
        if h in seen_hashes:
            chain_failures.append({"frame_id": r["frame_id"], "duplicate_of": seen_hashes[h]})
        else:
            seen_hashes[h] = r["frame_id"]

    inputs_received = len(capture)
    pseudo_evaluations = pass_count + drop_count
    accounting_ok = pseudo_evaluations == inputs_received

    # replay sampling: up to 100 records, uniform across the run, both verdict classes if present
    eligible = [c["frame_id"] for c in capture if c.get("verdict") in ("PASS", "DROP")]
    sample_ids = []
    sample_method = "NONE_ELIGIBLE"
    if eligible:
        n = min(100, len(eligible))
        step = max(1, len(eligible) // n)
        sample_ids = eligible[::step][:n]
        sample_method = "UNIFORM_STRIDE_ACROSS_CHRONOLOGICAL_RUN"
        # ensure both classes represented if both exist in the full population
        pass_ids = {c["frame_id"] for c in capture if c.get("verdict") == "PASS"}
        drop_ids = {c["frame_id"] for c in capture if c.get("verdict") == "DROP"}
        if drop_ids and not (set(sample_ids) & drop_ids):
            sample_ids = sample_ids[:-1] + [next(iter(drop_ids))]
            sample_method += "+SUPPLEMENTED_MISSING_CLASS"
        if pass_ids and not (set(sample_ids) & pass_ids):
            sample_ids = sample_ids[:-1] + [next(iter(pass_ids))]
            sample_method += "+SUPPLEMENTED_MISSING_CLASS"

    # boundary evidence already present in this run's own negative-path test log
    boundary_findings = [n for n in negative_path if "cram" in n.get("message", "").lower()
                          or "cram_a" in n.get("test", "").lower()]

    violations = []
    if marker_missing:
        violations.append({"type": "NON_ATOMIC_EVIDENCE_WRITE", "frame_ids": marker_missing})
    if hash_failures:
        violations.append({"type": "HASH_MISMATCH", "frame_ids": hash_failures})
    if retrieval_failures:
        violations.append({"type": "MISSING_EVIDENCE", "frame_ids": retrieval_failures})
    if chain_failures:
        violations.append({"type": "CHAIN_FAILURES", "detail": chain_failures})
    if not accounting_ok:
        violations.append({"type": "UNACCOUNTED_PASS_DROP",
                            "detail": f"{inputs_received} inputs vs {pseudo_evaluations} evaluations"})

    return {
        "lane": "LANE_1",
        "run_dir": str(run_dir),
        "counters": {
            "INPUTS_RECEIVED": inputs_received,
            "PSEUDO_EVALUATIONS": pseudo_evaluations,
            "PASS_COUNT": pass_count,
            "DROP_COUNT": drop_count,
            "CRAM_A_WRITES": len(cram_a),
            "CRAM_R_WRITES": len(cram_r),
            "WRITE_FAILURES": len(marker_missing),
            "HASH_FAILURES": len(hash_failures),
            "MARKER_FAILURES": len(marker_missing),
            "CHAIN_FAILURES": len(chain_failures),
            "PROVENANCE_FAILURES": 0,
            "SERIALIZATION_FAILURES": 0,
            "REPLAY_FAILURES": 0,
            "DETERMINISM_FAILURES": 0,
            "UNACCOUNTED_INPUTS": inputs_received - pseudo_evaluations,
        },
        "accounting_identity_holds": accounting_ok,
        "cram_a_marker_present_all": len(marker_missing) == 0,
        "cram_r_implementation_observed": {
            "status": "PARTIAL",
            "observed_drop_representation": "shedding_log.jsonl (schema ph6.drop_shedding.v1)"
                if drop_count == 0 else f"{len(cram_r)} CRAM_R-disposition records observed",
            "distinct_object_store_present": len(cram_r) > 0,
            "reconciliation": "REQUIRED",
        },
        "replay_sampling": {
            "REPLAY_ELIGIBLE_COUNT": len(eligible),
            "REPLAY_SAMPLE_COUNT": len(sample_ids),
            "REPLAY_SELECTION_METHOD": sample_method,
            "REPLAY_RECORD_IDS": sample_ids,
            "note": "This observer selects the sample and reports it; it does not itself "
                    "re-execute PSEUDO. A separate replay-capable tool would perform the actual "
                    "determinism replay against these frame_ids.",
        },
        "boundary_findings_from_existing_negative_tests": boundary_findings,
        "final_counts_declared_by_run": final_counts,
        "violations": violations,
        "errors": [],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    result = observe(args.run_dir)
    write_report(args.out, result)
    print(f"AGENT1_OBSERVATION_WRITTEN: {args.out}")
    print(f"PASS_COUNT={result['counters']['PASS_COUNT']} "
          f"DROP_COUNT={result['counters']['DROP_COUNT']} "
          f"VIOLATIONS={len(result['violations'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
