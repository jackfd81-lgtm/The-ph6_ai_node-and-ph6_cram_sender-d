"""
LMPQ-001 PM-01..PM-05 single-experience bench slice.

Milestone 1 per the frozen LMPQ-001 spec + operator direction is not 1,000
experiences: it is one complete, verifiable chain (E001 -> CRAM evidence ->
PSEUDO-M -> PSEUDO-A -> token -> SoSo -> provenance -> rehydration -> AI ->
verified source/hash), executed with existing PH6 components only.

This test asserts the concrete, defensible claims the chain makes about
itself. It does NOT claim the full PM-01..PM-05 procedures (which need
multiple experiences, e.g. PM-02's E001..E004 continuity chain) have been
executed -- see PH6_SOURCE/DEPLOYMENT/PH6-LMPQ001-single-chain-bench-*.md
for the per-test qualification status, which distinguishes "interface
exercised once" from "full test procedure executed."
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ph6.lmpq001_single_chain_bench import (
    KNOWN_MISSING_COMPONENTS,
    run_single_chain,
)
from ph6_l2_expand.topology_reconstruct import reconstruct_topology

EXPECTED_STEPS = [
    "cram_evidence_pseudo_m_pseudo_a",
    "readiness_attention_signal",
    "ph6_token_rt_vdt_vlt",
    "soso_continuity",
    "provenance_trace_to_source",
    "rehydration",
    "ai_deterministic_pass",
    "verified_source_hash",
]


@pytest.fixture
def chain_report(tmp_path):
    return run_single_chain(tmp_path)


def test_chain_reaches_every_expected_step_without_halting(chain_report):
    step_names = [s.step for s in chain_report.steps]
    assert step_names == EXPECTED_STEPS, (
        "Chain halted or diverged before reaching every expected step: "
        f"{step_names}"
    )


def test_no_step_reports_fail_or_blocked(chain_report):
    bad = [(s.step, s.status) for s in chain_report.steps if s.status not in ("PASS_PENDING_REVIEW",)]
    assert bad == [], f"One or more chain steps did not complete: {bad}"


def test_cram_evidence_verdict_is_pass_with_no_missing_files(chain_report):
    cram_step = next(s for s in chain_report.steps if s.step == "cram_evidence_pseudo_m_pseudo_a")
    assert cram_step.detail["verdict"] == "PASS"
    assert cram_step.detail["missing_files"] == []


def test_token_chain_reaches_vlt(chain_report):
    tok_step = next(s for s in chain_report.steps if s.step == "ph6_token_rt_vdt_vlt")
    assert tok_step.detail["vlt_token_id"] is not None
    assert tok_step.detail["vlt_cram_ref_hash"] == \
        chain_report.steps[0].detail["authority_hash"]


def test_provenance_traces_back_to_the_same_authority_hash(chain_report):
    prov_step = next(s for s in chain_report.steps if s.step == "provenance_trace_to_source")
    assert prov_step.detail["hashes_match"] is True
    assert prov_step.detail["cram_a_files_missing"] == []


def test_rehydration_reconstructs_from_audit_chain_alone(chain_report):
    rehydrate_step = next(s for s in chain_report.steps if s.step == "rehydration")
    assert rehydrate_step.detail["token_count"] > 0
    assert rehydrate_step.detail["chain_errors"] == []


def test_ai_pass_does_not_mutate_original_evidence(chain_report):
    """
    Core PM-01 claim: AI-derived output must remain distinguishable from,
    and must not mutate, the original preserved evidence. The replay_check
    step re-derives the authority_hash from the original raw bytes + metrics
    independently of anything the AI step touched; a mismatch here would
    mean the AI step (or anything after CRAM commit) corrupted the record.
    """
    replay_step = next(s for s in chain_report.steps if s.step == "verified_source_hash")
    assert replay_step.detail["replay_ok"] is True

    cram_step = chain_report.steps[0]
    assert replay_step.detail["authority_hash"] == cram_step.detail["authority_hash"]


def test_known_missing_components_list_is_unchanged():
    """
    Guards against silently forgetting a gap. If a future change implements
    one of these (e.g. an actual AHT token type), this test should be
    updated deliberately in the same change -- not left to drift silently.
    """
    expected_keys = {
        "Life CRAM (named component)",
        "BCV2",
        "RLT (Real Loss Token)",
        "PLT (Predicted Loss Token)",
        "AHT (rehydration token)",
        "SoSo-JEDI (as a provenance-lookup component)",
    }
    assert set(KNOWN_MISSING_COMPONENTS.keys()) == expected_keys


def test_cram_authority_hash_is_deterministic_across_independent_runs(tmp_path):
    """Same seed -> byte-identical CRAM authority_hash, every run."""
    report_a = run_single_chain(tmp_path / "run_a")
    report_b = run_single_chain(tmp_path / "run_b")

    hash_a = report_a.steps[0].detail["authority_hash"]
    hash_b = report_b.steps[0].detail["authority_hash"]
    assert hash_a == hash_b


def test_topology_reconstruction_is_deterministic_for_a_fixed_audit_chain(chain_report):
    """
    Reconstructing the SAME persisted tok_advisory_audit.jsonl chain twice
    gives the same topology_hash (this is the property ER-1E already
    proved and this test reconfirms it here).

    NOT tested here (documented finding, not a regression): two
    INDEPENDENT single_chain runs at different wall-clock times produce
    DIFFERENT topology hashes even from byte-identical evidence, because
    ph6_l2_expand.token_types.make_rt/make_vdt/make_vlt stamp `created_at`
    from the wall clock at reconstruction time rather than carrying a
    timestamp forward from the persisted tok audit event. This is an
    existing property of ph6_l2_expand's reconstruction pipeline, not
    something this bench harness introduces or attempts to fix.
    """
    audit_path = Path(next(s for s in chain_report.steps if s.step == "ph6_token_rt_vdt_vlt").detail["audit_chain_path"])
    _, hash_1, _ = reconstruct_topology(audit_path)
    _, hash_2, _ = reconstruct_topology(audit_path)
    assert hash_1 == hash_2
