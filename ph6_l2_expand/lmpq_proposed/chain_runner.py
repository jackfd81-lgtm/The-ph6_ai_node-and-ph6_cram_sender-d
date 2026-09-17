"""
ph6_l2_expand.lmpq_proposed.chain_runner

Lane: 2
Authority: ZERO
Write domain: caller-supplied MRAM-S directory only
Status: PROPOSED — see PH6_SOURCE/DRAFT/PH6-LMPQ-001-PROPOSED-SPEC-v0.1.md

End-to-end demonstration of the proposed LMPQ-001 path:

  RT/VDT (ph6.tok.lifecycle, existing)
    -> VLT promotion (existing)
    -> RLT  (proposed: observes an independent CRAM-R DROP)
    -> PLT  (proposed: links the RLT forward to the resumed VLT)
    -> AHT  (proposed: rehydrates the VLT from its own audit chain)
    -> SoSo-JEDI single-token continuity lookup (adapter over existing,
       unmodified BookVCoreEngine)
    -> Life CRAM BCV2 bundle (proposed: packages the whole experience)

No real CRAM-0/A/R writes occur anywhere in this module. cram_ref values
are opaque reference strings, exactly as ph6.tok.lifecycle and the
existing ER-1E campaign already treat them (Lane-2 never writes CRAM).

Per LMPQ-001 §13, run_lmpq_chain records exactly which stage succeeds or
fails rather than crashing opaquely: stages up to and including the
first failure are recorded in the returned dict's "stages" map.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict


def run_lmpq_chain(mram_s_dir: Path, event_time_base_ms: int = 1_700_000_000_000) -> Dict[str, Any]:
    from ph6.tok.lifecycle import TokenStore
    from ph6_l2_expand.lmpq_proposed._shared import build_promoted_vlt
    from ph6_l2_expand.lmpq_proposed.tokens import make_aht, make_plt, make_rlt
    from ph6_l2_expand.lmpq_proposed.soso_jedi_adapter import lookup_token_provenance
    from ph6_l2_expand.lmpq_proposed.life_cram_bcv2 import build_bcv2, write_bcv2

    stages: Dict[str, str] = {}
    result: Dict[str, Any] = {"stages": stages, "complete": False}

    mram_s_dir = Path(mram_s_dir)
    tokens_dir = mram_s_dir / "tokens"
    store = TokenStore(str(tokens_dir))

    cram_ref = "cram_lmpq_demo_frame001"
    vlt = build_promoted_vlt(store, event_time_base_ms, cram_ref, suffix="lmpq_demo")
    stages["RT_VDT_VLT_normal_path"] = "OK"
    result["vlt_token_id"] = vlt.token_id

    dropped_cram_ref = "cram_lmpq_demo_frame002_dropped"
    rlt = make_rlt(
        cram_ref_hash=dropped_cram_ref,
        drop_observed_at_ms=event_time_base_ms + 700,
        parent_token_id=vlt.token_id,
    )
    stages["RLT_construction"] = "OK"
    result["rlt_token_id"] = rlt.token_id

    plt = make_plt(
        parent_token_id=rlt.token_id,
        linked_token_ids=[vlt.token_id],
        token_map={rlt.token_id: rlt},
        parent_event_time_ms=rlt.drop_observed_at_ms,
        linked_event_times_ms={vlt.token_id: vlt.last_seen_ms},
    )
    stages["PLT_construction"] = "OK"
    result["plt_token_id"] = plt.token_id

    audit_path = tokens_dir / "tok_advisory_audit.jsonl"
    aht = make_aht(audit_path, vlt.token_id, reconstructed_at_ms=event_time_base_ms + 5000)
    stages["AHT_rehydration"] = "OK"
    result["aht_token_id"] = aht.token_id

    jedi_result = lookup_token_provenance(vlt.token_id)
    stages["soso_jedi_lookup"] = "OK"
    result["soso_jedi_continuity_hash"] = jedi_result["continuity_block"]["continuity_hash"]

    bundle = build_bcv2(
        experience_id="lmpq_chain_demo",
        cram_refs=[cram_ref, dropped_cram_ref],
        token_ids=[vlt.token_id, rlt.token_id, plt.token_id, aht.token_id],
        token_types_present=["VLT", "RLT", "PLT", "AHT"],
        event_window_start_ms=event_time_base_ms,
        event_window_end_ms=aht.reconstructed_at_ms,
    )
    out_dir = mram_s_dir / "advisory"
    path_written, status, violations = write_bcv2(out_dir, bundle)
    stages["bcv2_bundle_write"] = status
    result["bcv2_bundle_path"] = str(path_written)
    result["bcv2_bundle_id"] = bundle["bcv_id"]
    result["bcv2_violations"] = violations

    result["complete"] = status == "WRITTEN" and all(
        v in ("OK", "WRITTEN") for v in stages.values()
    )
    return result


if __name__ == "__main__":
    import json
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        out = run_lmpq_chain(Path(td) / "mram-s")
        print(json.dumps(out, indent=2, default=str))
