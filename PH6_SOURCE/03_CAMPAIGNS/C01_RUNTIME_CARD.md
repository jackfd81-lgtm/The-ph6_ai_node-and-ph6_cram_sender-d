# C01 Runtime Card

```text
TASK_ID:        C01
OBJECTIVE:      300-frame full-stack coherence test
CURRENT_STATE:  Architecture-backed / evidence pending
PRIORITY:       1 (first campaign)
```

---

## INPUTS

```text
PSEUDO  = ON
SoSo    = ON
TOK     = ON
Swarm   = OFF
Source  = camera stream
```

---

## EXPECTED OUTPUTS

```text
logs/run_<stamp>/manifest.json
postrun_report_<stamp>.json
replay_receipt_<stamp>.json
hash_chain_receipt_<stamp>.blake2b
MRAM-S advisory artifacts (TOK/SoSo only)
```

---

## COMMANDS

```bash
# Step 1: Pre-run drift scan
python3 PH6_SOURCE/TOOLS/governance_drift_scan.py --scan-root PH6_SOURCE

# Step 2: Run stack (300 frames minimum)
python3 ph6_console.py --frames 300 --full-stack

# Step 3: Post-run verification
python3 ph6/audit.py --verify-run <run_stamp>

# Step 4: TOK-LEAK-001 — toggle TOK, hashes must match
python3 ph6_console.py --frames 300 --full-stack --tok-disabled
# result_set_hash with TOK=ON must equal result_set_hash with TOK=OFF

# Step 5: Replay verification
python3 ph6/cram_pu/runtime/ --replay <run_stamp>

# Step 6: Post-run drift scan
python3 PH6_SOURCE/TOOLS/governance_drift_scan.py --scan-root PH6_SOURCE
```

---

## PASS CRITERIA

```text
frames_processed >= 300
PSEUDO emitted PASS or DROP for every frame
PSEUDO output contains: entropy, laplacian_var, motion_fraction, reasons[]
No forbidden fields: motion_score, motion_decay_score
CRAM-A writes completed (no orphaned tmp files)
TOK artifacts in MRAM-S only — no CRAM-A writes
TOK-LEAK-001: result_set_hash identical with TOK ON and TOK OFF
Replay: identical result_set_hash to original run
Hash-chain receipt intact
PostRun report generated
Drift scan PASS before and after
RSYNC not blocked
```

---

## FAIL CRITERIA

```text
frames_processed < 300 and no crash
Swarm active during run (contaminated baseline — restart required)
Forbidden field found in PSEUDO output
PSEUDO read any Lane 2 advisory output
TOK wrote to CRAM-A
TOK emitted verdict, PASS, DROP, or authority-implying result field
TOK-LEAK-001 fails: hashes differ
Replay hash differs from original
Hash-chain receipt fails
RSYNC blocked, delayed, or resource-starved
PostRun report missing or malformed
Drift scan fails after run
```

---

## FORBIDDEN ACTIONS

```text
threshold changes
PASS/DROP semantic changes
replay modifications
Lane 2 authority grants
Swarm activation during this baseline run
```

---

## CLOSURE EVIDENCE

```text
PH6_SOURCE/EVIDENCE_CAMPAIGNS/RECEIPTS/C01_CLOSURE_RECEIPT.md
Required: run stamp, frame count, replay hash match, human sign-off
```

---

## OUTPUT FORMAT

```text
CAMPAIGN: C01
STATUS: PASS / FAIL / INVALID
FRAMES:
PSEUDO_VERDICTS:
CRAM_WRITES:
SOSO_TOK_ARTIFACTS:
LANE2_LEAKAGE:
RSYNC_BLOCKING:
REPLAY_RESULT:
RESULT_SET_HASH:
AUDIT_CHAIN:
ARTIFACT_PATH:
NEXT_ACTION:
```

---

## NEXT STEP AFTER C01 PASS

```text
C02 — Real Pi-to-Pi transfer (OI-03 gate)
```
