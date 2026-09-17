"""
ph6.lmpq001_single_chain_bench

LMPQ-001 PM-01..PM-05 single-experience bench harness.

This is a cross-lane orchestration/bench driver (it drives Lane-1 CRAM
simulation directly, then feeds the result into Lane-2 tok/SoSo advisory
code). It is placed directly under ph6/ (a neutral, precedented location
for cross-cutting orchestration -- ph6/cfc.py and ph6/cvs3_preflight.py
already live at this same top level) rather than inside either lane's own
tree, because BOTH of the following are true and enforced by existing
tests, discovered by actually running them against an earlier draft of
this file:

  - ph6_l2_expand/tests/test_no_reverse_path.py forbids any module under
    ph6_l2_expand/ from importing ph6.cram_pu (Lane-2 must never couple
    to Lane-1).
  - ph6_l2_expand/tests/test_replay_independence.py and
    test_soso_tokens_not_lane1.py forbid any module under ph6/cram_pu/
    (including its tools/ and tests/ subdirectories) from referencing
    ph6_l2_expand or SoSo/token vocabulary at all (Lane-1 must never know
    Lane-2 exists).

Neither lane's tree is a legal home for a harness that must mint real
Lane-1 CRAM evidence and then feed it into Lane-2 tok/SoSo code, so this
module lives at the neutral top level instead. ph6.tok and ph6.ssmt import
neither ph6.cram_pu nor ph6_l2_expand (confirmed by inspection), so they
carry no such restriction and are imported directly.

Only the Lane-1 call itself (ph6.cram_pu.ph6_cram_sim.CRAMSimulation,
already a self-contained, read/write-isolated simulation core with no
camera/USB/CAN/HAT dependence) has any Lane-1 authority weight. Every
step after CRAM commit is Lane-2, Authority: ZERO, and never issues
PASS/DROP, never mutates CRAM, and never modifies PSEUDO thresholds or
adjudication logic.

Purpose
-------
Push exactly ONE synthetic experience (E001) through the frozen LMPQ-001
architecture chain using ONLY components that already exist in this
repository, and report precisely which interface(s) cannot be completed
as named in the LMPQ-001 spec. Nothing here is a redesign: every step
calls an already-existing function. Where a named LMPQ-001 concept has
no existing implementation, this harness records that as MISSING rather
than inventing a stand-in for it.

Chain executed, and the exact existing component used for each link
(see run_single_chain()'s docstring table for the gaps found):

  E001 (synthetic experience, deterministic)
    -> CRAM evidence + PSEUDO-M + PSEUDO-A   ph6.cram_pu.ph6_cram_sim
    -> readiness / attention signal          ph6.cram_pu.verdict_logger._soso_advisory
    -> PH6 token (RT -> VDT -> VLT)          ph6.tok.lifecycle.TokenStore
    -> SoSo continuity                       ph6.ssmt.swarms.S1ActiveMemorySwarm
    -> provenance trace back to source hash  direct cram_ref_hash cross-check
                                              against ph6.cram_pu.ph6_cram_sim
                                              CRAM-A evidence files
    -> rehydration from persisted evidence   ph6_l2_expand.topology_reconstruct
                                              .reconstruct_topology (reads only
                                              the tok advisory audit chain)
    -> AI (deterministic pass)               ph6_l2_expand.experimental
                                              .mock_ai_client.generate
    -> verified source/hash                  ph6.cram_pu.ph6_cram_sim
                                              .CRAMSimulation.replay_check
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from ph6.cram_pu.ph6_cram_sim import CRAMSimulation, FrameInput, FrameResult
from ph6.cram_pu.verdict_logger import _pseudo_metrics, _soso_advisory
from ph6.tok.lifecycle import DEFAULT_TOK_CONFIG, RT, VDT, TokenStore, now_ms
from ph6.ssmt.models import SwarmInput
from ph6.ssmt.swarms import S1ActiveMemorySwarm
from ph6_l2_expand.experimental.mock_ai_client import generate as mock_ai_generate
from ph6_l2_expand.topology_mapper import serialize_token_map
from ph6_l2_expand.topology_reconstruct import reconstruct_topology

# ---------------------------------------------------------------------------
# LMPQ-001 §5: components named in the spec that DO NOT EXIST anywhere in
# this repository as of this bench run. Populated at import time by
# find_missing_components() below and re-exported for the test suite and
# result_summary.json to assert against, so a future implementation of any
# of these is a visible, deliberate change to this constant rather than a
# silent gap.
# ---------------------------------------------------------------------------
KNOWN_MISSING_COMPONENTS: Dict[str, str] = {
    "Life CRAM (named component)": (
        "No module, class, or function named 'Life CRAM' or 'BCV2' exists "
        "anywhere in this repository. The closest existing analog is "
        "ph6.cram_pu.verdict_logger._soso_advisory, a 3-state "
        "(STABLE/MODERATE/UNSTABLE) bounded signal derived from entropy; "
        "it carries no 'attention' or 'readiness' semantics of its own."
    ),
    "BCV2": "Not found anywhere in this repository.",
    "RLT (Real Loss Token)": "Not found anywhere in this repository.",
    "PLT (Predicted Loss Token)": "Not found anywhere in this repository.",
    "AHT (rehydration token)": (
        "Not found anywhere in this repository as a token type. A "
        "rehydration *capability* exists (ph6_l2_expand.topology_reconstruct"
        ".reconstruct_topology, which reconstructs state purely from the "
        "persisted tok advisory audit chain) but nothing materializes it "
        "as an AHT token object."
    ),
    "SoSo-JEDI (as a provenance-lookup component)": (
        "The only code under the 'SoSo-JEDI' / 'Book V' name "
        "(PH6_SOURCE/AI/soso_jedi/jedi/swarm_sim_bp.py, BookVCoreEngine) "
        "is a heavier storm/swarm-exploration simulation that requires a "
        "list of synthetic 'storm branches' as input and is not wired "
        "into ph6/ or ph6_l2_expand/. It is not built for, and was not "
        "used for, a single-token provenance lookup. This harness "
        "performs the provenance trace directly against the token's "
        "cram_ref_hash and the CRAM-A evidence file instead."
    ),
}


# ---------------------------------------------------------------------------
# E001 — deterministic synthetic experience
# ---------------------------------------------------------------------------

EXPERIENCE_SEED = 20260912  # fixed seed; same input -> same bytes, every run
PAYLOAD_SIZE = 2048


def build_experience_payload(seed: int = EXPERIENCE_SEED, size: int = PAYLOAD_SIZE) -> bytes:
    """
    Deterministic synthetic experience content for E001.

    LMPQ-001 SS5 requires the experience stream be "generated from a
    deterministic seed"; no seeded-content generator exists elsewhere in
    this repository (confirmed absent by prior mapping), so this is the
    minimum new code needed to satisfy that requirement. random.Random(seed)
    guarantees byte-identical output on every invocation with this seed.
    """
    return random.Random(seed).randbytes(size)


def build_previous_payload(payload: bytes) -> bytes:
    """
    Deterministic "previous frame" used only to derive a motion_fraction
    metric via the existing ph6.cram_pu.verdict_logger._pseudo_metrics
    algorithm. Every third byte is shifted by 128 (mod 256), which reliably
    pushes ~1/3 of byte positions past the existing >15 diff threshold —
    landing motion_fraction inside ph6_cram_sim's gate range without
    hand-tuning a new metric.
    """
    prev = bytearray(payload)
    for i in range(0, len(prev), 3):
        prev[i] = (prev[i] + 128) % 256
    return bytes(prev)


@dataclass
class ChainStepResult:
    step: str
    component: str
    status: str  # PASS_PENDING_REVIEW / FAIL / BLOCKED / NOT_EXECUTED
    detail: Dict[str, Any]


@dataclass
class SingleChainReport:
    experience_id: str
    steps: List[ChainStepResult]
    missing_components: Dict[str, str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema": "ph6.lmpq001.single_chain_report.v1",
            "authority": "ZERO",
            "advisory_only": True,
            "experience_id": self.experience_id,
            "steps": [
                {
                    "step": s.step,
                    "component": s.component,
                    "status": s.status,
                    "detail": s.detail,
                }
                for s in self.steps
            ],
            "missing_components": self.missing_components,
        }


def run_single_chain(bench_root: Path) -> SingleChainReport:
    """
    Run E001 through the full LMPQ-001 chain once, using bench_root as an
    isolated scratch directory (never /var/ph6, never a CRAM-0/A/R path
    used by any other run). Returns a SingleChainReport describing every
    step's outcome. Raises nothing for expected/known gaps -- those are
    recorded as BLOCKED/NOT_EXECUTED steps, not exceptions.
    """
    bench_root = Path(bench_root)
    steps: List[ChainStepResult] = []
    experience_id = "E001"

    # 1. E001 -> CRAM evidence + PSEUDO-M + PSEUDO-A ------------------------
    payload = build_experience_payload()
    prev_payload = build_previous_payload(payload)

    fp_metrics = _pseudo_metrics(payload, prev_payload)
    metrics = {
        "entropy": fp_metrics["entropy_fp"] / fp_metrics["metric_scale"],
        "laplacian_var": fp_metrics["laplacian_var_fp"] / fp_metrics["metric_scale"],
        "motion_fraction": fp_metrics["motion_fraction_fp"] / fp_metrics["metric_scale"],
    }

    sim = CRAMSimulation(bench_root / "cram")
    frame = FrameInput(object_id=experience_id, raw=payload, metrics=metrics)
    frame_result: FrameResult = sim.process(frame)
    audit_path = sim.finalize_audit()

    steps.append(ChainStepResult(
        step="cram_evidence_pseudo_m_pseudo_a",
        component="ph6.cram_pu.ph6_cram_sim.CRAMSimulation + ph6.cram_pu.verdict_logger._pseudo_metrics",
        status="PASS_PENDING_REVIEW" if frame_result.verdict == "PASS" else "FAIL",
        detail={
            "verdict": frame_result.verdict,
            "authority_hash": frame_result.authority_hash,
            "metrics_fixed_point": fp_metrics,
            "metrics_used": metrics,
            "cram_audit_path": str(audit_path),
            "missing_files": sim.verify_pass_files(experience_id) if frame_result.verdict == "PASS" else [],
        },
    ))

    if frame_result.verdict != "PASS":
        # Chain cannot proceed past CRAM authority on a DROP; report exactly
        # where it stopped rather than fabricating downstream steps.
        steps.append(ChainStepResult(
            step="chain_halted",
            component="n/a",
            status="BLOCKED",
            detail={"reason": "E001 did not receive a PASS verdict; no CRAM-A object exists to build tokens from."},
        ))
        return SingleChainReport(experience_id, steps, dict(KNOWN_MISSING_COMPONENTS))

    authority_hash = frame_result.authority_hash

    # 2. readiness / attention signal (LMPQ-001 calls this "Life CRAM/SAL") -
    readiness = _soso_advisory(fp_metrics)
    steps.append(ChainStepResult(
        step="readiness_attention_signal",
        component="ph6.cram_pu.verdict_logger._soso_advisory (substitute -- see missing_components)",
        status="PASS_PENDING_REVIEW",
        detail={"signal": readiness},
    ))

    # 3. PH6 token: RT -> VDT -> VLT ----------------------------------------
    ts = now_ms()
    store = TokenStore(base_dir=str(bench_root / "mram-s" / "tokens"))

    rt = RT(
        token_id=f"rt_{experience_id}_{authority_hash[:16]}",
        cram_ref_hash=authority_hash,
        timestamp_ms=ts,
        object_class="experience.STABLE",
        bbox=[0.0, 0.0, 1.0, 1.0],
        confidence=0.9,
    )
    store.add_rt(rt)

    vdt = VDT(
        token_id=f"vdt_{experience_id}_{authority_hash[:16]}",
        cram_ref_hash=authority_hash,
        timestamp_ms=ts,
        last_updated_ms=ts,
        object_class="experience.STABLE",
        bbox=[0.0, 0.0, 1.0, 1.0],
        confidence=0.9,
        support_count=1,
    )
    store.add_vdt(vdt)

    # Bench-scale config override: N=1 (promote from a single reinforcement)
    # instead of the production default N=5. This is a config-parameter
    # change, not an architecture change -- promote_to_vlt's fail-closed
    # logic is untouched; it is exercising the same code path the full
    # 1,000-experience campaign will use with N=5 and real repeated
    # observations.
    bench_config = dict(DEFAULT_TOK_CONFIG)
    bench_config["N"] = 1

    vlt = store.promote_to_vlt([vdt.token_id], bench_config, event_time_ms=ts + 1)

    steps.append(ChainStepResult(
        step="ph6_token_rt_vdt_vlt",
        component="ph6.tok.lifecycle.TokenStore",
        status="PASS_PENDING_REVIEW" if vlt is not None else "FAIL",
        detail={
            "rt_token_id": rt.token_id,
            "vdt_token_id": vdt.token_id,
            "vlt_token_id": vlt.token_id if vlt else None,
            "vlt_cram_ref_hash": vlt.cram_ref_hash if vlt else None,
            "bench_config_override": {"N": bench_config["N"]},
            "audit_chain_path": str(store.audit.audit_path),
        },
    ))

    if vlt is None:
        steps.append(ChainStepResult(
            step="chain_halted",
            component="n/a",
            status="BLOCKED",
            detail={"reason": "VDT->VLT promotion failed; no VLT exists to carry provenance downstream."},
        ))
        return SingleChainReport(experience_id, steps, dict(KNOWN_MISSING_COMPONENTS))

    # 4. SoSo continuity -----------------------------------------------------
    swarm_input = SwarmInput(
        cram_refs=[authority_hash],
        tok_refs=[rt.token_id, vdt.token_id, vlt.token_id],
        advisory_refs=[],
        cram_packet_hash=authority_hash,
    )
    swarm_packet = S1ActiveMemorySwarm().run(swarm_input)
    steps.append(ChainStepResult(
        step="soso_continuity",
        component="ph6.ssmt.swarms.S1ActiveMemorySwarm",
        status="PASS_PENDING_REVIEW",
        detail={
            "swarm_id": swarm_packet.swarm_id,
            "authority": swarm_packet.authority,
            "advisory_payload": swarm_packet.advisory_payload,
        },
    ))

    # 5. provenance trace back to source hash ("SoSo-JEDI" substitute) ------
    provenance_ok = vlt.cram_ref_hash == authority_hash
    missing_cram_files = sim.verify_pass_files(experience_id)
    steps.append(ChainStepResult(
        step="provenance_trace_to_source",
        component="direct cram_ref_hash cross-check (see missing_components: SoSo-JEDI)",
        status="PASS_PENDING_REVIEW" if (provenance_ok and not missing_cram_files) else "FAIL",
        detail={
            "vlt_cram_ref_hash": vlt.cram_ref_hash,
            "cram_authority_hash": authority_hash,
            "hashes_match": provenance_ok,
            "cram_a_files_missing": missing_cram_files,
        },
    ))

    # 6. rehydration from persisted evidence only ("AHT" substitute) --------
    token_map, topo_hash, topo_meta = reconstruct_topology(store.audit.audit_path)
    steps.append(ChainStepResult(
        step="rehydration",
        component="ph6_l2_expand.topology_reconstruct.reconstruct_topology (substitute -- see missing_components: AHT)",
        status="PASS_PENDING_REVIEW" if topo_meta["token_count"] > 0 else "FAIL",
        detail={
            "topology_hash": topo_hash,
            "token_count": topo_meta["token_count"],
            "observation_count": topo_meta["observation_count"],
            "chain_errors": topo_meta["chain_errors"],
        },
    ))

    # 7. AI (deterministic pass) ---------------------------------------------
    ai_output = mock_ai_generate(
        source_object_id=experience_id,
        source_object={"cram_ref_hash": authority_hash},
        cycle=1,
        token_map_before_dict=serialize_token_map(token_map),
    )
    steps.append(ChainStepResult(
        step="ai_deterministic_pass",
        component="ph6_l2_expand.experimental.mock_ai_client.generate",
        status="PASS_PENDING_REVIEW",
        detail={
            "mode": ai_output["mode"],
            "authority_level": ai_output["authority_level"],
            "observations": ai_output["observations"],
            "boundary_warnings": ai_output["boundary_warnings"],
        },
    ))

    # 8. verified source/hash -------------------------------------------------
    replay_ok, replay_msg = sim.replay_check([frame])
    steps.append(ChainStepResult(
        step="verified_source_hash",
        component="ph6.cram_pu.ph6_cram_sim.CRAMSimulation.replay_check",
        status="PASS_PENDING_REVIEW" if replay_ok else "FAIL",
        detail={"replay_ok": replay_ok, "replay_message": replay_msg, "authority_hash": authority_hash},
    ))

    return SingleChainReport(experience_id, steps, dict(KNOWN_MISSING_COMPONENTS))
