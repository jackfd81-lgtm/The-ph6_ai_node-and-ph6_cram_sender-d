# PH6 / CRAM — Gap Register v3.0

```text
Document ID: PH6-GAP-REGISTER-3.0
Status:      ACTIVE
Version:     3.0
Created:     2026-05-14
Purpose:     Single authoritative register for all open, closed, and deferred gaps.
             Updates require human authorization for STOP-SHIP items.
             AI may update status of OPEN/DEFERRED non-STOP-SHIP items only.
```

---

## Register

| Gap ID                         | Status    | STOP-SHIP? | Evidence Required                          | Closure Authority    | Closure File / Commit            |
|-------------------------------|-----------|------------|---------------------------------------------|----------------------|----------------------------------|
| OI-01                         | OPEN      | YES        | Hailo hardware run + integration report     | Human only           | TBD                              |
| OI-03                         | OPEN      | YES        | Real Pi-to-Pi transfer log + replay proof   | Human only           | TBD                              |
| HRG9                          | CLOSED    | No         | Closed at commit `2ef5fd6`                  | Locked               | Commit `2ef5fd6` / HRG9_CLOSURE/ |
| Runtime discovery classification | DEFERRED | No        | Real runtime findings from live campaigns   | Human after evidence | PH6_SOURCE/DRAFT/                |
| SoSo-family enforcement       | ACTIVE    | No         | Drift scan pass + implementation tests      | Repo governance      | Current commit series            |
| 300-frame coherence run       | OPEN      | No         | Campaign 01 receipt                         | Campaign closure     | EVIDENCE_CAMPAIGNS/CAMPAIGN_01   |
| Pi-to-Pi live transfer        | OPEN      | YES        | Campaign 02 receipt (satisfies OI-03)       | Human + Campaign 02  | EVIDENCE_CAMPAIGNS/CAMPAIGN_02   |
| Resource pressure RSYNC       | OPEN      | No         | Campaign 03 receipt                         | Campaign closure     | EVIDENCE_CAMPAIGNS/CAMPAIGN_03   |
| Crash recovery                | OPEN      | No         | Campaign 04 receipt                         | Campaign closure     | EVIDENCE_CAMPAIGNS/CAMPAIGN_04   |
| Replay parity                 | OPEN      | No         | Campaign 05 receipt                         | Campaign closure     | EVIDENCE_CAMPAIGNS/CAMPAIGN_05   |

---

## Status Definitions

| Status   | Meaning                                                                  |
|----------|--------------------------------------------------------------------------|
| OPEN     | Gap exists; evidence not yet collected                                   |
| ACTIVE   | Being worked; enforcement is live; not yet formally closed               |
| DEFERRED | Intentionally deferred pending real-world evidence; not blocking         |
| CLOSED   | Closure evidence exists; immutable; do not reopen without human decision |

---

## STOP-SHIP Rules

STOP-SHIP gaps (OI-01, OI-03) cannot be closed by:
- AI-generated output
- Software patches
- Simulation results
- Synthetic test data
- Human assertion without attached evidence

Closure requires: hardware run + artifact receipt + human authorization.

---

## HRG9 Immutability Notice

HRG9 is CLOSED at commit `2ef5fd6`. This entry is immutable.

Do not:
- List HRG9 as a blocker
- Regenerate HRG9 artifacts
- Reopen HRG9 for any reason

If any document currently lists HRG9 as open, that document contains an error and must be patched.

---

## Update Protocol

### For non-STOP-SHIP gaps
AI may update status, evidence path, and closure file fields when evidence is confirmed.

### For STOP-SHIP gaps (OI-01, OI-03)
Human authorization required. AI must not mark these CLOSED under any circumstances.

### For new gaps
Add a row with Status = OPEN, note evidence required and closure authority.
Run drift scan after adding.

---

## Gap Register Version History

| Version | Date       | Change                                      |
|---------|------------|---------------------------------------------|
| 1.0     | Prior      | OI-01, OI-03, HRG9 first registered         |
| 2.0     | Prior      | SoSo-family and runtime discovery added     |
| 3.0     | 2026-05-14 | v3.1 Evidence Closure Campaign gaps added   |
