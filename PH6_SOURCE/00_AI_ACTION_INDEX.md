# PH6 / CRAM — AI Action Index

```text
Document ID: PH6-AI-ACTION-INDEX-1.0
Status:      ACTIVE
Version:     v3.1 Evidence Closure Campaign phase
Purpose:     Single-page action guide for every AI agent entering this repo.
             Companion to 00_AI_AGENT_READ_FIRST.md (authority constraints).
             Companion to AI_ENTRY_INDEX.md (reading order map).
```

---

## Start Here

Every AI agent must execute these steps before proposing or editing anything.

### Step 1 — Read authority constraints

```text
PH6_SOURCE/00_AI_AGENT_READ_FIRST.md
```

This file contains forbidden actions, patch classification, authority matrix, and
pre-commit checklist. It overrides everything else.

### Step 2 — Read governance state

```text
PH6_SOURCE/GOVERNANCE/governance_manifest.json
```

This is the machine-readable authority source. Check current lane states,
forbidden fields, and schema versions before touching any file.

### Step 3 — Run drift scan

```bash
python3 PH6_SOURCE/TOOLS/governance_drift_scan.py --scan-root PH6_SOURCE
```

Do not propose changes if the drift scan fails. Report the failure and stop.

### Step 4 — Check git state

```bash
git status --short
git diff --check
```

Do not proceed on a dirty tree unless the task explicitly targets uncommitted work.

---

## Current Authority State

| Component             | Lane | Authority    | May Touch PASS/DROP? |
|-----------------------|------|--------------|----------------------|
| CRAM / PSEUDO-A       | 1    | FULL         | Yes                  |
| Smart spigot          | 0.5  | DROP_ONLY    | No                   |
| Physical sensors      | 0    | NONE         | No                   |
| SoSo / TOK / Swarm    | 2    | ZERO         | No                   |
| SSMT / JEDI / MRAM-S  | 2    | ZERO         | No                   |
| All AI models (LLMs)  | 2    | ZERO         | No                   |
| RSYNC / export        | 5    | EXPORT_SOVEREIGN | No               |

**RSYNC is Priority Zero. It must never be blocked, delayed, or resource-starved.**

---

## Current STOP-SHIP Items

| ID    | Description                             | Gating Condition      |
|-------|-----------------------------------------|-----------------------|
| OI-01 | Hailo hardware integration incomplete   | Hardware-gated        |
| OI-03 | Real Pi-to-Pi live transfer unverified  | Hardware-gated        |

These gates cannot be closed by software patches or AI-generated evidence.
Human-provided hardware run receipts are required.

---

## Closed Items — Do Not Reopen

| ID    | Description     | Closed At Commit |
|-------|-----------------|------------------|
| HRG9  | Evidence gate   | `2ef5fd6`        |

HRG9 is CLOSED. Do not generate HRG9 artifacts. Do not list HRG9 as a blocker.

---

## Forbidden Changes Without Explicit Human Authorization and ADR

- PASS/DROP threshold changes
- CRAM write contract changes
- Replay dependency rule changes
- RSYNC behavior changes (must remain non-blocking)
- Schema drift without version bump and registration
- Lane 2 authority expansion (it is ZERO and must remain ZERO)
- Sealing any DRAFT document

---

## Required Pre-Edit Commands

```bash
python3 PH6_SOURCE/TOOLS/governance_drift_scan.py --scan-root PH6_SOURCE
git status --short
```

---

## Required Post-Edit Commands

```bash
python3 PH6_SOURCE/TOOLS/governance_drift_scan.py --scan-root PH6_SOURCE
git diff --check
```

---

## What AI May Do (Class A / D actions)

- Draft and update documents in `PH6_SOURCE/DRAFT/`
- Generate test templates and evidence campaign stubs
- Run drift scans and report results
- Summarize diffs and changes
- Propose ADRs (but not approve them)
- Patch advisory-only files (SoSo, TOK, MRAM-S) with Authority ZERO preserved
- Update this index or the gap register

## What AI Must Not Do (Class C / E actions)

- Change PASS/DROP semantics
- Change thresholds
- Change the CRAM write contract
- Grant Lane 2 authority
- Touch replay dependency rules
- Block or delay RSYNC
- Treat a draft document as sealed doctrine
- Treat AI-generated output as authoritative evidence
- Self-authorize a governance change

---

## Current Phase

```text
PH6 / CRAM v3.1 — Evidence Closure Campaign
```

Goal: runtime proof, not doctrine expansion.

Priority order:
1. 300-frame full-stack coherence run
2. Pi-to-Pi live transfer (closes OI-03)
3. Resource pressure / RSYNC non-blocking campaign
4. Crash recovery campaign
5. Replay parity campaign

Evidence campaigns are tracked in: `PH6_SOURCE/EVIDENCE_CAMPAIGNS/`
Gap register is at: `PH6_SOURCE/GAP_REGISTER_v3.0.md`
Model handoff is at: `PH6_SOURCE/AI_HANDOFF/PH6_MODEL_HANDOFF_CURRENT.md`

---

## Expected Clean Posture

After any work session, verify:

```text
drift scan:        PASS
working tree:      clean
new doctrine seal: NONE until evidence campaigns produce receipts
open STOP-SHIP:    OI-01, OI-03 (hardware-gated; do not falsely close)
```
