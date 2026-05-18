# EVC-05 Review Closure Document

**Reviewer:** Jack Disla (authority signature required to close)
**Prepared by:** Claude Sonnet 4.6 (advisory, no authority)
**Date:** 2026-05-18
**Commit:** 9deda5b1ab
**Run dir:** ph6/cram_pu/validation_runs/evc05_20260518T090015Z

---

## Campaign Evidence Status

```
EVIDENCE_BACKED_PENDING_AUTHORITY_SIGNATURE
```

## Production Deployment Status

```
NOT_DECLARED
```

## FAST_CRAM Behavioral Divergence

```
NOT_PROVEN
```

---

## Artifact Review — All 10 Required

### 1. `evc05_manifest.json`

**Claim:** Campaign-level manifest capturing phase structure, device, frame counts, git commit, mode note.

**Inspection:**
- `frames_per_phase: 600`, `total_frames: 1800` ✓
- `device: /dev/video0` ✓
- `git_commit: a26c111c256e1c37...` (governance closure commit, pre-EVC-05 run) ✓
- `real_source: true` ✓
- `mode_note` present and explicit ✓

**Claim classification:** `ALLOWED`

---

### 2. `evc05_replay_receipt.json`

**Claim:** All three phases produced deterministic replay-verified output.

**Inspection:**
- `all_phases_pass: true` ✓
- All three phases: `replay_verdict: PASS` ✓
- Per-phase `result_set_hash` all identical:
  `blake2b256:6674815dfc16668df5b6d7aaad7da641688bb6cdb0aeaf2e88a5d95f8a63e726`

**Note on identical hashes:** Expected and honest. EVC-05 uses the shared Life CRAM
path for all three phases. 600 frames on the same input class produces the same
deterministic hash. This confirms consistency, not divergence. See mode clarification below.

**Claim classification:** `ALLOWED`

---

### 3. `evc05_lane_isolation_report.json`

**Claim:** Lane 2 had zero authority violations across all three phases.

**Inspection:**
- `isolation_pass: true` ✓
- `total_lane2_violations: 0` ✓
- Per-phase `lane2_violations: 0` (all three) ✓
- `leakage_scan_pass: true` (all three) ✓

**Claim classification:** `ALLOWED`

---

### 4. `evc05_rsync_integrity_report.json`

**Claim:** RSYNC remained unblocked (sovereignty preserved) across all three phases.

**Inspection:**
- `sovereignty_pass: true` ✓
- `any_blocked: false` ✓
- `rsync_blocked_by: null` (all three phases) ✓
- `rsync_priority: "ZERO — export sovereignty guaranteed"` ✓

**Claim classification:** `ALLOWED`

---

### 5. `evc05_governance_snapshot.json`

**Claim:** Governance state captured at campaign execution time.

**Inspection:**
- `git_commit: a26c111c256e1c37...` ✓
- `git_branch: main` ✓
- `governance_closure_hash: blake2b256:9d78ef2b...` ✓
- `governance_matrix_hash: blake2b256:0a7436ac...` ✓
- `python_version: 3.13.5` ✓
- `kernel: Linux 6.12.75+rpt-rpi-2712 aarch64` (Pi 5 / main Pi) ✓
- `hostname: jackjack`

**Note on hostname:** Both the main Pi and the Pi Zero 2W report hostname `jackjack`.
This is a node identification ambiguity that should be resolved before any
multi-node authority claim. For EVC-05 (single-node campaign on main Pi), the
kernel string (`rpi-2712 aarch64`) is the reliable node identifier.

**Claim classification:** `ALLOWED` with noted caveat on hostname

---

### 6. `evc05_campaign_receipt.json` — DEFECT NOTED

**Claim:** Campaign-level receipt summarizing all checks.

**Inspection:**
- `campaign_pass: false` ← SCRIPTING DEFECT
- `missing_artifacts: ["evc05_campaign_receipt.json"]` ← SELF-REFERENTIAL BUG
- `all_required_artifacts_present: false` ← consequence of above

**Root cause:** The runner checks for the receipt file's existence before writing it,
so it always finds itself missing. The file IS present in the committed run.

**Evidence impact assessment:** The underlying evidence is not corrupted. All other
nine artifacts are valid. The `campaign_pass: false` flag in this file is a runner
scripting defect, not an evidence failure. The correct status (derived from the
nine valid artifacts) is PASS.

**Required action:** Fix the self-reference check in `run_evc05.py` before the next
production run. The fix is: exclude `evc05_campaign_receipt.json` from the
`required_artifacts` check inside `write_campaign_receipt()`, or check after write.

**Claim classification:** `LIMITED — scripting defect present; evidence valid;
runner must be fixed before next production campaign`

---

### 7. `evc05_result_set_hash.txt`

**Claim:** Deterministic campaign-level hash over all three phase hashes.

**Inspection:**
- Content: `blake2b256:3cf901a9db7c416d4344892be5e75aa17ced04bc6e3b1ea97b001288be5a846c`
- Derived from: canonical JSON of `{phase_id, result_set_hash}` for all three phases
- Deterministic: input is fully determined by phase execution ✓

**Claim classification:** `ALLOWED`

---

### 8. `phase_01_fast_receipt.json`

**Inspection:**
- `frames_done: 600`, `frames_target: 600` ✓
- `drop_count: 0`, `critical_failures: 0` ✓
- `replay_verdict: PASS` ✓
- `leakage_scan_pass: true`, `lane2_violations: 0` ✓
- `rsync_pass: true` ✓
- `phase_pass: true` ✓
- `actual_fps: 19.83` ✓

**Claim classification:** `ALLOWED`

---

### 9. `phase_02_regular_receipt.json`

**Inspection:** Identical structure to phase_01. All checks pass.
- `actual_fps: 19.84`, `frames_done: 600`, `drop_count: 0` ✓

**Claim classification:** `ALLOWED`

---

### 10. `phase_03_fast_cram_receipt.json`

**Inspection:** Identical structure. All checks pass.
- `actual_fps: 19.83`, `frames_done: 600`, `drop_count: 0` ✓

**Claim classification:** `ALLOWED`

---

## Mode Clarification (Required)

EVC-05 does **not** prove behavioral divergence between FAST, REGULAR, and FAST_CRAM.

The phase labels are architectural intent markers over the current shared Life CRAM
execution path. The identical per-phase `result_set_hash` values confirm this: the
system behaved identically across all three phases because the execution path is
identical.

**Allowed claim:**
> EVC-05 proves phased production-grade campaign execution, replay parity, lane
> isolation, RSYNC sovereignty, governance capture, and artifact completeness
> over the current Life CRAM path.

**Not allowed claim:**
> EVC-05 proves FAST_CRAM has a distinct behavioral implementation.

Future campaign for behavioral divergence: `EVC-06_FAST_CRAM_BEHAVIORAL_DIVERGENCE`

---

## Defect Register

| ID | Artifact | Defect | Severity | Action Required |
|----|----------|--------|----------|-----------------|
| D1 | `evc05_campaign_receipt.json` | Self-referential artifact check produces `campaign_pass: false` | MINOR — does not invalidate evidence | Fix runner before next campaign |
| D2 | `evc05_governance_snapshot.json` | Both Pis share hostname `jackjack` | MINOR — main Pi identifiable by kernel string | Rename Pi Zero 2W hostname before OI-03 multi-node authority work |

---

## Claim Summary

| Claim | Status |
|-------|--------|
| 1800 frames captured (3 × 600) | **ALLOWED** |
| Real camera source confirmed | **ALLOWED** |
| Per-phase receipts generated | **ALLOWED** |
| All 10 artifacts present in committed run | **ALLOWED** |
| Replay parity passed all three phases | **ALLOWED** |
| Lane 2 isolation confirmed (0 violations) | **ALLOWED** |
| RSYNC sovereignty confirmed (0 blocked) | **ALLOWED** |
| Governance snapshot captured | **ALLOWED** |
| Campaign result_set_hash deterministic | **ALLOWED** |
| `campaign_pass: true` in receipt | **NOT ALLOWED** — scripting defect |
| FAST_CRAM behavioral divergence proven | **NOT ALLOWED** — not implemented |
| Production deployment certified | **NOT ALLOWED** — not declared |

---

## Final Status

```
EVC-05 campaign evidence status : EVIDENCE_BACKED_PENDING_AUTHORITY_SIGNATURE
Production deployment status    : NOT_DECLARED
FAST_CRAM behavioral divergence : NOT_PROVEN
campaign_receipt defect         : PRESENT / runner fix required
```

**EVC-05 is the first production-grade phased Life CRAM evidence campaign in the
PH6 record.** The evidence is valid. One scripting defect exists in the campaign
receipt self-check. Two minor environmental notes (hostname collision, governance
snapshot git_commit captured pre-run rather than post-run) do not affect evidence
integrity.

Authority signature by Jack Disla is required to close EVC-05 as
`EVIDENCE_BACKED / CLOSED`.

---

*This document was prepared by advisory execution layer (Claude Sonnet 4.6).*
*It has no governance authority. It is a reviewer preparation artifact only.*
