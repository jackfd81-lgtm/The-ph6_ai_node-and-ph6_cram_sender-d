# PH6 Courtroom Evidence Readiness Matrix

**Schema:** ph6.governance.courtroom_evidence_readiness.v1  
**Status:** PROTOTYPE_PARTIAL — gap analysis only, not a claim of admissibility  
**Proposed by:** claude-code-lane2 | **Ratified by:** null  
**Standard reference:** Federal Rule of Evidence 702; NIST SP 800-86; ISO/IEC 17025

---

## Summary

| State | Count |
|-------|-------|
| PRESENT | 3 |
| PARTIAL | 9 |
| NOT_PRESENT | 2 |
| **Total categories** | **14** |
| Blocking gaps | **0** |
| Prototype grade | PARTIAL_READINESS |

No gaps currently block prototype operation. All gaps are improvement targets for the finished device.

---

## Readiness Matrix

| Category | State | Current Evidence | Gap |
|----------|-------|-----------------|-----|
| Operator identity | PARTIAL | hostname in run manifest; no formal operator_id | No operator_id or login record in run_status.json |
| Device identity | PARTIAL | hostname + model in session boot; camera roles established | No serialized hardware manifest; camera serials not captured |
| Method version | PARTIAL | test_registry.json provides method_id and command | No method_version field; git HEAD not in run artifacts |
| Script hash | NOT_PRESENT | Script path recorded; hash not captured | Script could be modified after execution without detection |
| Config hash | NOT_PRESENT | No independent config structure | Runtime parameters not independently hashed |
| Sensor calibration state | PARTIAL | brightness and entropy parsed; Camera B=PRIMARY | No structured calibration record; focus mode not captured |
| Raw artifact manifest | PARTIAL | artifacts list in run_status.json; no file hashes | Output files listed but not hashed |
| CRAM chain | PRESENT | CRAM audit chain; .blake2b markers; RSYNC export mandatory | Export receipt not always linked to desktop run artifacts |
| Replay result | PRESENT | REPLAY_PARITY in CRAM harness; 20/20 checks pass | Replay not run as standard step in every production test |
| Error rate | PARTIAL | motion_fraction and frame counts in stdout; DROP verdicts recorded | No structured error_rate summary field in run artifacts |
| Known limitations | PARTIAL | Production clearance declaration bounds scope | Known limitations not in every run artifact |
| AI/advisory boundary | PRESENT | Lane-1/Lane-2 enforced; PASS/DROP only from Lane-1; Authority:ZERO | Boundary in code but not always explicit in run artifact JSON |
| Report generation | PARTIAL | Markdown + JSON for certification runs; not all run types | Report format not standardized across all test registry entries |
| Chain of custody | PARTIAL | CRAM audit chain; run_status.json; git history | No unified custody_chain.json per run |

---

## Detail By Category

### Operator Identity
**FRE 702 question:** Who operated the system?  
**Required:** operator_id, login_timestamp_utc, hostname, session_id  
**Action:** Add operator_id to run_status.json and session boot record

### Device Identity
**FRE 702 question:** What device was used?  
**Required:** device serial numbers, camera IDs (A and B), firmware version, Pi model  
**Action:** Add hardware_manifest.json per run including `lsusb`, `v4l2-ctl` output

### Method Version
**FRE 702 question:** What validated method was used?  
**Required:** method_id, method_version, registry_entry_id, git_head  
**Action:** Add method_version and git_head to run_status.json

### Script Hash
**FRE 702 question:** Is the method unchanged from when it was validated?  
**Required:** script_path, script_blake2b, script_sha256  
**Action:** Hash test script at preflight time; record in run_status.json

### Config Hash
**FRE 702 question:** Were the parameters the same as the validated configuration?  
**Required:** config_path, config_blake2b  
**Action:** Define config structure per test method; hash at preflight

### Sensor Calibration State
**FRE 702 question / ISO 17025:** Was the instrument calibrated?  
**Required:** focus_mode, exposure_mode, brightness_baseline, entropy_baseline, known_limitations  
**Action:** Add calibration_state to run artifacts with v4l2-ctl values

### Raw Artifact Manifest
**Chain of custody question:** What files were produced and are they unmodified?  
**Required:** artifact_path, artifact_blake2b, artifact_sha256, size_bytes, timestamp_utc  
**Action:** Hash each artifact at test completion; add to run_status.json

### CRAM Chain
**Chain of custody:** Unbroken from ingest through preservation to export.  
**State: PRESENT** — CRAM audit chain, .blake2b markers, RSYNC export mandatory. Gap: export receipt not always linked to desktop run directory.

### Replay Result
**Reproducibility:** Same input → same hash output.  
**State: PRESENT** — REPLAY_PARITY passes in CRAM harness. Gap: not automated in every production run.

### Error Rate
**FRE 702 question:** What is the known error rate?  
**Required:** drop_rate, read_failure_count, frame_loss_count, sensor_drift_indicators  
**Action:** Add error_rate section to run completion record

### Known Limitations
**FRE 702 question:** What are the scope and validity constraints?  
**Required:** scope_bounds, environmental_bounds, known_failure_modes, exclusions  
**Action:** Add known_limitations to test registry entries and run artifacts

### AI/Advisory Boundary
**FRE 702 / NIST AI RMF question:** Is AI interpretation distinguishable from measurement?  
**State: PRESENT** — Lane-1/Lane-2 boundary enforced. PASS/DROP only from Lane-1. SoSo labeled PROPOSED. Authority:ZERO in UI. Gap: authority_statement not always explicit in run artifact JSON.

### Report Generation
**Completeness:** Human-readable + machine-readable summary.  
**Action:** Standardize report format; require both human/JSON for all registered tests

### Chain of Custody
**Courtroom question:** Unbroken custody from acquisition to presentation.  
**Action:** Add custody_chain.json per run linking acquisition → preservation → export → report

**Storage doctrine note:** Git history records *code* history, not *evidence* custody. The chain of custody must be established by CRAM audit chain, storage manifests, and export records — not by git commit history. Git is a prototype source-control layer; evidence authority must be backend-agnostic and must survive without git in production.

---

## Improvement Priority

| Priority | Action | Category |
|----------|--------|----------|
| High | Add script hash to preflight + run_status.json | Script hash |
| High | Add git_head and method_version to run_status.json | Method version |
| High | Add hardware_manifest.json per run | Device identity |
| Medium | Add operator_id to run_status.json | Operator identity |
| Medium | Standardize report format across all registry entries | Report generation |
| Medium | Add error_rate section to run completion | Error rate |
| Low | Add custody_chain.json per run | Chain of custody |
| Low | Add calibration_state with v4l2-ctl values | Calibration |

---

*Lane-2 advisory document. This is a design target, not a claim of current admissibility. Operator ratification required.*
