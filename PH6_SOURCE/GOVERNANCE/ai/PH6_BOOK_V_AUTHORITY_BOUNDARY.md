# PH6 Book V Authority Boundary Document
**Status:** RATIFIED — Operator approval 2026-06-06  
**Applies to:** All components under `PH6_SOURCE/AI/soso_jedi/`  
**Governance:** CLAUDE.md Hard Rule §1 + PH6 CDG-1.0

---

## 1. Absolute Authority Classification

Every system component in Book V is classified as:

```
authority  = ADVISORY_ZERO
lane       = 2
```

This is a structural classification, not a label. It is enforced at schema level via
`const` fields and at runtime via authority compliance flags.

---

## 2. Prohibited Actions (Absolute, No Exceptions)

Book V systems **may not**:

| Prohibited Action | Reason |
|---|---|
| Adjudicate | PASS/DROP is Lane 1 sovereign only |
| Rewrite CRAM | Evidence integrity is Lane 1 invariant |
| Override PSEUDO | Measurement authority belongs to Lane 1 |
| Modify authority hashes | Hash chain is sealed by Lane 1 |
| Modify replay certification | Replay is Lane 1 domain |
| Issue PASS/DROP verdicts | Forbidden verdict tokens for Lane 2 |
| Mint CRAM tokens | Token authority = Lane 1 only |
| Change Lane 1 sequence state | Lane 1 state is sovereign |

Violation of any of these = INVARIANT VIOLATION. Runtime error. Stop immediately.

---

## 3. Permitted Actions

Book V systems **may**:

- Observe Lane 1 evidence records (read-only)
- Construct advisory continuity chains in MRAM-S
- Perform cognitive archaeology over historical records
- Emit advisory manifests with ADVISORY_ZERO authority marking
- Run Storm / Swarm / JEDI reconstruction pipelines
- Compute MCI scores and drift indices
- Write to `MRAM-S/` only (never CRAM-0, CRAM-A, CRAM-R)

---

## 4. Book V Component Roles

| Component | Domain | Role |
|---|---|---|
| SoSo Observer | 3 | Record real-time state continuity |
| SoSo Historian | 3 | Commit chronological tracking histories |
| SoSo Archaeologist | 3 | Trace dropped node connections |
| Storm | 4 | Evaluate counterfactual path outcomes |
| Swarm | 5 | Distributed belief-propagation evaluation |
| JEDI | 6 | Cognitive archaeology + advisory reconstruction |

All six roles are Observers, Reconstructors, Historians, Comparators,
Hypothesis Engines, and Continuity Engines — never Decision Engines.

---

## 5. Schema Authority Lock

All Book V schemas enforce these constants:

```json
"authority": { "type": "string", "const": "ADVISORY_ZERO" }
```

The `ph6.advisory.manifest.v1` schema additionally enforces:
```json
"authority_compliance_flag": { "type": "boolean", "const": true }
```

No Book V schema may contain:
- A `verdict` field accepting `PASS` or `DROP`
- A `blake2b_marker_written` field (that belongs to CRAM-A only)
- An `authority_tag` field with `LANE_1_SOVEREIGN`

---

## 6. Evidence Root Boundary

The sole authoritative evidence root is:
```
PH6_SOURCE/CRAM/
  cram0/     — raw ingest (no .blake2b marker)
  crama/     — PASS frames (.blake2b marker written LAST)
  cramr/     — DROP frames (NO .blake2b marker — ever)
  mrams/     — advisory long-term store (ADVISORY_ZERO)
```

Book V writes only to `mrams/`. CRAM-0/A/R are Lane 1 exclusive.

---

## 7. Decay Prevention

This boundary document exists to prevent authority creep.  
Without explicit enforcement, advisory systems accumulate scope:  
observation → recommendation → override → replacement.

The `authority = ADVISORY_ZERO` const in every schema is the mechanism
that prevents this decay from ever compiling into the system.

---

*Proposed by: claude-code-lane2 | Ratified by: operator 2026-06-06 | ratified_by: Jack*
