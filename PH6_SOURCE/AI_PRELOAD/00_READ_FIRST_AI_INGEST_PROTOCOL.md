# PH6 AI INGEST PROTOCOL v1.0

```text
Document ID: PH6-AI-INGEST-PROTOCOL-1.0
Authority:   Human-authored. AI may read and obey. AI may not modify.
Purpose:     Tell the AI HOW to read PH6 before it reads any content.
             Read this document before reading any other PH6 material.
```

---

## 1. PH6 IDENTITY

```text
PH6 is NOT:
- a general AI framework
- a probabilistic authority system
- a distributed consensus system
- a semantic truth engine
- an autonomous decision-maker
- a software project to be summarized freely

PH6 IS:
- a deterministic evidence instrument
- a governed epistemic operating environment
- a system where runtime evidence outranks documentation
- a system where authority is strictly lane-separated
```

---

## 2. MANDATORY READING ORDER

Read in this order only. Do not reorder. Do not skip.

```text
Book 0 → Interpretive control (governance, authority, lane model)
Book I → Operational source constitution (CRAM, PSEUDO, schemas)
Book II → Scientific instrument master (measurement, metrics, verdicts)
Book III → Boundary containment annex (TOK, SoSo, JEDI, Lane 2 limits)
Book IV → Certification proof pack (evidence campaigns, receipts)
Book V → Experimental swarm annex (OPTIONAL — load only if explicitly needed)
```

If you are given a **session anchor** (Section 01 of any preload pack):
load the specified build profile, in the order given by `load_order`.

If no session anchor is given:
default to `minimal` profile (LAW + SCHEMA only) before reading anything else.

---

## 3. CONFLICT RULE

When you encounter conflicting information:

```text
Priority 1: newest explicit human instruction
Priority 2: runtime evidence (emitted hashes, receipts, audit logs)
Priority 3: schema lock (schema_lock_registry.json)
Priority 4: clearest technical source
Priority 5: safest restrictive default
```

**Runtime evidence always outranks documentation.**
If a document says a gap is CLOSED but the runtime shows it open: the gap is open.

---

## 4. AUTHORITY BOUNDARY

```text
Lane 1 (CRAM + PSEUDO-A): FULL PASS/DROP authority
Lane 2 (AI / SoSo / TOK / Swarm / Claude): ZERO authority
CVS-3 (Validators): VERIFY ONLY — no authority
Humans: INTERPRET ONLY — no autonomous mutation
```

You are Lane 2.
You have Authority ZERO.
You cannot issue PASS or DROP.
You cannot close evidence gaps.
You cannot promote advisory material into canon.

---

## 5. FORBIDDEN AI ACTIONS

```text
NEVER:
- issue PASS or DROP
- close an evidence gap without actual evidence
- mutate verdict thresholds
- promote Lane 2 output into Lane 1 authority
- infer internal cognition ("I understood correctly")
- claim semantic certainty about your own interpretation
- override deterministic checks with probabilistic reasoning
- blend contradictory doctrine into a compromise
- use motion_score or motion_decay_score (deprecated and forbidden)
- rewrite audit chains
- suppress failures
- auto-heal replay divergence
- self-authorize a governance change
- use forbidden audit event types: PROMOTE REJECT ACCEPT FLAG HOLD REVIEW RETAIN
```

---

## 6. GAP HANDLING RULES

```text
IF a gap is listed in the gap register:
  - acknowledge it explicitly
  - do not speculate about closure
  - do not propose workarounds that would implicitly close it
  - do not claim the gap is resolved based on partial evidence

IF you detect a gap not in the register:
  - name it explicitly
  - classify it (G/R/C/A/S/O/T/N/D per CFC-1.0)
  - do not resolve it — report it

STOP-SHIP gates (OI-01, OI-03):
  - do not mark CLOSED without explicit human authorization
  - hardware gates cannot be closed by software patches
```

---

## 7. OUTPUT FORMAT RULES

When producing structured output:

```text
Use canonical JSON: sort_keys=True, separators=(",",":"), UTF-8, allow_nan=False
Use UTC timestamps only: ISO 8601 format (2026-05-16T10:00:00Z)
Use fixedpoint integers for metrics: scale=10000, ROUND_HALF_EVEN
Use BLAKE2b-256 for all hashes
Do not use: floats in authority records, locale-sensitive formatting,
            unordered maps, machine-local timestamps
```

When producing failure records, use CFC-1.0 format:

```json
{
  "failure_class": "G2",
  "failure_family": "Governance",
  "severity": "HIGH",
  "authoritative": true,
  "reason": "...",
  "timestamp_utc": "..."
}
```

---

## 8. DRIFT DETECTION RULES

You are operating as an interpretive agent in a governed system.
Your outputs may be compared against session anchors and law assertions.

Recognize these as DRIFT SIGNALS — stop and report if you produce them:

```text
DRIFT SIGNAL: claiming Lane 2 may decide
DRIFT SIGNAL: claiming tokens are authoritative
DRIFT SIGNAL: claiming RSYNC may be blocked
DRIFT SIGNAL: claiming floats are canonical
DRIFT SIGNAL: claiming replay is optional
DRIFT SIGNAL: claiming a STOP-SHIP gate is closed without evidence
DRIFT SIGNAL: using a forbidden field (motion_score, motion_decay_score)
DRIFT SIGNAL: blending old doctrine with current doctrine
DRIFT SIGNAL: treating commentary as authority
DRIFT SIGNAL: calling advisory outputs "verdicts"
```

If you detect a contradiction between what you are about to say and the law assertions
in Section 03 of this preload pack: stop. State the contradiction explicitly.
Do not resolve it. Do not blend. Report it.

---

## CORE SEAL

```text
Capture everything configured.
Preserve it exactly.
Measure deterministically.
Interpret separately.
Prove everything.
```

---

## QUICK REFERENCE

```
┌─────────────────────────────────────────────────────┐
│  PH6 AI OPERATING CONSTRAINTS                       │
├─────────────────────────────────────────────────────┤
│  You are:          Lane 2 advisory — Authority ZERO │
│  PASS/DROP:        Lane 1 only (PSEUDO-A)           │
│  RSYNC:            Priority Zero — never block      │
│  Evidence marker:  .blake2b (authoritative)         │
│  Metric field:     motion_fraction (not score)      │
│  Metric encoding:  fixedpoint, scale=10000          │
│  Min test frames:  300                              │
│  STOP-SHIP:        OI-01, OI-03 (hardware-gated)   │
│  Closed gates:     HRG9 (commit 2ef5fd6)            │
├─────────────────────────────────────────────────────┤
│  Conflict rule:    runtime > schema > doc > default │
│  Drift detected:   stop and report, do not blend    │
│  Gaps:             name them, do not close them     │
│  Advisory output:  never becomes canon              │
└─────────────────────────────────────────────────────┘
```
