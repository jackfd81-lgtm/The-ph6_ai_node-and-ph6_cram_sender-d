# Campaign 05 — Replay Parity

```text
Campaign ID:  C05
Status:       OPEN
Phase:        PH6 / CRAM v3.1 — Evidence Closure Campaign
Priority:     5
Purpose:      Prove replay produces identical deterministic results from the same
              input set, independent of Lane 2 advisory state.
```

---

## Objective

Prove that CRAM-R (replay path) is perfectly deterministic: given the same
input evidence set, it always produces the same PSEUDO verdicts, the same
result_set_hash, and the same audit chain expectations — regardless of what
Lane 2 advisory components emitted during the original run.

Lane 2 outputs (SoSo, TOK, MRAM-S) must not affect replay results.
Lane 2 outputs must have replay_dependency = false.

---

## Required Minimum

- Original run: minimum 300 frames with full stack active.
- Replay must be run at least twice on the same evidence set.
- Both replays must produce identical result_set_hash.
- A third replay must be run with Lane 2 advisory outputs deliberately excluded.
- All three result_set_hash values must match.

---

## Proof Chain

```text
Original run (300+ frames, full stack)
  → evidence set captured (CRAM-A writes, hash receipts)
  → result_set_hash_original recorded

Replay 1 (standard replay, same evidence set)
  → result_set_hash_replay_1
  → must equal result_set_hash_original

Replay 2 (standard replay, same evidence set, second execution)
  → result_set_hash_replay_2
  → must equal result_set_hash_original

Replay 3 (Lane 2 outputs excluded, same evidence set)
  → result_set_hash_replay_3
  → must equal result_set_hash_original
  → proves Lane 2 outputs are NOT replay dependencies
```

---

## Commands

```bash
# Pre-run drift scan
python3 PH6_SOURCE/TOOLS/governance_drift_scan.py --scan-root PH6_SOURCE

# Original run (full stack, 300+ frames)
# [Replace with actual run command]
python3 ph6_console.py --frames 300 --full-stack
# Note: record run_stamp and result_set_hash

# Replay 1
python3 ph6/cram_pu/runtime/ --replay <run_stamp>
# Note: record result_set_hash_replay_1

# Replay 2 (second execution, same stamp)
python3 ph6/cram_pu/runtime/ --replay <run_stamp>
# Note: record result_set_hash_replay_2

# Replay 3 (Lane 2 excluded)
python3 ph6/cram_pu/runtime/ --replay <run_stamp> --exclude-lane2-advisory
# Note: record result_set_hash_replay_3

# Hash comparison
echo "Original:  <result_set_hash_original>"
echo "Replay 1:  <result_set_hash_replay_1>"
echo "Replay 2:  <result_set_hash_replay_2>"
echo "Replay 3:  <result_set_hash_replay_3>"

# Post-run drift scan
python3 PH6_SOURCE/TOOLS/governance_drift_scan.py --scan-root PH6_SOURCE
```

---

## Expected Artifacts

```text
original_run_receipt_<stamp>.json
replay_1_receipt_<stamp>.json
replay_2_receipt_<stamp>.json
replay_3_receipt_<stamp>.json
parity_comparison_report_<stamp>.json    (all four hashes, PASS/FAIL per comparison)
```

---

## PASS Criteria

- [ ] Original run: frames_processed >= 300
- [ ] result_set_hash_replay_1 == result_set_hash_original
- [ ] result_set_hash_replay_2 == result_set_hash_original
- [ ] result_set_hash_replay_3 == result_set_hash_original
- [ ] PSEUDO verdicts are identical across all three replays
- [ ] Audit chain expectations are identical across all three replays
- [ ] Lane 2 advisory outputs (SoSo, TOK, MRAM-S) have replay_dependency = false confirmed
- [ ] Drift scan passes before and after all replays

---

## FAIL Criteria

- Any result_set_hash diverges between the original run and any replay
- PSEUDO verdicts differ between replays on the same evidence set
- Audit chain expectations differ between replays
- Any Lane 2 advisory output was found to affect a replay verdict
- replay_dependency != false for any Lane 2 component
- Replay 3 (Lane 2 excluded) produces a different hash than the others

---

## Lane 2 Non-Dependency Verification

A specific check must be logged for each Lane 2 component:

| Component | replay_dependency value | Expected | Result |
|-----------|------------------------|----------|--------|
| SoSo      | false                  | false    | TBD    |
| TOK       | false                  | false    | TBD    |
| MRAM-S    | false                  | false    | TBD    |
| SSMT      | false                  | false    | TBD    |

All must be false. Any true value is an automatic FAIL.

---

## Closure Evidence

```text
PH6_SOURCE/EVIDENCE_CAMPAIGNS/RECEIPTS/C05_CLOSURE_RECEIPT.md
```

Required contents:
- Run stamp
- Frame count
- All four result_set_hash values (must be identical)
- Lane 2 replay_dependency verification table (all false)
- Human sign-off
