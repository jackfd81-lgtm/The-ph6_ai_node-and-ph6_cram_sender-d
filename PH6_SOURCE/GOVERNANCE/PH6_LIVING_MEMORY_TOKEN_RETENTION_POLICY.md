# PH6 Living Memory and Token Retention Policy

**Schema:** ph6.governance.living_memory_token_retention.v1  
**Status:** PROPOSED — prototype-ready governance  
**Proposed by:** claude-code-lane2 | **Ratified by:** null  
**AI contribution:** `{"proposed_by":"claude-code-lane2","proposed_at_utc":"2026-06-06T00:00:00Z","ratified_by":null}`

---

## 1. Living Evidence Memory

PH6 Living Memory is **append-only, one-way, and rehydratable**.

It is not a database to be edited. It is an accumulating record of what was known, when it was known, and what authority backed it.

### Memory May

```
reopen evidence (read-only review)
replay evidence (CRAM replay)
inspect preserved artifacts
compare old and new evidence
rehydrate anchor packs (AHT → RT rebuild)
summarize evidence (produces advisory M4 record)
map answer origin (trace to CRAM and PSEUDO sources)
support AI explanation (provides M4 context)
```

### Memory May Not

```
mutate CRAM evidence
rewrite records
replace old evidence with new evidence
reverse authority decisions
convert theory into fact
allow AI to become evidence authority
allow SoSo to override PSEUDO
delete prior memory tiers
```

---

## 2. One-Way Circle Rule

Memory may loop back for review. It cannot loop back for authority revision.

```
Review loop:     evidence → AI review → new record → forward event
                 (circular reference to old evidence is fine)
                 (creates new forward-only audit event)

Authority loop:  NOT PERMITTED
                 (old CRAM evidence may not be revised based on new AI explanation)
                 (old PSEUDO verdict may not be retroactively changed)
```

Old evidence is referenced, not changed. The loop is circular for review but linear for authority.

Every review that references prior evidence **must** produce a new forward audit event. The old event is not modified.

---

## 3. Memory Tier Retention Policy

| Tier | Name | Retention | Decay | Rehydration |
|------|------|-----------|-------|-------------|
| `M0_RAW` | Raw CRAM Reference | Permanent | None | N/A — CRAM is the source |
| `M1_MEASURED` | PSEUDO-Measured Memory | Permanent | None | Replay from CRAM |
| `M2_CONTEXTUAL` | SoSo Continuity Memory | Long-term | Configurable after operator review | From SoSo + CRAM |
| `M3_TOKENIZED` | Tokenized / Topology Memory | Long-term | Configurable | From token manifest |
| `M4_AI_ADVISORY` | AI Advisory Memory | Medium-term | Configurable | From Decision Review Record |
| `M5_RATIFIED` | Operator-Ratified Memory | Long-term | Only by operator action | From ratification record |
| `M6_DOCTRINE` | Governance-Level Memory | Permanent | Only by governance update | From governance docs |

**M0 and M1 are never expired.** They are the foundation of the entire memory hierarchy. Any decay of higher tiers must preserve links to M0/M1.

---

## 4. Token-Loss Mitigation

Token-loss is detected and managed through the low-level physics classes.

| Class | Meaning | Mitigation |
|-------|---------|-----------|
| `RT` | Real Token — fully backed | No mitigation needed |
| `RLT` | Real-Loss Token — RT lost from accessible storage | AHT created; lineage preserved; recovery attempted |
| `PLT` | Predicted-Loss Token — RT at risk | Operator warned; backup triggered if possible |
| `VLT` | Virtual Longevity Token — no CRAM backing | Labeled as advisory; not promoted without backing |
| `VDT` | Virtual Decay Token — expected to expire | Labeled; not used in authority decisions |
| `AHT` | Anchor Handle Token — identity stub | Used during rebuild/rehydration; replaced by RT on success |

### Token-Loss Response Protocol

```
1. Detect loss (storage check, hash verify, or SoSo drift warning)
2. Create RLT for the lost RT — preserves identity and lineage
3. Create AHT — preserves handle for rehydration attempt
4. Log to audit.jsonl (forward-only)
5. Notify operator
6. Attempt rehydration from CRAM if available
7. If rehydration succeeds: AHT → RT (new version edge)
8. If rehydration fails: AHT remains; RLT marks the gap
```

---

## 5. Token Promotion Rules

Tokens may only be promoted through version edges. A version edge is recorded as a new token with:

```json
{
  "supersedes": "<prior_token_id>",
  "version": "<new_version>",
  "parent_token_ids": ["<prior_token_id>"]
}
```

**Prohibited promotions without operator ratification:**

```
M4_AI_ADVISORY → M5_RATIFIED    requires operator ratification
M5_RATIFIED → M6_DOCTRINE       requires operator ratification + governance scan PASS
VDT → VLT                       requires updated evidence backing
AHT → RT                        requires successful CRAM rehydration
```

**Self-promotion is not permitted.** AI may not create a `M5_RATIFIED` or `M6_DOCTRINE` record for its own output.

---

## 6. Rehydration

Rehydration reconstructs a lost or degraded token from preserved CRAM evidence.

**Rehydration is valid when:**

```
Source CRAM evidence is intact and hash-verified
Rehydration method is documented in token record
Rehydrated token version is higher than original
Original token ID is preserved in parent_token_ids
```

**Rehydration is not valid when:**

```
Source CRAM evidence is missing or hash-fails
Rehydration would alter the evidence content
Rehydration would change a PSEUDO verdict
```

A rehydration that fails must create an AHT for future recovery and log the failure to audit.

---

## 7. Decay and Expiration

Decay is configurable per tier (M2–M4) by operator. Expired tokens are not deleted — they are marked with `superseded_by` pointing to a `DECAY_RECORD` token.

**Decay rules:**

```
Decay may not erase lineage.
Decay may not erase authority source IDs.
Decay may not reduce M0 or M1 records.
Decay must be approved by operator for M5 and M6.
Every decay event produces a forward audit event.
```

---

## 8. Token Compression Policy

Compression reduces token size. It does not reduce lineage.

**Compression classes:**

| Class | Meaning |
|-------|---------|
| `LOSSLESS` | All fields preserved; format reduced only |
| `LOSSY_DECLARED` | Some fields removed; all removed fields named in `lost_fields_declared` |
| `LOSSY_SUMMARY` | Replaced by summary; original preserved in separate record |

`operator_review_required: true` for any compression with `loss_class` other than `LOSSLESS`.

Compression must preserve:

```
source IDs
authority level
version edges (supersedes / superseded_by)
canonical hash of original
created_at_utc
```

Compression may not remove these fields even in `LOSSY_DECLARED` mode.

---

## 9. Anchor Pack and Rehydration Candidates

SoSo identifies rehydration candidates through continuity drift analysis. When SoSo detects a token that is at risk (`PLT` risk), it may recommend:

```
create_anchor_pack:
  - identify all RT and VLT tokens linked to this evidence set
  - hash and record their current state
  - create AHT stubs for each
  - create a rehydration_candidate record
  - notify operator
```

The anchor pack does not change authority. It preserves handles for future recovery.

---

*Lane-2 advisory document. No authority changes. Operator ratification required.*
