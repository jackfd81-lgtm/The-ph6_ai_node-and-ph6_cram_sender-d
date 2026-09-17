# PH6 Complete Test Evidence Audit v1.0

```text
Document ID:   PH6-EVIDENCE-AUDIT-1.0
Status:        PROPOSED — Lane-2 advisory work product. Authority ZERO.
Prepared by:   Claude Sonnet 5 (claude-code-lane2), read-only forensic audit
Prepared at:   2026-09-12
Audit branch:  claude/ph6-complete-test-evidence-audit-kzo1em
Repository:    jackfd81-lgtm/The-ph6_ai_node-and-ph6_cram_sender-d
Companion doc: PH6_SOURCE/DEPLOYMENT/PH6-PROTOTYPE-QUALIFICATION-MASTER-LEDGER-v1.0.md
```

```json
{"proposed_by":"claude-code-lane2","proposed_at_utc":"2026-09-12T15:24:36Z","api_call_log_ref":"session_014vqrkuWLNMvf5QAUWxKqBy","ratified_by":null}
```

This document does not close any gap, ratify any campaign, or declare production readiness. Where a closure or ratification is reported below, it is reporting a pre-existing, git-committed human decision (Jack Disla) found in repository history — not issuing a new one. PASS/DROP authority belongs to PSEUDO-A (Lane-1) only; nothing in this document is, or claims to be, a PASS/DROP verdict.

---

## 1. Executive Verdict

- **Architecture / governance documentation: EXTENSIVE but INTERNALLY CONTRADICTORY.** The repository contains a mature, well-specified governance model (campaign matrix, closure schema, gap register, authority doctrine) but three of its own governance artifacts currently disagree about the status of the two STOP-SHIP gates (see §26).
- **Software-layer qualification (Lane-1/Lane-2 boundary, CRAM commit/hash scheme, replay): CHARACTERIZED and largely VERIFIED at the code level.** 100/100 unit/integration tests recorded at HRG9 closure (2026-05-06, software-only); the BLAKE2b-256 canonical-hash scheme was independently re-derived and confirmed correct by this audit (§21); Lane-1/Lane-2 write-boundary guard clauses are real code, not self-report (§20).
- **Hardware-layer qualification: PARTIAL and NARROW.** One real USB webcam, one real Pi 5, no confirmed second physical node, no ESP32-CAM artifact, no multi-hour endurance run, no physical power-loss test, Hailo never implemented (descoped).
- **Distributed-system (OI-03) qualification: OPEN, despite a `CLOSED` governance record.** The evidence for "real Pi-to-Pi transfer" does not conclusively establish two physically separate running machines (§17).
- **Production clearance: A human (Jack Disla) DID declare a narrowly scoped production clearance** (`PH6-PROD-CLEAR-2026-05-18-001`, commit `11966dee7`) covering only single-node Lane-1 operation plus rsync-as-export. This declaration is real, git-committed, and is the current HEAD state of `closure_status.json`. It explicitly excludes Hailo, distributed authority, remote PASS/DROP, and all Lane-2 authority.
- **Can the architecture be "frozen"?** The Lane-1/CRAM authority architecture and hash scheme are stable and internally consistent — no code-level violation of the CLAUDE.md hard rules was found. The **governance documentation layer is not frozen**: CLAUDE.md itself (the primary AI-context file for this very session) still lists OI-03 as STOP-SHIP-OPEN, directly contradicting `closure_status.json`'s `CLOSED` state for OI-03A/B/C. This is an operational hazard for any future AI or human session, not just a paperwork issue.
- **Is implementation "verified"?** No. Most executed campaigns (C08–C13, TOK-1, SOSO-1, LCC-01A/B/C) sit at lifecycle state EXECUTED / VERIFIED (evidence exists, replay parity holds, hashes are internally consistent) but are **not CLOSED and not human-RATIFIED** (`reviewer: null` in `closure_status.json`). Only C07, OI-03A/B/C, and EVC-05 carry a named human reviewer and `closed: true`.
- **Suitable as an implementation source of truth?** The raw evidence artifacts (cram_store records, manifests, resource traces) are suitable and largely trustworthy at the file level. The three governance index documents (CLAUDE.md, GAP_REGISTER_v3.0.md, PH6_SOURCE/VALIDATION/campaign_matrix.json) are **not currently mutually consistent** and must be reconciled by the operator before being trusted as a single source of truth (§26, §28).

---

## 2. Repository Scope

Investigated: current branch `claude/ph6-complete-test-evidence-audit-kzo1em` (HEAD `cafcc3737c`), forked from `main`. `main` and the audit branch are identical at the point this investigation began (working tree clean, no divergent commits). **The clone is shallow**, rooted at commit `055302a54a` (2026-05-18T02:25:59-05:00) — no history before that point is locally resolvable. This means `evidence_commit` fields recorded in `closure_status.json` for campaigns generated on 2026-05-17 (C08, C09, C10, C11, C12, C13, TOK-1, SOSO-1) **cannot be drift-checked against their exact historical commit** in this environment; only campaigns from 2026-05-18 onward (OI-03A/B/C, EVC-05) could be verified against their recorded `evidence_commit`. This is a genuine tooling limitation of this audit, not a repository defect — flagged explicitly rather than silently worked around.

422,517 total files were present in the working tree; 267,227 are JSON, dominated by ~66,133 individual per-frame CRAM-A records (plus matching `.blake2b` sidecars) under `ph6/cram_pu/validation_runs/` and `ph6/cram_pu/runtime/`.

---

## 3. Evidence Rules Applied

Per the audit brief's governance model, this document maintains: documented ≠ implemented; specified ≠ implemented; implemented ≠ inspected; inspected ≠ tested; tested ≠ verified; verified ≠ closed; closed ≠ ratified; execution ≠ closure; replay ≠ new observation; AI capability ≠ authority. No claim below was promoted across these boundaries without an artifact demonstrating the transition. Where only a narrative document exists, the entry is marked NARRATIVE-ONLY / NOT FOUND, never upgraded to VERIFIED.

---

## 4. Test Taxonomy

- **SOFTWARE** — code/harness/simulation behavior, no physical hardware in the loop (or hardware behavior is incidental/mocked).
- **HW_COMPONENT** — one physical hardware component exercised (e.g. one USB webcam).
- **HW_INTEGRATION** — multiple real components operating together on one physical system.
- **HW_SYSTEM** — multiple physical nodes / genuine distributed behavior.
- **QUALIFICATION** — defined configuration + executed acceptance criteria + evidence + independent verification + formal closure/ratification.

No test in this repository currently meets the full QUALIFICATION bar. The closest are C07 (governance scan) and EVC-05 (production-clearance gate), both CLOSED with a named human reviewer, but even these are SOFTWARE-class, not hardware qualification.

---

## 5. Complete Test Inventory

See the companion **Master Qualification Ledger** for the full row-level table (Test ID / Campaign / Requirement / Date / Hardware / Node / Commit / Configuration / Runner / Expected / Actual / Artifact / Hash / Evidence Grade / Result / Replay / Recovery / Drift / Reproduction Command / Closure Authority / Ratification / Lifecycle State). Summary counts:

| Class | Count | Examples |
|---|---|---|
| SOFTWARE (synthetic pipeline stress) | 6 complete campaigns (C08, C09, C10, C11, C12, C13) + 4 C13 attempts total | 54,600 frames configured, 39,445 independently FILE-VERIFIED PASS records |
| HW_COMPONENT (real single camera) | 3 (LCC-01A/B/C) | 5,100 frames, 0 DROP, `/dev/video0` |
| HW_INTEGRATION | 2–3 (av_contention, gap16_r2, esp_cam_soso_3000 dual-webcam) | contention/disconnect findings, §11–13 |
| HW_SYSTEM (claimed) | 3 (OI-03A/B/C) | claimed cross-node; physical separation UNRESOLVED, §17 |
| Lane-2 isolation | 2 executed (TOK-1, SOSO-1), 2 never run (SOSO-LIFE-1, TOK-LIFE-1) | §20 |
| Governance/software gate | 2 CLOSED+RATIFIED (C07, EVC-05) | §26 |
| Specified only, never executed | C01, C02(as such), C03, C04(as such), C05(as such), C06(as such) | §12 |
| Not found at all | C14, C15, C16 | §12 |

---

## 6. Software-Core Tests

HRG9 (closed commit `2ef5fd6`, immutable per CLAUDE.md, not relitigated here) recorded 100/100 unit/integration tests passing across three suites (43 SSMT + 37 CRAM-PU + 20 frame_filter) at attestation date 2026-05-06, `evidence_head_commit af712d0`, with `full_production_clearance: false` at that time ("withheld pending OI-01 + OI-03"). This is the SOFTWARE-layer baseline: Lane-1/Lane-2 separation, audit schema compliance, RSYNC-priority-zero, and "Lane-2 cannot write CRAM" were all gate-checked here, 11 days before any hardware evidence campaign began. Class: SOFTWARE. Lifecycle: CLOSED (per CLAUDE.md, do not reopen).

This audit independently re-derived the BLAKE2b-256 canonical hash scheme (§21) and confirmed `ph6/cram_pu/schemas/canonical.py` has not changed since the 2026-05-18 campaigns closed (`git diff <evidence_commit>..HEAD -- ph6/cram_pu/schemas/canonical.py` = empty for OI-03A/B/C and EVC-05, the only campaigns whose evidence_commit resolves in this shallow clone).

---

## 7. Pi 5 Hardware Tests

Confirmed real-hardware facts (all point-in-time snapshots, not sustained monitoring): hostname `jackjack`, kernel `Linux 6.12.75+rpt-rpi-2712 aarch64` (Debian 6.12.75-1+rpt1), ~8GB RAM, `nvme0n1` 1.8T root + external `sda` 953.9G USB NVMe (AMicro AM8180 enclosure, `uas` driver), no throttling flagged (`throttled=0x0`), one `cram_pu.service` systemd unit (`Restart=on-failure`, no run log attached). No raw `/proc/cpuinfo` model/revision dump was found anywhere in the repo — Pi 5 model identity is narrative only. No `rsyncd.conf`/daemon config exists; RSYNC is invoked ad hoc per campaign script. Longest continuous measured run: 1057.6s (~17.6 min, C13). Class: HW_COMPONENT (point-in-time), not HW_SYSTEM endurance.

---

## 8. Camera Tests

Every real-camera test (av_contention, gap16_r2, LCC-01 family) requests 30fps via `cv2.CAP_PROP_FPS` and actually achieves **~19–20 fps at 640×480 MJPG**, consistently across independent scripts — a repeatable driver/hardware ceiling, not a one-off bug. LCC-01A/B/C (300/1200/3600 frames) are the cleanest real-camera evidence in the repo: 0 DROP, replay-parity PASS, hash-recomputed-consistent, `/dev/video0`. A separate dual-USB-camera test series (`DUAL_USB_CAMERA`) produced **non-reproducible, contradictory results between runs** — one run shows Camera B failing catastrophically (documented USB reset/disconnect), a later "recovered" run shows the opposite (Camera A degraded, Camera B clean) — with no reconciling document. Classify dual-camera "final report" as PROPOSED/advisory only, not closed qualification. Full per-campaign table in the Ledger §2.

---

## 9. ESP32-CAM Tests

Two unrelated things share ESP-branded naming:

1. `PH6-ESP32CAM-GOVERNANCE-OPERATIONAL-TEST-20260515.md` claims a real ESP32-CAM at `http://192.168.254.191/capture` (C01: 300/300 frames 0 failures; C01E: 5-minute endurance, 441 frames/300.671s, 0 failures) — **but the referenced run directory, manifest.json, frame_log.csv, and postrun_summary.json do not exist anywhere in this repository.** Only inline hash values typed into the markdown remain. **Classification: claim NARRATIVE-ONLY / UNVERIFIABLE from repo contents.** This is the closest match to the audit brief's "300-frame test" + "five-minute endurance" claim, and it cannot be independently verified.
2. `esp_cam_soso_3000` is actually a **dual real USB-webcam test** (3000 frames each, `/dev/video0` + `/dev/video2`) with a separate ESP_S1 advisory RSSI/telemetry sidecar (never captures images, Authority ZERO). This has real per-frame hashes and is HW_INTEGRATION-grade, but it is **not** an ESP32-CAM imaging test — the filename is misleading.

**Exact qualification scope: no independently verifiable ESP32-CAM imaging evidence exists in this repository.**

---

## 10. Audio Tests

Standalone audio (`audio_test_20260515T095839Z`): 180/180 chunks PASS, 0 dropped, 0 overruns, per-chunk BLAKE2b hashes. Clean HW_COMPONENT baseline for the microphone/ALSA path alone.

---

## 11. Audio/Video Integration

`av_contention_20260515T100841Z` (no fault injected): 1195/1195 video frames PASS but fps capped at 19.9 (requested 30), audio clean (0 overruns) — `contention_verdict: "VIDEO_DEGRADED"`. This is a genuine **resource-contention finding**, not a drop-count failure: video throughput degrades under concurrent audio capture even though no frames are lost. `gap16_r2_20260515T101657Z`: camera physically disconnected at 18.065s (351/600 frames, 30 DROP), audio simultaneously failed (`arecord_rc=1`, 5330 overruns) — thermal was stable (49.6→48.5→49.6°C, ruling out thermal cause). Separating causes as required: **HW_COMPONENT** = camera dropping off the USB bus under load (evidence toward GAP-16B, still correctly OPEN per the register's own 5-minute-isolation closure bar, not met by this 18s run); **configuration limitation** = requesting 30fps against a ~20fps device ceiling, present in every real-camera test regardless of fault; **software/instrumentation defect** = audio capture (`arecord`) only fails during the same run the camera disconnects, suggesting a shared-resource/driver interaction rather than an independent audio defect. GAP-16A (contention degrades video without dropping frames) is CONFIRMED and evidence-backed; GAP-16B (disconnect) remains correctly OPEN.

---

## 12. Recovery Tests

No test named or scoped as "C04 Crash Recovery" was ever executed. A directory literally named `evc04_...` exists but tests an unrelated gap (payload replay/metric parity, EVC-04), not crash recovery — this is a naming collision that must not be read as C04 evidence. `PH6_SOURCE/EVIDENCE_CAMPAIGNS/CAMPAIGN_04_CRASH_RECOVERY.md` remains `Status: OPEN`, consistent with no execution artifacts existing. **C04: NOT FOUND / OPEN.**

---

## 13. Power-Loss Tests

Two artifacts exist, both **in-process software simulation, not real power loss**: `PH6_CLOSEKIT/failure_injection/fi_01_power_loss_mid_commit.py` (a function that simply skips `os.replace()` — no `SIGKILL`, no real interruption) and EVC-01 (`ph6/cram_pu/evc01_crash_simulation.py`, 4 scenarios each completing in 0.001–0.003 seconds against `tempfile.mkdtemp()` stores). EVC-01's own receipt states `"authority":"VERIFY_ONLY"` and treats hardware-level power-loss testing as a separate, unaddressed follow-up. **No `kill -9` of a live process and no physical unplug test exist anywhere in this repository. Physical power-loss qualification remains OPEN.**

---

## 14. Thermal Tests

Point-in-time readings only, embedded at the start of individual test scripts: 47.4–50.7°C range across LCC-01C, GAP-16 R2, and C13 (the only runs with any thermal sampling at all). No dedicated thermal-characterization campaign (ambient sweep, sustained max-load soak, throttle-threshold test) exists.

---

## 15. Endurance Tests

The longest continuous wall-clock run in the entire repository is **C13's final attempt: 1057.6 seconds (~17.6 minutes)**, and its 24,000 "frames" are synthetic fixed-size payloads (one phase's frames are all exactly 900 bytes — physically impossible for a real camera), not real-time camera capture. C09's 12,000 frames complete in 67.6 seconds — throughput, not duration. **No run in this repository exceeds 18 minutes of continuous wall-clock duration.** A short point-in-time health observation must not be called "production endurance," and none of the above qualifies as such.

---

## 16. OI-01/Hailo

**DESCOPED**, not physically tested, not simulated, not implemented beyond placeholder comments (`ph6_ai_node/ai_node_server.py:29,36`: "Placeholder — wire Hailo inference here" / "Hailo inference not wired yet"). Descope decision: commit `a26c111c25`, "Jack Disla," `reviewed_at_utc 2026-05-18T08:50:40Z`, reason "Hailo hardware integration deferred to future hardware revision... does not block single-node or cross-node evidence certification." No Hailo SDK import, driver call, or inference code exists anywhere. This is a legitimate formal descope (human-attributed, git-committed) — it must not be confused with a completed hardware qualification, and it directly contradicts `GAP_REGISTER_v3.0.md`'s still-current `OI-01 | OPEN | STOP-SHIP: YES` row (§26).

---

## 17. OI-03 Distributed Transfer

This is the single most consequential unresolved question in the repository, and it received independent corroboration from two separate audit passes in this investigation:

**Evidence supporting a real cross-node transfer:** distinct target IP `192.168.254.189` (matches the Pi Zero 2W in CLAUDE.md's node table), `ssh_connectivity: PASS` in the prep receipt, 0 hash mismatches across 1214/4814/14414 transferred files (OI-03A/B/C respectively), full CRAM-chain and departure/arrival checks PASS, `closed: true` with named human reviewer "Jack Disla."

**Evidence casting doubt:**
- The canonical transfer tool, `ph6/cram_pu/tools/run_oi03_pi_to_pi_transfer.py`, defines two explicit code paths: `_rsync_local()` (loopback, emits status `PASS_LOCAL`, docstring: "Simulates Pi-to-Pi using local filesystem paths... network topology not tested") and `_rsync_remote()` (real SSH transfer, requires `--dest-host`, emits `PASS_REMOTE`). **Neither status marker, nor a `dest_host` field, nor an `OI03_PI_TO_PI_TRANSFER_PASS` flag appears anywhere in the actual OI-03A/B/C receipts** — the artifacts that exist do not carry the fingerprint this tool would produce in either mode.
- `oi03a_receipt.json`'s `run_dir_dest` is recorded as `/home/jack/ph6_oi03_receive/oi03a_20260518T081014Z` — a bare local-filesystem-style path, consistent with the `_rsync_local()` code branch (`dst.mkdir(...)`, plain `rsync -a --checksum <src>/ <dst>/`), not with a captured `user@host:path` remote spec that `_rsync_remote()` would produce.
- `PH6_SOURCE/06_HANDOFF/PH6-OI03-TWO-PI-TRANSFER-PREFLIGHT.md` (dated 2026-05-15, three days before the OI-03 closure) is a formal Pi-1/Pi-2 identification, SSH, and reachability checklist with **every item unchecked**, header "Status: OPEN — awaiting second Pi 5," and the explicit sentence: "Real Pi-to-Pi transfer on physical hardware has not been executed." No later commit shows this checklist completed.
- The EVC-05 human-facing review document itself states: *"Both the main Pi and the Pi Zero 2W report hostname `jackjack`. This is a node identification ambiguity that should be resolved before any multi-node authority claim."*
- OI-03A/B/C's `result_set_hash` values are **byte-identical** to LCC-01A/B/C's, and `oi03a_20260518T081014Z/` literally contains `lcc01_final_manifest.json` — confirming OI-03 transferred the *same* already-captured LCC-01 frame set rather than an independently captured-and-transferred dataset. (This is not inherently improper for a transfer-integrity test, but it means OI-03 is not additional frame-capture volume beyond LCC-01, and it removes one potential source of independent cross-node corroboration — a fresh capture timestamped and hashed only on the receiving side.)

**Verdict: the hash/file-count integrity of the transferred payload is solid and independently file-verifiable (0 mismatches). Independent proof that the source and destination were two physically separate running machines is NOT conclusively established by the repository's artifacts.** Per the audit brief's required language: **physical distributed-system qualification for OI-03 remains OPEN**, notwithstanding `closure_status.json`'s `closed: true` / `closure_decision: CLOSED` marking. This is a finding for the operator to resolve — either by producing a `PASS_REMOTE`-marked run of the canonical tool, or by confirming through direct knowledge that the 2026-05-18 transfer did in fact cross the network to the Pi Zero 2W.

---

## 18. C01–C16

Full detail in Ledger §1. Summary: **C07 is the only campaign among C01–C16 that is CLOSED and RATIFIED under its own literal ID.** C08–C13 are all EXECUTED/VERIFIED (real artifacts, replay parity PASS, internally consistent) but not CLOSED and not reviewed (`reviewer: null`). C01, C03, C04, C05, C06 exist only as specifications in `evidence_campaign_matrix.json` — their named runner modules (`ph6.governance.*`, `ph6.cert.*`, `ph6.tests.crash_recovery_campaign`, `ph6.tests.lane2_isolation_campaign`, `ph6.replay.*`) do not exist anywhere in `ph6/`. C02 (OI-03's spec-matrix identity) was executed, but under the separate ID "OI-03," never reconciled back to "C02" in the matrix. C06 (Lane-2 isolation) was likewise executed under separate IDs "TOK-1"/"SOSO-1," never reconciled back to "C06." **C14, C15, C16: NOT FOUND anywhere in the repository — zero references of any kind.** C13 required 4 attempts (2 early operator-stopped, 1 undocumented mid-run stop, 1 complete) — only the 4th is the operative evidence.

---

## 19. AI/Gemini/Claude Tests

**Zero logged AI-model transcripts exist anywhere in this repository.** Every "Gemini"/"Claude"/"AI" reference found is governance doctrine (what Lane-2 AI may/may not do), a component roster entry, a forbidden-pattern regex, or onboarding text — never an actual dated prompt/response/result record. **The historical "slow prompt" test: NOT FOUND** — zero matches for any spelling, and this audit did not construct a replacement test in its place, per instruction. **"OBS-ENVELOPE": NOT FOUND.**

---

## 20. Lane-2 Authority Tests

TOK-1 and SOSO-1 (isolation proofs) were actually executed (`ph6/cram_pu/tok_soso_isolation_proof.py`, real `tok_on/`/`tok_off/` run trees with per-frame CRAM records) and their core claim — that SoSo/Tokens write only to `/var/ph6/mram-s/*` and never touch CRAM or emit verdict fields — is **independently code-verified**, not just self-reported: `ph6/ssmt/*` and `ph6/tok/*` contain hard `RuntimeError`-raising write-root guard clauses, and `ph6/ssmt/tests/test_no_authority_leakage.py` is a genuine unit test asserting `authority == "NONE"` on real `SwarmScheduler` output. However, `closure_status.json`'s own `evidence_artifacts`/`artifact_hashes` fields for TOK-1/SOSO-1 are empty arrays despite the real run directory existing on disk — the governance record is disconnected from its own evidence. SOSO-LIFE-1 and TOK-LIFE-1 were never run at all (`state: "OPEN"`).

**A real doctrine-vs-code gap was found:** `ph6/tok/BOUNDARY.md` states TOK "may never issue PASS," yet `ph6/tok/rebuild.py:55` emits a field `"advisory_result": "PASS"` (under `authority:"ZERO"`, not the authoritative `verdict` field, and no code path was found reading it as authoritative — but the isolation-proof scanner does not catch it because it only checks for literal `pass`/`drop`/`verdict` key names). This is flagged for human review, not adjudicated here.

**No adversarial Lane-2 test** (real or simulated AI producing deliberately misleading/overconfident output, verified against an invariant PSEUDO-A verdict) exists in this repository. This is recommended as a **future** qualification test (SOSO-ADV-1/TOK-ADV-1 style), explicitly labeled here as a recommendation, not a historical fact.

`ph6/reflection/` (render/provenance layer) has no I/O code and cannot itself write to an authoritative record by inspection — but `authority_origin` labels are self-asserted by the caller with no verification mechanism inside Reflection, and the module `ph6/reflection/manifest_v1.py` (imported by `manifest_v2.py`) **does not exist in this checkout**, meaning the reflection layer as currently committed cannot actually be imported or tested.

---

## 21. Hash/Integrity Evidence

The BLAKE2b-256 scheme was independently re-derived by this audit (not merely read from docs): `cram_hash` = `blake2b256(canonical_json(record_minus_cram_hash_field))`, **not** a hash of raw file bytes (confirmed by direct `hashlib.blake2b` computation against 3 sampled records — canonical-JSON match, raw-byte mismatch, exactly as the scheme's non-circularity design requires). `.blake2b` sidecars match the internal `cram_hash` field in every sample checked. Repo-wide, all 66,133 `cram_*.json` records have exactly 66,133 matching `.json.blake2b` sidecars (clean 1:1 pairing, no orphans found). **HASH VERIFIED** at the scheme/mechanism level.

**A genuine evidentiary gap:** zero DROP-verdict records were found anywhere in any `cram_store/` in the repository. The "CRAM-R never gets a `.blake2b` marker" rule (CLAUDE.md hard rule 9) is therefore **UNRESOLVED / untested by example** — not violated, but nothing in this repository demonstrates a DROP record with the marker correctly absent, because DROP records are not preserved as individual files anywhere found; only aggregate `drop_count` fields exist. This is worth closing with a dedicated DROP-preservation check in a future campaign.

Campaign-level manifest hashes (OI-03A/B/C's 1214/4814/14414-file checks, LCC-01/C08/C09/C10/C13 artifact_hashes files) are **MANIFEST VERIFIED** — internally consistent and traced to the correct scheme, but not independently re-hashed file-by-file by this audit at that scale.

---

## 22. Replay Evidence

Every executed campaign with a `replay_parity`/`replay_verdict` field reports PASS, and cross-segment/cross-phase `result_set_hash` values match exactly where expected (C08's 3 segments share one hash; C13's 7 phases replay-verify individually). EVC-04 (payload replay verdict/metric comparison, 300 frames, 0 mismatches, original and replay verdict hashes byte-identical) is the cleanest dedicated replay-parity evidence in the repo. No replay failure was found anywhere.

---

## 23. Failure Injection

Only `fi_01_power_loss_mid_commit.py` (in-process, no real kill) and the failure-injection directory's broader `PH6_CLOSEKIT/failure_injection/` scripts (e.g. `fi_06_replay_corruption.py`, proving replay correctly rejects a tampered verdict via hash mismatch) exist — all SOFTWARE-class, in-process simulations. No OS-level process kill and no physical fault injection (power, network partition, disk-full) were found.

---

## 24. Historical Frame Counts

**No document in this repository's current HEAD asserts a literal "30,000 frames"** (exhaustive grep of every `.md` file: zero matches, with or without a comma). This audit cannot confirm or deny an external narrative citing that figure, because it does not trace to any artifact in this repo as of this audit.

**VERIFIED PHYSICAL FRAME TOTAL (independently file-counted, PASS/CRAM-A only, matched `.blake2b` sidecar present): 66,133 records repo-wide.** Of these:
- **5,100 are real single-camera captures** (LCC-01A 300 + LCC-01B 1200 + LCC-01C 3600, `/dev/video0`, 0 DROP). OI-03A/B/C transfer this *same* 5,100-frame set (identical hashes) — do not double-count as an additional 5,100.
- **~61,000 remaining are synthetic staged pipeline-stress PASS records** (C08 2,469 + C09 8,232 + C10 4,114 + C11 4,114 + C12 2,057 + C13-final 16,459 = 37,445, plus 618 in a separate `ph6/cram_pu/runtime/run_20260515T111525Z` dir outside the campaign structure, plus a separate real-camera 12,000-frame SoSo/Token re-analysis run — see below — whose per-frame records were not individually preserved as files, only summarized).
- A **second, distinct "12,000-frame" campaign** exists and must not be confused with C09: `PH6-USB-CAM-PSEUDO-SOSO-TOK-12000-v1` (run `20260529T202849Z`, 12 days after C09) is a **real** `/dev/video0` capture, 15fps target, **800.0 seconds (~13.3 minutes) duration**, 14.999 measured avg fps, PASS 11,933 / DROP 67 (granular drop reasons: 66 EXTREME_BLUR, 1 EXTREME_BLACK_FRAME), with SoSo/Token Lane-2 advisory analysis layered on top. Its evidence grade is lower than C09 or LCC-01: no `cram_store/` was found for this run — only aggregate summary/report JSON (final_report.md, drift_map.json, token_summary.json) — so it is **MANIFEST-VERIFIED, not FILE-VERIFIED**. This is the single largest real-time real-camera-duration run found anywhere in the repository (13.3 minutes vs. LCC-01C's 3.1 minutes), and any "30,000-frame" narrative external to this repo may plausibly derive from summing subsets of these campaigns — but no artifact in this repo performs or claims that sum.

**Internal consistency finding (positive):** a ~68.57–68.6% PASS ratio recurs exactly across every synthetic staged campaign regardless of target size (823/1200, 8232/12000, 4114/6000×2, 2057/3000, 16459/24000) — internally consistent with a fixed deterministic synthetic-payload generator/threshold, which is a genuine determinism-doctrine positive signal, but also confirms these are staged/synthetic content, not independently varied real-world captures.

---

## 25. 184223 Investigation

**184223 is not a PH6 frame, sequence, campaign, or record-count value.** It is a coincidental 6-hex-digit substring inside one BLAKE2b-256 `cram_hash` value: `50a9c3eabb45e24cefc624290adffae7482e81a1717bc8958ab18422397d994e` (belonging to `frame_id: 1777` in campaign `20260517T055650Z_C09_12000_staged_endurance`, `ph6/cram_pu/validation_runs/.../cram_store/cram_0000001777.json`). It appears exactly 3 times in the repository — once in that record's own `cram_hash` field, once in its `.blake2b` sidecar (which necessarily contains the same value), and once as the `prev_cram_hash` field of the very next record (`frame_id: 1779`, standard hash-chain linkage). No frame allocator, sequence counter, or campaign-numbering code anywhere in `ph6/cram_pu/schemas/canonical.py` or elsewhere produces or consumes the number 184223 as a discrete value; it is purely a byte-substring coincidence of hexadecimal hash output. The frame/sequence allocator itself (`frame_id` in `cram_pu_live.py` and related runners) is per-run, monotonic within a campaign directory, and resets to 1 for each new run directory — it does not persist globally across campaigns, and campaign directories are namespaced by timestamp + campaign label to prevent ID collision.

---

## 26. Git Drift and Documentation Contradictions

**Section merged per shared root cause: three governance-index documents currently disagree with each other and with the authoritative `closure_status.json`, and this audit could not fully drift-check the 2026-05-17 campaigns because the local clone is shallow-rooted at 2026-05-18T02:25:59.**

| # | Source A | Source B | Conflict | Newer Source | Primary Evidence | Required Human Decision |
|---|---|---|---|---|---|---|
| 1 | `GAP_REGISTER_v3.0.md` (content-dated 2026-05-14; last touched by an unrelated bulk commit `055302a5` at 2026-05-18 02:25, content not actually updated) — OI-01/OI-03 "OPEN … STOP-SHIP … Closure Authority: Human only … TBD" | `closure_status.json` (commit `11966dee7`, 2026-05-18 04:38) — OI-01 `DESCOPED`, OI-03A/B/C all `CLOSED`, reviewer "Jack Disla" | Direct status disagreement on both STOP-SHIP gates | closure_status.json (~2h13m later) | Raw rsync/camera artifacts support closure_status.json's claim that runs occurred; GAP_REGISTER was simply never regenerated afterward | Regenerate/supersede GAP_REGISTER_v3.0.md to reflect the 2026-05-18 decisions, and confirm the OI-03 closure specifically survives the physical-separation question in §17 |
| 2 | **`CLAUDE.md`** (the primary AI-context file for this very session) GAP table: "OI-03 (C02) \| OPEN \| YES \| Satisfies OI-03" | `closure_status.json` — OI-03A/B/C `CLOSED` | CLAUDE.md, which every future AI session loads as ground truth, still says OI-03 is STOP-SHIP-open | closure_status.json is newer, but CLAUDE.md is what actually governs session behavior | closure_status.json HEAD content | **Operationally the most urgent item in this audit**: reconcile CLAUDE.md's GAP table with closure_status.json, or every future Lane-2 session will act on stale STOP-SHIP status |
| 3 | `PH6_SOURCE/VALIDATION/campaign_matrix.json` (commit `055302a5`, 2026-05-18 02:25) — `"production_clearance_declared": false`, "may not be declared until all campaigns and STOP-SHIP gates are closed by human-reviewed evidence" | `closure_status.json` HEAD — `production_clearance_declared: true`, `DECLARED` | Direct boolean contradiction on the single most consequential flag in the repo | closure_status.json (~2h later same day) | N/A — gating policy vs. declaration | Confirm campaign_matrix.json's gating condition is actually satisfied, or mark that file superseded |
| 4 | `PH6_FULL_PRODUCTION_CLEARANCE/clearance_attestation.json` (2026-05-06) — treats "departure→arrival simulation" as acceptable OI-03 protocol proof, non-blocking | `evidence_campaign_matrix.json` STOP-SHIP rule — OI-03 explicitly "cannot be closed by … Simulation results" | Doctrinal reversal between 2026-05-06 and the current matrix | evidence_campaign_matrix.json (current) | HEAD-current, explicit | Confirm the 2026-05-06 attestation and its scoped clearance verdict are void/superseded |
| 5 | `PH6_FULL_PRODUCTION_CLEARANCE/open_items.json` — OI-01 marked blocking only for the "AI lane," not the whole system | `GAP_REGISTER_v3.0.md` — OI-01 listed as blanket whole-system STOP-SHIP | Scope disagreement on OI-01's blast radius | closure_status.json's later descope reasoning ("does not block single-node or cross-node evidence certification") sides with the narrower framing | closure_status.json | Confirm which OI-01 scope framing was operative when GAP_REGISTER's blanket STOP-SHIP label was written |
| 6 | `closure_status.json` at commit `37c62a2fff` — corrected to `production_clearance_status: "CANDIDATE_NOT_DECLARED"` | `closure_status.json` at commit `11966dee7` (3 commits later, same day) — re-declared `DECLARED`, `PH6-PROD-CLEAR-2026-05-18-001` | Not a live contradiction (HEAD is unambiguous) but a chronology worth recording: a correction was itself superseded by a second human-attributed declaration | `11966dee7` is HEAD | Both commits are human-attributed (`jackfd81-lgtm`, co-authored Claude Sonnet 4.6) | Confirm this second declaration reflects the operator's actual final intent (it reads as such — narrowly scoped, explicit exclusions listed) rather than an unintended reversion |

**Git drift for 2026-05-17 campaigns (C08, C09, C10, C11, C12, C13, TOK-1, SOSO-1): UNRESOLVED in this environment** — their recorded `evidence_commit` hashes predate the shallow-clone root and do not resolve locally. **Git drift for 2026-05-18 campaigns (OI-03A/B/C, EVC-05): VALID** — 58–63 commits have landed since their evidence_commit, 13–15 touching `cram_pu`/`ssmt`/`tok`/`GOVERNANCE`, but `git diff <evidence_commit>..HEAD -- ph6/cram_pu/schemas/canonical.py` is empty in every case — the hash/verdict core is byte-unchanged since these campaigns closed.

---

## 27. Documentation Contradictions

Consolidated into §26 above (the audit brief's Sections 26 and 27 cover the same material for this repository; splitting them would duplicate the table).

---

## 28. Open Qualification Gates

| Item | Classification | Status |
|---|---|---|
| OI-01 (Hailo) | GOVERNANCE / ARCHITECTURAL (resolved) | DESCOPED by human decision; GAP_REGISTER still stale — DOCUMENTATION gate remains open |
| OI-03 (Pi-to-Pi physical separation) | ENGINEERING / VERIFICATION | governance record says CLOSED; **physical-separation evidence is OPEN** per §17 — requires operator resolution |
| C01, C03, C04, C05, C06 (as literally specified) | ENGINEERING | OPEN — never executed under their own IDs |
| C14, C15, C16 | INFORMATIONAL | NOT FOUND — no specification exists to be open or closed |
| Physical power-loss test | OPERATIONAL / VERIFICATION | OPEN — only software simulation exists |
| Thermal/endurance multi-hour run | OPERATIONAL / VERIFICATION | OPEN — longest run is 17.6 minutes |
| ESP32-CAM imaging qualification | VERIFICATION | OPEN — claim exists, artifacts do not |
| DROP-record (CRAM-R) preservation example | VERIFICATION | UNRESOLVED — no DROP record found to test the "no .blake2b" rule against |
| CLAUDE.md / GAP_REGISTER / campaign_matrix.json reconciliation | GOVERNANCE | OPEN — see §26, item 2 is operationally urgent |
| Human review/ratification of C08–C13, TOK-1, SOSO-1 | VERIFICATION | OPEN — `reviewer: null` on all of them despite PASS_PENDING_REVIEW evidence |
| Adversarial Lane-2 test | ENGINEERING (recommended, not existing) | OPEN — recommended, not yet specified as a campaign |
| `ph6/tok/rebuild.py` `advisory_result:"PASS"` vs. BOUNDARY.md doctrine | ENGINEERING | OPEN — flagged for human review, not adjudicated |
| `ph6/reflection/manifest_v1.py` missing file | IMPLEMENTATION | OPEN — reflection layer cannot currently be imported/tested as committed |

Architectural and governance ambiguity items above (OI-01 documentation staleness, CLAUDE.md/GAP_REGISTER contradiction, OI-03 physical-separation ambiguity) should be resolved before this document set is treated as a stable source of truth. Implementation, verification, and operational gaps may legitimately remain open pending downstream hardware evidence.

---

## 29. Recommended Test Order

1. **Reconcile CLAUDE.md, GAP_REGISTER_v3.0.md, and PH6_SOURCE/VALIDATION/campaign_matrix.json against closure_status.json** (documentation only, zero risk, closes the most operationally dangerous gap in §26).
2. **Resolve OI-03 physical separation** — re-run `run_oi03_pi_to_pi_transfer.py` with an explicit `--dest-host` against a node with a distinct hostname/kernel fingerprint, capturing the `PASS_REMOTE` marker; or produce independent confirmation from the receiving Pi Zero 2W.
3. **Physical power-loss test** — real `kill -9` of a live ingest process, and ideally one genuine power interruption, against a running CRAM-A commit.
4. **Multi-hour thermal/endurance run** — extend past the current 17.6-minute maximum, on real camera input if possible.
5. **DROP-record preservation check** — force a DROP verdict and confirm a CRAM-R record is written without a `.blake2b` marker (closes the evidentiary gap in §21).
6. **ESP32-CAM imaging evidence** — either recover/regenerate the claimed 2026-05-15 run artifacts or re-run and commit them.
7. **Human review pass on C08–C13, TOK-1, SOSO-1** — populate `reviewer`/`reviewed_at_utc` in `closure_status.json` (pure governance action, no new testing required, since evidence already exists and is internally consistent).
8. **Adversarial Lane-2 test** (new campaign, e.g. SOSO-ADV-1) — feed deliberately misleading advisory content and confirm PSEUDO-A's verdict is byte-invariant.
9. Execute C01, C03, C04, C05, C06 under their own literal IDs, or formally retire/remap them to the IDs that actually cover their intent (OI-03→C02, TOK-1/SOSO-1→C06) so the governance matrix stops disagreeing with itself.

---

## 30. Final Qualification Status

Using only the language authorized by the audit brief:

- Lane-1 CRAM commit/hash scheme: **VERIFIED** (independently re-derived).
- Lane-1/Lane-2 write-boundary guards: **VERIFIED** (code-level, not self-report).
- HRG9 software baseline: **CLOSED** (immutable, 2026-05-06).
- C07 governance drift scan: **CLOSED / RATIFIED**.
- EVC-05 / scoped production clearance: **CLOSED / RATIFIED** (narrowly scoped, single-node + rsync-export only).
- C08–C13, TOK-1, SOSO-1: **EXECUTED / VERIFIED**, **NOT CLOSED**, **NOT RATIFIED**.
- LCC-01A/B/C: **EXECUTED / VERIFIED / OBSERVED** (real camera), **NOT RATIFIED**.
- OI-03A/B/C governance closure: **CLOSED** (record); underlying physical-separation claim: **OPEN / UNRESOLVED**.
- OI-01/Hailo: **DESCOPED** (never tested).
- Physical power-loss, multi-hour endurance, ESP32-CAM imaging: **OPEN**.
- Adversarial Lane-2 test: **NOT FOUND** (recommended).
- C01, C03, C04, C05, C06 (own IDs), C14, C15, C16: **NOT FOUND**.
- 184223: **REFUTED as a frame/sequence claim** — confirmed hash-substring coincidence.
- 30,000-frame claim: **NOT FOUND** in this repository's current documentation.

No use of CERTIFIED, PRODUCTION READY, FULLY VALIDATED, COMPLETELY TESTED, or ALL TESTS PASSED is supported by this repository's evidence, and none is used above.

---

## 33. Final Executive Question

*If I were taking PH6 today as a serious engineering prototype and preparing it for product qualification, exactly what has already been proven, exactly what remains unproven, and what are the next tests I should physically run?*

### ALREADY PROVEN (artifact-backed only)

- The BLAKE2b-256 canonical hash/commit chain is correctly implemented and non-circular (independently re-derived by this audit).
- Lane-1/Lane-2 write-boundary separation is enforced in real code (guard clauses + unit tests), not merely documented.
- A single Raspberry Pi 5 running real `/dev/video0` capture through the full CRAM-0→PSEUDO-M→PSEUDO-A→CRAM-A→replay pipeline produces internally consistent, hash-verified, 0-DROP results at up to 3,600 frames / ~3.1 minutes.
- The synthetic CRAM pipeline processes staged payloads up to 24,000 "frames" / ~17.6 minutes with deterministic, reproducible PASS/DROP ratios and passing replay parity.
- RSYNC-non-blocking behavior holds under every load condition tested so far (software and staged-hardware).
- USB audio/video resource contention measurably degrades video framerate (not frame-drop count) when audio capture runs concurrently — a real, repeatable HW_INTEGRATION finding.
- A human operator (Jack Disla) has explicitly, narrowly declared production clearance for single-node Lane-1 operation only, with Hailo/distributed-authority/remote-PASS-DROP explicitly excluded.

### STILL UNPROVEN / OPEN (evidence-supported gaps only)

- Two physically separate PH6 nodes have ever exchanged CRAM evidence over a real network link (hostname collision + missing PASS_REMOTE marker + unchecked preflight checklist).
- PH6 survives a real process kill or real power interruption mid-commit (only sub-10ms in-process simulation exists).
- PH6 sustains operation for hours under thermal/resource load (longest run is 17.6 minutes).
- Any ESP32-CAM imaging hardware has actually been exercised (claim exists, no artifacts).
- A DROP-path (CRAM-R) record has ever been preserved and independently inspected (no example found).
- Lane-2 (SoSo/Tokens/AI) authority-zero behavior survives deliberately adversarial/misleading advisory input.
- Camera behavior above ~20fps at 640×480 on this hardware (every real test hit the same driver ceiling).
- Dual-camera concurrent operation (two independent test runs contradict each other and are unreconciled).

### NEXT PHYSICAL TESTS (ordered by qualification importance and dependency)

1. Reconcile the governance documents (CLAUDE.md / GAP_REGISTER / campaign_matrix.json) — zero-risk prerequisite to trusting anything else.
2. Real Pi-to-Pi transfer with an unambiguous second physical node and the canonical tool's `PASS_REMOTE` marker.
3. Real process-kill and (if safe to arrange) real power-interruption test against a live commit.
4. Multi-hour endurance run on real camera input, with continuous thermal/resource sampling.
5. Recover or regenerate verifiable ESP32-CAM imaging evidence.
6. Dedicated DROP-record preservation test.
7. Human review/ratification pass on the six already-executed, already-consistent, still-unreviewed campaigns (C08–C13, TOK-1, SOSO-1) — this alone would close a large fraction of the "PASS_PENDING_REVIEW" backlog without any new testing.
8. Adversarial Lane-2 test campaign.
9. Reconciled dual-camera concurrent-operation retest.

---

*End of PH6_COMPLETE_TEST_EVIDENCE_AUDIT-v1.0.md. This document and its companion ledger are PROPOSED Lane-2 work product, Authority ZERO. No Open Item was closed, no production-readiness claim was made or implied beyond reporting pre-existing human decisions found in git history, and no authority file was modified in the course of this investigation.*
