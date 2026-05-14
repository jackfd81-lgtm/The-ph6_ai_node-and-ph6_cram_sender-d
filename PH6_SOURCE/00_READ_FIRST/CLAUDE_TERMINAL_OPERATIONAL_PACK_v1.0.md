# PH6 / CRAM v3.1 — CLAUDE TERMINAL OPERATIONAL PACK

```text
Mode:   Evidence Closure Campaign
Target: Raspberry Pi / terminal-based execution
Role:   Senior software engineer + deterministic systems operator
```

You are operating inside the PH6 / CRAM repository.

---

## PRIMARY OBJECTIVE

Move PH6 from architecture-backed toward evidence-backed by executing evidence campaigns, not by creating new doctrine.

---

## CURRENT STATUS

```text
PH6:    ARCHITECTURE-BACKED
HRG9:   CLOSED
OI-01:  OPEN / STOP-SHIP / Hailo hardware-gated
OI-03:  OPEN / STOP-SHIP / real Pi-to-Pi transfer not verified
Phase 1 control documents: created and committed
Next target: Campaign 01 — 300-frame full-stack coherence run
```

---

## DO NOT

```text
- create new doctrine
- seal new doctrine
- change thresholds
- change PASS/DROP semantics
- change CRAM write behavior
- change replay behavior
- change RSYNC behavior
- grant Lane 2 authority
- close gaps without closure evidence
```

---

## AUTHORITY MODEL

```text
PSEUDO  = Lane 1 deterministic authority
SoSo    = Lane 2 advisory only
TOK     = Lane 2 advisory only
Swarm   = Lane 2 / Book V advisory only
CRAM    = authoritative evidence storage
MRAM-S  = advisory storage only
RSYNC   = Priority Zero, never blocked
```

Core rule:

```text
PSEUDO decides.
TOK observes.
Swarm advises.
SoSo assists.
CRAM records truth.
RSYNC escapes first.
```

---

## EVIDENCE TRANSITION GATE

PH6 becomes evidence-backed only after all five campaigns PASS:

```text
C01  300-frame full-stack coherence PASS
C02  Real Pi-to-Pi transfer PASS / OI-03 CLOSED
C03  RSYNC non-blocking under pressure PASS
C04  Crash recovery + CRAM integrity PASS
C05  Replay parity PASS
```

AND all of the following hold:

```text
PSEUDO deterministic behavior preserved
Lane 2 remained Authority ZERO
TOK/Swarm caused no authority leakage
result_set_hash reproducible
audit chain intact
CRAM write contract preserved
```

---

## REQUIRED STARTUP CHECKS

```bash
git status --short
python3 PH6_SOURCE/TOOLS/governance_drift_scan.py --scan-root PH6_SOURCE
```

Expected drift result:

```text
result: PASS
critical: 0
high: 0
warn: 0
```

---

## READING ORDER

Read only what is needed for the current campaign.

```text
PH6_SOURCE/00_AI_ACTION_INDEX.md
PH6_SOURCE/GAP_REGISTER_v3.0.md
PH6_SOURCE/AI_HANDOFF/PH6_MODEL_HANDOFF_CURRENT.md
PH6_SOURCE/EVIDENCE_CAMPAIGNS/CAMPAIGN_01_300_FRAME_COHERENCE.md
```

---

## CURRENT TASK

Proceed to Campaign 01 only.

---

## CAMPAIGN 01 BASELINE CONFIG

```text
PSEUDO = ON
SoSo   = ON
TOK    = ON
Swarm  = OFF
```

---

## CAMPAIGN 01 PROOF CHAIN

```text
camera/input
→ PSEUDO
→ SoSo/TOK advisory
→ CRAM writes
→ PostRun
→ replay/hash-chain report
```

---

## MINIMUM VALID RUN

```text
frames >= 300
```

If the system crashes before 300 frames: preserve crash evidence and mark the run for Campaign 04 analysis.

---

## BEFORE RUNNING, REPORT

```text
1. exact command
2. expected artifacts
3. PASS/FAIL criteria
4. receipt output path
```

---

## AFTER RUNNING, REPORT

```text
1. frame count
2. PSEUDO verdict count
3. CRAM write count
4. SoSo/TOK advisory artifact count
5. Lane 2 leakage finding
6. RSYNC-blocking finding
7. replay/hash-chain result
8. final status: PASS, FAIL, or INVALID
```

---

## PASS CRITERIA

```text
frames >= 300
PSEUDO verdicts emitted
CRAM writes completed
SoSo/TOK remained advisory
no Lane 2 authority leakage
RSYNC not blocked
postrun report generated
replay/hash-chain verification passed
```

---

## FAIL CONDITIONS

```text
Lane 2 changes PSEUDO output
TOK/Swarm affects result_set_hash
CRAM-A differs when advisory systems are enabled/disabled
RSYNC blocks
replay differs
audit chain breaks
CRAM write contract fails
```

---

## INVALID CONDITIONS

```text
manual stop before 300 frames
missing required artifacts
unclear command path
untracked mutation of doctrine files
```

---

## CLOSURE PACKET

After each campaign, create:

```text
PH6_CLOSEKIT/campaigns/C01/
```

Required contents:

```text
manifest.json
run_receipt.json
postrun_report.md
replay_receipt.json
result_set_hash.txt
audit_chain_receipt.json
operator_notes.md
```

---

## OUTPUT DISCIPLINE

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

## STOP CONDITIONS

Stop immediately and report if:

```text
governance drift scan fails
git status shows unexpected doctrine mutation
PSEUDO reads Lane 2 advisory output
Lane 2 writes CRAM-A
RSYNC is blocked
replay hash differs
result_set_hash differs unexpectedly
CRAM write contract is changed
```

---

## FINAL OPERATING LAW

```text
Evidence first.
Gap closure second.
Doctrine patch third.
Seal consideration last.
```
