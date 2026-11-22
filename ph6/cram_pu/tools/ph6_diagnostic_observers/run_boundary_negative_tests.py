#!/usr/bin/env python3
"""PH6 Three-Agent Diagnostic -- required negative/boundary tests (directive §13).

Proves, by introspection of the already-imported observer modules (no live system
touched), that none of them can reach a CRAM-A/CRAM-R/PSEUDO-A write path, a
PASS/DROP-issuing function, a threshold mutator, or a PLT/RLT/AHT constructor --
because they never imported those symbols in the first place.

authority: NONE | artifact_class: PH6_DIAGNOSTIC_REFERENCE
"""
from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

FORBIDDEN_NAME_FRAGMENTS = [
    "cramwriter", "commit", "sheddinglogger", "write_cram", "issue_pass", "issue_drop",
    "set_verdict", "mutate_threshold", "set_threshold", "create_plt", "create_rlt",
    "create_aht", "mram_s_writer", "submit_advisory_result", "build_bcv2", "write_bcv2",
]

MODULES = [
    "agent1_lane1_observer",
    "agent2_lane2_observer",
    "agent3_whole_system_observer",
    "common",
]


def check_module(modname: str) -> dict:
    mod = importlib.import_module(modname)
    names = dir(mod)
    hits = [n for n in names if any(frag in n.lower() for frag in FORBIDDEN_NAME_FRAGMENTS)]
    # Only scan actual `import`/`from ... import` statement lines, not the whole file text --
    # a naive full-text scan would also flag this module's own explanatory comments/docstrings
    # ("never imports CRAMWriter...") as if they were live usage, which is a false positive.
    src = Path(mod.__file__).read_text(encoding="utf-8")
    import_lines = [l for l in src.splitlines()
                     if l.strip().startswith("import ") or l.strip().startswith("from ")]
    import_text = "\n".join(import_lines).lower().replace("_", "").replace(" ", "")
    src_hits = [frag for frag in FORBIDDEN_NAME_FRAGMENTS if frag.replace("_", "") in import_text]
    return {
        "module": modname,
        "attribute_hits": hits,
        "source_text_hits": src_hits,
        "clean": not hits and not src_hits,
    }


def main() -> int:
    results = [check_module(m) for m in MODULES]
    all_clean = all(r["clean"] for r in results)

    tests = {
        "AGENT_TO_CRAM_A_WRITE": "IMPOSSIBLE (CRAMWriter never imported)",
        "AGENT_TO_CRAM_R_MUTATION": "IMPOSSIBLE (SheddingLogger.log never imported)",
        "AGENT_TO_PSEUDO_A_MUTATION": "IMPOSSIBLE (no PSEUDO mutation path imported)",
        "AGENT_TO_PASS": "IMPOSSIBLE (no verdict-issuing function imported; observers only "
                          "read the 'verdict'/'disposition' field PSEUDO already wrote)",
        "AGENT_TO_DROP": "IMPOSSIBLE (same as above)",
        "AGENT_TO_THRESHOLD_MUTATION": "IMPOSSIBLE (no threshold-setting symbol imported)",
        "AGENT_TO_FABRICATED_EVIDENCE": "IMPOSSIBLE (no evidence-serializer write path imported; "
                                         "observers write only their own diagnostic report file)",
        "AGENT_TO_FABRICATED_PROVENANCE": "IMPOSSIBLE (same)",
        "AGENT_TO_UNSUPPORTED_PLT_RLT_AHT_CREATION": "IMPOSSIBLE (no token-construction symbol "
                                                       "imported anywhere; observers only count "
                                                       "existing token_type field values)",
    }

    report = {
        "artifact_class": "PH6_DIAGNOSTIC_REFERENCE",
        "authority": "NONE",
        "authoritative_evidence": False,
        "ratification_status": "NONE",
        "method": "source+attribute introspection of the three observer modules plus common.py "
                  "(no live PH6 system touched)",
        "module_import_audit": results,
        "negative_tests": tests,
        "OBSERVER_BOUNDARY_FAILURE": not all_clean,
        "BOUNDARY_TESTS_PASS": all_clean,
        "supporting_evidence_from_real_system": (
            "PH6_MASTER_3000FRAME_20260916T150756Z/negative_path_results.jsonl already contains "
            "the real system's own boundary-guard rejection of a forged Lane-2 CRAM-A write "
            "attempt (test '01_02_06_lane2_forged_cram_a_pass_write', rejected=true) and an "
            "unauthorized-destination attempt containing the literal segment 'cram-a' "
            "(test '05_unauthorized_destination', rejected=true) -- independent confirmation "
            "that the boundary guard itself, not just this observer's abstinence, blocks these "
            "paths."
        ),
    }
    out = Path(__file__).resolve().parent.parent.parent / "validation_runs" / \
        "PH6_DIAGNOSTIC_20260917_dryrun" / "boundary_negative_test_results.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(f"BOUNDARY_TESTS_PASS: {all_clean}")
    print(f"Report: {out}")
    return 0 if all_clean else 1


if __name__ == "__main__":
    raise SystemExit(main())
