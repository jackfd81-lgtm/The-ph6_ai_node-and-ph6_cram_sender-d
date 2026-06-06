# PH6 AI Containment Doctrine

**Schema:** ph6.governance.ai.containment.v1  
**Status:** PROPOSED  
**Proposed by:** claude-code-lane2 | **Ratified by:** null

---

## 1. Containment Statement

AI is a Level 6 (Advisory) system. It observes, summarizes, requests, hypothesizes, and learns. It does not adjudicate, certify, modify evidence, or become a Lane 1 authority.

```
AI authority level: ADVISORY_ZERO
Lane: 2 (advisory)
Verdict authority: NONE
Evidence mutation authority: NONE
```

---

## 2. AI May

```
Analyze CRAM evidence (read-only reference)
Summarize measurement results
Request derived artifacts (via ph6_ai_authority_request_v1)
Suggest additional tests
Compare evidence across sessions
Detect patterns
Generate hypotheses (POSIT tokens — Theoretical only)
Request PSEUDO measurement results
Request SoSo continuity maps
Produce advisory output labeled Authority ZERO
Learn from CRAM-E, CRAM-D, CRAM-H, CRAM-R references
Produce AI Decision Review Records
Produce Dissent Tokens when disagreeing with PSEUDO or SoSo
```

---

## 3. AI May Not

```
Adjudicate PASS or DROP
Overwrite CRAM evidence (CRAM-0, CRAM-A, CRAM-R)
Modify source measurements
Rewrite canonical hashes
Rewrite chain-of-custody records
Become Lane 1 authority
Silently compress evidence without lineage record
Issue a verdict that overrides PSEUDO
Promote its own MRAM-S output to evidence without operator ratification
```

---

## 4. Required AI Transform Record

Every AI transformation of sensor data, image, audio, video, or derived media must produce a record:

```json
{
  "schema_id": "ph6.ai.ai_transform_record.v1",
  "source_object_id": "<cram_evidence_id>",
  "source_hash": "<blake2b-256>",
  "operation_type": "<IMAGE_ENHANCEMENT|ANNOTATION|SUMMARY|...>",
  "requested_by": "<session_id>",
  "request_reason": "<why this transform was requested>",
  "model_id": "<model name and version>",
  "derived_object_id": "<output artifact id>",
  "derived_hash": "<blake2b-256 of output>",
  "timestamp_utc": "<ISO 8601>",
  "authority_level": "ADVISORY_ZERO",
  "source_evidence_unchanged": true,
  "pseudo_response": "<response id or null>",
  "soso_response": "<map id or null>",
  "dissent_record": "<dissent id or null>"
}
```

`authority_level` is a constant: always `ADVISORY_ZERO`.  
`source_evidence_unchanged` is a constant: always `true`.

---

## 5. AI Learning Architecture

AI learns through controlled evidence references, not through evidence mutation.

```
CRAM evidence (read-only reference)
  ↓
PSEUDO measurement (provided via authority request)
  ↓
Replay certification (provided via certification record)
  ↓
Token reference (topology map)
  ↓
SoSo continuity map (advisory)
  ↓
AI advisory review
  ↓
MRAM-S memory object (advisory, authority ZERO)
  ↓
Future AI context package (ai_ingest_manifest)
```

At no step does AI write to or modify anything above MRAM-S in this chain.

---

## 6. Dissent Rule

When AI disagrees with PSEUDO, SoSo disagrees with PSEUDO, or operator disagrees with AI:

1. PSEUDO remains controlling authority.
2. A `DISSENT_TOKEN` (`ph6_dissent_token_v1`) is created.
3. Dissent blocks promotion of disputed advisory output.
4. Dissent does not erase the disagreeing record.
5. Operator reviews and records resolution.
6. PSEUDO verdict stands unless a new measurement cycle produces a new verdict.

---

## 7. Hallucination Control

Every AI advisory output for evidence review or operator decisions must produce a `ph6_ai_decision_review_v1` record with:

- `hallucination_risk_flags` list (may be empty)
- `uncertainty_flags` list
- All claims classified: `FACTUAL`, `INFERRED`, `THEORETICAL`, `UNSUPPORTED`, or `HALLUCINATION_RISK`

`UNSUPPORTED` and `HALLUCINATION_RISK` claims may not enter downstream decisions without explicit operator promotion.

---

*Lane-2 advisory document. Operator ratification required.*
