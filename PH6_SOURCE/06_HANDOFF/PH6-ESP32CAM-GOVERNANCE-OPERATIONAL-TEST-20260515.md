# PH6 ESP32-CAM Governance Operational Test — 2026-05-15

```text
Report ID:    PH6-ESP32CAM-GOVERNANCE-OPERATIONAL-TEST-20260515
Date UTC:     2026-05-15T09:07:56Z
Host:         jackjack
Git Branch:   main
Git Commit:   2eee154  evidence: add GAP-16 Microdia audio+video USB contention
Verdict:      PASS
```

---

## Purpose

Pre-commit governance verification confirming that the PH6/CRAM repository,
governance controls, ESP32-CAM evidence artifacts, and operational test outputs
are coherent, clean, commit-ready, and free of authority drift.

---

## Scope

- Repository state inspection (Phase 1)
- Governance tool discovery (Phase 2)
- Governance drift scan execution (Phase 3)
- Forbidden-pattern scan across PH6_SOURCE and working directory (Phase 4)
- ESP32-CAM evidence artifact verification — two runs (Phase 5)
- Governance operational report creation (Phase 6)
- Git commit of governed artifacts (Phase 7)

---

## Explicit Non-Scope

This test does NOT:

- Create new doctrine
- Alter PSEUDO thresholds
- Alter CRAM write semantics
- Alter RSYNC behavior
- Alter Lane 1 authority
- Promote Lane 2 outputs to authority status

---

## Phase 1 — Repository State

| Field          | Value                                                            |
|----------------|------------------------------------------------------------------|
| Working Dir    | /home/jack                                                       |
| Branch         | main                                                             |
| Latest Commit  | 2eee154 evidence: add GAP-16 Microdia audio+video USB contention |
| Modified Files | PH6_SOURCE/AI_ENTRY_INDEX.md, ph6_status/status.json            |
| Untracked      | New artifacts (esp32cam, ph6_esp32cam_*, governance reports)     |

---

## Phase 2 — Governance Tools Located

| Tool                                        | Status    |
|---------------------------------------------|-----------|
| PH6_SOURCE/TOOLS/governance_drift_scan.py   | PRESENT   |
| verify_determinism.sh                       | NOT FOUND |
| check_export_nonblocking.sh                 | NOT FOUND |
| verify_schema_versions.sh                   | NOT FOUND |
| RECOVER.sh                                  | NOT FOUND |

---

## Phase 3 — Governance Drift Scan

Executed: `python3 PH6_SOURCE/TOOLS/governance_drift_scan.py --scan-root PH6_SOURCE`

```
PH6 GOVERNANCE DRIFT SCAN
  scan_root:   /home/jack/PH6_SOURCE
  generated:   2026-05-15T09:06:50Z
  result:      PASS
  critical:    0
  high:        0
  warn:        0
```

```json
{
  "schema": "ph6.governance.drift_report.v1",
  "scan_root": "/home/jack/PH6_SOURCE",
  "governance_dir": "/home/jack/PH6_SOURCE/GOVERNANCE",
  "generated_at_utc": "2026-05-15T09:06:50Z",
  "overall_result": "PASS",
  "critical_count": 0,
  "high_count": 0,
  "warn_count": 0,
  "total_findings": 0,
  "summary_by_check": {},
  "findings": []
}
```

**Governance scan verdict: PASS (0 findings)**

---

## Phase 4 — Forbidden-Pattern Scan

Scan command:
```
grep -RIn --exclude-dir=.git --exclude-dir=__pycache__ --exclude-dir=.cache \
  -E "motion_score|motion_decay_score|authority.*Lane 2|Lane 2.*PASS|Lane 2.*DROP| \
     SoSo.*PASS|SoSo.*DROP|TOK.*PASS|TOK.*DROP|Swarm.*PASS|Swarm.*DROP| \
     \.sha256.*authoritative|SHA256.*authoritative" \
  PH6_SOURCE .
```

### Findings Classification

All matches fall into one of the following benign categories:

| Category                            | Examples                                                        |
|-------------------------------------|-----------------------------------------------------------------|
| Governance prohibition registries   | forbidden_terms_registry.json, schema_lock_registry.json, governance_manifest.json |
| Policy / primer docs                | AI_ENTRY_INDEX.md, ACTIVE_SCHEMA_INDEX.md, 00_AI_AGENT_READ_FIRST.md, CLAUDE_RUNTIME_PRIMER_v1.0.md |
| Campaign docs (invalid conditions)  | CAMPAIGN_01_300_FRAME_COHERENCE.md, CAMPAIGN_01B_ADVISORY_EXPANSION.md, C01_RUNTIME_CARD.md |
| DRAFT governance contracts          | PH6-AI-CORE, PH6-SOSO-FAMILY-CONTRACT, PH6-TOK-* (DRAFT only) |
| HRG9 closure records                | hrg9_final_summary.md, hrg9_authority_boundary_report.json (audit rows, compliance status) |
| Enforcement / guard code            | bin/pseudo_soso_agent.py, frame_filter/ph6_full_stack_coherence.py, scripts/ph6_canon_lint.py |
| Failure injection test harness      | fi_04_lane2_contamination.py (synthetic drift injection for detection testing) |
| Audit infrastructure                | ph6/audit.py, ph6/tok/reconstruct.py, PH6_SOURCE/CERTIFICATION/audit_patched.py |
| Governance tool source              | PH6_SOURCE/TOOLS/governance_drift_scan.py (defines what it scans for) |
| Local backup mirror                 | PH6_LOCAL_BACKUPS/ (frozen checkpoint, not operational)         |
| This report                         | PH6-ESP32CAM-GOVERNANCE-OPERATIONAL-TEST-20260515.md (scan command inline) |

**No matches in active schemas, operational pipeline code, or CRAM write paths.**

**No Lane 2 outputs carry PASS/DROP authority in any operational file.**

**SHA256 appears only in contexts that prohibit its canonical authority use.**

**Forbidden-pattern scan verdict: CLEAN — no operational authority drift detected**

---

## Phase 5 — ESP32-CAM Evidence Artifact Verification

### C01 — 300-Frame Ingest

| Field               | Value                                                   |
|---------------------|---------------------------------------------------------|
| Run ID              | PH6-ESP32CAM-C01-300-FRAME-INGEST                      |
| Run Directory       | /home/jack/ph6_esp32cam_validation/run_20260515T082807Z |
| Camera Source       | http://192.168.254.191/capture                          |
| Schema              | ph6.esp32cam.postrun_summary.v1                         |
| Run Mode            | target_frames                                           |
| Target Frames       | 300                                                     |
| Completed Frames    | 300                                                     |
| Failed Frames       | 0                                                       |
| Total Retries       | 0                                                       |
| Saved JPGs          | 300 (filesystem count confirmed)                        |
| Completed UTC       | 2026-05-15T08:31:45.430727Z                             |
| Verdict             | PASS                                                    |

**Capture statistics:**

| Metric          | Value     |
|-----------------|-----------|
| avg_bytes       | 8978.74   |
| min_bytes       | 8641      |
| max_bytes       | 16418     |
| avg_capture_ms  | 576.20    |
| min_capture_ms  | 75.762    |
| max_capture_ms  | 3763.97   |

**Artifact inventory:**

| Artifact                | Size   | Present |
|-------------------------|--------|---------|
| manifest.json           | 528 B  | YES     |
| frame_log.csv           | 87 KB  | YES     |
| postrun_summary.json    | 580 B  | YES     |
| frames/frame_000001.jpg | JPEG 640×480 | YES |
| frames/frame_000300.jpg | JPEG 640×480 | YES |

**Hash sample — frame_000001.jpg (live verified):**

```
BLAKE2b: 02ff637b15770931d44846ebb6a91eb8de8f7f772eab2d9ea4770daa956179b1a48279b7115371620db1e447074452d71b54ef22f32d2400b0f4f48cabdaf4e5
SHA256:  430f441ffb966725089e76a5365bdd92836521825d9084ea4f2584c9742bd220
```

**Hash sample — frame_000300.jpg (live verified):**

```
BLAKE2b: 8685e4729fb0eba4e6fcde292e9782856301166c1a2cdc34c57049d5edce1e9a7e949df54af434ebca920b286c614bcb4fd3771e9a143f90384a2c980484d521
SHA256:  ba27e55c98568c56a86b3dc339a7c8ec300b859026a1abcca2d4cca7a6e7abec
```

**C01 evidence verdict: PASS**

---

### C01E — 5-Minute Duration Endurance

| Field                 | Value                                                   |
|-----------------------|---------------------------------------------------------|
| Run ID                | PH6-ESP32CAM-C01E-5MIN-ENDURANCE                       |
| Run Directory         | /home/jack/ph6_esp32cam_validation/run_20260515T084238Z |
| Camera Source         | http://192.168.254.191/capture                          |
| Schema                | ph6.esp32cam.postrun_summary.v1                         |
| Run Mode              | duration_capped                                         |
| Run Duration          | 300.671 sec                                             |
| Target Frames         | 9999 (ceiling)                                          |
| Minimum Valid Frames  | 300                                                     |
| Completed Frames      | 441                                                     |
| Failed Frames         | 0                                                       |
| Total Retries         | 0                                                       |
| Saved JPGs            | 441 (filesystem count confirmed)                        |
| Completed UTC         | 2026-05-15T08:47:39.577743Z                             |
| Verdict               | PASS                                                    |

**Capture statistics:**

| Metric          | Value     |
|-----------------|-----------|
| avg_bytes       | 8662.09   |
| min_bytes       | 8545      |
| max_bytes       | 9569      |
| avg_capture_ms  | 530.80    |
| min_capture_ms  | 60.707    |
| max_capture_ms  | 1901.665  |

**Artifact inventory:**

| Artifact                | Size   | Present |
|-------------------------|--------|---------|
| manifest.json           | 529 B  | YES     |
| frame_log.csv           | 127 KB | YES     |
| postrun_summary.json    | 712 B  | YES     |
| frames/frame_000001.jpg | JPEG 640×480 | YES |
| frames/frame_000441.jpg | JPEG 640×480 | YES |

**Hash sample — frame_000001.jpg (live verified):**

```
BLAKE2b: 8e7e7943bcdc0091bee1c09dc67c6517ad1b46ae788d1012ae3c52ae1a3fbf32a69edd4cf95a249cbbd0ca693366d20b29381ba30c354ed6cbf1cf89ed5a0ce2
SHA256:  48e8e2c43438c09fdca817fbc0e886237d0c733f7ba4781781c60c8e2e525fd2
```

**Hash sample — frame_000441.jpg (live verified):**

```
BLAKE2b: 61b4dec9ecbd20da4858d2c2ef7ee3967a8029529217984f48b59a83277e3131f505d1f751c3a2af60c4ce61ab5bd5393a05a1aea5e382cb465a5a375044debf
SHA256:  f41afcfa55c60eaffa1b5152f460f5243d57105b796718abc33560aff62d9388
```

**C01E evidence verdict: PASS**

---

## Pass/Warn/Invalid Criteria

| Criterion                                               | Threshold              | Result   |
|---------------------------------------------------------|------------------------|----------|
| Governance drift scan                                   | 0 critical, 0 high     | PASS     |
| Forbidden-pattern scan — no operational violations      | Zero active violations | CLEAN    |
| C01 completed_frames >= 300                             | 300                    | 300      |
| C01 failed_frames == 0                                  | 0                      | 0        |
| C01 postrun verdict == PASS                             | PASS                   | PASS     |
| C01 filesystem JPG count == completed_frames            | 300                    | 300      |
| C01 all artifacts present                               | manifest+log+summary   | YES      |
| C01E completed_frames >= 300 (minimum_valid_frames)     | 300                    | 441      |
| C01E failed_frames == 0                                 | 0                      | 0        |
| C01E run_duration_sec >= 300                            | 300s                   | 300.671s |
| C01E postrun verdict == PASS                            | PASS                   | PASS     |
| C01E filesystem JPG count == completed_frames           | 441                    | 441      |
| C01E all artifacts present                              | manifest+log+summary   | YES      |
| Lane 2 authority leakage in operational code            | ZERO                   | ZERO     |

---

## Final Operational Verdict

```
OPERATIONAL VERDICT: PASS
```

All criteria satisfied:
- Governance drift scan: **PASS** (0 findings, 0 critical, 0 high, 0 warn)
- Forbidden-pattern scan: **CLEAN** (all matches in prohibition docs, test harness, and guard code — zero operational violations)
- C01 300-frame ingest: **PASS** (300/300 frames, 0 failures, 0 retries, all artifacts verified, hashes confirmed live)
- C01E 5-minute endurance: **PASS** (441 frames, 300.671s, 0 failures, 0 retries, all artifacts verified, hashes confirmed live)

---

## Open Issues

None. No governance warnings, no authority drift, no evidence gaps.

---

## Next Recommended Gate

**OI-03: Two-Pi Transfer Gate**

With C01 (300-frame ingest) and C01E (5-minute endurance) both closed at PASS,
the ESP32-CAM evidence campaign is complete for the C01 device. The next
actionable gate per project status lock is OI-03: two-Pi transfer validation,
which requires a second Raspberry Pi 5 to be available.

Prior to OI-03, the following optional actions are available:
- Register C01 and C01E results in the evidence campaign index
- Confirm GAP-16 (USB audio+video contention) is documented against the correct hardware configuration
- Begin CAMPAIGN_01B advisory expansion if advisory lane hardware is available
