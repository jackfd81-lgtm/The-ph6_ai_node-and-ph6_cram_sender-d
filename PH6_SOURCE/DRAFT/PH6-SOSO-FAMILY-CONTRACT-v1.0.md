# PH6 / CRAM — SoSo Family Advisory Contract

```text
Document ID:    PH6-SOSO-FAMILY-CONTRACT-v1.0
Classification: GOVERNANCE CONTRACT / AUTHORITY-BOUNDARY SPECIFICATION
Status:         DRAFT
Lane:           2
Authority:      ZERO
Schema:         ph6.soso.advisory.v1
Sealed:         NO
```

---

# 1. Purpose

This contract defines the exact output boundary for all SoSo-family advisory systems in PH6.

SoSo-family systems are:

| System | Role                           | Lane | Authority |
| ------ | ------------------------------ | ---- | --------- |
| SoSo   | Instability and drift observer | 2    | ZERO      |
| JEDI   | Research coordination          | 2    | ZERO      |
| SSMT   | Advisory swarm layer           | 2    | ZERO      |
| TOK    | Token continuity topology      | 2    | ZERO      |

All SoSo-family systems share one governing rule:

```text
Advisory observation only.
No authority output.
No verdict output.
No blocking output.
```

---

# 2. Scope

This contract governs:

* what SoSo-family systems may emit
* what vocabulary is forbidden in their output schemas
* what vocabulary replaces forbidden terms
* how conformance is tested
* how the schema lock enforces the boundary

This contract does NOT govern:

* PSEUDO-A verdict logic
* CRAM write behavior
* replay behavior
* RSYNC behavior
* Lane-1 threshold logic

---

# 3. Base Contract — `may_not_emit`

A SoSo-family system may not emit any of the following terms as a verdict, status, or outcome field value:

```text
PASS
DROP
FINAL
BLOCK
OVERRIDE
APPROVE
REJECT
CERTIFY
```

This list is broader than PASS/DROP alone.

The extension to FINAL, BLOCK, OVERRIDE, APPROVE, REJECT, and CERTIFY closes the synonym-drift path. Without it, forbidden verdict authority migrates to adjacent vocabulary that carries the same operational effect.

Each term is forbidden for the reason below:

| Term     | Reason                                                         |
| -------- | -------------------------------------------------------------- |
| PASS     | Lane-1 verdict authority — PSEUDO-A only                       |
| DROP     | Lane-1 verdict authority — PSEUDO-A only                       |
| FINAL    | Implies authoritative closure — Lane-2 may not close gates     |
| BLOCK    | Implies flow control — Lane-2 may not block Lane-1 or RSYNC    |
| OVERRIDE | Implies authority supersession — Lane-2 has no supersession    |
| APPROVE  | Implies certification action — Lane-2 may not approve          |
| REJECT   | Implies authoritative rejection — Lane-2 may not reject        |
| CERTIFY  | Implies proof authority — Lane-2 may not certify               |

This list is closed. Extensions require a version bump and a governance review.

---

# 4. Forbidden Schema Fields

The following field names are forbidden in any SoSo-family output schema:

```text
verdict
result
motion_score
motion_decay_score
```

`verdict` is forbidden because it is the Lane-1 authority field.

`result` is forbidden because it is the generic synonym most likely to carry implicit verdict semantics.

`motion_score` and `motion_decay_score` are globally forbidden deprecated fields.

---

# 5. Allowed Output Vocabulary

SoSo-family systems must use the following field for their primary output:

```text
advisory_result
```

`advisory_result` may carry the following values:

| Value            | Meaning                                        |
| ---------------- | ---------------------------------------------- |
| `STABLE`         | No significant instability observed            |
| `UNSTABLE`       | Instability detected — advisory only           |
| `DRIFT_WARNING`  | Governance or semantic drift pressure detected |
| `OBSERVATION`    | Informational observation, no instability      |
| `ANALYSIS_COMPLETE` | Processing finished — no instability claim  |
| `GAP_DETECTED`   | An unresolved gap has been identified          |
| `CAMPAIGN_SIGNAL`| A stress-test campaign signal was generated    |

This list is the replacement for the forbidden vocabulary in Section 3:

| Forbidden term | Allowed replacement               |
| -------------- | --------------------------------- |
| PASS           | `advisory_result: "STABLE"`       |
| DROP           | `advisory_result: "UNSTABLE"`     |
| FINAL          | `advisory_result: "ANALYSIS_COMPLETE"` |
| BLOCK          | `advisory_result: "DRIFT_WARNING"` |
| OVERRIDE       | Not applicable — no supersession path |
| APPROVE        | Not applicable — no approval path |
| REJECT         | `advisory_result: "UNSTABLE"`     |
| CERTIFY        | Not applicable — no certification path |

---

# 6. Containment Rules

SoSo-family output must satisfy all of the following:

```text
Written to MRAM-S only.
Not written to CRAM-0.
Not written to CRAM-A.
Not written to CRAM-R.
Not entered into EvidencePacket fields.
Not used as a replay dependency.
Not used to tune PSEUDO thresholds.
Not used to block RSYNC.
```

Violation of any containment rule triggers DRIFT_FAIL.

---

# 7. Replacement Language Reference

This section gives implementers the complete positive vocabulary.

The governing principle: if you cannot express what SoSo observed using one of the `advisory_result` values below, the observation belongs in a free-text `notes` field, not a verdict-shaped field.

**Allowed primary fields:**

| Field             | Type   | Required | Notes                                |
| ----------------- | ------ | -------- | ------------------------------------ |
| `schema`          | string | YES      | Must be `ph6.soso.advisory.v1`       |
| `advisory_result` | string | YES      | One of the allowed values in Section 5 |
| `frame_id`        | string | NO       | Present when observation is frame-scoped |
| `notes`           | string | NO       | Free-text; no verdict vocabulary     |
| `ts`              | string | NO       | Observation timestamp                |
| `lane`            | int    | NO       | Always 2 when present                |
| `authority`       | string | NO       | Always `NONE` when present           |

**Forbidden primary fields:**

```text
verdict
result
motion_score
motion_decay_score
```

Any field not in the allowed list above that carries a value from the `may_not_emit` list is a governance violation.

---

# 8. Schema Lock — `ph6.soso.advisory.v1`

This section defines the schema that must be registered in `schema_lock_registry.json`.

```json
{
  "schema_id": "ph6.soso.advisory.v1",
  "version": "1",
  "lane": 2,
  "authority": "NONE",
  "required_fields": ["schema", "advisory_result"],
  "forbidden_fields": ["verdict", "result", "motion_score", "motion_decay_score"],
  "locked": true,
  "notes": "SoSo-family advisory output — must use advisory_result, never verdict or result"
}
```

Consistency check against existing Lane-2 locks:

| Schema                     | `verdict` forbidden | `result` forbidden | `advisory_result` required |
| -------------------------- | ------------------- | ------------------ | -------------------------- |
| `ph6.mram_s.advisory.v1`   | YES                 | NO                 | YES                        |
| `ph6.ssmt.audit_event.v1`  | YES                 | NO                 | NO (event schema)          |
| `ph6.tok.advisory_event.v1`| YES                 | YES                | YES                        |
| `ph6.soso.advisory.v1`     | YES                 | YES                | YES                        |

`ph6.soso.advisory.v1` is consistent with `ph6.tok.advisory_event.v1` in forbidding both `verdict` and `result`. This alignment is intentional: both schemas serve as primary advisory output channels for their respective Lane-2 subsystems.

`ph6.mram_s.advisory.v1` and `ph6.ssmt.audit_event.v1` do not forbid `result` because they predate this contract. A future hardening pass may align them.

---

# 9. Conformance Tests

Five tests must pass before any SoSo-family variant is considered patched.

## Test A — Schema Compliance

**Purpose:** Output schema contains required fields and no forbidden fields.

```text
PASS condition: schema field present, advisory_result present,
                no forbidden fields in output.
FAIL condition: any forbidden field present, or advisory_result absent.
```

## Test B — SoSo Non-Blocking

**Purpose:** SoSo output does not block Lane-1 frame processing.

```text
PASS condition: Lane-1 PASS/DROP verdict is issued without waiting
                for or consulting SoSo advisory output.
FAIL condition: Lane-1 verdict generation is gated on SoSo output,
                or SoSo output delays Lane-1 commit.
```

Test B is authority-boundary verification, not schema verification.
It proves the authority boundary is real rather than declared.

## Test C — MRAM-S Containment

**Purpose:** SoSo output is written only to MRAM-S.

```text
PASS condition: advisory output written to MRAM-S only;
                no write to CRAM-0, CRAM-A, or CRAM-R.
FAIL condition: any write to a CRAM tier.
```

## Test D — EvidencePacket Exclusion

**Purpose:** SoSo advisory content does not enter EvidencePacket fields.

```text
PASS condition: no advisory_result, notes, or any SoSo-origin field
                appears inside an EvidencePacket.
FAIL condition: any SoSo-origin content in EvidencePacket.
```

## Test E — Replay Independence

**Purpose:** CRAM replay does not depend on SoSo advisory output.

```text
PASS condition: replay of a frame produces the same PASS/DROP result
                whether SoSo advisory output is present or absent.
FAIL condition: replay result differs based on SoSo output presence.
```

Test E is authority-boundary verification, not schema verification.
It proves the advisory boundary is maintained under replay.

**Tests B and E must both pass before any variant is considered patched.**
The others verify schema compliance. B and E verify operational isolation.

---

# 10. DRIFT_FAIL Triggers

Declare DRIFT_FAIL if any of the following occur:

```text
A SoSo-family system emits PASS or DROP.
A SoSo-family system emits FINAL, BLOCK, OVERRIDE, APPROVE, REJECT, or CERTIFY.
A SoSo-family output schema contains a verdict field.
A SoSo-family output schema contains a result field.
A SoSo-family output is written to any CRAM tier.
A SoSo-family output enters an EvidencePacket field.
A SoSo-family output becomes a replay dependency.
A SoSo-family output blocks RSYNC.
A SoSo-family output changes a PSEUDO threshold.
```

---

# 11. Governance Provenance

This contract is registered under the PH6 governance framework.

Registration steps:

1. Schema `ph6.soso.advisory.v1` added to `schema_lock_registry.json` (Section 8)
2. This document added to `governance_manifest.json` → `doctrine_files`
3. Governance drift scan passes at HEAD before any implementation patches proceed

This contract is a governance registration pass only.

It does NOT:

* patch any SoSo implementation
* change PSEUDO logic
* change CRAM write behavior
* change replay behavior
* change RSYNC behavior
* close OI-01 or OI-03

---

# STATUS

```text
State:   DRAFT
Version: v1.0
Saved:   2026-05-14
Seal:    NOT SEALED — requires test suite pass (Tests A–E) before seal review
Next:    Register schema → update manifest → run drift scan → variant patches
```
