# PH6 Test History Matrix v1.0

```text
Document ID:  PH6-TEST-HISTORY-MATRIX-1.0
Status:       PROPOSED (Lane-2 output — awaiting operator ratification)
Authority:    NONE. This document is an evidence INDEX. It adjudicates nothing.
              It does not itself close any gap, campaign, or STOP-SHIP item.
Prepared by:  claude-code-lane2
Prepared:     2026-09-12
Scope:        PH6 Raspberry Pi 5 subsystem, as reflected by files physically
              present in this repository at commit cafcc3737c (branch
              claude/ph6-test-history-matrix-7o690d). No repository, hardware,
              or runtime outside this checkout was inspected.
```

## 0. Purpose and boundary

This matrix is **the authoritative test-status INDEX**, not an authority source
for PH6 verdicts. It records what was tested, what evidence exists, and what
each source document itself claims. It does not re-adjudicate PASS/DROP
verdicts, does not upgrade any status beyond what its cited source states, and
does not close any Gap Register entry. Closure of OI-01, OI-03, or any
campaign remains governed exclusively by `PH6_SOURCE/GAP_REGISTER_v3.0.md`
and by the human-authorization rules stated there.

**Method:** every row below is drawn directly from a file in this repository,
with an explicit citation. No status, hash, or frame count in this document
was inferred, estimated, or carried over from conversational narrative. Where
a prior narrative summary (including one supplied by the operator during this
session, sourced from a separate AI conversation) conflicts with the files in
this repository, the repository file is treated as authoritative and the
conflict is flagged in §5, not silently resolved.

## 1. Field legend

| Field | Values | Meaning |
|---|---|---|
| **Documented Status** | verbatim or near-verbatim from source | The status the source file itself asserts — never upgraded |
| **Evidence Class** | Observation / Measurement / Validation / Replay / Recovery / Governance | Observation = raw sensor capture; Measurement = derived metric against a target/spec; Validation = deterministic logic/software correctness; Replay = re-execution reproducing a prior result; Recovery = fault/crash/failure-injection behavior; Governance = scan/attestation/declaration of compliance |
| **Artifact Integrity** | Hash verified / Sidecar verified / Missing / Unresolved | Hash verified = a BLAKE2b/SHA256 digest is present and matches; Sidecar verified = `.blake2b` marker presence/count checked; Missing = no artifact/hash found in source; Unresolved = artifact referenced but integrity check itself is pending/not run |
| **Reproduction Requirement** | None / Repeat after drift / Repeat because incomplete / Repeat because failed | None = closed finding, no further run planned; Repeat after drift = stable pass, re-run only if code/config changes; Repeat because incomplete = scope not yet fully executed; Repeat because failed = the run itself did not meet its own pass criteria |
| **Evidence State** (§4 only) | CANONICAL / RATIFIED / VERIFIED / RECORDED / SPECIFIED / PROPOSED / INFERRED / UNKNOWN / SUPERSEDED | Per PH6 second-order review doctrine — never collapsed |

---

## 2. STOP-SHIP gates (OI-01, OI-03)

| ID | Item | Documented Status | Evidence Class | Artifact Integrity | Reproduction Requirement | Latest Evidence Date | Source(s) |
|---|---|---|---|---|---|---|---|
| OI-01 | Hailo AI inference wiring | **DESCOPED** by operator decision — `closure_decision: "DESCOPED"`, `closed: true`, `production_clearance_impact: "NONE — descoped by operator decision"` | Governance | Missing (no hardware artifact expected — scope excluded) | None (excluded from current scope; would require a *new* evidence campaign + operator declaration to bring back in scope) | 2026-05-18 | `PH6_SOURCE/GOVERNANCE/closure_status.json` (campaigns.OI-01), `production_clearance_declaration.json`, `PH6_PRODUCTION_CLEARANCE_SEAL_2026-05-18.md` |
| OI-03A/B/C | Cross-node rsync export + hash-continuity to second node (jackjack, 192.168.254.189) at 300/1200/3600 frames | **CLOSED** (bounded scope only) — `closure_decision: "CLOSED"`, artifact_hash_check / cram_chain_check / departure_arrival_check all PASS, 0 mismatches | Measurement + Replay | Hash verified (0 mismatches across all three frame counts) | None *for the bounded scope declared* (export/hash-continuity only) | 2026-05-18 | `closure_status.json` (campaigns.OI-03A/B/C), `production_clearance_declaration.json` §evidence_basis |
| OI-03 (full) | Real network-mode, live two-Pi PASS/DROP-authority transfer | **NOT CLOSED** — explicitly "remains STOP-SHIP until remote test passes"; all three phase receipts show `remote_mode:false` / `PASS_LOCAL`; `distributed_authority_proven: false`, `multi_writer_cram_proven: false` | Measurement | Unresolved (local-mode result_set_hash_match true, but no remote-mode artifact exists) | Repeat because incomplete | 2026-06-17 (still cited as open in ER-1E) | `PH6_SOURCE/VALIDATION/campaign_matrix.json` (EVC-03, open_stop_ship_gates), `GOVERNANCE/evidence_campaign_matrix.json` (OI-03 entry), `EVIDENCE_CAMPAIGNS/RECEIPTS/OI03_PHASE1-3_*.json`, `DEPLOYMENT/PH6-er1e-real-multivlt-artifact-campaign-20260617.md`, `PH6-er1d-lite-proof-20260617.md` |

**Reconciliation note:** OI-01 and OI-03 are not in a single state. OI-01 is
*descoped* (removed from required scope, not resolved). OI-03 has a narrow,
genuinely evidenced closure (bounded export/hash-continuity between two
physical nodes) dated 2026-05-18, but the broader claim — a live two-Pi
PASS/DROP-authority transfer — remains open as of the most recent dated
evidence in the repository (2026-06-17). Both the operator's own
`production_clearance_declaration.json` and the later ER-1D/ER-1E reports
agree on this: OI-03 "remains open" for anything beyond the bounded scope.

---

## 3. Evidence Campaigns (C01–C05) and GAP-16

| ID | Item | Documented Status | Evidence Class | Artifact Integrity | Reproduction Requirement | Latest Evidence Date | Source(s) |
|---|---|---|---|---|---|---|---|
| C01 | 300-frame environmental coherence campaign | **OPEN** — `closure_status: "OPEN"` in campaign matrix; campaign doc header `Status: OPEN`; no `C01_CLOSURE_RECEIPT.md` exists; pre-C01 spine proof explicitly lists 6 remaining closure items | Validation | Missing (closure receipt not created) | Repeat because incomplete | 2026-05-15 (last touched, still open) | `EVIDENCE_CAMPAIGNS/CAMPAIGN_01_300_FRAME_COHERENCE.md`, `GOVERNANCE/evidence_campaign_matrix.json`, `RECEIPTS/PRE_C01_CRAM_SPINE_PROOF_20260515.md` |
| — | Sub-proof: CRAM spine (synthetic packets, 300 frames, 206 PASS / 94 DROP) | PASS (of the sub-proof only) — explicitly "does NOT prove" full C01 (lists TOK not wired, wrong PSEUDO metrics used, synthetic not real frames, missing entry point) | Validation | Hash verified (per-run) | None for this sub-proof; Repeat because incomplete for full C01 | 2026-05-15 | `RECEIPTS/PRE_C01_CRAM_SPINE_PROOF_20260515.md` |
| — | Sub-proof: TOK_LEAK_001 isolation (TOK-on vs TOK-off, 300 packets) | PASS — identical result_set_hash across both runs, both dated | Replay | Hash verified (`a80b1463f1729c5c...`) | None (isolation proof stands); does not by itself close C01 | 2026-05-16 | `RECEIPTS/TOK_LEAK_001_20260515T111936Z.json`, `TOK_LEAK_001_20260516T083748Z.json` |
| — | Sub-proof: ESP32-CAM C01 ingest-only (300 frames) + C01E endurance (441 frames / 300.7s) | PASS / PASS — 0 failed, 0 retries; governance drift PASS 0C/0H/0W | Observation | Hash verified (BLAKE2b + SHA256 given for sampled frames) | None for this hardware sub-run; does not close full multi-component C01 spec | 2026-05-15 | `EVIDENCE_CAMPAIGNS/PH6-ESP32CAM-GOVERNANCE-OPERATIONAL-TEST-20260515.md` |
| C01B | Advisory expansion (swarm) | **OPEN**, explicitly blocked: "C01 baseline must be CLOSED first" | Validation | Missing | Repeat because incomplete (gated on C01) | 2026-05-14 | `EVIDENCE_CAMPAIGNS/CAMPAIGN_01B_ADVISORY_EXPANSION.md` |
| C02 | Real Pi-to-Pi transfer (would satisfy full OI-03) | **OPEN** — "AI must not mark OI-03 CLOSED. Human authorization required."; no `C02_CLOSURE_RECEIPT.md` | Measurement | Missing | Repeat because incomplete | 2026-06-17 (still cited open) | `EVIDENCE_CAMPAIGNS/CAMPAIGN_02_PI_TO_PI_TRANSFER.md`, ER-1D/ER-1E reports |
| C03 | Resource/RSYNC pressure | **OPEN** | Measurement | Missing | Repeat because incomplete | 2026-05-14 | `EVIDENCE_CAMPAIGNS/CAMPAIGN_03_RESOURCE_PRESSURE_RSYNC.md` |
| C04 | Crash recovery (hardware) | **OPEN**. Related EVC-01 continuity test is `SIMULATION_PASS` only — explicitly not a hardware substitute | Recovery | Missing (hardware); simulated sub-test hash not confirmed in extraction | Repeat because incomplete | 2026-05-14 | `EVIDENCE_CAMPAIGNS/CAMPAIGN_04_CRASH_RECOVERY.md`, `VALIDATION/campaign_matrix.json` (EVC-01) |
| C05 | Replay parity (full campaign) | **OPEN** — Lane-2 dependency table (SoSo, TOK, MRAM-S, SSMT) still shows `Result: TBD` for every row | Replay | Missing | Repeat because incomplete | 2026-05-14 | `EVIDENCE_CAMPAIGNS/CAMPAIGN_05_REPLAY_PARITY.md` |
| GAP-16A | USB AV contention, video degradation under load | **CLOSED / STABLE-CONFIRMED** — reproducible and measurable; "no further action required unless hardware changes" | Observation | Hash verified (per-frame BLAKE2b in av_contention/gap16_r2 reports) | None (characterized, not remediated — it is a documented hardware limitation) | 2026-05-15 | `EVIDENCE_CAMPAIGNS/GAPS/GAP-16-MICRODIA-AUDIO-VIDEO-CONTENTION.md` |
| GAP-16B | USB camera disconnect under AV load | **CLOSED / AV-LOAD-INDUCED-CONFIRMED** per the gap file itself (cable fault ruled out, no further isolation required) | Observation | Hash verified (per-frame BLAKE2b, 381 records in gap16_r2 run) | None (characterized, not remediated) | 2026-05-15 | same file as above |

**Contradiction flagged:** `PH6_SOURCE/GAP_REGISTER_v3.0.md` (v3.0, dated
2026-05-14 — the file CLAUDE.md names as the single authoritative gap
register) lists **GAP-16B as OPEN**. The GAP-16 detail file itself, dated one
day later (2026-05-15), states GAP-16B is CLOSED/CONFIRMED. The register was
never updated to reflect this. This is a live register/detail-file
inconsistency, not a resolution I am authorized to make — see §5.

---

## 4. Hardware observation/measurement runs (not campaign-gated)

| ID | Item | Documented Status | Evidence Class | Artifact Integrity | Reproduction Requirement | Latest Evidence Date | Source(s) |
|---|---|---|---|---|---|---|---|
| — | USB camera extended stability (target 7200 frames / 300s @24fps) | **FAIL** — 4087/7200 frames captured, 19.894 actual fps (outside 22–26 target), duration error −31.52%, 1 read failure | Measurement | Unresolved (no pass-path hash sequence produced; run did not meet its own criteria) | **Repeat because failed** | 2026-05-15 | `ph6_usb_camera_tests/extended_stability_20260515T094741Z.json` |
| — | USB standalone audio capture (180 chunks) | **PASS** — 180/180, 0 dropped/silent/overruns | Observation | Hash verified (per-chunk BLAKE2b-256, 180 records) | Repeat after drift | 2026-05-15 | `ph6_usb_camera_tests/audio_test_20260515T095839Z/audio_test_report.json` |
| — | ESP32-CAM 300-frame + 441-frame endurance | **PASS / PASS** (see C01 sub-proof row above) | Observation | Hash verified | Repeat after drift | 2026-05-15 | `EVIDENCE_CAMPAIGNS/PH6-ESP32CAM-GOVERNANCE-OPERATIONAL-TEST-20260515.md` |
| — | USB NVMe (AM8180) transport diagnostic | **PROPOSED** — technical_state GOOD, bus/driver/thermal checks PASS, but `cram_a_eligible: false`; 3 open sub-gaps (GAP-12 UUID duplication, GAP-13 FUA unverified, GAP-15 thermal blind spot); no SMART telemetry available | Measurement | Unresolved (no SMART/hash telemetry) | Repeat because incomplete | 2026-06-18 | `PH6_SOURCE/DEPLOYMENT/PH6_USB_NVME_AM8180_20260618_001.md` |
| — | Long-duration thermal/power qualification (stress-ng 300s+, checklist Phase 6) | **NOT EXECUTED** — checklist items unchecked `[ ]` | Measurement | Missing | Repeat because incomplete (has never run) | 2026-05-19 (checklist authored; still unchecked) | `PH6_SOURCE/DEPLOYMENT/DEPLOYMENT_CHECKLIST.md` |
| — | Distributed cluster / Zero 2W sentinel first test (checklist Phase 5) | **NOT EXECUTED** — checklist items unchecked `[ ]` | Measurement | Missing | Repeat because incomplete | 2026-05-19 | `PH6_SOURCE/DEPLOYMENT/DEPLOYMENT_CHECKLIST.md` |

**Reconciliation note:** the operator-supplied reconstruction narrative
listed "USB calibration repeatability: Verified." No repository file supports
an unqualified "Verified" for USB camera endurance — the one executed
full-duration run on record (2026-05-15) has a documented **FAIL** verdict,
and no later successful full-duration re-run exists in this repository. The
12,000-frame USB camera test under `PH6_SOURCE/TESTS/USB_CAMERA_12000/` is
architecture/specification documentation only (a README describing a planned
6-phase test); it contains no executed run results.

---

## 5. Software validation suites (deterministic logic, non-hardware)

| ID | Item | Documented Status | Evidence Class | Artifact Integrity | Reproduction Requirement | Latest Evidence Date | Source(s) |
|---|---|---|---|---|---|---|---|
| — | CRAM-PU-LIVE-1.0 full suite (ssmt 43 + cram_pu 37 + frame_filter 20) | **PASS** 100/100 | Validation | Hash verified (commit 95327f1; sidecar inventory present) | Repeat after drift | 2026-05-06 | `PH6_FULL_PRODUCTION_CLEARANCE/full_test_suite.json` |
| — | HRG9 closeout full suite (ssmt 43 + cram_pu 37) | **PASS** 80/80; FI 8/8 (Lane-1) + 13/13 (Lane-2) | Validation + Recovery (simulated) | Sidecar verified (1400/1400 `.blake2b` markers, 0 missing) | Repeat after drift | 2026-05-06 | `PH6_HRG9_CLOSEOUT/FULL_TEST_SUITE/combined_results.json`, `PH6_SOURCE/HRG9_CLOSURE/hrg9_final_summary.md` |
| — | Lane separation boundary proof (5 proofs, e.g. SSMT cannot write Lane-1 paths, verdict never SSMT-derived) | **PASS** | Validation | N/A (logic assertions, no hash artifact) | Repeat after drift | 2026-05-06 | `PH6_HRG9_CLOSEOUT/LANE_SEPARATION/boundary_proof.json` |
| — | Internal system smoke harness (20 checks: forbidden-field guard, atomic-write contract, CRAM_PASS authority hash) | **PASS** 20/20, hash `014652358db408cf...` reproduced (matches CLAUDE.md known-good anchor) | Validation + Replay | Hash verified | Repeat after drift | 2026-05-28 (×2 runs, same hash both times) | `PH6_SOURCE/DEPLOYMENT/PH6_INTERNAL_SYSTEM_TEST_20260528T073318Z.md`, `...T082914Z.md` |
| — | Replay parity receipt (independent replay vs. original) | **PASS** — hashes identical, `blake2b256:3487aff9...`, SoSo advisory state confirmed not used in replay | Replay | Hash verified | Repeat after drift | 2026-05-06 | `PH6_SOURCE/HRG9_CLOSURE/hrg9_replay_parity_receipt.json` |
| — | ER-1A/1B proof suite | **PASS** 17/17 (8/8 + 9/9) | Validation | N/A | Repeat after drift | 2026-06-16 | `PH6_SOURCE/DEPLOYMENT/PH6-broad-integration-baseline-20260616.md` |
| — | `ph6_l2_expand` full suite | **PASS** 63/63 | Validation | N/A | Repeat after drift | 2026-06-16 | same |
| — | `ph6/tok` suite | **PASS** 12/12 | Validation | N/A | Repeat after drift | 2026-06-16 | same |
| — | ER-1E multi-VLT artifact campaign (5 classes × 3 cycles, 181 tokens) | **PASS** 12/12; full suite 95/95 (l2_expand + tok) | Validation + Replay | Hash verified (sha256 manifest) | Repeat after drift | 2026-06-17 | `PH6_SOURCE/DEPLOYMENT/PH6-er1e-real-multivlt-artifact-campaign-20260617.md` |
| — | ER-1D-LITE token lifecycle replay proof | **PASS** (8 named guarantees, CONFIRMED) — explicitly states it does NOT prove live hardware, Pi-to-Pi, or C01 | Validation + Replay | N/A stated in extraction | Repeat after drift | 2026-06-17 | `PH6_SOURCE/DEPLOYMENT/PH6-er1d-lite-proof-20260617.md` |

All rows in this section are **software/logic evidence**. None constitute
hardware validation of camera, USB, power, thermal, or network-transport
behavior — that distinction must not be collapsed (per PASS 3.5/PASS 10
doctrine: "tested ≠ verified" across evidence classes).

---

## 6. Closure packets / governance declarations (roll-up attestations)

| ID | Item | Documented Status | Evidence Class | Artifact Integrity | Reproduction Requirement | Latest Evidence Date | Source(s) |
|---|---|---|---|---|---|---|---|
| — | CRAM-PU-LIVE-1.0 closeout | `CLOSED_AS_REPRODUCIBLE_LIVE_AUTHORITY_NODE_HARNESS`; explicitly `production_clearance: false`, `hrg9_clearance: false` | Governance | Hash verified (commit-pinned) | Repeat after drift | 2026-05-06 | `PH6_CLOSEOUT_PACKET/CRAM_PU_LIVE_1_0/closeout_attestation.json` |
| — | HRG9 closeout | `CLOSED_AS_HRG9_STYLE_EVIDENCE_PACKET`; `production_clearance: false`; **HRG9 gap itself CLOSED, immutable** (per Gap Register — do not reopen) | Governance | Sidecar verified | None (HRG9 is closed and immutable) | 2026-05-06 | `PH6_HRG9_CLOSEOUT/hrg9_attestation.json`, `PH6_SOURCE/HRG9_CLOSURE/hrg9_final_summary.md` |
| — | Full Production Clearance (10-gate proof layer) | `CLEARED_WITH_KNOWN_OPEN_ITEMS`; `full_production_clearance: false`; explicit `next_gate: "OI-01_HAILO_WIRING + OI-03_TWO_PI_LIVE_TRANSFER"` | Governance | N/A | Repeat because incomplete (superseded in scope by 2026-05-18 declaration below) | 2026-05-06 | `PH6_FULL_PRODUCTION_CLEARANCE/clearance_attestation.json`, `open_items.json` |
| — | Production Clearance Declaration `PH6-PROD-CLEAR-2026-05-18-001` | `production_clearance: "DECLARED"` — **bounded**: single-node instrument cleared; cross-node rsync to jackjack cleared *only* as export/hash-continuity; explicitly **not cleared** for Hailo, multi-writer CRAM, distributed authority, remote PASS/DROP authority, remote CRAM-A write authority, Kubernetes CRAM-A storage, or any Lane-2 authority | Governance | Hash verified (evidence_basis cites 0-mismatch checks) | None *within declared bounds*; a new campaign + declaration required to extend scope | 2026-05-18 | `PH6_SOURCE/GOVERNANCE/production_clearance_declaration.json`, `PH6_PRODUCTION_CLEARANCE_SEAL_2026-05-18.md`, `closure_status.json` |

**This is the current, most authoritative operator-issued clearance
statement in the repository.** It is narrower than "production hardened" and
narrower than the operator-supplied reconstruction narrative implied: it is a
**bounded, single-node** clearance with named exclusions, not a general
production-readiness certification of the whole PH6 Pi 5 system.

---

## 7. Reconciled high-level ledger (repository evidence only)

This replaces the "Current high-level ledger" carried over from the pasted
narrative, which is not fully supported by this repository's contents. Status
values below are the most recent documented status found; PASS/FAIL/OPEN
values are quoted from source, not asserted by this document.

| Area | Repository-evidenced status | Not "Verified" (unqualified) because |
|---|---|---|
| CRAM deterministic core (software) | PASS — 100/100, 80/80 suites; hash anchor reproduces | — (software validation is solid) |
| Lane separation / authority boundary | PASS — 5/5 boundary proofs | — |
| HRG9 evidence gate | CLOSED, immutable | — |
| Replay parity (software) | PASS — hash match | Full campaign-level replay parity (C05) is still OPEN |
| ESP32-CAM ingestion (300 + 441 frames) | PASS | Scoped to ESP32-CAM only, not full C01 multi-component spec |
| USB camera audio capture | PASS (180/180) | — |
| USB camera video endurance | **FAIL** (last executed run, 2026-05-15) | Only run on record did not meet its own pass criteria; no successful re-run found |
| GAP-16 (AV contention / disconnect) | CLOSED as characterized finding | Characterization ≠ remediation — this is a documented hardware limitation, not a fix |
| 300-frame environmental campaign (C01) | OPEN | No closure receipt; sub-proofs explicitly disclaim full closure |
| Advisory expansion (C01B) | OPEN | Gated on C01 |
| Pi-to-Pi transfer (C02 / full OI-03) | OPEN | Only local-mode/bounded export-hash evidence exists |
| Resource/RSYNC pressure (C03) | OPEN | No executed evidence found |
| Crash recovery (C04) | OPEN | Only a simulated software fault-injection test exists, not hardware |
| Replay parity full campaign (C05) | OPEN | Dependency table unfilled (TBD) |
| Hailo (OI-01) | DESCOPED | Excluded from scope by operator decision, not resolved |
| Long-duration thermal/power qualification | NOT EXECUTED | Checklist items unchecked |
| Production certification (unbounded) | NOT DECLARED | Only a bounded, single-node clearance (2026-05-18) exists |

**Recommended project status** (as evidenced, for operator ratification):

`PH6 Raspberry Pi 5 — SOFTWARE LANE-1/LANE-2 ARCHITECTURE VALIDATED (100% of
executed unit/replay suites PASS); HARDWARE EVIDENCE CAMPAIGNS PARTIALLY
CLOSED (bounded single-node clearance DECLARED 2026-05-18); ENVIRONMENTAL/
ENDURANCE CAMPAIGNS (C01–C05) OPEN; OI-01 DESCOPED; OI-03 OPEN BEYOND BOUNDED
SCOPE.`

This is a narrower — and more precisely evidenced — status than either "PH6
Raspberry Pi 5 — ENGINEERING VALIDATED / PRODUCTION HARDENING IN PROGRESS"
(the operator-supplied reconstruction's proposed freeze) or "prototype." The
software/architecture layer supports the stronger framing; the hardware
endurance/environmental layer does not yet, per the files in this repository.

---

## 8. Open Issue Register (this pass)

| ID | Class | Item | Action needed | Authority |
|---|---|---|---|---|
| THM-01 | GOVERNANCE | `GAP_REGISTER_v3.0.md` lists GAP-16B as OPEN; the GAP-16 detail file (one day newer) states it is CLOSED/CONFIRMED | Human decision: update the register or explain why it wasn't | Human only (register updates for non-STOP-SHIP items may be AI-proposed, but conflict resolution should be reviewed) |
| THM-02 | GOVERNANCE | `CLAUDE.md` "OPEN ITEMS" table (last updated 2026-06-13) does not reflect the 2026-05-18 bounded production-clearance declaration (OI-01 DESCOPED, OI-03A/B/C CLOSED-bounded) — it still shows both as flatly OPEN/STOP-SHIP with no scope nuance | Human decision: reconcile CLAUDE.md against `production_clearance_declaration.json` | Human only |
| THM-03 | ENGINEERING | No successful full-duration USB camera endurance run exists after the 2026-05-15 FAIL; no re-run evidence found | Schedule/execute a re-run under EVIDENCE_CAMPAIGNS discipline | Human / campaign closure |
| THM-04 | VERIFICATION | Long-duration thermal/power qualification (`DEPLOYMENT_CHECKLIST.md` Phase 6) has never been executed | Execute and record | Human |
| THM-05 | VERIFICATION | C04 crash recovery has only a simulated (software) fault-injection proxy (`fi_01_power_loss_mid_commit.py`); no physical power-loss/crash-recovery hardware evidence exists | Execute Campaign 04 on hardware | Human / campaign closure |
| THM-06 | INFORMATIONAL | The operator-supplied reconstruction narrative for this task referenced an attachment ("Pasted text(135).txt") that was not actually present in this session or repository | None — flagged for transparency; this matrix was built from repository files instead, per the operator's own fallback instruction | — |

---

## 9. Evidence-state register (selected key claims)

| Claim | Evidence State |
|---|---|
| "HRG9 is CLOSED, immutable" | CANONICAL (Gap Register + closeout packet agree; do not reopen) |
| "OI-01 is DESCOPED" | RATIFIED (explicit operator declaration, 2026-05-18, named signatory) |
| "OI-03A/B/C bounded closure" | RATIFIED (same declaration) |
| "OI-03 full live transfer" | RECORDED as OPEN (multiple dated sources agree; not yet VERIFIED closed) |
| "C01–C05 OPEN" | RECORDED (campaign docs + matrix agree) |
| "GAP-16A/B CLOSED as characterized" | RECORDED (source file states this; not independently re-verified in this pass) |
| "USB camera endurance FAIL" | RECORDED (single executed run; no superseding evidence found) |
| "Software suites 100/100, 80/80, 95/95, 63/63, 17/17, 12/12 PASS" | RECORDED (JSON/MD result files read directly) |
| "PH6 is production-hardened / engineering-validated" (operator's proposed freeze) | Not adopted as-is — narrowed to the §7 recommended status; the stronger framing is a PROPOSED characterization, not something this repository's files fully support at the hardware/environmental layer |

---

## 10. AI Contribution Signature

```json
{"proposed_by":"claude-code-lane2","proposed_at_utc":"2026-09-12T00:00:00Z","api_call_log_ref":"ph6-test-history-matrix-v1.0-20260912","ratified_by":null}
```

**This document is PROPOSED.** It requires operator (Jack) review and
ratification before being treated as the canonical test-status index. No
status in this document authorizes closing any Gap Register entry, campaign,
or STOP-SHIP item — closure remains governed exclusively by
`PH6_SOURCE/GAP_REGISTER_v3.0.md`.
