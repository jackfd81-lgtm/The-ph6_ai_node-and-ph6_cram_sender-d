"""
ph6_l2_expand.lmpq_proposed._shared

Lane: 2
Authority: ZERO
Write domain: MRAM-S only (delegated to ph6.tok.lifecycle.TokenStore)

Small helper shared by chain_runner.py and bench_four_experiences.py so
both build VDT->VLT promotions the same deterministic way. Not part of
the public token-type surface.
"""

from __future__ import annotations

from typing import Any


def build_promoted_vlt(store: Any, event_base_ms: int, cram_ref: str, suffix: str) -> Any:
    """Build 5 VDTs on cram_ref and promote them to a VLT, deterministically."""
    from ph6.tok.lifecycle import VDT, DEFAULT_TOK_CONFIG

    vdt_ids = []
    for i in range(5):
        t = event_base_ms + i * 100
        vdt = VDT(
            token_id=f"vdt_{suffix}_{i:03d}",
            cram_ref_hash=cram_ref,
            timestamp_ms=t,
            last_updated_ms=t,
            object_class="lmpq_object",
            bbox=[10.0 + i, 20.0, 100.0, 60.0],
            confidence=0.8,
            support_count=1,
        )
        store.add_vdt(vdt)
        vdt_ids.append(vdt.token_id)

    vlt = store.promote_to_vlt(vdt_ids, DEFAULT_TOK_CONFIG, event_time_ms=event_base_ms + 600)
    if vlt is None:
        raise RuntimeError(f"VLT promotion failed for suffix={suffix!r}")
    return vlt
