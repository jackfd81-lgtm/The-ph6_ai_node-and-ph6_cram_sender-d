"""
ph6_l2_expand.lmpq_proposed.bench_four_experiences

Lane: 2
Authority: ZERO
Write domain: caller-supplied MRAM-S directory only
Status: PROPOSED — see PH6_SOURCE/DRAFT/PH6-LMPQ-001-PROPOSED-SPEC-v0.1.md

LMPQ-001 PM-02: the minimum required four-experience bench.

  Experience 1 — normal successful path      (RT/VDT -> VLT only)
  Experience 2 — DROP/loss path               (RT/VDT/VLT + RLT + PLT)
  Experience 3 — rehydration path              (RT/VDT/VLT + AHT)
  Experience 4 — provenance/continuity path    (RT/VDT/VLT + PLT + AHT +
                                                 SoSo-JEDI continuity lookup)

Each experience runs in its own MRAM-S subdirectory (its own token store
and audit chain) so the four are independent and can be inspected or
re-run individually.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict


def _experience_1_normal_path(root: Path, t0: int) -> Dict[str, Any]:
    from ph6.tok.lifecycle import TokenStore
    from ph6_l2_expand.lmpq_proposed._shared import build_promoted_vlt
    from ph6_l2_expand.lmpq_proposed.life_cram_bcv2 import build_bcv2, write_bcv2

    stages: Dict[str, str] = {}
    tokens_dir = root / "experience_1" / "tokens"
    store = TokenStore(str(tokens_dir))

    cram_ref = "cram_bench_exp1_frame001"
    vlt = build_promoted_vlt(store, t0, cram_ref, suffix="exp1")
    stages["RT_VDT_VLT_normal_path"] = "OK"

    bundle = build_bcv2(
        experience_id="lmpq_bench_experience_1_normal",
        cram_refs=[cram_ref],
        token_ids=[vlt.token_id],
        token_types_present=["VLT"],
        event_window_start_ms=t0,
        event_window_end_ms=vlt.last_seen_ms,
    )
    path_written, status, violations = write_bcv2(root / "experience_1" / "advisory", bundle)
    stages["bcv2_bundle_write"] = status

    return {"stages": stages, "bcv2_bundle_id": bundle["bcv_id"], "violations": violations}


def _experience_2_drop_loss_path(root: Path, t0: int) -> Dict[str, Any]:
    from ph6.tok.lifecycle import TokenStore
    from ph6_l2_expand.lmpq_proposed._shared import build_promoted_vlt
    from ph6_l2_expand.lmpq_proposed.tokens import make_plt, make_rlt
    from ph6_l2_expand.lmpq_proposed.life_cram_bcv2 import build_bcv2, write_bcv2

    stages: Dict[str, str] = {}
    tokens_dir = root / "experience_2" / "tokens"
    store = TokenStore(str(tokens_dir))

    cram_ref = "cram_bench_exp2_frame001"
    vlt = build_promoted_vlt(store, t0, cram_ref, suffix="exp2")
    stages["RT_VDT_VLT_normal_path"] = "OK"

    dropped_cram_ref = "cram_bench_exp2_frame002_dropped"
    rlt = make_rlt(
        cram_ref_hash=dropped_cram_ref,
        drop_observed_at_ms=t0 + 700,
        parent_token_id=vlt.token_id,
    )
    stages["RLT_construction"] = "OK"

    plt = make_plt(
        parent_token_id=rlt.token_id,
        linked_token_ids=[vlt.token_id],
        token_map={rlt.token_id: rlt},
        parent_event_time_ms=rlt.drop_observed_at_ms,
        linked_event_times_ms={vlt.token_id: vlt.last_seen_ms},
    )
    stages["PLT_construction"] = "OK"

    bundle = build_bcv2(
        experience_id="lmpq_bench_experience_2_drop_loss",
        cram_refs=[cram_ref, dropped_cram_ref],
        token_ids=[vlt.token_id, rlt.token_id, plt.token_id],
        token_types_present=["VLT", "RLT", "PLT"],
        event_window_start_ms=t0,
        event_window_end_ms=rlt.drop_observed_at_ms,
    )
    path_written, status, violations = write_bcv2(root / "experience_2" / "advisory", bundle)
    stages["bcv2_bundle_write"] = status

    return {
        "stages": stages,
        "bcv2_bundle_id": bundle["bcv_id"],
        "violations": violations,
        "evidence_deleted_asserted_false": rlt.evidence_deleted is False,
    }


def _experience_3_rehydration_path(root: Path, t0: int) -> Dict[str, Any]:
    from ph6.tok.lifecycle import TokenStore
    from ph6_l2_expand.lmpq_proposed._shared import build_promoted_vlt
    from ph6_l2_expand.lmpq_proposed.tokens import make_aht
    from ph6_l2_expand.lmpq_proposed.life_cram_bcv2 import build_bcv2, write_bcv2

    stages: Dict[str, str] = {}
    exp_dir = root / "experience_3"
    tokens_dir = exp_dir / "tokens"
    store = TokenStore(str(tokens_dir))

    cram_ref = "cram_bench_exp3_frame001"
    vlt = build_promoted_vlt(store, t0, cram_ref, suffix="exp3")
    stages["RT_VDT_VLT_normal_path"] = "OK"

    audit_path = tokens_dir / "tok_advisory_audit.jsonl"
    aht = make_aht(audit_path, vlt.token_id, reconstructed_at_ms=t0 + 9000)
    stages["AHT_rehydration"] = "OK"

    bundle = build_bcv2(
        experience_id="lmpq_bench_experience_3_rehydration",
        cram_refs=[cram_ref],
        token_ids=[vlt.token_id, aht.token_id],
        token_types_present=["VLT", "AHT"],
        event_window_start_ms=t0,
        event_window_end_ms=aht.reconstructed_at_ms,
    )
    path_written, status, violations = write_bcv2(exp_dir / "advisory", bundle)
    stages["bcv2_bundle_write"] = status

    return {
        "stages": stages,
        "bcv2_bundle_id": bundle["bcv_id"],
        "violations": violations,
        "aht_is_replay": aht.is_replay,
        "aht_new_observation": aht.new_observation,
    }


def _experience_4_provenance_continuity_path(root: Path, t0: int) -> Dict[str, Any]:
    from ph6.tok.lifecycle import TokenStore
    from ph6_l2_expand.lmpq_proposed._shared import build_promoted_vlt
    from ph6_l2_expand.lmpq_proposed.tokens import make_aht, make_plt
    from ph6_l2_expand.lmpq_proposed.soso_jedi_adapter import lookup_token_provenance
    from ph6_l2_expand.lmpq_proposed.life_cram_bcv2 import build_bcv2, write_bcv2

    stages: Dict[str, str] = {}
    exp_dir = root / "experience_4"
    tokens_dir = exp_dir / "tokens"
    store = TokenStore(str(tokens_dir))

    cram_ref_a = "cram_bench_exp4_frame001"
    vlt_a = build_promoted_vlt(store, t0, cram_ref_a, suffix="exp4a")
    cram_ref_b = "cram_bench_exp4_frame002"
    vlt_b = build_promoted_vlt(store, t0 + 2000, cram_ref_b, suffix="exp4b")
    stages["RT_VDT_VLT_normal_path_x2"] = "OK"

    plt = make_plt(
        parent_token_id=vlt_a.token_id,
        linked_token_ids=[vlt_b.token_id],
        token_map={vlt_a.token_id: vlt_a},
        parent_event_time_ms=vlt_a.last_seen_ms,
        linked_event_times_ms={vlt_b.token_id: vlt_b.first_seen_ms},
    )
    stages["PLT_construction"] = "OK"

    audit_path = tokens_dir / "tok_advisory_audit.jsonl"
    aht = make_aht(audit_path, vlt_a.token_id, reconstructed_at_ms=t0 + 9000)
    stages["AHT_rehydration"] = "OK"

    jedi_result = lookup_token_provenance(plt.token_id)
    stages["soso_jedi_lookup"] = "OK"

    bundle = build_bcv2(
        experience_id="lmpq_bench_experience_4_provenance_continuity",
        cram_refs=[cram_ref_a, cram_ref_b],
        token_ids=[vlt_a.token_id, vlt_b.token_id, plt.token_id, aht.token_id],
        token_types_present=["VLT", "PLT", "AHT"],
        event_window_start_ms=t0,
        event_window_end_ms=vlt_b.last_seen_ms,
        topology_hash=jedi_result["continuity_block"]["continuity_hash"],
    )
    path_written, status, violations = write_bcv2(exp_dir / "advisory", bundle)
    stages["bcv2_bundle_write"] = status

    return {
        "stages": stages,
        "bcv2_bundle_id": bundle["bcv_id"],
        "violations": violations,
        "soso_jedi_continuity_hash": jedi_result["continuity_block"]["continuity_hash"],
    }


def run_four_experience_bench(root: Path, t0: int = 1_800_000_000_000) -> Dict[str, Any]:
    root = Path(root)
    return {
        "experience_1_normal_path": _experience_1_normal_path(root, t0),
        "experience_2_drop_loss_path": _experience_2_drop_loss_path(root, t0 + 100_000),
        "experience_3_rehydration_path": _experience_3_rehydration_path(root, t0 + 200_000),
        "experience_4_provenance_continuity_path": _experience_4_provenance_continuity_path(
            root, t0 + 300_000
        ),
    }


if __name__ == "__main__":
    import json
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        out = run_four_experience_bench(Path(td) / "mram-s")
        print(json.dumps(out, indent=2, default=str))
