# Campaign 01B — Advisory Expansion (Swarm-Enabled Variant)

```text
Campaign ID:   C01B
Status:        OPEN
Phase:         PH6 / CRAM v3.1 — Evidence Closure Campaign
Priority:      1B (runs after C01 baseline is closed)
Purpose:       Prove Swarm, enabled as MRAM-S advisory sidecar only,
               does not affect deterministic system state.
Prerequisite:  C01 baseline must be CLOSED first.
               C01B uses C01 result_set_hash as the reference value.
Baseline:      PSEUDO=ON  SoSo=ON  TOK=ON  Swarm=ON (MRAM-S only)
```

---

## Objective

Prove that adding Swarm as an advisory sidecar does not change any deterministic
system output: PSEUDO verdicts, CRAM-A contents, replay hash, or audit authority chain.

Swarm must remain an advisory ensemble. It must never become a voting authority.

```
PSEUDO decides.
Tokens observe continuity.
Swarm advises collectively.
Only Lane 1 can affect PASS/DROP.
```

---

## Prerequisite: C01 Must Be Closed First

Do not run C01B until:
- C01 closure receipt exists at `RECEIPTS/C01_CLOSURE_RECEIPT.md`
- C01 result_set_hash is recorded and signed
- Human has verified C01 passed all criteria

The C01 result_set_hash is the reference value for SWARM-ZERO-001.

---

## Authority Class Summary

| Component   | Lane   | Authority          | Writes To           | Role in this campaign                       |
|-------------|--------|--------------------|---------------------|---------------------------------------------|
| PSEUDO      | Lane 1 | **Authoritative**  | CRAM-A / audit      | Deterministic PASS/DROP engine — unchanged  |
| TOK         | Lane 2 | **Authority ZERO** | MRAM-S only         | Advisory continuity — unchanged from C01    |
| Swarm       | Lane 2 | **Authority ZERO** | MRAM-S only         | Advisory ensemble sidecar — ON for C01B     |

---

## Swarm Operating Constraints for C01B

Swarm is active in C01B as an advisory sidecar only.

**Swarm may produce:**

```text
advisory_observations
agent_disagreements
false_consensus_warning
drift_pressure_note
epistemic_diversity_report
```

**Swarm must not produce:**

```text
verdict
result
pass_drop_recommendation
threshold_update
commit_decision
authority_score
```

Any Swarm output that contains those forbidden fields is an automatic FAIL.

---

## Proof Chain

```text
camera / input (same input set as C01 baseline)
  → PSEUDO (Lane 1 — deterministic, unchanged from C01)
  → SoSo advisory (Lane 2, MRAM-S, unchanged from C01)
  → TOK advisory (Lane 2, MRAM-S/tokens, unchanged from C01)
  → Swarm advisory (Lane 2, MRAM-S only, NEW in C01B)
  → CRAM-A writes (unchanged from C01)
  → PostRun report
  → replay verification
  → hash comparison against C01 result_set_hash
```

---

## SWARM-ZERO-001 Test (Core Proof)

This is the mandatory proof test for C01B.

```bash
# Reference: C01 result_set_hash (from RECEIPTS/C01_CLOSURE_RECEIPT.md)
# Record: result_set_hash_c01=<value from C01 receipt>

# C01B run: Swarm enabled, same input set
python3 ph6_console.py --frames 300 --full-stack --swarm-enabled
# Record: result_set_hash_c01b

# Comparison
echo "C01 (Swarm OFF):  <result_set_hash_c01>"
echo "C01B (Swarm ON):  <result_set_hash_c01b>"
# Must be equal. If different: Swarm is affecting deterministic state — FAIL.
```

**What must match (C01 vs C01B):**

```text
PSEUDO verdicts (frame by frame)
CRAM-A contents
replay result_set_hash
audit authority chain
RSYNC behavior
```

**What may differ (C01 vs C01B):**

```text
MRAM-S advisory artifacts
Swarm advisory logs
Swarm agent reports
```

---

## Required Minimum

- Minimum 300 frames processed.
- C01 must be closed before this run begins.
- Swarm must be configured as MRAM-S advisory sidecar only.
- No Swarm output may touch CRAM-A, PSEUDO, or RSYNC.
- SWARM-ZERO-001 must be executed and logged.

---

## Commands

```bash
# Step 1: Confirm C01 is closed
cat PH6_SOURCE/EVIDENCE_CAMPAIGNS/RECEIPTS/C01_CLOSURE_RECEIPT.md
# Verify result_set_hash is present

# Step 2: Pre-run drift scan
python3 PH6_SOURCE/TOOLS/governance_drift_scan.py --scan-root PH6_SOURCE

# Step 3: C01B run (Swarm enabled)
python3 ph6_console.py --frames 300 --full-stack --swarm-enabled

# Step 4: Post-run verification
python3 ph6/audit.py --verify-run <run_stamp>

# Step 5: Replay verification
python3 ph6/cram_pu/runtime/ --replay <run_stamp>

# Step 6: SWARM-ZERO-001 comparison
echo "C01 hash:   <c01_result_set_hash>"
echo "C01B hash:  <c01b_result_set_hash>"

# Step 7: Inspect Swarm advisory outputs (MRAM-S only)
ls -la /var/ph6/mram-s/swarm/

# Step 8: Post-run drift scan
python3 PH6_SOURCE/TOOLS/governance_drift_scan.py --scan-root PH6_SOURCE
```

---

## Expected Artifacts

```text
logs/run_c01b_<stamp>/
validation_runs/c01b_<stamp>/
postrun_report_c01b_<stamp>.json
replay_receipt_c01b_<stamp>.json
swarm_advisory_log_<stamp>.json          (MRAM-S artifacts only)
swarm_zero_001_comparison_<stamp>.json   (hash comparison result)
```

---

## PASS Criteria

**Stack:**
- [ ] Run configuration: PSEUDO=ON, SoSo=ON, TOK=ON, Swarm=ON (MRAM-S)
- [ ] frames_processed >= 300
- [ ] C01 was closed before this run

**SWARM-ZERO-001:**
- [ ] C01B result_set_hash == C01 result_set_hash
- [ ] PSEUDO verdicts are frame-by-frame identical to C01
- [ ] CRAM-A contents are identical to C01
- [ ] Replay hash matches C01 replay hash

**Swarm:**
- [ ] Swarm wrote advisory artifacts to MRAM-S only
- [ ] Swarm did not write to CRAM-A
- [ ] Swarm output contains no verdict, result, PASS, DROP, or threshold fields
- [ ] Swarm advisory artifacts differ from C01 MRAM-S (expected — confirms Swarm was active)

**System:**
- [ ] RSYNC not blocked
- [ ] PostRun report generated without errors
- [ ] Drift scan passes before and after

---

## FAIL Criteria

- C01B result_set_hash differs from C01 result_set_hash (Swarm affecting deterministic state)
- Any Swarm output contains verdict, result, PASS, DROP, or threshold field
- Swarm wrote to CRAM-A
- PSEUDO verdicts differ from C01 on same frames
- RSYNC blocked during Swarm advisory inference
- C01 was not closed before this run began
- frames_processed < 300 without crash evidence

---

## Gap Closed by This Campaign

C01B does not close any STOP-SHIP gap directly. It provides:

- Proof that Swarm can be safely enabled as advisory sidecar
- Proof of zero Lane 2 authority leakage under Swarm load
- Prerequisite evidence for any future Swarm operational use

---

## Closure Evidence

```text
PH6_SOURCE/EVIDENCE_CAMPAIGNS/RECEIPTS/C01B_CLOSURE_RECEIPT.md
```

Required contents:
- C01 reference result_set_hash
- C01B result_set_hash
- SWARM-ZERO-001 comparison result: PASS
- Frame count
- Swarm advisory artifact count (confirming Swarm was active)
- Human sign-off
