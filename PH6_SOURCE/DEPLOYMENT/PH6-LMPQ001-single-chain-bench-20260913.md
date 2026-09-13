# LMPQ-001 PM-01..PM-05 — Single-Chain Bench (Milestone 1)

```text
Status:      PROPOSED
Authority:   ZERO
Spec:        PH6_SOURCE/DRAFT/... LMPQ-001 (supplied in-session, not yet
             committed to this repo as a standalone doc -- see note below)
Milestone:   1 of the operator's stated progression
             (1 -> 10-20 fixtures -> 1,000 experiences -> cross-session -> multi-model)
Date:        2026-09-13
```

## What this is

Per LMPQ-001 §29 ("inspect the existing repository; map existing
implementations to PM-01 through PM-16; ... implement only the minimum
test harness necessary"), and the operator's explicit instruction to stop
auditing and execute the prototype, this pushes exactly one synthetic
experience (E001) through the full chain:

```
E001 -> CRAM evidence -> PSEUDO-M -> PSEUDO-A -> token (RT->VDT->VLT)
     -> SoSo continuity -> provenance trace -> rehydration -> AI -> verified source/hash
```

using only components that already existed in this repository before this
change. No authority file was modified. No production-clearance statement
was generated. No test result is self-ratified — every step is capped at
`PASS_PENDING_REVIEW`, never `PASS_VERIFIED` (LMPQ-001 §25/§29).

## Result: the chain completes end-to-end

All 8 steps reached `PASS_PENDING_REVIEW`; nothing halted or failed. See
`PH6_SOURCE/ARTIFACTS/LMPQ001_PM01_05_SINGLE_CHAIN_20260913/result_summary.json`
for the full trace (authority_hash `5244884280c369...`, VLT
`vlt_5e0a04fb3337a98dbdd49984`, topology_hash `84d65cec996d79...`) and
`qualification_matrix.json` for the per-PM-test breakdown.

## Which interfaces exist vs. don't (the actual finding)

| LMPQ-001 concept | Repository reality |
|---|---|
| CRAM evidence + PSEUDO-M + PSEUDO-A | Exists and works: `ph6.cram_pu.ph6_cram_sim.CRAMSimulation` |
| PH6 token RT / VDT / VLT | Exists and works: `ph6.tok.lifecycle.TokenStore` (real promotion, real audit chain) |
| SoSo continuity | Exists and works: `ph6.ssmt.swarms.S1ActiveMemorySwarm` |
| Rehydration capability | Exists: `ph6_l2_expand.topology_reconstruct.reconstruct_topology` (reconstructs purely from the persisted audit chain) |
| **Life CRAM (named) / BCV2** | **Does not exist anywhere in this repository under any name.** Nearest analog: `_soso_advisory`, a 3-state (STABLE/MODERATE/UNSTABLE) signal — not an attention/readiness system. |
| **RLT (Real Loss Token)** | **Does not exist.** |
| **PLT (Predicted Loss Token)** | **Does not exist.** |
| **AHT (rehydration token)** | **Does not exist as a token type** (the rehydration capability above exists but isn't materialized as an AHT object). |
| **SoSo-JEDI (as a provenance lookup)** | The only code under that name (`PH6_SOURCE/AI/soso_jedi`, Book-V storm/swarm engine) is a heavier, unwired simulation that takes synthetic "storm branches" as input — not built for, and not used for, a single-token provenance lookup. This bench traces provenance directly via `cram_ref_hash` instead. |

**PM-01** (Preservation): `PASS_PENDING_REVIEW` — full procedure executed
including an AI summarization pass; original CRAM-A evidence file verified
byte-unchanged both by `replay_check` and an independent on-disk hash
check.

**PM-02** (Continuity): `NOT_EXECUTED` — needs a 4-experience chain
(E001..E004); out of scope for a 1-experience milestone.

**PM-03** (SoSo-JEDI Provenance): `PASS_PENDING_REVIEW` for the functional
requirement (hash traced to source); the named Book-V component itself was
not exercised (see table above).

**PM-04** (Life CRAM Attention): `BLOCKED` — the named component doesn't
exist; a substitute was exercised but this is an architecture decision,
not something this harness can resolve.

**PM-05** (Token-Lifecycle): `FAIL` as specified — RT/VDT/VLT sub-path is
`PASS_PENDING_REVIEW`; RLT/PLT/AHT sub-path is `BLOCKED` (components don't
exist). Building them is a real implementation gap, explicitly out of
scope for "minimum non-authoritative integration harness."

## Also found, not fixed (existing-code properties, not new bugs)

1. **Lane boundary confirmed the hard way.** An earlier draft of this
   harness lived under `ph6_l2_expand/` and separately under
   `ph6/cram_pu/tools/`; both placements failed pre-existing boundary
   tests (`test_no_reverse_path.py`, `test_replay_independence.py`,
   `test_soso_tokens_not_lane1.py`) because Lane-1 (`cram_pu`) and Lane-2
   (`ph6_l2_expand`) are each forbidden from referencing the other, in
   both directions. The harness now lives at the neutral top level
   (`ph6/lmpq001_single_chain_bench.py`, alongside the existing
   `ph6/cfc.py` and `ph6/cvs3_preflight.py`), which is the only place a
   cross-lane orchestrator can legally exist. Full test suite (294 tests
   across `ph6/` + `ph6_l2_expand/`, excluding 4 pre-existing unrelated
   collection errors and 1 pre-existing root-user environment failure)
   passes clean with the harness in place.
2. **Topology-hash determinism is chain-scoped, not run-scoped.**
   `ph6_l2_expand.token_types.make_rt/make_vdt/make_vlt` stamp `created_at`
   from the wall clock at reconstruction time rather than carrying a
   timestamp from the persisted tok audit event. Reconstructing the *same*
   audit chain twice is deterministic (matches what ER-1E already proved,
   and is reconfirmed by this bench's own test suite); two *independent*
   campaign runs at different wall-clock times are not bit-identical in
   their topology hash even from identical evidence. Not fixed here —
   flagged for whoever owns `ph6_l2_expand.token_types` next.

## Files

```
ph6/lmpq001_single_chain_bench.py                 (harness, Lane-1+Lane-2 orchestration)
ph6/run_lmpq001_single_chain.py                    (CLI runner -> result_summary.json)
ph6/tests/test_lmpq001_pm01_pm05_single_chain.py   (10 tests, all passing)
PH6_SOURCE/ARTIFACTS/LMPQ001_PM01_05_SINGLE_CHAIN_20260913/
  manifest.json            (sha256 for every artifact below)
  result_summary.json      (full 8-step chain trace)
  qualification_matrix.json (PM-01..PM-05 status, per LMPQ-001 SS25 vocabulary)
  ai_response_log.jsonl    (manual AI summarization pass for PM-01)
  tok_advisory_audit.jsonl (real ph6.tok hash-chained audit log for this run)
  cram_audit.jsonl         (real CRAM audit log for this run)
```

Reproduce: `PYTHONPATH=. python3 ph6/run_lmpq001_single_chain.py <output_dir>`

## Next step (per operator direction)

If the operator ratifies this milestone, the natural next step is 10–20
fixtures (enough to exercise PM-02's continuity chain and PM-05's
production N=5 promotion threshold instead of this bench's N=1 override),
still using existing components — not the 1,000-experience campaign yet.

## AI Contribution Signature

```json
{"proposed_by":"claude-code-lane2","proposed_at_utc":"2026-09-13T06:00:00Z","api_call_log_ref":"lmpq001-pm01-05-single-chain-20260913","ratified_by":null}
```
