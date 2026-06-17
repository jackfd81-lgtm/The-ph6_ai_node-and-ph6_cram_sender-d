# PH6 ER-1D-LITE Proof — 2026-06-17

timestamp_utc: 2026-06-17T00:00:00Z
authority: ZERO
classification: ER1D_LITE_ISOLATED_LIVE_STYLE_REPLAY_PROOF

## Summary

ER-1D-LITE is an isolated live-style replay proof. It proves that advisory
evidence generated through the real token lifecycle path (TokenStore + add_vdt
+ promote_to_vlt) can be preserved in an isolated temporary advisory audit
chain, reconstructed into topology across separate invocations, and made to
reject corruption.

## Scope

- Proof type: isolated live-style replay proof
- Lane: 2
- Authority: ZERO
- Write domain: tmp_path (isolated test directory only)

## Guarantees

| Guarantee | Status |
|-----------|--------|
| No snapshot cache introduced | CONFIRMED |
| No live MRAM-S mutation (/var/ph6/mram-s) | CONFIRMED |
| No Lane-1 authority introduced | CONFIRMED |
| No CRAM-A / CRAM-R / PASS / DROP / verdict writes | CONFIRMED |
| No mean_confidence used or emitted | CONFIRMED |
| No ER-1C implementation | CONFIRMED — ER-1C remains deferred |

## Prerequisites

- **ER-1A** (test_er1a_proof.py) — advisory chain reconstruction and
  determinism across invocations. Must pass before ER-1D-LITE.
- **ER-1B** (test_er1b_proof.py) — spatial/object fields in VLT audit
  events. Provides the ER-1B promotion payload schema used here.

ER-1D-LITE builds on ER-1A and ER-1B. Both remain required.

## What ER-1D-LITE Proves

1. The real token lifecycle path (TokenStore VDT → VLT promotion) generates
   a valid advisory audit chain containing ER-1B spatial fields (object_class,
   centroid, bbox, support_count, first_seen_ms, last_seen_ms) with no
   mean_confidence.

2. Topology can be reconstructed from that chain in a first invocation with
   a valid BLAKE2b-256 topology hash, correct observation count, and full
   spatial field preservation in source_objects.

3. A second reconstruction in a fresh call path produces identical topology
   hash, source object count, object classes, and spatial field content.

4. After deleting derived output files (live materialization, receipts),
   reconstruction from the advisory evidence chain alone produces the same
   topology hash.

5. A corrupted advisory chain is rejected: validate_chain_integrity returns
   False and reconstruct_topology raises ValueError.

6. No writes occur to /var/ph6/mram-s, CRAM-A, CRAM-R, PASS, DROP,
   verdict paths, or any snapshot cache during the full lifecycle and
   reconstruction.

## What ER-1D-LITE Does NOT Prove

- Live Pi hardware integration (OI-01, OI-03 remain open)
- Pi-to-Pi transfer or replay (C02 remains open)
- Any CRAM-A / Lane-1 authority path
- ER-1C (deferred)
- 300-frame coherence campaign (C01 remains open)

## Test File

```
ph6_l2_expand/tests/test_er1d_lite_live_style_replay.py
```

Tests: 8
- test_er1d_lite_chain_generated_via_real_lifecycle
- test_er1d_lite_first_reconstruction
- test_er1d_lite_dual_reconstruction_deterministic
- test_er1d_lite_reconstruction_after_cache_deletion
- test_er1d_lite_corrupt_chain_rejected
- test_er1d_lite_no_mrams_mutation
- test_er1d_lite_no_cram_verdict_writes
- test_er1d_lite_no_lane1_imports

## AI Contribution Signature

```json
{"proposed_by":"claude-code-lane2","proposed_at_utc":"2026-06-17T09:30:00Z","api_call_log_ref":"er1d-lite-20260617","ratified_by":null}
```
