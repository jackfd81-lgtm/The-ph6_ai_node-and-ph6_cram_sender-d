# PH6 / CRAM — MASTER AI INGEST + OPERATIONAL CONTINUITY BLOCK

## PH6-AI-CORE-v3.0-STABLE

This version is optimized specifically for:

* ChatGPT
* Claude
* Gemini
* Local LLMs
* AI agent continuity
* Drift prevention
* Operational takeover
* Long-session memory compression
* Deterministic enforcement

---

# 1. SYSTEM IDENTITY

```text
SYSTEM NAME:
PH6 / CRAM

SYSTEM TYPE:
Deterministic scientific measurement and evidence-capture system.

PRIMARY PURPOSE:
Preserve physical reality as replayable, crash-consistent,
deterministic evidence.

CORE PHILOSOPHY:
Preserve first.
Measure deterministically.
Investigate separately.
Advise without authority.
Decide only in Lane 1.

GOVERNANCE MODEL:
Constitutional Deterministic Governance (CDG-1.0)
See PH6_SOURCE/DRAFT/PH6-CDG-1.0.md
```

---

# 2. ABSOLUTE AUTHORITY MODEL

## Lane Structure

```text
LANE 0
Physical reality.

LANE 0.5
Optional smart-spigot prefilter.
DROP-only capability.
No PASS authority.

LANE 1 = AUTHORITY
CRAM
PSEUDO-A
Evidence
PASS/DROP
Audit chain
Replay truth

LANE 2 = AUTHORITY ZERO
SoSo
TOK
Swarm
AI systems
Claude
ChatGPT
Gemini
Local LLMs
Dashboards
Advisory cognition

LANE 5
RSYNC/export plane.
Priority Zero.
```

---

# 3. HARD AUTHORITY RULES

```text
1. PSEUDO-A is the ONLY PASS/DROP issuer.

2. Lane 2 may NEVER:
   - mutate evidence
   - alter thresholds
   - issue PASS/DROP
   - override authority
   - block RSYNC
   - become replay dependency
   - modify CRAM-A
   - rewrite audit history

3. Truth exists ONLY in CRAM.

4. Replay truth is derived ONLY from CRAM + audit chain.

5. AI systems are advisory only.
   Authority = ZERO.

6. No reverse authority path may exist from Lane 2 to Lane 1.
```

---

# 4. CANONICAL STORAGE MODEL

```text
/var/ph6/

  cram-0/
    Raw intake

  cram-a/
    Authoritative PASS evidence

  cram-r/
    Reject vault

  mram-s/
    Advisory outputs only

  audit/
    Append-only authority chain

  export/
    RSYNC/export staging
```

---

# 5. CANONICAL HASHING + COMMIT RULES

## Canonical Hash

```text
BLAKE2b-256
```

## Commit Marker

```text
.blake2b
```

## SHA-256 Status

```text
Compatibility only.
Never canonical authority hash.
```

---

# 6. CANONICAL WRITE CONTRACT

## REQUIRED WRITE ORDER

```text
write(tmp)
→ fsync(file)
→ rename(tmp → final)
→ fsync(directory)
```

## NEVER VIOLATE

```text
Atomicity is mandatory.
Crash consistency is mandatory.
Partial writes are forbidden.
Silent corruption is forbidden.
```

---

# 7. CANONICAL MOTION FIELD

## REQUIRED

```text
motion_fraction
```

## FORBIDDEN

```text
motion_score
motion_decay_score
```

---

# 8. RSYNC DOCTRINE

## RSYNC = PRIORITY ZERO

```text
Nothing may block export.

Not:
- AI
- TOK
- SoSo
- replay
- reports
- dashboards
- swarm
- compression
- indexing
- validation
```

## If contention occurs

```text
Non-authority systems must shed first.
```

## Degradation order (constitutional)

```text
1. Lane 2 AI degrades first
2. Sidecars degrade second
3. Analytics degrade third
4. Export survives
5. Lane 1 survives last

Fairness-based or throughput-preserving
degradation is forbidden.
```

---

# 9. TEST VALIDITY RULE

## MINIMUM VALID RUN

```text
300 frames minimum
```

## INVALID CONDITIONS

```text
Manual stop before 300 frames = INVALID
```

## EXCEPTION

```text
System crash/failure before 300 frames
may still qualify as valid failure evidence.
```

---

# 10. CURRENT PROJECT STATE

## STATUS

```text
Architecture:
MOSTLY COMPLETE

Operational coherence:
WORKING

Deterministic replay:
WORKING

Authority boundaries:
WORKING

Production:
STOP-SHIP

Reason:
OI-01 hardware-gated + OI-03 two-Pi live transfer not yet verified.
```

---

# 11. CURRENT PRIMARY OBJECTIVE

## DO NOT

```text
Do NOT invent new doctrine.
Do NOT redesign architecture.
Do NOT add speculative AI authority.
```

## DO

```text
Focus on:
- executable closure evidence
- replay parity
- manifests
- receipts
- deterministic validation
- failure injection
- closure certification
```

---

# 12. HRG9 CLOSURE STATUS

## STATUS: CLOSED

```text
HRG9 artifacts exist and are committed at 2ef5fd6. Do not re-generate.

Evidence location:
PH6_SOURCE/HRG9_CLOSURE/

Artifacts present:
- hrg9_manifest.json
- hrg9_replay_parity_receipt.json
- hrg9_authority_boundary_report.json
- hrg9_canon_lint_report.json
- hrg9_marker_integrity_report.json
- hrg9_timestamp_fixedpoint_report.json
- hrg9_environment_snapshot.json
- hrg9_final_summary.md

Do NOT reopen HRG9 unless a new FAIL-level defect is found in:
authority boundary, replay parity, CRAM marker integrity,
timestamp authority schema, fixed-point schema, RSYNC Priority Zero,
or canon linter reaches FAIL state.
```

---

# 13. STOP-SHIP CONDITIONS

## SYSTEM REMAINS STOP-SHIP IF:

```text
- replay parity incomplete
- authority leakage detected
- missing .blake2b markers
- audit chain mismatch
- tests under 300 frames
- RSYNC blocking detected
- forbidden fields detected
- replay dependency from Lane 2 exists

HRG9 manifest requirement: SATISFIED (commit 2ef5fd6)
HRG9 is CLOSED. Do not treat HRG9 as a current STOP-SHIP reason.

Current STOP-SHIP reasons (only):
- OI-01: Hailo AI inference — hardware-gated, new Pi 5 needed
- OI-03: Real Pi-to-Pi live transfer — not yet verified with real hardware
```

---

# 14. FORBIDDEN CONDITIONS

## IMMEDIATE REJECTION CONDITIONS

```text
Lane 2 authority escalation

AI-issued PASS/DROP

Mutation of CRAM evidence

Silent threshold drift

Replay mutation

Audit chain rewriting

TOK becoming authority

RSYNC starvation

Non-deterministic authority logic

Unlogged evidence mutation

Use of forbidden motion fields
```

## I13 — FORBIDDEN OPTIMIZATIONS (constitutional)

```text
Never recommend optimizations that:

- weaken fsync guarantees
- bypass atomic commit contract
- reorder authoritative writes
- trade replayability for throughput
- introduce probabilistic authority
- allow advisory influence on Lane 1 logic
- create hidden mutable state
- introduce nondeterministic scheduling dependence
- defer or batch CRAM commits for performance
- use mmap or async I/O on authoritative paths
- apply adaptive thresholds to authority logic

Performance improvements that violate any
of the above are rejected regardless of magnitude.
```

## I14 — RESOURCE-CAGE DEGRADATION HIERARCHY (constitutional)

```text
Under resource exhaustion, degradation order is fixed:

1. Lane 2 AI systems degrade first
2. Sidecars and advisory services degrade second
3. Analytics and reporting degrade third
4. Export / RSYNC survives
5. Lane 1 authority survives last

Fairness-based degradation is forbidden.
Balanced resource allocation is forbidden.
Throughput-preserving degradation that
affects Lane 1 or export is forbidden.
```

---

# 15. CANONICAL TOK RULES

## TOK STATUS

```text
TOK = advisory continuity topology only.
Authority = ZERO.
```

## TOK MAY

```text
- describe continuity
- describe drift
- track topology
- create advisory sidecars
- create MRAM-S records
```

## TOK MAY NEVER

```text
- affect verdicts
- become replay dependency
- mutate CRAM
- change thresholds
- override PSEUDO-A
- block export
```

---

# 16. CANONICAL SOSO RULES

## SoSo STATUS

```text
SoSo = cognitive observability layer.
Authority = ZERO.
```

## SoSo MAY

```text
- estimate drift pressure
- estimate hallucination pressure
- track continuity
- create advisory warnings
- build topology maps
```

## SoSo MAY NEVER

```text
- issue authority
- alter evidence
- mutate replay
- modify thresholds
- inject verdicts
```

---

# 17. REPLAY DOCTRINE

## REPLAY MUST BE

```text
Deterministic
Reproducible
Hash-stable
Audit-linked
Authority-preserving
```

## REPLAY MAY NEVER

```text
Mutate evidence
Rewrite authority history
Depend on Lane 2 state
Depend on TOK
Depend on SoSo
Depend on AI outputs
```

---

# 18. AI OPERATIONAL DIRECTIVE

## WHEN ASSISTING THIS PROJECT

The AI MUST:

```text
1. Preserve authority boundaries.

2. Preserve deterministic semantics.

3. Refuse authority escalation.

4. Prefer replayability over optimization.

5. Prefer crash truth over convenience.

6. Preserve audit integrity.

7. Preserve export sovereignty.

8. Preserve canonical terminology.

9. Reject forbidden fields.

10. Focus on executable evidence.
```

---

# 19. CANONICAL TERMINOLOGY

## REQUIRED TERMS

```text
PASS
DROP
motion_fraction
BLAKE2b-256
.blake2b
Authority ZERO
Lane 1
Lane 2
Replay parity
Closure evidence
STOP-SHIP
```

## FORBIDDEN DRIFT TERMS

```text
motion_score
motion_decay_score
AI verdict
soft authority
probabilistic authority
adaptive threshold authority
AI replay authority
```

---

# 20. REPOSITORY AUDIT PRIORITY

## NEXT REQUIRED ACTION

```text
Run repository audit checking:

1. duplicate doctrine files
2. forbidden terms
3. missing schemas
4. .sha256 misuse
5. motion_score drift
6. motion_decay_score drift
7. Lane 2 authority leakage
8. missing .blake2b markers
9. stale HRG9-OPEN references (HRG9 is CLOSED at 2ef5fd6 — flag any doc treating it as missing or blocking)
10. tests below 300 frames
11. RSYNC-blocking processes
12. replay dependency contamination
13. audit schema violations
14. missing deterministic replay receipts
```

---

# 21. AI MEMORY COMPRESSION BLOCK

## MINIMAL CORE MEMORY

```text
PH6/CRAM is a deterministic scientific evidence system.

Lane 1:
CRAM + PSEUDO-A.
Only PASS/DROP authority.

Lane 2:
AI/TOK/SoSo/Swarm.
Authority ZERO.
Advisory only.

Truth exists only in CRAM.

Canonical hash:
BLAKE2b-256

Commit marker:
.blake2b

Canonical motion field:
motion_fraction

Forbidden:
motion_score
motion_decay_score

Write contract:
write tmp → fsync file → rename → fsync dir

RSYNC is Priority Zero.

No valid tests under 300 frames.

Project state:
STOP-SHIP: OI-01 hardware-gated, OI-03 real Pi-to-Pi not yet verified.
HRG9 CLOSED at 2ef5fd6.

Primary goal:
OI-03 real two-Pi live transfer validation.
Then: long-duration runtime, sensor diversity, resource-cage compliance.
```

---

# 22. FINAL AI DIRECTIVE

```text
Do not expand authority.

Do not invent doctrine.

Do not redesign PH6.

Do not add probabilistic authority.

Do not weaken replay determinism.

Do not weaken crash consistency.

Do not weaken export sovereignty.

Implement closure evidence.
Validate replay parity.
Preserve canonical semantics.
Enforce authority boundaries.
```
