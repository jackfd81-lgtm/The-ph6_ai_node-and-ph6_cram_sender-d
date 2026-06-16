# PH6 AI Decision Review and Hallucination Control

**Schema:** ph6.governance.ai_decision_review.v1  
**Status:** PROPOSED — prototype-ready governance  
**Proposed by:** claude-code-lane2 | **Ratified by:** null  
**AI contribution:** `{"proposed_by":"claude-code-lane2","proposed_at_utc":"2026-06-06T00:00:00Z","ratified_by":null}`

---

## 1. AI Limitation Statement

PH6 does **not** claim to expose private AI model reasoning.

PH6 **does** prove:

```
evidence path        — what CRAM evidence was used
context path         — what SoSo and token context was active
authority boundary   — where AI advisory ends and PSEUDO authority begins
declared explanation — what explanation the AI offered and why
review trail         — whether an operator reviewed and ratified the answer
```

The AI is an interpreter, not an authority. Its explanation is a secondary artifact, not a measurement.

---

## 2. What PH6 Proves vs What It Does Not Claim

| PH6 Proves | PH6 Does Not Claim |
|------------|-------------------|
| What evidence was provided to the AI | What the AI "really thought" |
| What PSEUDO verdict the AI received | That the AI understood the evidence correctly |
| What the AI declared in its output | That the AI has no undetected errors |
| Whether operator reviewed the answer | That the AI's explanation is complete |
| The hash of the AI's output | That hidden model reasoning is auditable |
| The model identity and session ID | The AI's internal weights or state |

---

## 3. AI Decision Review Record

Every AI advisory output that may be used in evidence review, governance, or operator decision-making **must** produce a `ph6_ai_decision_review_v1` record.

**Required fields:**

| Field | Purpose |
|-------|---------|
| `schema_id` | `ph6.ai_decision_review.v1` |
| `answer_id` | Unique identifier for this AI output |
| `created_at_utc` | ISO 8601 timestamp |
| `mode` | LEGAL / SCIENTIFIC / EXPERIMENTAL / THEORETICAL |
| `model_identity` | Model name, version, session ID |
| `evidence_inputs` | CRAM IDs used |
| `soso_inputs` | SoSo map IDs used |
| `token_inputs` | Token IDs used |
| `claims` | Array of structured claim objects |
| `uncertainty_flags` | Declared uncertainty markers |
| `hallucination_risk_flags` | Declared hallucination risk markers |
| `output_hash` | BLAKE2b-256 hash of the output text |
| `review_status` | PENDING / REVIEWED / RATIFIED / DISPUTED |

---

## 4. Claim Classifications

Every claim in an AI Decision Review Record carries a `claim_class`.

| Class | Meaning |
|-------|---------|
| `FACTUAL` | Directly supported by cited CRAM or PSEUDO evidence |
| `INFERRED` | Logically derived from supported claims; derivation documented |
| `THEORETICAL` | Based on general knowledge; no specific evidence link |
| `UNSUPPORTED` | No evidence link identified; flagged for review |
| `HALLUCINATION_RISK` | Claim could not be verified against any cited input |

Claims of class `UNSUPPORTED` or `HALLUCINATION_RISK` must not be used in downstream authority decisions without explicit operator promotion.

---

## 5. Hallucination-Risk Flags

A `hallucination_risk_flags` list is required in every review record. Flags are declared by the AI or the review process.

**Standard flags:**

| Flag | Trigger |
|------|---------|
| `NO_EVIDENCE_LINK` | Claim has no cited CRAM or PSEUDO source |
| `CONTEXT_MISMATCH` | Evidence provided does not support the claim made |
| `OUT_OF_SCOPE` | Claim is outside the declared measurement scope |
| `MODEL_UNCERTAINTY` | AI explicitly flagged low confidence |
| `CONTRADICTION_WITH_PSEUDO` | AI output contradicts a PSEUDO verdict |
| `STALE_CONTEXT` | Evidence inputs are from a prior session or time window |

The presence of a flag does not invalidate the AI output. It marks it for review. A `CONTRADICTION_WITH_PSEUDO` flag also triggers a `DISSENT_TOKEN`.

---

## 6. Unsupported-Claim Detection

During review, any claim lacking a source link to cited evidence inputs is automatically classified `UNSUPPORTED`.

Rules:

```
AI may not promote UNSUPPORTED claims to downstream decisions.
AI may not suppress HALLUCINATION_RISK flags.
AI may revise its explanation — the revised version produces a new answer_id.
The original answer_id record is preserved unchanged (append-only).
Revised answers must link to prior answer_id in source_ids.
```

An answer marked all-`FACTUAL` with no flags is still secondary advisory. It does not become primary evidence.

---

## 7. Model Identity Requirement

Every AI Decision Review Record must include `model_identity`. Minimum fields:

```json
{
  "model_name": "claude-sonnet-4-6",
  "session_id": "<unique session identifier>",
  "api_call_log_ref": "<stamp or reference>",
  "context_hash": "<BLAKE2b-256 of prompt + context>"
}
```

`context_hash` allows future verification that the AI was given the specific context it claims to have used.

---

## 8. Courtroom-Safe Framing

PH6 evidence review must use this framing when presenting AI outputs:

```
This is an advisory interpretation produced by an AI system.
It is classified as Lane-2 secondary advisory output.
It has Authority: ZERO.

The primary measurement authority is PSEUDO (Lane-1 deterministic).
The primary evidence authority is CRAM.
The AI interpretation is linked to those authorities but does not override them.

The evidence path, context path, authority boundary, and declared explanation
are recorded and verifiable. The AI's internal reasoning is not claimed to be
exposed or auditable beyond its declared output.
```

PH6 does not claim that Lane-2 AI output satisfies FRE 702 expert witness standards independently. Lane-2 output supports, contextualizes, and reviews Lane-1 deterministic output. Lane-1 PSEUDO output and CRAM evidence chain are the FRE 702 candidates.

---

## 9. Schema Reference

`ph6_ai_decision_review_v1.schema.json` — located in `PH6_SOURCE/SCHEMAS/`

Cross-references:
- `PH6_TOKEN_MEMORY_AI_DERIVED_EVIDENCE_DOCTRINE.md` — token classes and authority model
- `PH6_AUTHORITY_MODE_HIERARCHY.md` — mode definitions
- `PH6_COURTROOM_EVIDENCE_READINESS.md` — evidence readiness matrix

---

*Lane-2 advisory document. No authority changes. Operator ratification required.*
