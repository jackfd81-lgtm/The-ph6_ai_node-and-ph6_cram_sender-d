# PH6 / LMPQ-001 — Proposed Token & Continuity Extension

```text
Document ID: PH6-LMPQ-001-PROPOSED-SPEC-v0.1
Classification: BOOK V / LANE-2 ADVISORY TOKEN TOPOLOGY (PROPOSED)
Status: PROPOSED — NOT RATIFIED
Proposed by: claude-code-lane2
Ratified by: null
Primary Home: Book V — SoSo, JEDI, Tokens, Living Observation
Cross-Links:
- PH6_SOURCE/GOVERNANCE/tokens/PH6_TOKEN_TOPOLOGY_DOCTRINE.md
- PH6_SOURCE/DRAFT/PH6-TOKENS-LIVING-CRAM-v1.1.md
- ph6/tok/lifecycle.py (RT/VDT/VLT reference implementation)
- ph6_l2_expand/token_types.py (LOCKED — RT/VDT/VLT only, not modified by this document)
Authority: ZERO
Write Boundary: /var/ph6/mram-s/ (advisory only, via ph6_l2_expand.mram_s_writer)
Replay Dependency: FORBIDDEN
EvidencePacket Participation: FORBIDDEN
PASS/DROP Authority: FORBIDDEN
```

---

## 0. Why this document exists

`PH6_TOKEN_TOPOLOGY_DOCTRINE.md` §4 ranks `VLT > AHT > PLT > VDT` but never
defines `AHT` or `PLT` in its Token Physics Classes table (§3), and never
mentions `RLT` at all. No document in this repository defines "LMPQ-001,"
"PM-01..PM-05," or a required "E001" path. This document is the first
attempt to define `RLT`, `PLT`, `AHT`, and a Life-CRAM bench-evidence
bundle format ("BCV2") concretely enough to implement and test, so that a
human reviewer has something specific to ratify or reject — rather than
code inventing behavior with no traceable design record.

**This document is PROPOSED. It grants no authority. It is not evidence
that LMPQ-001 exists as a prior specification — it is new design work.**

---

## 1. Naming derivation (stated explicitly, not asserted as pre-existing)

Following the existing convention where a token's initials are literally
its name (`RT` = Reference Token, `VDT` = Virtual Decay/Drift Token,
`VLT` = Virtual Longevity Token):

| Token | Expansion | Initials check |
|-------|-----------|-----------------|
| `RLT` | **R**eference **L**oss **T**oken | R-L-T ✓ |
| `PLT` | **P**rovenance **L**ink **T**oken | P-L-T ✓ |
| `AHT` | **A**rchival **H**ydration **T**oken | A-H-T ✓ |

All three remain **Lane-2, Authority ZERO, MRAM-S only**, in a new
`ph6_l2_expand.lmpq_proposed` namespace that is never added to
`ph6_l2_expand.schemas.TOKEN_TYPES` / `token_policy.ALLOWED_TOKEN_TYPES`.
Those two names remain locked to exactly `{RT, VDT, VLT}` — this document
does not propose changing that lock, and the implementation must not
either. Promotion of RLT/PLT/AHT into the authoritative token set is a
separate, later, explicitly-ratified decision (see §6).

---

## 2. RLT — Reference Loss Token

```text
Purpose:
  An advisory reference recording that a Lane-1 CRAM-R (DROP) commit was
  observed. It observes a loss; it does not cause, decide, or reverse it.

Triggering event:
  A DROP (CRAM-R) commit already made by PSEUDO-A. RLT is constructed
  strictly after the fact, from the DROP's already-existing reference
  hash — never before, never speculatively.

Evidence referenced:
  cram_ref_hash of the dropped evidence packet (opaque string — RLT never
  copies or reconstructs packet contents).

Provenance:
  parent_token_id: optional RT/VDT/VLT this loss pertains to, if any
  drop_observed_at_ms: event-time of the DROP commit (never wall-clock
    at RLT-construction time — see §5)

Invariant (locked in the dataclass, cannot be constructed otherwise):
  evidence_deleted: always False.
  DROP != DELETE. The evidence stays in CRAM-R; RLT is a pointer to it,
  not a replacement for it, and never implies removal.

Forbidden:
  Issuing or implying a verdict. Modifying the DROP record. Being used
  as a replay dependency. Being written outside MRAM-S.
```

## 3. PLT — Provenance Link Token

```text
Purpose:
  Advisory continuity link across a provenance gap (most commonly the
  gap an RLT records, but generally any parent -> resumed-chain link).

Triggering event:
  An RLT (or any RT/VDT/VLT) exists and a later set of tokens resumes
  the chain. PLT records that linkage explicitly rather than leaving it
  implicit.

Parent / relationship:
  parent_token_id: the RLT (or RT/VDT/VLT) the link originates from.
  linked_token_ids: non-empty list of RT/VDT/VLT ids that resume the
    chain after the parent.
  continuity_gap_ms: deterministic difference between the parent's
    event-time and the earliest linked token's event-time. Never
    computed from wall-clock "now."

Validation:
  Construction fails closed (raises) if parent_token_id is not present
  in the caller-supplied token map, or if linked_token_ids is empty.
  This is the "invalid parent token" / "broken provenance" negative
  path required by LMPQ-001 §12.

Forbidden:
  Same constraints as RLT — no verdict, no CRAM/PSEUDO mutation, no
  replay dependency.
```

## 4. AHT — Archival Hydration Token

```text
Purpose:
  Records a deterministic rehydration (replay) of a prior token's state
  from the existing ph6/tok advisory audit hash-chain
  (ph6.tok.reconstruct.validate_chain_integrity + chain walk). AHT wraps
  the existing rehydration primitive; it does not create a second one.

Triggering event:
  A caller asks to rehydrate source_token_id from a specific audit chain.

Locked fields (cannot be constructed otherwise):
  is_replay: always True.
  new_observation: always False.
  Replay != New Observation. Persistence != Truth. AHT can never be
  mistaken for a fresh observation because the dataclass will not allow
  new_observation=True to be set.

Determinism:
  event_time_ms: the ORIGINAL token's event-time, preserved unchanged.
  reconstructed_at_ms: when THIS replay was executed — kept in a
    separate field, and explicitly excluded from reconstructed_state_hash
    so replaying the same chain twice (at different wall-clock times)
    produces an identical hash. This is the fix for the nondeterminism
    pattern found in ph6_l2_expand/token_types.py:29-30 (utc_now_iso()
    used as a hash-relevant default) — applied here as the corrected
    pattern rather than repeated.

Failure behavior:
  Raises if the audit chain fails hash-chain integrity validation
  (altered/tampered source evidence), or if source_token_id does not
  appear in the chain (invalid rehydration reference / missing source
  evidence).
```

## 5. Timestamp discipline (LMPQ-001 §11)

Every new dataclass in this document takes event-time as an **explicit
required argument**, never a wall-clock default at construction time —
following `ph6/tok/lifecycle.py`'s existing `event_time_ms` parameter
pattern, and explicitly *not* following `ph6_l2_expand/token_types.py`'s
`utc_now_iso()` default (a confirmed live bug, out of scope to fix here
since it belongs to the locked RT/VDT/VLT module — noted for the
operator separately). Any wall-clock-derived field (e.g.
`reconstructed_at_ms`) is kept out of the deterministic hash input.

## 6. Life CRAM / "BCV2" — Bounded Campaign Vector, schema v2

No document or code anywhere in the repository uses the literal term
"BCV2." Life CRAM itself is real (`LCC-01A/B/C`, `EVC-05`,
`ph6/cram_pu/tools/life_cram_lcc_01_live_camera.py`). This document
defines **BCV2** as a new, explicitly-versioned, Lane-2 advisory bundle
schema (`ph6.lmpq.life_cram_bcv2.v1`) that packages one "experience"
(a bounded slice of a Life CRAM sequence) into a single deterministic,
hash-addressable record for LMPQ-001's four-experience bench (PM-02):

```json
{
  "schema": "ph6.lmpq.life_cram_bcv2.v1",
  "authority": "ZERO",
  "advisory_only": true,
  "bcv_id": "blake2b-256 of (experience_id, cram_refs, token_ids)",
  "experience_id": "string",
  "cram_refs": ["..."],
  "token_ids": ["... sorted ..."],
  "token_types_present": ["... sorted set ..."],
  "topology_hash": "blake2b-256 or null if not computed",
  "event_window": {"start_ms": 0, "end_ms": 0},
  "constraints": {
    "may_write_cram": false,
    "may_modify_evidence": false,
    "may_affect_pseudo": false,
    "may_issue_verdict": false,
    "may_block_rsync": false
  }
}
```

This reuses `ph6_l2_expand.mram_s_writer.write_advisory` for persistence
(atomic write, boundary-guard quarantine on forbidden vocabulary) rather
than inventing a second storage mechanism.

## 7. SoSo-JEDI integration

`PH6_SOURCE/AI/soso_jedi/jedi/swarm_sim_bp.py` (`BookVCoreEngine`) is
unmodified by this document. It performs Storm → Swarm → JEDI continuity
reconstruction, not single-token lookup, which is why the prior
investigation could not use it directly for LMPQ-001's provenance-lookup
requirement. The adapter added here (`lmpq_proposed/soso_jedi_adapter.py`)
derives a deterministic per-token seed from `blake2b256(token_id)` and
calls the engine's existing public methods unchanged, returning its
existing `ADVISORY_ZERO` output tagged with the source token id. No new
authority is created; SoSo-JEDI's own authority ceiling is unchanged.

## 8. What this document does NOT do

- Does not modify `ph6_l2_expand/token_types.py`, `token_policy.py`, or
  `schemas.py` (the locked RT/VDT/VLT set is untouched).
- Does not modify `ph6_l2_expand/tests/test_token_classes_locked.py` or
  `test_soso_tokens_not_lane1.py`.
- Does not write to CRAM-0/CRAM-A/CRAM-R.
- Does not grant RLT/PLT/AHT any authority, or promote them into
  `ALLOWED_TOKEN_TYPES`.
- Does not modify `PH6_SOURCE/AI/soso_jedi/jedi/swarm_sim_bp.py`.

## 9. Ratification path

```text
Implementation (this document + ph6_l2_expand/lmpq_proposed/) → testing →
evidence (bench artifacts) → operator review → only then: a separate,
explicit decision on whether RLT/PLT/AHT are promoted into
ALLOWED_TOKEN_TYPES, and whether BCV2 becomes a canonical Life CRAM
artifact schema.
```

---

{"proposed_by":"claude-code-lane2","proposed_at_utc":"2026-09-13T00:00:00Z","api_call_log_ref":"session_018YAqUsASJSjhEyWe2bbmaH","ratified_by":null}
