# PH6-EVC-1.0 — Evidence Validation Campaign Matrix

```text
Document ID:  PH6-EVC-1.0
Status:       ACTIVE
Authority:    Human-authored. AI may read and apply. AI may not modify.
Purpose:      Map every remaining open evidence gap to a named executable campaign
              with explicit pass conditions, required artifacts, and closure rules.
Machine ref:  PH6_SOURCE/VALIDATION/campaign_matrix.json
```

---

## Governing Rule

A gap is not closed until its required campaign evidence is produced
and reviewed by a human operator.

```text
Software changes cannot substitute for runtime, hardware, endurance,
or transfer evidence.

Unit tests cannot substitute for runtime evidence.

AI output cannot substitute for hardware evidence.

Production clearance requires all campaigns and STOP-SHIP gates closed
by human-reviewed artifacts.
```

---

## Current Status

```text
LOCAL TOOLING:       COMPLETE FOR CURRENT PHASE
EVIDENCE CAMPAIGNS:  NEXT
PRODUCTION CLEARANCE: NOT DECLARED
OPEN ITEMS:          HARDWARE / RUNTIME / ENDURANCE EVIDENCE REQUIRED
```

| Domain                      | Status                              |
| --------------------------- | ----------------------------------- |
| AI preload                  | COMPLETE                            |
| Session drift scanner       | COMPLETE                            |
| Session receipt chain       | IMPLEMENTED / LOCAL-VERIFIED        |
| CRAM ingest receipt chain   | IMPLEMENTED / UNIT-VERIFIED         |
| VRC-1.0                     | IMPLEMENTED / UNIT-TESTED (18/18)   |
| Governance scan             | OPERATIONAL                         |
| Production clearance        | NOT DECLARED                        |

---

## Campaign Map

| Campaign | Gap Closed                  | Closes STOP-SHIP | Evidence Class  | Status |
| -------- | --------------------------- | ---------------- | --------------- | ------ |
| EVC-01   | crash_receipt_continuity    | No               | RUNTIME         | OPEN   |
| EVC-02   | long_run_chain_behavior     | No               | RUNTIME         | OPEN   |
| EVC-03   | remote_transfer_chain       | OI-03            | HARDWARE_RUNTIME | OPEN  |
| EVC-04   | verdict_metric_payload_replay | No             | RUNTIME         | OPEN   |
| EVC-05   | production_clearance        | —                | HUMAN_REVIEW    | OPEN   |

---

## EVC-01 — Crash Receipt Continuity

**Gap:** `crash_receipt_continuity`
**Prerequisite:** None

**Objective:**
Prove that the CRAM ingest receipt chain survives a crash or power loss during
receipt emission. After restart, the chain verifier must either report the chain
intact or detect and correctly classify the break.

**Commands:**
```bash
# Start ingest run (minimum 10 frames)
# Send SIGKILL mid-run:  kill -9 <pid>
# Restart ingest process
python3 -c "from ph6.cram_pu.ingest_receipt_verify import verify_receipt_chain; ..."
python3 -m ph6.cram_pu.vrc  # certify post-restart
```

**Required Artifacts:**
- `ingest_receipt_log.jsonl` — state before crash
- `ingest_receipt_log.jsonl` — state after restart
- `ph6.ingest_receipt_verify.v1` report — `chain_intact` or explicit break classified
- `ph6.vrc_receipt.v1` — certification run post-restart
- Crash timestamp and process state at time of kill

**Pass Condition:**
Receipt chain verifier correctly reports chain status after restart. If broken,
all breaks are detected and classified. No silent corruption. VRC-1.0 does not
suppress failures.

**Fail Condition:**
Silent corruption, verifier misreports chain as intact when broken, or VRC-1.0
produces a passing certification over a broken chain.

**Closes:** `crash_receipt_continuity`
**Remains Open:** OI-01, OI-03, all other gaps

---

## EVC-02 — Long-Run Receipt Chain Behavior

**Gap:** `long_run_chain_behavior`
**Prerequisite:** None

**Objective:**
Prove that the CRAM ingest receipt chain remains deterministic and intact across
at least 300 frames or 5 minutes of continuous ingest.

**Commands:**
```bash
# Run CRAM-PU for 300+ frames (or 5–30 min)
python3 ph6/cram_pu/ingest_receipt_verify.py  # verify at completion
python3 -m ph6.cram_pu.vrc  # certify completed store
# Confirm event_seq monotonic 1..N, no gaps
```

**Required Artifacts:**
- `ingest_receipt_log.jsonl` — minimum 300 entries
- `ph6.ingest_receipt_verify.v1` report — `chain_intact = true`
- `ph6.vrc_receipt.v1` with `result_set_hash`
- Frame count vs receipt count comparison
- Run duration and timestamp span

**Pass Condition:**
Chain intact across 300+ receipts. VRC-1.0 certifies cleanly. `event_seq`
monotonic 1..N. `result_set_hash` is stable.

**Fail Condition:**
Any chain break, event_seq gap, verifier failure, or VRC certification failure.

**Closes:** `long_run_chain_behavior`
**Remains Open:** OI-01, OI-03, all other gaps

---

## EVC-03 — Remote Chain Continuity (OI-03)

**Gap:** `remote_transfer_chain`
**Closes STOP-SHIP:** OI-03
**Prerequisites:** Two Raspberry Pi units active and network-connected

**Objective:**
Prove that the CRAM ingest receipt chain and CRAM commit chain survive a real
Pi-to-Pi transfer with full hash continuity. Receiving Pi must be able to verify
the chain without mutation. This is also the closure evidence for OI-03.

**Commands:**
```bash
# Pi-A: Run CRAM ingest (300+ frames)
# Pi-A → Pi-B: Run RSYNC/transfer pipeline
# Pi-B: Verify
python3 ph6/cram_pu/ingest_receipt_verify.py  # on transferred log
python3 -m ph6.cram_pu.vrc  # certify transferred store
# Compare result_set_hash: Pi-A == Pi-B required
```

**Required Artifacts:**
- `ingest_receipt_log.jsonl` from Pi-A
- `ingest_receipt_log.jsonl` from Pi-B (transferred, unmodified)
- `ph6.ingest_receipt_verify.v1` from Pi-B — `chain_intact = true`
- `ph6.vrc_receipt.v1` from Pi-B with `result_set_hash` matching Pi-A
- Transfer log showing RSYNC completion and file hashes
- Confirmation that no hash was rewritten on receive

**Pass Condition:**
Pi-B `chain_intact = true`. `result_set_hash` identical on Pi-A and Pi-B.
No hash mutations during transfer. VRC-1.0 certifies on Pi-B.

**Fail Condition:**
Any hash mismatch, chain break, mutation, or `result_set_hash` divergence.

**Closes:** `remote_transfer_chain`, `OI-03`
**Remains Open:** OI-01, all other gaps

---

## EVC-04 — Payload Replay Verdict and Metric Comparison

**Gap:** `verdict_metric_payload_replay`
**Prerequisite:** Completed CRAM run with stored payloads in CRAM-0

**Objective:**
Prove that PSEUDO-M and PSEUDO-A produce identical verdicts and fixed-point
metrics when re-run on the original stored payload bytes. This closes the
boundary named in VRC-1.0: verdict and metric comparison requires payload
access not stored in the receipt chain.

**Commands:**
```bash
# For each INGEST_ACCEPTED frame: load payload from CRAM-0
# Re-run VerdictLogger on payload
# Compare verdict, entropy_fp, laplacian_var_fp, motion_fraction_fp
# Verify metric_schema = ph6.metrics.fixedpoint.v1, metric_scale = 10000
# Record any mismatch as R1 (replay parity failure)
```

**Required Artifacts:**
- Replay comparison report: frame-by-frame verdict match
- Replay comparison report: frame-by-frame metric match (fixed-point)
- Zero R1 failures — all verdicts and metrics match
- `result_set_hash` from original run
- `result_set_hash` from replay run — must match

**Pass Condition:**
All replayed verdicts and fixed-point metrics match stored values exactly.
`result_set_hash` identical. Zero R1 failures.

**Fail Condition:**
Any verdict mismatch, metric mismatch, or `result_set_hash` divergence.
A metric mismatch due to float rounding indicates a fixedpoint encoding violation.

**Closes:** `verdict_metric_payload_replay`
**Remains Open:** OI-01, OI-03, crash and transfer gaps

---

## EVC-05 — Production Clearance Review Gate

**Gap:** `production_clearance`
**Prerequisites:** EVC-01 through EVC-04 PASS + OI-01 CLOSED + OI-03 CLOSED

**Objective:**
Human-conducted gate review. This is the only path to production clearance.
No software artifact, unit test, or AI output may substitute for this review.

**Required Artifacts:**
- EVC-01 through EVC-04 evidence receipts
- OI-01 hardware integration report (human-authored)
- OI-03 transfer receipt from EVC-03
- Final governance drift scan report at HEAD
- Final `ph6.vrc_receipt.v1` with `result_set_hash`
- Human-signed production clearance record

**Pass Condition:**
All prerequisites met. Human operator reviews and signs.

**Fail Condition:**
Any prerequisite not met. Any open STOP-SHIP gate. AI claims production
clearance without human review.

**Closes:** `production_clearance`

---

## Closure Authority

```text
Who may close a gap:       Human operator only
AI may close:              NO
Software patch may close:  NO
Unit test may close:       NO

Exception: EVC-01 through EVC-04 produce machine-generated evidence
artifacts. A human must review those artifacts before the gap is closed.
The artifacts are evidence, not closure.
```

---

## Open STOP-SHIP Gates

| Gate | Description | Closed By | Status |
| ---- | ----------- | --------- | ------ |
| OI-01 | Hailo hardware integration incomplete | Hardware run + report | OPEN |
| OI-03 | Real Pi-to-Pi live transfer not yet certified | EVC-03 | OPEN |
