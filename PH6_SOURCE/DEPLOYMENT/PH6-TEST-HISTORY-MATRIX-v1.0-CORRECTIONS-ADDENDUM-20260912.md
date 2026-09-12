# PH6 Test History Matrix v1.0 — Corrections Addendum

```text
Document ID:  PH6-TEST-HISTORY-MATRIX-1.0-CORRECTIONS-1
Status:       PROPOSED (Lane-2 output — awaiting operator ratification)
Authority:    NONE. This document adjudicates nothing and closes nothing.
Target:       PR #13 — PH6-TEST-HISTORY-MATRIX-v1.0-20260912.md
              (branch claude/ph6-test-history-matrix-7o690d, commit 16be74e2fd)
Prepared by:  claude-code-lane2
Prepared:     2026-09-12
Method:       Independent re-inspection of the primary repository evidence
              cited (and not cited) by PR #13. Prior AI summaries, the
              operator's pasted narrative, and PR #13's own prose were
              treated as claims to verify, not as ground truth. Every
              finding below cites the exact file this session opened.
```

## 0. Purpose

This addendum does **not** edit `PH6-TEST-HISTORY-MATRIX-v1.0-20260912.md` in
place — that file lives on PR #13's own branch and this document does not
touch it. This is a companion correction report, to be merged into the
matrix (or kept alongside it) at the operator's discretion. It does not
close, ratify, or reopen anything.

## 1. Verified correct (no change needed)

The following PR #13 claims were independently re-checked against the cited
source files and confirmed accurate:

- OI-01 DESCOPED / OI-03A/B/C bounded-CLOSED / OI-03 full transfer NOT
  CLOSED — verified against `GOVERNANCE/closure_status.json`,
  `GOVERNANCE/production_clearance_declaration.json`, and
  `EVIDENCE_CAMPAIGNS/RECEIPTS/OI03_PHASE3_PI_TO_PI_20260516T084757Z.json`
  (`remote_mode: false`, `status: "PASS_LOCAL"`, `destination_node: "local"`).
- C01–C05 all OPEN, C01B gated on C01 — verified against campaign doc
  headers (e.g. `CAMPAIGN_01_300_FRAME_COHERENCE.md:4` reads
  `Status: OPEN` verbatim).
- GAP-16A/B CLOSED per the GAP-16 detail file, vs. GAP_REGISTER_v3.0.md
  still showing GAP-16B OPEN — verified; both documents read exactly as
  PR #13 quotes them.
- GAP-12/13/15 OPEN — verified against
  `PH6_USB_NVME_AM8180_20260618_001.md` lines 127-129, 147-151.
- USB camera `extended_stability_20260515T094741Z.json` FAIL
  (4087/7200 frames, 19.894 fps, -31.52% duration error, 1 read failure) —
  verified byte-for-byte against the source JSON.
- Software suite PASS counts — verified byte-for-byte:
  `PH6_FULL_PRODUCTION_CLEARANCE/full_test_suite.json` (100/100),
  `PH6_HRG9_CLOSEOUT/FULL_TEST_SUITE/combined_results.json` (80/80).
- Production Clearance Declaration `PH6-PROD-CLEAR-2026-05-18-001` scope
  and exclusions — verified verbatim against
  `GOVERNANCE/production_clearance_declaration.json`.

## 2. Corrections required

### 2.1 §3 is materially incomplete — an entire executed-evidence tier is missing

PR #13 §3 covers only C01–C05 and GAP-16. `GOVERNANCE/closure_status.json`
and `GOVERNANCE/evidence_campaign_matrix.json` contain the following
**already-executed** campaigns that PR #13 does not mention at all:

| ID | State (source) | Frames | Notes |
|---|---|---|---|
| C07 | CLOSED (human-reviewed, Jack Disla, 2026-05-18) | — | Governance drift scan, 0 CRITICAL/HIGH |
| C08 | PASS_PENDING_REVIEW, `closed: false` | 3600 | All 3 segments (FAST/REGULAR_CRAM/FAST_CRAM) PASS |
| C09 | PASS_PENDING_REVIEW, `closed: false` | 12,000 | 0 critical failures, replay parity PASS |
| C10 | PASS_PENDING_REVIEW, `closed: false` | 6,000 @ 15fps | PSEUDO family PASS |
| C11 | PASS_PENDING_REVIEW, `closed: false` | 6,000 @ 30fps | PSEUDO family PASS |
| C12 | PASS_PENDING_REVIEW, `closed: false` | 3,000 @ 50fps | PSEUDO family PASS |
| C13 | PASS_PENDING_REVIEW, `closed: false` | 24,000 | 7 phases, degradation intentional-by-design |
| OI-03 (evidence_campaign_matrix.json entry, distinct from C02) | PASS_PENDING_REVIEW, `closed: false` | 300/1200/3600 (levels A/B/C) | `distributed_authority_proven: false`, `multi_writer_cram_proven: false` stated explicitly in this file |
| LCC-01A/B/C | PASS_PENDING_REVIEW, `closed: false` | 300/1200/3600 | Real camera source (`/dev/video0`, `real_source: true`) |
| LIFE-CRAM-PU-1, TOK-LIFE-1, SOSO-LIFE-1 | OPEN | — | Not yet run |

**Correction:** add a §3-equivalent table for C06–C13, OI-03 (the
`evidence_campaign_matrix.json` definition), LCC-01, and the three
Life-CRAM isolation campaigns, sourced from `GOVERNANCE/closure_status.json`
and `GOVERNANCE/evidence_campaign_matrix.json`. All of these are
`PASS_PENDING_REVIEW` / `closed: false` — correctly *not* CLOSED, but their
existence and automated-PASS state should be visible to any reader relying
on PR #13 as the test-status index.

*Prior art:* `PH6_SOURCE/GOVERNANCE/open_material_register.md` (OM-01/OM-02,
2026-05-17) already flagged that C13 was once missing from
`closure_status.json` and was fixed in that audit — i.e., this repository
has a known history of campaigns silently dropping out of whichever index
is being maintained. The same failure mode recurred in PR #13.

### 2.2 THM-03 is an unsupported categorical claim

PR #13's Open Issue Register states:

> THM-03 ... "No successful full-duration USB camera endurance run exists
> after the 2026-05-15 FAIL; no re-run evidence found"

This is **false as stated**. `PH6_SOURCE/TESTS/DUAL_USB_CAMERA/` exists in
the repository and was not inspected by PR #13. It contains, among other
runs:

- `esp_cam_soso_3000/20260604_110933/json/ph6_esp_context_3000_report.json`
  — dated 2026-06-04 (after the FAIL), `elapsed_s: 310.46`, dual USB camera,
  3000 frames configured / 3000 captured on **both** cameras,
  `drop_rate: 0.0003` each, `governance_violations: 0`,
  `replay_integrity: "MATCH"`, top-level
  `"final_status": "PH6_ESP_CONTEXT_VALIDATION_PASS"`.
- `20260603_055215/dual_smoke_report.json` — same-day, camera B recorded
  `drop_count: 300/300` (100% drop), overall `"verdict": "SMOKE_HOLD"` —
  i.e. USB camera reliability past 2026-05-15 is a **mixed** picture, not a
  uniform silence.

**Caveat, so this isn't over-corrected:** the June runs use a different
harness/profile (dual-camera, 15 fps target, 3000 frames, 310s) than the
original failed test (`extended_stability`, single-camera, 24 fps target,
7200 frames, 300s target). No file in the repository shows the *original*
`extended_stability` test type re-run successfully. THM-03 should be
narrowed to that precise claim, not stated as a blanket "no re-run
evidence found."

**Correction:** rewrite THM-03 to: *"No re-run of the original
`extended_stability` 7200-frame/24fps single-camera test exists. A
different-profile dual-camera 3000-frame/310s run
(`DUAL_USB_CAMERA/esp_cam_soso_3000/20260604_110933`) did pass cleanly on
2026-06-04, and a same-tree 2026-06-03 dual-camera smoke test recorded a
100%-drop failure on one camera — USB camera reliability remains an open,
mixed picture, not a documented silence."*

### 2.3 Internal-system-test hash row overclaims precision

PR #13 §5 states the internal system test hash `014652358db408cf...`
"reproduced (matches CLAUDE.md known-good anchor)" and labels Artifact
Integrity "Hash verified." Both source reports
(`PH6_INTERNAL_SYSTEM_TEST_20260528T073318Z.md` and `...T082914Z.md`) print
**only the first 16 of the 64 hex characters** of the digest, followed by
`...`. The 16-character prefix does match the CLAUDE.md anchor
(`014652358db408cf7977c3e99ab3cceb57ee01d7bf7c265daaaead625485a2d7`), but
neither source file records the full digest, so full byte-for-byte
reproduction is not independently verifiable from these two reports alone.

**Correction:** relabel Artifact Integrity for this row as "Hash verified
(16/64-hex prefix only; full digest not printed in either source report)"
rather than an unqualified "Hash verified."

### 2.4 New governance finding not raised anywhere in PR #13

See companion document
`PH6_SOURCE/GOVERNANCE/GAP_REGISTER_AMENDMENT_PENDING_FINDING.md` for a
finding that is arguably more significant than PR #13's own THM-01/THM-02:
`GAP_REGISTER_v3.0.md` itself — the document CLAUDE.md designates as *the*
single authoritative register — has never been amended to reflect the
2026-05-18 human-signed `closure_status.json` (OI-01 DESCOPED, OI-03A/B/C
CLOSED). Its own `Closure File / Commit` column still reads `TBD` for both
STOP-SHIP rows.

### 2.5 C02 vs. the `evidence_campaign_matrix.json` "OI-03" entry

`GOVERNANCE/evidence_campaign_matrix.json` defines **two different**
campaigns against the same underlying gap (`OI-03`):

- `C02` — "OI-03 Real Pi-to-Pi Transfer Validation" — `closure_status:
  "OPEN"`, requires `transfer_manifest_source.json`,
  `transfer_manifest_destination.json`, `pre_transfer_hashes.json`,
  `post_transfer_hashes.json`, `rsync_log.txt`. **None of these artifacts
  exist anywhere in the repository.** C02 as specifically defined has
  never been executed.
- `OI-03` (a separate entry, `category: "cross_node_transfer"`) —
  `closure_status: "PASS_PENDING_REVIEW"`, backed by the OI-03A/B/C levels
  that *are* executed and hash-verified.

PR #13 treats "OI-03" as a single throughline without flagging that the
governance index itself defines two non-identical campaigns for the same
gap, one never run (C02) and one executed (OI-03/OI-03A-C). This is not a
new closure claim — it is a naming/definition ambiguity in the source
governance file itself.

**Correction:** add an Open Issue Register row noting this dual-definition
and recommending either (a) C02 be explicitly retired/superseded in favor
of the OI-03/A-C definition, or (b) the two be reconciled into one
campaign_id with one required-artifact list.

## 3. 184223 — resolved (not a matrix row, but referenced in operator narrative this session)

Repository-wide search (`rg -l "184223"`, all tracked and untracked files,
excluding `.git`) returns exactly one file trio, all under
`ph6/cram_pu/validation_runs/20260517T055650Z_C09_12000_staged_endurance/phase_C_FAST_CRAM/cram_store/`:
`cram_0000001777.json`, `cram_0000001779.json`,
`cram_0000001777.json.blake2b`. In every occurrence, "184223" is a
coincidental 6-character substring inside a 64-character BLAKE2b-256
digest (`cram_hash`/`prev_cram_hash`: `...ab18422397d994e`). `frame_id` for
these records is 1777 and 1779 — within C09's own per-phase 2000-frame
bound, not a repository-wide counter. **There is no `sequence`,
`frame_id`, `total_frames`, or cumulative-count field anywhere in the
repository whose value is 184223.** Neither "184,223 cumulative frames
tested" nor "184223 is a verified PH6 sequence value" is supported by
repository evidence; the accurate statement is that 184223 is an incidental
hash substring with no independent significance.

## AI Contribution Signature

```json
{"proposed_by":"claude-code-lane2","proposed_at_utc":"2026-09-12T00:00:00Z","api_call_log_ref":"ph6-test-history-matrix-corrections-addendum-20260912","ratified_by":null}
```

**This document is PROPOSED.** It corrects and supplements PR #13; it does
not supersede, close, or ratify anything, and does not itself become
canonical until the operator reviews both this addendum and PR #13
together.
