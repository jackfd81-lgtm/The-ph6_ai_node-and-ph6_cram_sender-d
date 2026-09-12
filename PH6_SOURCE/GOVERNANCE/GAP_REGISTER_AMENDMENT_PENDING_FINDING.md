# Finding: GAP_REGISTER_v3.0.md Not Amended Despite Signed Closure Evidence

```text
Document ID: PH6-GOV-FINDING-GAPREG-AMEND-1
Status:      PROPOSED (Lane-2 output — awaiting operator review)
Authority:   NONE. This document closes nothing and amends nothing.
             It does not modify GAP_REGISTER_v3.0.md or CLAUDE.md.
Prepared by: claude-code-lane2
Prepared:    2026-09-12
Severity:    GOVERNANCE (documentation-authority drift, not a technical defect)
```

## Summary

`PH6_SOURCE/GAP_REGISTER_v3.0.md` declares itself, in its own header:

> "Single authoritative register for all open, closed, and deferred gaps."

Its STOP-SHIP rule (for OI-01 and OI-03) states:

> "Closure requires: hardware run + artifact receipt + human authorization."

and its register table requires a `Closure File / Commit` value once a gap
closes. As of this finding, `GAP_REGISTER_v3.0.md` (created/dated
2026-05-14, never edited since per its own version history table) still
lists:

| Gap ID | Status | STOP-SHIP? | Closure File / Commit |
|---|---|---|---|
| OI-01 | OPEN | YES | TBD |
| OI-03 | OPEN | YES | TBD |

## The conflicting evidence

`PH6_SOURCE/GOVERNANCE/closure_status.json`, `last_updated_utc:
"2026-05-18T08:50:40Z"` (four days after the register's own date), contains:

- `campaigns.OI-01`: `"state": "DESCOPED"`, `"closure_decision":
  "DESCOPED"`, `"reviewer": "Jack Disla"`, `"reviewed_at_utc":
  "2026-05-18T08:50:40Z"`.
- `campaigns.OI-03A"/"OI-03B"/"OI-03C"`: `"state": "CLOSED"`,
  `"closure_decision": "CLOSED"`, `"reviewer": "Jack Disla"`,
  `"reviewed_at_utc": "2026-05-18T08:50:40Z"`, each with an explicit
  0-mismatch `artifact_hash_check` (1214 / 4814 / 14414 files respectively)
  and 0-mismatch `cram_chain_check` / `departure_arrival_check`.

`PH6_SOURCE/GOVERNANCE/production_clearance_declaration.json`
(`declaration_id: "PH6-PROD-CLEAR-2026-05-18-001"`, `declared_by: "Jack
Disla"`) independently corroborates the same closures and adds an explicit
operator statement: *"OI-01 is descoped. Distributed authority is not
proven and not claimed."*

By the register's own stated evidentiary bar (hardware run — the OI-03A/B/C
runs did move real capture data between two named nodes; artifact receipt —
present as `closure_status.json`; human authorization — present as
`reviewer: "Jack Disla"`), this looks like it satisfies closure for OI-01
(as descoped) and OI-03A/B/C (bounded scope only — full live remote-mode
transfer remains genuinely open, see below). **But nobody has amended the
register itself.** The `Closure File / Commit` column was never filled in,
and the `Status` column was never updated.

## Why this is not the same as PR #13's THM-01/THM-02

PR #13 (`PH6-TEST-HISTORY-MATRIX-v1.0-20260912.md`) flags two adjacent but
distinct staleness problems:

- THM-01: the GAP-16 detail file vs. the register's GAP-16B row.
- THM-02: `CLAUDE.md`'s OPEN ITEMS table vs. the 2026-05-18 declaration.

Neither THM item flags that **the register itself** — not just CLAUDE.md,
which merely mirrors the register — carries the same staleness for its two
highest-severity (STOP-SHIP) rows. This is a distinct, higher-severity
instance of the same failure mode, because the register is the document
every other artifact (including CLAUDE.md) is supposed to defer to.

## What this finding does NOT do

- It does not mark OI-01 or OI-03 CLOSED, DESCOPED, or anything else.
- It does not edit `GAP_REGISTER_v3.0.md`.
- It does not assert that OI-03 (full live remote-mode PASS/DROP-authority
  transfer) is closed — the repository evidence is explicit that it is not:
  `EVIDENCE_CAMPAIGNS/RECEIPTS/OI03_PHASE3_PI_TO_PI_20260516T084757Z.json`
  records `"remote_mode": false`, `"status": "PASS_LOCAL"`, and
  `GOVERNANCE/evidence_campaign_matrix.json`'s OI-03 entry itself states
  `"distributed_authority_proven": false, "multi_writer_cram_proven":
  false`. The finding here is narrower and purely procedural: the
  register's bookkeeping for the *bounded* OI-03A/B/C closure and the OI-01
  descope has not been kept in sync with the signed evidence that already
  exists.

## Recommended human decision (per GAP_REGISTER_v3.0.md's own Update Protocol)

`GAP_REGISTER_v3.0.md` states: *"For STOP-SHIP gaps (OI-01, OI-03): Human
authorization required. AI must not mark these CLOSED under any
circumstances."* Consistent with that rule, this finding recommends — but
does not perform — one of the following, at the operator's discretion:

1. Amend the register's OI-01 row to `DESCOPED`, citing
   `closure_status.json` and `production_clearance_declaration.json` as the
   `Closure File / Commit`, OR
2. Split the OI-03 row into a bounded sub-row (`CLOSED`, citing the same
   evidence) and a full-scope sub-row (remains `OPEN`, STOP-SHIP), mirroring
   the distinction PR #13's matrix already draws, OR
3. Explicitly state, in the register or elsewhere, why the register was
   intentionally left unamended (e.g., if the operator considers
   `closure_status.json` insufficient authority to update the register
   without a separate, explicit register-edit step).

No option above is selected by this document. This is a report, not a
decision.

## AI Contribution Signature

```json
{"proposed_by":"claude-code-lane2","proposed_at_utc":"2026-09-12T00:00:00Z","api_call_log_ref":"gap-register-amendment-pending-finding-20260912","ratified_by":null}
```
