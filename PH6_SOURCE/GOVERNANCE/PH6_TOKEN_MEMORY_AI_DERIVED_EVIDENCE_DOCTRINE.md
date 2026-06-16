# PH6 Token Memory and AI-Derived Evidence Doctrine

**Schema:** ph6.governance.token_memory_ai_derived_evidence.v1  
**Status:** PROPOSED — prototype-ready governance  
**Proposed by:** claude-code-lane2 | **Ratified by:** null  
**AI contribution:** `{"proposed_by":"claude-code-lane2","proposed_at_utc":"2026-06-06T00:00:00Z","ratified_by":null}`

---

## 1. Final System Architecture

```
REALITY
  → SENSORS
  → CRAM PRIMARY EVIDENCE
  → PSEUDO DETERMINISTIC AUTHORITY
  → SOSO CONTINUITY / DRIFT / COMPARISON
  → TOKEN TOPOLOGY
  → AI REQUEST / REVIEW / TRANSFORM
  → SECONDARY DERIVED EVIDENCE
  → LIVING MEMORY OBJECT
  → AI DECISION REVIEW RECORD
  → OPERATOR RATIFICATION
  → FORWARD-ONLY AUDIT EVENT
```

This flow is one-way for authority. Every AI step produces secondary artifacts linked to the primary evidence above it, never replacing it.

---

## 2. Non-Negotiable Authority Rules

```
CRAM preserves evidence.
PSEUDO judges deterministic measurement.
SoSo maps continuity and drift.
Tokens preserve structure, lineage, topology, and memory.
AI may request, explain, transform, and learn.
AI may not rewrite authority.
```

---

## 3. Token Governance Classes

These classes describe the governance role of a token. Every token record includes `token_class`.

| Class | Role |
|-------|------|
| `CRAM_EVIDENCE_TOKEN` | References preserved CRAM evidence packet |
| `PSEUDO_VERDICT_TOKEN` | References PSEUDO deterministic verdict (PASS or DROP) |
| `SOSO_MAP_TOKEN` | References SoSo continuity/drift map output |
| `VERSION_TOKEN` | Marks a version boundary or schema migration point |
| `TOPOLOGY_TOKEN` | References node/device/fleet topology record |
| `AI_REQUEST_TOKEN` | Records an AI query to PSEUDO or SoSo |
| `AI_TRANSFORM_TOKEN` | Records an AI-derived secondary artifact |
| `MEMORY_TOKEN` | Living memory object — see Section 9 |
| `POSIT_TOKEN` | Structured hypothesis — see Section 10 |
| `DISSENT_TOKEN` | Disagreement record — see Section 8 |
| `NEURO_MAP_TOKEN` | Feature/relationship map from AI analysis |

---

## 4. Low-Level Token Physics Classes

These classes describe the stability and lifecycle of a token.

| Class | Meaning |
|-------|---------|
| `RT` | Real Token — backed by durable CRAM evidence |
| `VLT` | Virtual Longevity Token — advisory persistence, no CRAM backing |
| `VDT` | Virtual Decay Token — advisory, expected to expire |
| `RLT` | Real-Loss Token — RT lost from accessible storage; lineage preserved |
| `PLT` | Predicted-Loss Token — RT predicted to be at risk |
| `AHT` | Anchor Handle Token — stub preserving identity during rebuild/rehydration |

### Token Authority Ranking

```
CRAM-preserved evidence
  > RT  > RLT  > VLT  > AHT  > PLT  > VDT
  > AI explanation
```

No token may erase or replace another token. A token may only supersede another through a new version edge recorded in `supersedes` / `superseded_by`.

---

## 5. AI / PSEUDO / SoSo Request Model

Every AI request to PSEUDO or SoSo must be recorded as an `AI_REQUEST_TOKEN` and an `ph6_ai_authority_request_v1` record.

### AI May Ask PSEUDO For

```
deterministic measurements
gate values and thresholds
PASS / DROP verdicts
canonical hashes
replay status
contradiction flags
CRAM evidence references
```

### AI May Ask SoSo For

```
continuity maps
topology summaries
token-loss warnings
virtual-token stability estimates
drift warnings
rehydration candidates
```

### AI May Not

```
revise CRAM evidence
revise PSEUDO verdicts
revise gate thresholds or logic
override Legal authority
override Scientific authority
override Experimental authority
issue its own PASS or DROP verdict
promote its own output to primary evidence
```

AI may update its explanation after receiving PSEUDO or SoSo results. The explanation remains secondary.

---

## 6. AI-Derived Evidence Rules

AI may alter image, audio, video, or derived sensor media only by creating **secondary artifacts** linked to original CRAM evidence.

```json
"authority_status": "SECONDARY_DERIVED_EVIDENCE_ONLY",
"may_replace_primary_evidence": false
```

These two fields are constants in `ph6_ai_transform_record_v1`. They are not operator-configurable.

AI-transformed media must link to the original CRAM artifact via `source_cram_ids`. Every transform produces a `ph6_ai_transform_record_v1` record and a corresponding `AI_TRANSFORM_TOKEN`.

---

## 7. Dissent

A `DISSENT_TOKEN` (schema: `ph6_dissent_token_v1`) is created whenever:

```
AI disagrees with PSEUDO
AI disagrees with SoSo
SoSo disagrees with PSEUDO
Operator disagrees with AI
Operator disagrees with PSEUDO
PSEUDO detects contradiction in its own output
```

**Dissent blocks promotion, not evidence.**

If AI and SoSo agree but PSEUDO disagrees: PSEUDO is controlling authority. A DISSENT_TOKEN is created; PSEUDO verdict stands.

Dissent records are append-only. They are never deleted. `blocking_status` may be updated to `RESOLVED` by operator ratification, but the original dissent record remains.

---

## 8. Living Memory Tiers

PH6 Living Memory is stratified. Every `MEMORY_TOKEN` declares its tier in `memory_tier`.

| Tier | Name | Description |
|------|------|-------------|
| `M0_RAW` | Raw CRAM Reference | Direct reference to CRAM evidence packet |
| `M1_MEASURED` | PSEUDO-Measured Memory | Memory derived from PSEUDO deterministic output |
| `M2_CONTEXTUAL` | SoSo Continuity Memory | Memory from SoSo continuity / drift map |
| `M3_TOKENIZED` | Tokenized / Topology Memory | Token-based and topology memory |
| `M4_AI_ADVISORY` | AI Advisory Memory | AI-generated explanation or inference |
| `M5_RATIFIED` | Operator-Ratified Memory | Operator-approved memory record |
| `M6_DOCTRINE` | Governance-Level Memory | Ratified governance or doctrine record |

**Promotion rules:**
- AI memory (`M4_AI_ADVISORY`) cannot promote itself.
- AI memory must be linked to CRAM, PSEUDO, SoSo, tokens, or operator ratification before use in downstream decisions.
- Promotion from `M4` to `M5_RATIFIED` requires explicit operator ratification.
- Promotion from `M5` to `M6_DOCTRINE` requires operator ratification and governance scan PASS.

---

## 9. Posit / Hypothesis

A `POSIT_TOKEN` (schema: `ph6_posit_v1`) is a structured theory. It is not evidence.

```
POSIT = structured theory, not evidence.
```

Posit `support_level` values:
- `THEORETICAL` — no supporting evidence yet
- `CANDIDATE` — plausible, pending investigation
- `SUPPORTED_BY_EVIDENCE` — supported by CRAM or PSEUDO output, not yet validated
- `VALIDATED_BY_PSEUDO` — PSEUDO has confirmed

`may_affect_authority: false` and `may_affect_memory: false` unless explicitly promoted by operator.

A posit can never become a CRAM record or PSEUDO verdict without going through the full measurement and verification cycle.

---

## 10. Token Compression

Token compression reduces stored token size. It does not reduce lineage.

**Compression rules:**
```
May reduce text size.
May not erase lineage.
May not remove authority source IDs.
May not remove version edges.
Must produce a ph6_token_compression_record_v1.
Must declare all lost fields in lost_fields_declared.
```

`operator_review_required = true` whenever `loss_class` is not `LOSSLESS`.

Compression is not authority mutation. Compressed tokens remain secondary to the originals until originals are formally superseded via version edge.

---

## 11. Schema References

| Schema | Purpose |
|--------|---------|
| `ph6_token_v1` | Generic token record |
| `ph6_ai_authority_request_v1` | AI request to PSEUDO/SoSo |
| `ph6_authority_response_v1` | PSEUDO/SoSo response to AI request |
| `ph6_ai_transform_record_v1` | AI-derived secondary artifact record |
| `ph6_dissent_token_v1` | Disagreement record |
| `ph6_posit_v1` | Structured hypothesis |
| `ph6_token_compression_record_v1` | Token compression audit record |
| `ph6_living_memory_object_v1` | Living memory object |
| `ph6_neuro_map_v1` | AI feature/relationship map |
| `ph6_ai_decision_review_v1` | AI decision review and hallucination control |

---

*Lane-2 advisory document. No authority changes. Operator ratification required.*
