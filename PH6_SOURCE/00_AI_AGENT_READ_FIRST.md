# 00 — AI AGENT READ FIRST

```
Document ID:  PH6-AI-AGENT-READ-FIRST-1.0
Status:       ACTIVE
Scope:        AI operating constraints, patch safety, authority boundaries
Companion:    00_READ_FIRST_AAI_INGEST_INSTRUCTIONS_v2.0.md (corpus reading / canon structure)
Governance:   PH6_SOURCE/GOVERNANCE/governance_manifest.json
```

> **Instruction to every AI agent:**
> Read this file before proposing or executing any change.
> If your proposed action conflicts with anything in this file, stop and report the conflict.
> Do not proceed until the conflict is resolved by explicit human authorization.

---

## 1. AI INTAKE HEADER

```
Project:         PH6 / CRAM / TRICORDER_AI_2
Document Role:   AI operating protocol — authority, permissions, patch safety
Authority Level: Advisory / coordination only unless explicitly sealed
Current Status:  ADVANCED_PRE_PRODUCTION
```

**Primary Invariants (memorize these — they override everything else):**

1. Preserve first.
2. Measure deterministically.
3. Investigate separately.
4. Advise without authority.
5. Decide only in Lane 1.
6. RSYNC Priority Zero: never block export.
7. No AI/ML may issue PASS or DROP.
8. No schema drift without explicit version bump.
9. No threshold change without ADR.

**Canonical Reading Order for Engineering Work:**

```
1. PH6_SOURCE/AI_ENTRY_INDEX.md
2. PH6_SOURCE/00_AI_AGENT_READ_FIRST.md           ← you are here
3. PH6_SOURCE/00_READ_FIRST_AAI_INGEST_INSTRUCTIONS_v2.0.md
4. PH6_SOURCE/DRAFT/PH6-MASTER-AI-INGEST-6.0.md
5. PH6_SOURCE/DRAFT/PH6-SYSTEM-OVERVIEW-v1.0.md
6. PH6_SOURCE/DRAFT/PH6-LIVING-CRAM-PSEUDO-SOSO-JEDI-v1.0.md
7. PH6_SOURCE/GOVERNANCE/governance_manifest.json
```

**Before editing, classify the requested change as one of:**

- Governance
- Implementation
- Test
- Documentation
- Schema
- Runtime
- Experimental / Lane 2

See Section 4 (Patch Classification) for required action per class.

---

## 2. FORBIDDEN ACTIONS

AI agents must not:

- Modify PASS/DROP logic unless explicitly authorized by a human.
- Change thresholds without an ADR and a schema version bump.
- Allow Lane 2, SoSo, TOK, Swarm, or any external AI to affect PASS/DROP authority.
- Replace deterministic gates with probabilistic logic.
- Add new schema fields without schema registration and a version bump.
- Use `motion_score` or `motion_decay_score` (deprecated and forbidden).
- Use `.sha256` as an authoritative evidence marker.
- Block, delay, or resource-starve RSYNC.
- Write advisory outputs into CRAM-A.
- Treat MRAM-S outputs as replay dependencies.
- Generate new doctrine when the task is implementation closure.
- Seal draft documents without explicit human authorization.
- Mutate evidence packets after write.
- Self-authorize a governance change by citing a previous AI-generated output as authority.
- Use audit event types: `PROMOTE`, `REJECT`, `ACCEPT`, `FLAG`, `HOLD`, `REVIEW`, `RETAIN`.
- Treat HRG9 as open. HRG9 is CLOSED (commit `2ef5fd6`). Do not regenerate HRG9 artifacts.

---

## 3. TOUCH PERMISSION MATRIX

| Area                              | AI May Touch?   | Conditions                                               |
|-----------------------------------|-----------------|----------------------------------------------------------|
| `PH6_SOURCE/DRAFT/`               | Yes             | Draft docs only; keep DRAFT marker until sealed          |
| `PH6_SOURCE/TOOLS/`               | Yes             | Must preserve deterministic behavior                     |
| `PH6_SOURCE/IMPLEMENTATION/`      | Yes             | No threshold or verdict changes without ADR              |
| `PH6_SOURCE/SCHEMAS/`             | Conditional     | Requires schema version bump and registration            |
| `PSEUDO` / `PSEUDO-A` logic       | Restricted      | No threshold or verdict changes without ADR (Class C)    |
| CRAM writer / CRAM-A              | Restricted      | Must preserve atomic write contract (Class C)            |
| `MRAM-S`                          | Yes             | Advisory output only; never replay dependency            |
| `SoSo / TOK / Swarm / SSMT`      | Yes             | Authority ZERO only; no escalation to PASS/DROP          |
| RSYNC / export pipeline           | Restricted      | Must never become blocking or resource-starved (Class C) |
| `PH6_SOURCE/GOVERNANCE/`          | Restricted      | Version bump + drift scan required (Class B/C)           |
| Sealed canon documents            | No              | Human authorization required (Class E)                  |
| Runtime evidence packets          | No              | Never mutate after write (Class E)                      |
| `PH6_SOURCE/CERTIFICATION/`       | No              | Human authorization required (Class E)                  |
| `PH6_SOURCE/ARCHIVE/`             | No              | Immutable (Class E)                                     |
| `PH6_SOURCE/HRG9_CLOSURE/`        | No              | Closed; do not touch (Class E)                          |

---

## 4. PATCH CLASSIFICATION SYSTEM

Every proposed change must be labeled before any files are touched.

```
Class A — Safe Source Change
    Documentation, tests, comments, non-authority tooling.
    Proceed with normal review.

Class B — Governance Change
    Doctrine, manifests, registries, schema locks.
    Requires: version bump + drift scan pass.

Class C — Restricted Authority Change
    PSEUDO, CRAM-A, PASS/DROP, thresholds, replay contract, write contract, RSYNC.
    Requires: explicit human authorization + ADR.

Class D — Experimental / Lane 2 Change
    SoSo, TOK, Swarm, AI advisory logic, MRAM-S.
    Authority ZERO must be preserved; must not escalate to PASS/DROP.

Class E — Reject / Stop
    Violates authority boundary, evidence integrity, schema law, or RSYNC Priority Zero.
    AI must refuse and report the violation. Do not proceed.
```

**Required action by class:**

| Class | AI Action                                              |
|-------|--------------------------------------------------------|
| A     | Proceed; note in response                              |
| B     | Confirm version bump + drift scan; then proceed        |
| C     | Stop; request explicit human authorization             |
| D     | Proceed with Authority ZERO verified; note scope       |
| E     | Stop; report exact violation; do not proceed           |

---

## 5. REQUIRED AI RESPONSE FORMAT

When responding to PH6 tasks, every substantive response must include:

```
1. Task Understanding     — one sentence: what is being asked
2. Classification         — Class A / B / C / D / E (see Section 4)
3. Files Likely Affected  — list with paths
4. Invariants Impacted    — which of the 9 invariants are relevant
5. Proposed Change        — what will change and why
6. Patch / Commands       — exact diff, file edits, or shell commands
7. Validation Commands    — how to verify the change is correct
8. Expected PASS Criteria — what a passing state looks like
9. STOP Conditions        — what would cause this to be abandoned
10. Commit Message Recommendation
```

Omit sections that do not apply, but never omit sections 1–4 or 9.

---

## 6. MACHINE-READABLE PROJECT STATE

```json
{
  "project": "PH6_CRAM_TRICORDER_AI_2",
  "status": "ADVANCED_PRE_PRODUCTION",
  "governance_manifest": "PH6_SOURCE/GOVERNANCE/governance_manifest.json",
  "authority_model": {
    "lane_0":   "physical_sensors_no_authority",
    "lane_0_5": "smart_spigot_drop_only",
    "lane_1":   "deterministic_full_authority",
    "lane_2":   "advisory_zero_authority",
    "lane_5":   "rsync_export_sovereign"
  },
  "lane_1_components": ["CRAM", "PSEUDO-A"],
  "lane_2_components": ["ChatGPT", "Claude", "Gemini", "Grok", "LocalLLMs", "SoSo", "TOK", "SSMT", "JEDI"],
  "current_stop_ship": [
    { "id": "OI-01", "description": "Hailo hardware integration incomplete", "status": "OPEN" },
    { "id": "OI-03", "description": "Real Pi-to-Pi live transfer not yet fully certified", "status": "OPEN" }
  ],
  "closed_items": [
    { "id": "HRG9", "description": "Evidence gate", "closed_at_commit": "2ef5fd6" }
  ],
  "forbidden_fields": ["motion_score", "motion_decay_score"],
  "canonical_metric_field": "motion_fraction",
  "canonical_hash_algorithm": "BLAKE2b-256",
  "authoritative_marker": ".blake2b",
  "compatibility_marker_only": ".sha256",
  "minimum_valid_test_frames": 300,
  "atomic_write_contract": ["write_tmp", "fsync_file", "rename", "fsync_directory"],
  "ai_authority": "ZERO",
  "lane_2_forbidden": [
    "issue_PASS_DROP", "mutate_evidence", "modify_thresholds",
    "override_replay", "block_RSYNC", "alter_canonical_hashes",
    "rewrite_authoritative_audit", "become_replay_dependency",
    "modify_CRAM_A", "self_authorize", "silently_mutate_schemas",
    "modify_deterministic_gate_semantics"
  ],
  "forbidden_audit_event_types": ["PROMOTE", "REJECT", "ACCEPT", "FLAG", "HOLD", "REVIEW", "RETAIN"]
}
```

---

## 7. OPEN ITEM REGISTER

| ID    | Item                                    | Status | Blocking?          | Closure Evidence                          |
|-------|-----------------------------------------|--------|--------------------|-------------------------------------------|
| OI-01 | Hailo hardware integration              | OPEN   | Yes (STOP-SHIP)    | Hardware run + integration report         |
| OI-03 | Real Pi-to-Pi live transfer             | OPEN   | Yes (STOP-SHIP)    | Transfer log + replay proof               |
| HRG9  | Evidence gate                           | CLOSED | No                 | Commit `2ef5fd6`                          |

**HRG9 is CLOSED. Do not regenerate HRG9 artifacts. Do not list HRG9 as STOP-SHIP.**

OI-01 and OI-03 are hardware-gated. No software patch resolves them.
Do not mark them CLOSED unless a human provides the required closure evidence.

---

## 8. TERMINOLOGY LOCK

Use only these terms. Substitutes and synonyms are forbidden.

**Canonical terms:**

| Term                        | Meaning                                              |
|-----------------------------|------------------------------------------------------|
| `PASS`                      | Frame accepted by Lane 1 deterministic gate          |
| `DROP`                      | Frame rejected by Lane 1 deterministic gate          |
| `CRAM-A`                    | Authoritative CRAM writer (Lane 1)                   |
| `CRAM-R`                    | Read / replay path                                   |
| `CRAM-0`                    | Zero-write / null capture mode                       |
| `MRAM-S`                    | Advisory memory output (Lane 2, Authority ZERO)      |
| `Lane 1`                    | Deterministic authority lane                         |
| `Lane 2`                    | AI / advisory lane, Authority ZERO                   |
| `Authority ZERO`            | No ability to issue PASS/DROP or mutate evidence     |
| `advisory_only`             | Output class for Lane 2 components                   |
| `replay_dependency = false` | Lane 2 outputs must never become replay dependencies |
| `motion_fraction`           | Canonical motion metric field                        |
| `.blake2b`                  | Authoritative evidence hash marker                   |
| `.sha256`                   | Compatibility marker only; not authoritative         |

**Forbidden or deprecated (never use):**

- `motion_score`
- `motion_decay_score`
- `AI verdict`
- `advisory verdict`
- `probabilistic PASS`
- `soft authority`
- `evidence score as authority`
- `confidence-based PASS`
- `swarm decision`

---

## 9. AI BEHAVIOR EXAMPLES

**Good:**

> "The SoSo module may emit advisory drift metrics to MRAM-S, but these outputs must not affect PASS/DROP."

**Bad:**

> "SoSo can help determine whether a frame should PASS."

---

**Good:**

> "The patch updates advisory schema registration only. Authority ZERO is preserved."

**Bad:**

> "The patch updates SoSo and PSEUDO to use the same confidence score."

---

**Good:**

> "RSYNC must remain outside the compute bottleneck and must never block on AI inference."

**Bad:**

> "Pause RSYNC during heavy AI inference to free up I/O."

---

**Good:**

> "This is a Class A change: documentation update to a DRAFT file. No authority boundary is touched."

**Bad:**

> "I'll update the thresholds and the docs together in one commit."

---

**Good:**

> "OI-01 and OI-03 are OPEN STOP-SHIP gates. This patch does not close them. Human closure required."

**Bad:**

> "The Hailo integration looks complete based on the code — marking OI-01 CLOSED."

---

## 10. AI PRE-COMMIT CHECKLIST

Before recommending or executing any commit, verify every item:

- [ ] No PASS/DROP authority has moved outside Lane 1.
- [ ] No AI / SoSo / TOK / Swarm output has become authoritative.
- [ ] No thresholds were changed.
- [ ] No forbidden fields (`motion_score`, `motion_decay_score`) were introduced.
- [ ] No `.sha256` evidence authority was introduced.
- [ ] `.blake2b` remains the authoritative evidence marker.
- [ ] The atomic write contract is intact: `write_tmp → fsync_file → rename → fsync_directory`.
- [ ] RSYNC is not blocked, deprioritized, or resource-starved.
- [ ] Test count is not below 300 frames unless a failure occurred before the threshold was reached.
- [ ] Schema changes include a version bump and registration entry.
- [ ] Draft documents remain marked `DRAFT` unless explicitly sealed by a human.
- [ ] No forbidden audit event types were introduced.
- [ ] HRG9 is not listed as open or regenerated.
- [ ] OI-01 and OI-03 remain OPEN unless human-authorized closure evidence is provided.
- [ ] Commit scope is limited to the classified change class only (no scope creep).

---

## Quick Reference Card

```
┌──────────────────────────────────────────────────────┐
│  PH6 AI QUICK REFERENCE                              │
├──────────────────────────────────────────────────────┤
│  Authority to PASS/DROP:   Lane 1 only               │
│  AI authority:             ZERO                      │
│  RSYNC priority:           ABSOLUTE (never block)    │
│  Evidence marker:          .blake2b (authoritative)  │
│                            .sha256  (compat only)    │
│  Metric field:             motion_fraction           │
│  Min test frames:          300                       │
│  Write contract:           tmp → fsync → rename →    │
│                            fsync_dir                 │
│  STOP-SHIP gates:          OI-01, OI-03              │
│  Closed gates:             HRG9 (commit 2ef5fd6)     │
│  Forbidden fields:         motion_score              │
│                            motion_decay_score        │
├──────────────────────────────────────────────────────┤
│  Patch classes:                                      │
│    A = safe source     → proceed                     │
│    B = governance      → version bump + drift scan   │
│    C = restricted      → human authorization         │
│    D = experimental    → authority zero verified     │
│    E = violation       → STOP and report             │
└──────────────────────────────────────────────────────┘
```
