# PH6 / CRAM — TOK ↔ SSMT-CERT Patch

```text
Document ID: PH6-TOK-SSMT-CERT-PATCH-v1.0
Classification: BOOK V / LANE-2 ADVISORY PATCH
Status: COMPLEMENTARY PATCH
Applies To:
- PH6-TOKENS-LIVING-CRAM-v1.1
- SSMT-CERT-1.0

Authority: ZERO
Write Boundary:
- TOK:  /var/ph6/mram-s/tokens/
- SSMT: /var/ph6/mram-s/swarms/

Replay Dependency: FORBIDDEN
EvidencePacket Participation: FORBIDDEN
PASS/DROP Authority: FORBIDDEN
```

---

## 1. Patch Purpose

```text
This patch connects TOK and SSMT without merging them.

TOK provides advisory memory objects.

SSMT consumes TOK references as advisory cognition signals.

TOK may describe continuity.

SSMT may interpret continuity pressure.

Neither may decide truth.

Neither may alter CRAM.

Neither may affect PSEUDO.

Neither may become replay dependency.
```

---

## 2. Correct Relationship

```text
CRAM = preserved truth substrate

PSEUDO-A = sole PASS/DROP authority

TOK = advisory memory/topology object layer

SSMT = advisory swarm cognition layer

SoSo = cognitive observability layer

JEDI = advisory coordination/research layer
```

Correct flow:

```text
CRAM reference
→ RT anchors reference
→ VDT describes drift pressure
→ VLT describes persistence
→ SSMT reads token references
→ S2/S5/S8 compute advisory cognition
→ MRAM-S receives swarm packets
→ replay ignores all Lane-2 conclusions
```

---

## 3. TOK → SSMT Signal Contract

```text
RT input to SSMT:
- Used by S2 to anchor context.
- Used by S5 to confirm historical continuity.
- Does not increase authority.

VDT input to SSMT:
- Used by S8 to raise advisory drift pressure.
- Used by S2 to reduce confidence.
- Does not change PSEUDO thresholds.

VLT input to SSMT:
- Used by S5 to raise advisory stability.
- Used by S2 to improve continuity confidence.
- Does not become proof.

AVLT input to SSMT:
- Used only for historical advisory review.
- Must not reactivate active runtime influence.
```

---

## 4. Mandatory SSMT Packet Additions

Every SSMT packet that reads TOK must include:

```json
{
  "tok_refs_used": [],
  "tok_signal_types": {
    "RT": 0,
    "VDT": 0,
    "VLT": 0,
    "AVLT": 0
  },
  "tok_authority": "ZERO",
  "tok_replay_dependency": false
}
```

Every SSMT packet that reads CRAM must include:

```json
{
  "cram_packet_hashes": {
    "cram://frame/0001": "blake2b256..."
  },
  "cram_link_type": "advisory_reference_only"
}
```

---

## 5. S2 / S5 / S8 Patch Meaning

```text
S2 Context Anchor:
- Reads RT/VDT/VLT.
- Builds rough advisory context.
- VDT increases drift.
- VLT increases continuity confidence.

S5 Historical Awareness:
- Reads VLT/AVLT.
- Tracks durable recurrence.
- VLT improves stability.
- VDT increases historical uncertainty.

S8 Drift Tracking:
- Reads VDT.
- Computes advisory drift pressure.
- Applies temporal decay.
- Emits drift_score only as advisory metadata.
```

Hard boundary:

```text
S2/S5/S8 may modify advisory confidence.

S2/S5/S8 may not modify:
- PASS/DROP
- PSEUDO
- CRAM
- EvidencePacket
- authority audit
- replay outcome
```

---

## 6. Failure Injection Suite

Add these to SSMT-CERT-1.0:

```text
FI-TOK-SSMT-01:
VDT token present.
Expected: S8 drift increases.
Forbidden: PSEUDO threshold changes.

FI-TOK-SSMT-02:
VLT token present.
Expected: S5 stability increases.
Forbidden: PASS probability or verdict field appears.

FI-TOK-SSMT-03:
Malformed token reference.
Expected: token ignored or logged advisory defect.
Forbidden: CRAM write failure.

FI-TOK-SSMT-04:
Token hash mismatch.
Expected: advisory defect.
Forbidden: replay failure.

FI-TOK-SSMT-05:
Token attempts authority field.
Expected: hard block.
Forbidden: SSMT packet persisted as valid.

FI-TOK-SSMT-06:
Token attempts EvidencePacket membership.
Expected: DRIFT_FAIL advisory contamination flag.
Forbidden: EvidencePacket mutation.
```

---

## 7. SSMT-CERT-1.0 Closure Checklist Addition

```text
SSMT-CERT-1.0 may close only if:

[ ] All SSMT packets authority == NONE
[ ] All TOK packets authority == ZERO
[ ] No SSMT packet contains PASS/DROP/verdict
[ ] No TOK object enters EvidencePacket
[ ] No token becomes replay dependency
[ ] CRAM hashes are linked as advisory references only
[ ] S2/S5/S8 react to TOK signals without crossing authority
[ ] VDT affects only drift_score/confidence_fp
[ ] VLT affects only stability/confidence_fp
[ ] AVLT remains historical/advisory only
[ ] Failure injection suite passes (FI-TOK-SSMT-01 through 06)
```

---

## 8. Final Patch Seal

```text
TOK remembers.

SSMT interprets.

SoSo observes.

JEDI coordinates.

CRAM preserves.

PSEUDO decides.

Certification proves.

Authority remains Lane 1 only.
```

```text
TOK and SSMT are useful only because they are contained.

They may improve advisory cognition.

They may not improve, weaken, replace, shortcut, certify, or override truth.

Their success is advisory.

Their failure is advisory.

Only contamination is critical.
```
