# Campaign 01 — 300-Frame Full-Stack Coherence Run

```text
Campaign ID:  C01
Status:       OPEN
Phase:        PH6 / CRAM v3.1 — Evidence Closure Campaign
Priority:     1 (First)
Purpose:      Prove the full stack operates correctly as one integrated system.
Baseline:     PSEUDO=ON  SoSo=ON  TOK=ON  Swarm=OFF
Variant:      See CAMPAIGN_01B_ADVISORY_EXPANSION.md (Swarm=ON)
```

---

## Objective

Prove that the complete PH6 stack — from camera input through PSEUDO, advisory
layers, CRAM writes, and PostRun — operates coherently for a minimum of 300 frames
without authority violations, write contract failures, or RSYNC blocking.

This is the foundational coherence proof. All other campaigns build on it.

---

## Authority Class Summary

Three components are active in this campaign. They are **not interchangeable**.

| Component   | Lane   | Authority          | Writes To              | Role in this campaign                     |
|-------------|--------|--------------------|------------------------|-------------------------------------------|
| PSEUDO      | Lane 1 | **Authoritative**  | CRAM-A / audit         | Deterministic PASS/DROP engine — central  |
| TOK         | Lane 2 | **Authority ZERO** | MRAM-S only            | Advisory continuity / drift-observation   |
| Swarm       | Lane 2 | **Authority ZERO** | (excluded from C01)    | Quarantined — tested separately in C01B   |

```
PSEUDO decides.
Tokens observe continuity.
Swarm advises collectively.
Only Lane 1 can affect PASS/DROP.
```

---

## Proof Chain

```text
camera / input
  → PSEUDO (Lane 1 deterministic gate — emits PASS/DROP, metrics, reasons)
  → SoSo advisory (Lane 2, MRAM-S only, no PASS/DROP)
  → TOK advisory (Lane 2, MRAM-S/tokens only, no PASS/DROP)
  → [Swarm: OFF in C01 baseline — see C01B]
  → CRAM-A writes (atomic write contract enforced)
  → PostRun report generated
  → replay verification
  → hash-chain receipt
```

---

## Required Minimum

- Minimum 300 frames processed unless the system crashes before completion.
- If crash occurs before 300 frames: the crash itself becomes evidence. Log and preserve crash artifacts.
- Stack configuration: PSEUDO=ON, SoSo=ON, TOK=ON, Swarm=OFF.
- PSEUDO must emit deterministic PASS/DROP, metrics, and reasons[] for every frame.
- CRAM-A must complete atomic writes for all PASS frames.
- TOK must emit advisory continuity artifacts to MRAM-S only — no CRAM-A writes.
- SoSo and TOK must remain advisory (no PASS/DROP issued from Lane 2).
- Swarm is excluded from this baseline run.
- RSYNC must not be blocked at any point.

---

## PSEUDO Requirements

PSEUDO is the deterministic authority engine. It must not be optional.

- PSEUDO must emit a deterministic PASS or DROP for every frame.
- PSEUDO must use canonical metrics only: `entropy`, `laplacian_var`, `motion_fraction`.
- PSEUDO must not read Lane 2 advisory outputs (SoSo, TOK, Swarm, MRAM-S).
- PSEUDO must not use wall-clock time as a decision input.
- PSEUDO must not use AI language, probabilistic scoring, or confidence values.
- Replay must reproduce the identical verdict sequence from the same input.
- Forbidden fields must not appear: `motion_score`, `motion_decay_score`.

Expected PSEUDO output schema per frame:

```json
{
  "verdict": "PASS or DROP",
  "metrics": {
    "entropy": "<fixed_precision_value>",
    "laplacian_var": "<fixed_precision_value>",
    "motion_fraction": "<fixed_precision_value>"
  },
  "reasons": []
}
```

---

## TOK Requirements

TOK (Tokens) are advisory continuity and drift-observation sidecars. Authority ZERO.

- TOK may emit: RT (reference token), VDT (drift token), VLT (longevity token), AVLT.
- TOK writes only to MRAM-S: `/var/ph6/mram-s/tokens/`
- TOK must not write to CRAM-A under any condition.
- TOK output must not affect PSEUDO verdicts, CRAM-A contents, replay, or RSYNC.
- Token rebuild hash must match on replay.
- Token mismatch must log an advisory warning only — not a verdict or error.

TOK hard prohibitions (immediate FAIL if any appear in output):

```text
PASS field
DROP field
verdict field
result field implying authority
replay_dependency = true
threshold mutation
RSYNC blocking
CRAM-A write
```

**TOK-LEAK-001 test (required as part of C01):**

```bash
# Run 1: TOK enabled
python3 ph6_console.py --frames 300 --full-stack --tok-enabled
# Record: result_set_hash_tok_on

# Run 2: TOK disabled (same input set)
python3 ph6_console.py --frames 300 --full-stack --tok-disabled
# Record: result_set_hash_tok_off

# Verify hashes match
echo "TOK ON:  <result_set_hash_tok_on>"
echo "TOK OFF: <result_set_hash_tok_off>"
# Must be equal. If different: Lane 2 authority leak — FAIL.
```

---

## Swarm Requirements (Baseline: OFF)

Swarm is quarantined from C01 baseline. It is tested separately in Campaign 01B.

**Why:** keep the first evidence run clean. Prove the deterministic spine first.

If Swarm is accidentally enabled during C01:
- Stop the run immediately.
- Document the accidental activation.
- Restart with Swarm=OFF.
- Do not count the mixed run as C01 baseline evidence.

The Swarm test (SWARM-ZERO-001) is defined in Campaign 01B.

---

## Commands

```bash
# Step 1: Pre-run drift scan
python3 PH6_SOURCE/TOOLS/governance_drift_scan.py --scan-root PH6_SOURCE

# Step 2: Launch full-stack run (minimum 300 frames)
# [Replace with actual run command for your stack]
python3 ph6_console.py --frames 300 --full-stack

# Step 3: Post-run verification
python3 ph6/audit.py --verify-run <run_stamp>

# Step 4: Replay verification
# [Replace with actual replay command]
python3 ph6/cram_pu/runtime/ --replay <run_stamp>

# Step 5: Post-run drift scan
python3 PH6_SOURCE/TOOLS/governance_drift_scan.py --scan-root PH6_SOURCE
```

---

## Expected Artifacts

```text
logs/run_<stamp>/
validation_runs/<stamp>/
manifest.json
postrun_report_<stamp>.json
replay_receipt_<stamp>.json
hash_chain_receipt_<stamp>.blake2b
```

---

## PASS Criteria

**Stack:**
- [ ] Run configuration: PSEUDO=ON, SoSo=ON, TOK=ON, Swarm=OFF
- [ ] frames_processed >= 300
- [ ] RSYNC ran without being blocked

**PSEUDO (Lane 1):**
- [ ] PSEUDO emitted PASS or DROP for every frame
- [ ] PSEUDO output contains `metrics` (entropy, laplacian_var, motion_fraction)
- [ ] PSEUDO output contains `reasons[]`
- [ ] No forbidden fields (`motion_score`, `motion_decay_score`) in PSEUDO output
- [ ] No AI or Lane 2 dependency found in PSEUDO verdict path

**CRAM-A:**
- [ ] All CRAM-A writes completed (no partial writes, no orphaned tmp files)

**TOK (Lane 2):**
- [ ] TOK advisory artifacts written to MRAM-S only
- [ ] No TOK writes to CRAM-A
- [ ] TOK-LEAK-001: result_set_hash with TOK=ON equals result_set_hash with TOK=OFF

**Replay:**
- [ ] Replay produces identical result_set_hash as original run
- [ ] Hash-chain receipt is intact

**PostRun:**
- [ ] PostRun report generated without errors
- [ ] Drift scan passes before and after

---

## FAIL Criteria

**Stack:**
- frames_processed < 300 and no crash occurred (unexplained short run)
- Swarm was active during this run (contaminated baseline — restart required)

**PSEUDO:**
- PSEUDO did not emit a verdict for any frame
- Forbidden field (`motion_score`, `motion_decay_score`) found in PSEUDO output
- PSEUDO verdict path reads any Lane 2 advisory output

**CRAM-A:**
- Any CRAM-A write left a tmp file without completing rename

**TOK:**
- TOK wrote to CRAM-A
- TOK emitted a PASS, DROP, verdict, or authority-implying result field
- TOK-LEAK-001 fails: result_set_hash changes when TOK is toggled

**Replay:**
- Replay produces a different result_set_hash than the original run
- Hash-chain receipt fails verification

**System:**
- RSYNC was blocked, delayed, or resource-starved by AI or analysis
- PostRun report missing or malformed
- Drift scan fails after the run

---

## Closure Evidence

This campaign is CLOSED when the following file exists and is human-verified:

```text
PH6_SOURCE/EVIDENCE_CAMPAIGNS/RECEIPTS/C01_CLOSURE_RECEIPT.md
```

Required contents:
- Run stamp
- Frame count
- Replay hash match confirmation
- Human sign-off

---

## Campaign Notes

If the system crashes before 300 frames, do not restart and count combined.
Each run is independent. Document the crash as a separate finding and
open Campaign 04 (Crash Recovery) if not already open.
