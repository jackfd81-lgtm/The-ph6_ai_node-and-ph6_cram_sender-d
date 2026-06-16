# PH6 Token Topology Doctrine

**Schema:** ph6.governance.tokens.topology.v1  
**Status:** PROPOSED  
**Proposed by:** claude-code-lane2 | **Ratified by:** null

---

## 1. Token Purpose

Tokens help AI and SoSo preserve continuity, reference evidence, and track lineage. Tokens do not carry authority over evidence. They are references, not evidence.

```
Token authority: ZERO (unless directly linked to certified Lane 1 evidence — 
                        even then the token is a reference, not evidence)
```

---

## 2. Token Chain

```
Evidence
  ↓
Reference Tokens (RT)
  ↓
Evidence Tokens (ET)
  ↓
Measurement Tokens (MT)
  ↓
Continuity Tokens (CT)
  ↓
Hypothesis Tokens (HT)
  ↓
Topology Graph
  ↓
MRAM-S
```

---

## 3. Token Classes

### Governance Token Classes

| Class | Purpose |
|-------|---------|
| `CRAM_EVIDENCE_TOKEN` | References preserved CRAM evidence packet |
| `PSEUDO_VERDICT_TOKEN` | References PSEUDO PASS/DROP verdict record |
| `SOSO_MAP_TOKEN` | References SoSo continuity/drift map |
| `VERSION_TOKEN` | Marks version boundary or schema migration |
| `TOPOLOGY_TOKEN` | References node/device/fleet topology record |
| `AI_REQUEST_TOKEN` | Records AI query to PSEUDO or SoSo |
| `AI_TRANSFORM_TOKEN` | Records AI-derived secondary artifact |
| `MEMORY_TOKEN` | Living memory object in MRAM-S |
| `POSIT_TOKEN` | Structured hypothesis — Theoretical only |
| `DISSENT_TOKEN` | Disagreement record between AI, SoSo, PSEUDO, or operator |
| `NEURO_MAP_TOKEN` | AI feature/relationship map |

### Token Physics Classes

| Class | Meaning |
|-------|---------|
| `RT` | Reference Token — direct evidence reference |
| `ET` | Evidence Token — links to specific CRAM evidence packet |
| `MT` | Measurement Token — links to PSEUDO measurement output |
| `CT` | Continuity Token — SoSo continuity record reference |
| `HT` | Hypothesis Token — links to POSIT record |
| `DT` | Dissent Token — links to DISSENT_TOKEN record |
| `VDT` | Virtual Decay Token — advisory, expected to expire |
| `VLT` | Virtual Longevity Token — advisory persistence, no CRAM backing |
| `AT` | Authority Request Token — records AI request to PSEUDO/SoSo |
| `ART` | Authority Response Token — records PSEUDO/SoSo response to AI |
| `TCR` | Token Compression Record — audit record of token compression event |

---

## 4. Token Authority Ranking

```
CRAM-preserved evidence
  > RT > ET > MT > CT > HT
  > VLT > AHT > PLT > VDT
  > AI explanation
```

No token may erase or replace another token.  
A token supersedes another only through a new version edge recorded in `supersedes` / `superseded_by`.

---

## 5. Token Compression Rule

Token compression reduces stored token size. It does not reduce lineage.

Every compression event must declare:

```
input_token_ids       — all tokens compressed
output_token_id       — resulting compressed token
compression_method    — MERGE | SUMMARIZE | DEDUPLICATE | TRUNCATE_DECLARED
loss_class            — LOSSLESS | LOSSY_DECLARED | LOSSY_SUMMARY
preserved_fields      — fields guaranteed in output
lost_fields_declared  — fields removed (must be explicit)
source_hashes         — hashes of input tokens
authority_status      — always ADVISORY_ZERO for compressed tokens
review_status         — PENDING | REVIEWED | RATIFIED
```

`operator_review_required: true` for any `loss_class` other than `LOSSLESS`.

Compression must preserve: source IDs, authority level, version edges, canonical hash of original, created_at_utc.

---

## 6. Token Topology Graph

The token topology graph (`ph6_token_topology_graph.v1`) maps relationships between tokens and evidence.

It is advisory only. It does not grant authority. It helps AI and SoSo navigate lineage and identify gaps.

Required graph fields: `graph_id`, `generated_at_utc`, `nodes` (token IDs), `edges` (relationships), `authority_status: "ADVISORY_ONLY"`, `graph_hash`.

---

*Lane-2 advisory document. Operator ratification required.*
