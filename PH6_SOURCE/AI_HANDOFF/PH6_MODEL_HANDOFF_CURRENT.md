# PH6 / CRAM — Current Model Handoff Pack

```text
Document ID: PH6-MODEL-HANDOFF-CURRENT-1.0
Status:      ACTIVE
Version:     v3.1 Evidence Closure Campaign phase
Date:        2026-05-14
Purpose:     Clean handoff document for any AI model (ChatGPT, Claude, Gemini, Codex,
             or future sessions) starting a new session on this repo.
             Read this before reading anything else.
```

---

## System Identity

PH6 / CRAM is a **deterministic scientific measurement and evidence instrument**.

It captures, classifies, writes, and replays measurement frames with a fixed
deterministic authority model. No component may modify its own authority at runtime.
No AI or advisory system may issue PASS or DROP.

---

## Operating Law — Nine Invariants

These override everything. If any proposed action violates these, stop.

1. Preserve first.
2. Measure deterministically.
3. Investigate separately.
4. Advise without authority.
5. Decide only in Lane 1.
6. RSYNC Priority Zero: never block export.
7. No AI/ML may issue PASS or DROP.
8. No schema drift without explicit version bump.
9. No threshold change without ADR.

---

## Current System State

```text
Governance version:   1.2 (SEALED commit 6d3e56c)
Phase:                v3.1 — Evidence Closure Campaign
SoSo-family:          Governance-registered; advisory contract enforcement implemented
Runtime discovery:    DRAFT only (not sealed)
HRG9:                 CLOSED — commit 2ef5fd6
OI-01:                OPEN / STOP-SHIP — Hailo hardware-gated
OI-03:                OPEN / STOP-SHIP — Real Pi-to-Pi transfer not yet certified
```

---

## Authority Model

Three components require distinct handling. They are **not interchangeable**.

| Component        | Lane   | Authority          | Writes To       | Role                                        |
|------------------|--------|--------------------|-----------------|---------------------------------------------|
| PSEUDO           | Lane 1 | **Authoritative**  | CRAM-A / audit  | Deterministic PASS/DROP engine              |
| TOK (Tokens)     | Lane 2 | **Authority ZERO** | MRAM-S only     | Advisory continuity / drift observation     |
| Swarm            | Lane 2 | **Authority ZERO** | MRAM-S only     | Advisory ensemble — quarantined until C01B  |
| SoSo             | Lane 2 | **Authority ZERO** | MRAM-S only     | Advisory sidecar                            |
| SSMT / JEDI      | Lane 2 | **Authority ZERO** | MRAM-S only     | Advisory layers                             |
| All AI models    | Lane 2 | **Authority ZERO** | (none)          | No write access                             |
| Smart spigot     | Lane 0.5 | DROP_ONLY        | (pre-filter)    | Pre-filter only                             |
| Physical sensors | Lane 0 | NONE               | (none)          | Input only                                  |
| RSYNC / export   | Lane 5 | EXPORT_SOVEREIGN   | External        | Non-blocking export                         |

```
PSEUDO decides.
Tokens observe continuity.
Swarm advises collectively.
Only Lane 1 can affect PASS/DROP.
```

Lane 2 authority is permanently ZERO. It cannot be escalated. AI models are Lane 2.

---

## Reading Order for Engineering Work

```
1. PH6_SOURCE/AI_HANDOFF/PH6_MODEL_HANDOFF_CURRENT.md   ← you are here
2. PH6_SOURCE/00_AI_ACTION_INDEX.md                     ← action guide
3. PH6_SOURCE/00_AI_AGENT_READ_FIRST.md                 ← authority constraints
4. PH6_SOURCE/GOVERNANCE/governance_manifest.json        ← machine-readable state
5. PH6_SOURCE/GAP_REGISTER_v3.0.md                      ← current gap state
6. PH6_SOURCE/EVIDENCE_CAMPAIGNS/                        ← proof campaign templates
```

---

## What AI May Do

- Draft documents in `PH6_SOURCE/DRAFT/`
- Generate and update evidence campaign templates
- Run governance drift scans
- Summarize diffs and changes
- Propose ADRs (but not approve or seal them)
- Patch advisory-only files (SoSo, TOK, MRAM-S) while preserving Authority ZERO
- Update the gap register for non-STOP-SHIP items when evidence is confirmed
- Update this handoff document when system state changes

---

## What AI Must Not Do

- Change PASS/DROP semantics or thresholds
- Change the CRAM write contract
- Grant Lane 2 authority to any component
- Touch replay dependency rules
- Block or delay RSYNC
- Seal any DRAFT document
- Treat AI-generated output as authoritative evidence
- Close OI-01 or OI-03 (hardware-gated; human closure required)
- Reopen or regenerate HRG9 artifacts
- Self-authorize any governance change

---

## Pre-Session Commands

Run before any edit session:

```bash
python3 PH6_SOURCE/TOOLS/governance_drift_scan.py --scan-root PH6_SOURCE
git status --short
```

---

## Current Priority Queue

The system needs **runtime proof**, not more doctrine.

```text
1. C01   — 300-frame full-stack coherence run (PSEUDO=ON, SoSo=ON, TOK=ON, Swarm=OFF)
2. C01B  — Advisory expansion: Swarm enabled, MRAM-S only (requires C01 closed first)
3. C02   — Pi-to-Pi live transfer (closes OI-03)
4. C03   — Resource pressure / RSYNC non-blocking
5. C04   — Crash recovery
6. C05   — Replay parity
```

Campaign templates: `PH6_SOURCE/EVIDENCE_CAMPAIGNS/`

Do not propose new doctrine until campaign receipts exist.

---

## Canonical Terms

| Use This                | Not This                                    |
|-------------------------|---------------------------------------------|
| `PASS`                  | approve, accept, validate, promote          |
| `DROP`                  | reject, fail, filter                        |
| `CRAM-A`                | authoritative writer, main CRAM             |
| `Lane 1`                | deterministic layer, core layer             |
| `Lane 2`                | AI layer, advisory layer, soft layer        |
| `Authority ZERO`        | limited authority, advisory authority       |
| `motion_fraction`       | motion_score, motion_decay_score            |
| `.blake2b`              | .sha256 (sha256 is compatibility only)      |
| `advisory_only`         | advisory verdict, soft PASS                 |
| `replay_dependency: false` | anything implying Lane 2 outputs replay |

---

## Handoff Maintenance Rule

Update this file whenever:
- System phase changes
- A STOP-SHIP item is closed
- Governance version is bumped
- A new STOP-SHIP item is added
- The priority queue changes

This file should always reflect the **current state**, not historical state.
Previous state belongs in git history and the gap register.
