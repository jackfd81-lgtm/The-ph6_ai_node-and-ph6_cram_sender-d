# PH6 ER-1E Real Multi-VLT Artifact Campaign — 2026-06-17

timestamp_utc: 2026-06-17T00:00:00Z
authority: ZERO
classification: ER1E_REAL_MULTIVLT_ARTIFACT_CAMPAIGN

## Summary

ER-1E is a real multi-VLT artifact campaign proof. It extends ER-1D-LITE from
3 in-memory VLT objects to 5 distinct object classes across 3 temporal cycles,
with committed artifact files verified by sha256 in manifest.json. The advisory
evidence chain is preserved in the repository under PH6_SOURCE/ARTIFACTS/.

## Scope

- Proof type: real multi-VLT artifact campaign
- Lane: 2
- Authority: ZERO
- Write domain: PH6_SOURCE/ARTIFACTS/ER1E_REAL_MULTIVLT_20260617/ (committed artifacts)

## Campaign Parameters

| Parameter | Value |
|-----------|-------|
| FIXED_T0 | 4_000_000_000_000 ms (ER-1E anchor) |
| Object classes | vehicle, person, bicycle, sign, doorway |
| Cycles | 3 |
| VDTs per promotion | 5 |
| Cycle spacing | 2000 ms |
| Spatial drift | 5.0 px/cycle (x-axis) |
| Confidence | 0.78 |
| Total VLT promotions | 15 (5 objects × 3 cycles) |
| Total tokens | 181 |

## Committed Artifacts

```
PH6_SOURCE/ARTIFACTS/ER1E_REAL_MULTIVLT_20260617/
  source_observations.jsonl    sha256: 93fa6a45d679d6b90ab90bdad05c7e75dd6f3e8298921a6f0df2365123c0ed5d
  tok_advisory_audit.jsonl     sha256: 787125cb80b9187cdd14d688fd68f5bfb7fd70b9f674b17b9e78cf36868bc58b
  reconstruction_report.json   sha256: a8b41ed779b504677f92e052634ed46b61633c18af01f9a7a95763e399c2c2e8
  manifest.json                (written last; manifest hash not self-referential)
```

Topology hash (generation-time, session-stable): `d46151852f3062d87bfdffd8dc4a8848beeb49c5cc13b2f53c4bd7124aaff2e3`

Note on topology hash stability: `token_types.make_rt/make_vdt/make_vlt` use
`utc_now_iso()` for `created_at` (1-second wall-clock granularity). Topology
hash is stable within a Python session but differs across sessions. Tests assert
within-session hash equality; they do not compare against this generation-time
value. See test_er1e_reconstruction_deterministic for the explicit design note.

## Guarantees

| Guarantee | Status |
|-----------|--------|
| Multi-object: 5 distinct VLT classes | CONFIRMED |
| Multi-cycle: 3 cycles with distinct first_seen_ms | CONFIRMED |
| Spatial drift across cycles | CONFIRMED (bbox x += 5.0 px/cycle) |
| No snapshot cache introduced | CONFIRMED |
| No live MRAM-S mutation (/var/ph6/mram-s) | CONFIRMED |
| No Lane-1 authority introduced | CONFIRMED |
| No CRAM-A / CRAM-R / PASS / DROP / verdict writes | CONFIRMED |
| No mean_confidence used or emitted | CONFIRMED |
| ER-1B spatial fields preserved in audit chain | CONFIRMED |
| Audit chain integrity (BLAKE2b-256 chain) | CONFIRMED |
| sha256 of artifacts matches manifest | CONFIRMED |

## Prerequisites

- **ER-1A** (test_er1a_proof.py) — advisory chain reconstruction and determinism
- **ER-1B** (test_er1b_proof.py) — spatial/object fields in VLT audit events
- **ER-1D-LITE** (test_er1d_lite_live_style_replay.py) — isolated live-style replay proof

## What ER-1E Proves

1. The real token lifecycle path (TokenStore + add_vdt + promote_to_vlt) can
   generate a multi-object, multi-cycle advisory evidence chain with at least
   5 distinct object classes (vehicle, person, bicycle, sign, doorway).

2. All ER-1B spatial fields (object_class, centroid, bbox, support_count,
   first_seen_ms, last_seen_ms) survive the full promotion path and are present
   in every VDT_PROMOTED_TO_VLT event in the committed audit chain.

3. Each object class appears in exactly 3 observation cycles with distinct
   first_seen_ms timestamps, proving topology is not single-frame-only.

4. The committed artifact files have stable sha256 values matching manifest.json,
   making them verifiable evidence across repository clones.

5. Topology reconstructs deterministically within a Python session (hash1 == hash2)
   from the committed tok_advisory_audit.jsonl. Reconstruction from an isolated
   copy in tmp_path gives the same hash as the original.

6. A corrupted audit chain is rejected: validate_chain_integrity returns False
   and reconstruct_topology raises ValueError.

7. No writes occur to /var/ph6/mram-s, CRAM-0/A/R, PASS, DROP, verdict paths,
   snapshot, or cache files during the full lifecycle and reconstruction.

## What ER-1E Does NOT Prove

- Live Pi hardware integration (OI-01, OI-03 remain open)
- Pi-to-Pi transfer or replay (C02 remains open)
- Any CRAM-A / Lane-1 authority path
- ER-1C (snapshot cache, deferred indefinitely)
- 300-frame coherence campaign (C01 remains open)

## Files

```
ph6_l2_expand/er1e_campaign.py
ph6_l2_expand/tests/test_er1e_real_multivlt_artifact_campaign.py
PH6_SOURCE/ARTIFACTS/ER1E_REAL_MULTIVLT_20260617/{source_observations.jsonl,tok_advisory_audit.jsonl,reconstruction_report.json,manifest.json}
PH6_SOURCE/DEPLOYMENT/PH6-er1e-real-multivlt-artifact-campaign-20260617.md  (this file)
```

Tests: 12 / 12 PASS
Full suite: 95 / 95 PASS (ph6_l2_expand + ph6/tok)

## AI Contribution Signature

```json
{"proposed_by":"claude-code-lane2","proposed_at_utc":"2026-06-17T11:10:00Z","api_call_log_ref":"er1e-real-multivlt-20260617","ratified_by":null}
```
