# Campaign 01 — 300-Frame Full-Stack Coherence Run

```text
Campaign ID:  C01
Status:       OPEN
Phase:        PH6 / CRAM v3.1 — Evidence Closure Campaign
Priority:     1 (First)
Purpose:      Prove the full stack operates correctly as one integrated system.
```

---

## Objective

Prove that the complete PH6 stack — from camera input through PSEUDO, advisory
layers, CRAM writes, and PostRun — operates coherently for a minimum of 300 frames
without authority violations, write contract failures, or RSYNC blocking.

This is the foundational coherence proof. All other campaigns build on it.

---

## Proof Chain

```text
camera / input
  → PSEUDO (Lane 1 deterministic gate)
  → SoSo / TOK advisory (Lane 2, Authority ZERO, no PASS/DROP)
  → CRAM-A writes (atomic write contract enforced)
  → PostRun report generated
  → replay verification
  → hash-chain receipt
```

---

## Required Minimum

- Minimum 300 frames processed unless the system crashes before completion.
- If crash occurs before 300 frames: the crash itself becomes evidence. Log and preserve crash artifacts.
- Full stack enabled: PSEUDO, CRAM-A, SoSo/TOK advisory, RSYNC.
- PSEUDO must emit verdicts (PASS/DROP) for all frames.
- CRAM-A must complete atomic writes for all PASS frames.
- SoSo/TOK advisory must remain advisory (no PASS/DROP issued from Lane 2).
- RSYNC must not be blocked at any point.

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

- [ ] frames_processed >= 300
- [ ] All CRAM-A writes completed (no partial writes)
- [ ] PSEUDO emitted PASS or DROP for every frame
- [ ] SoSo/TOK advisory output is present but zero PASS/DROP issued
- [ ] RSYNC ran without being blocked
- [ ] PostRun report generated without errors
- [ ] Replay produces identical result_set_hash
- [ ] Hash-chain receipt is intact
- [ ] Drift scan passes before and after

---

## FAIL Criteria

- frames_processed < 300 and no crash occurred (unexplained short run)
- Any CRAM-A write left a tmp file without completing rename
- SoSo or TOK issued a PASS or DROP
- RSYNC was blocked, delayed, or resource-starved by AI or analysis
- PostRun report missing or malformed
- Replay produces a different result_set_hash than the original run
- Hash-chain receipt fails verification
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
