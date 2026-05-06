# PH6 / CRAM — Tokens in the Living CRAM System

```text
Document ID: PH6-TOKENS-LIVING-CRAM-v1.1
Classification: BOOK V / LANE-2 ADVISORY TOKEN TOPOLOGY
Status: CANON-ALIGNED UPDATE
Primary Home: Book V — SoSo, JEDI, Tokens, Living Observation
Cross-Links:
- Book 0 — Interpretive Control Plane
- Book III — One-Way Truth Membrane / Containment
- Book IV — Certification / Campaign Proof
Authority: ZERO
Write Boundary: /var/ph6/mram-s/tokens/
Replay Dependency: FORBIDDEN
EvidencePacket Participation: FORBIDDEN
PASS/DROP Authority: FORBIDDEN
```

---

## 1. Token Core Seal

```text
Tokens may describe continuity.

Tokens may describe drift.

Tokens may describe object history.

Tokens may describe advisory topology.

Tokens may assist SoSo and JEDI.

Tokens may support campaign planning.

Tokens may not decide truth.

Tokens may not write CRAM.

Tokens may not affect PSEUDO.

Tokens may not affect PASS/DROP.

Tokens may not become replay dependency.

Tokens may not enter the EvidencePacket.

Tokens live in MRAM-S only.

Tokens have Authority ZERO.
```

---

## 2. Token Definition

```text
A Token is a Lane-2 advisory continuity object.

It records relationship, recurrence, drift pressure, or long-term
observational pattern around CRAM-preserved evidence.

A Token is not evidence.

A Token is not truth.

A Token is not authority.

A Token is not a verdict source.

A Token is not a replacement for PSEUDO.

A Token is a bounded advisory memory artifact stored only in MRAM-S.
```

---

## 3. Correct System Placement

| Token Component        | Best Home        | Reason                                  |
| ---------------------- | ---------------: | --------------------------------------- |
| Token doctrine         | Book V           | Advisory research / topology            |
| Token containment rule | Book III         | One-way membrane enforcement            |
| Token AI-agent warning | Book 0           | Prevents misinterpretation              |
| Token replay exclusion | Book IV          | Certification must not depend on tokens |
| Token schema           | Book V appendix  | Implementation support                  |
| Token failure tests    | Book IV + Book V | Proves no Lane-2 bleed-through          |

---

## 4. Token Classes

### RT — Reference Token

```text
RT = Reference Token

Purpose:
- Points to already-preserved CRAM records.
- Creates a non-authoritative advisory reference.
- Helps SoSo and JEDI locate continuity anchors.

Allowed:
- Reference CRAM object IDs.
- Reference timestamps.
- Reference authority hashes.
- Reference campaign runs.

Forbidden:
- Copy CRAM payloads into MRAM-S as substitute evidence.
- Modify CRAM references.
- Claim truth status.
- Issue PASS/DROP.
```

### VDT — Virtual Drift Token

```text
VDT = Virtual Drift Token

Purpose:
- Tracks advisory drift pressure.
- Tracks instability around observations.
- Helps SoSo identify recurring uncertainty.

Allowed:
- Track repeated instability patterns.
- Track advisory contradiction.
- Track provenance weakness.
- Track measurement instability.

Forbidden:
- Change thresholds.
- Change PSEUDO behavior.
- Declare failure as authority.
- Close gaps.
```

### VLT — Virtual Longevity Token

```text
VLT = Virtual Longevity Token

Purpose:
- Tracks long-term continuity.
- Helps Living CRAM expose durable operational history.
- Supports campaign planning and system-health analysis.

Allowed:
- Track repeated object presence.
- Track continuity across runs.
- Track long-term advisory recurrence.
- Track token aging.

Forbidden:
- Become proof.
- Become evidence.
- Become replay requirement.
- Become PASS/DROP influence.
```

### AVLT — Archived Virtual Longevity Token

```text
AVLT = Archived Virtual Longevity Token

Purpose:
- Preserves retired VLT history inside MRAM-S.
- Keeps advisory continuity without active runtime influence.

Allowed:
- Store old advisory topology.
- Support later research review.
- Support non-authoritative historical analysis.

Forbidden:
- Reactivate automatically.
- Influence active verdict flow.
- Affect certification.
```

---

## 5. Token Role in Living CRAM

```text
Living CRAM remembers through CRAM.

Tokens observe around that memory.

CRAM is truth preservation.

Tokens are advisory topology.

CRAM participates in replay.

Tokens do not participate in replay.

CRAM is Lane 1.

Tokens are Lane 2.

CRAM is authoritative.

Tokens are descriptive.

Living CRAM may expose continuity.

Tokens may map continuity.

Only PSEUDO-A may decide.
```

---

## 6. Token Operational Chain

```text
CRAM preserves event.

PSEUDO adjudicates event.

Authority audit records event.

MRAM-S may receive advisory reference.

RT may anchor the CRAM reference.

VDT may observe drift pressure.

VLT may observe long-term recurrence.

SoSo may inspect token instability.

JEDI may use token topology for research planning.

Certification ignores token conclusions.

Replay ignores token conclusions.

Lane 1 remains unchanged.
```

---

## 7. Token Storage Boundary

```text
Allowed write path:

/var/ph6/mram-s/tokens/

Allowed token outputs:
- token JSON
- token audit sidecar
- token rebuild receipt
- token topology map
- token instability report
- token archive packet

Forbidden write paths:
- /var/ph6/cram-0/
- /var/ph6/cram-a/
- /var/ph6/cram-r/
- /var/ph6/audit/authority/
- /var/ph6/export/authority/
```

---

## 8. Token JSON Schema

```json
{
  "schema": "ph6.tok.token.v1",
  "token_id": "tok_000000",
  "token_type": "RT | VDT | VLT | AVLT",
  "authority": "ZERO",
  "advisory_only": true,
  "replay_dependency": false,
  "evidence_packet_member": false,
  "lane": "Lane-2",
  "storage_root": "/var/ph6/mram-s/tokens/",
  "cram_reference": {
    "object_id": "string",
    "authority_hash": "string",
    "cram_tier": "CRAM-0 | CRAM-A | CRAM-R"
  },
  "continuity": {
    "sequence": 0,
    "previous_token_hash": "GENESIS",
    "motion_fraction_fp": "0.0000",
    "drift_pressure_fp": "0.0000"
  },
  "constraints": {
    "may_write_cram": false,
    "may_modify_evidence": false,
    "may_affect_pseudo": false,
    "may_issue_verdict": false,
    "may_block_rsync": false
  },
  "created_utc": "YYYY-MM-DDTHH:MM:SSZ",
  "token_hash": "blake2b-256"
}
```

---

## 9. Token DRIFT_FAIL Additions

Add these to the master Living CRAM DRIFT_FAIL list:

```text
Declare DRIFT_FAIL if:

A token issues PASS.

A token issues DROP.

A token modifies a CRAM object.

A token modifies an EvidencePacket.

A token changes PSEUDO thresholds.

A token becomes required for replay.

A token becomes required for certification.

A token blocks RSYNC.

A token writes outside MRAM-S.

A token copies evidence payloads as substitute truth.

A token promotes advisory continuity into authority.

A token becomes a hidden dependency for SoSo, JEDI, or AI verdict-like behavior.
```

---

## 10. Token Certification Rule

```text
Tokens may be tested.

Tokens may be audited.

Tokens may be deterministically rebuilt.

Tokens may be compared across runs.

Tokens may produce advisory receipts.

But token success does not certify PH6.

Token failure does not invalidate CRAM truth.

Token mismatch is an advisory defect, not an authority defect,
unless the mismatch proves Lane-2 contamination of Lane 1.
```

---

## 11. Clean AI-Agent Control Seal

```text
PH6 / TOKENS — AI AGENT CONTROL SEAL

Tokens are Lane-2 advisory memory objects.

Tokens live only in MRAM-S.

Tokens have Authority ZERO.

Tokens may describe continuity, drift, recurrence, topology, and advisory instability.

Tokens may help SoSo observe.

Tokens may help JEDI plan research.

Tokens may help Book V explore safely.

Tokens may not write CRAM.

Tokens may not touch PSEUDO.

Tokens may not issue PASS or DROP.

Tokens may not modify EvidencePackets.

Tokens may not close Gap Register items.

Tokens may not certify production readiness.

Tokens may not block RSYNC.

Tokens may not become replay dependencies.

Tokens may not become authority through repetition, usefulness,
AI interpretation, or campaign success.

Correct rule:

CRAM preserves.
PSEUDO decides.
Certification proves.
Tokens describe.
SoSo observes.
JEDI coordinates.
Book V explores.
Authority remains Lane 1 only.
```

---

## 12. Strongest Final Wording

```text
Tokens are not truth.

Tokens are memory-shaped advisory topology around truth.

They may remember patterns.

They may expose continuity.

They may reveal instability.

They may assist SoSo and JEDI.

They may never decide.

They may never become replay law.

They may never become certification law.

They may never cross from MRAM-S into CRAM authority.

Tokens are useful because they are contained.
```
