# PH6 / CRAM System Status Report
## Deterministic Scientific Evidence Instrument
## Architecture, Runtime Health, and Production-Clearance Gates

```text
Document ID: PH6-SYSTEM-OVERVIEW-v1.0
Classification: SYSTEM STATUS / ARCHITECTURE REFERENCE
Status: DRAFT / ACTIVE DEVELOPMENT REFERENCE
Primary Home: Book 0 — Interpretive Control Plane
Authority Rule: PSEUDO-A remains sole PASS/DROP authority.
```

---

## 0. Executive Summary

PH6 / CRAM is a deterministic scientific evidence system designed to preserve, measure,
adjudicate, replay, and export sensor-derived evidence without allowing advisory AI to
control truth decisions.

The system is organized around strict lane separation:

```text
Lane 1: CRAM + PSEUDO
Authority path.
Preserves evidence and issues deterministic PASS / DROP verdicts.

Lane 2: SoSo / JEDI / Tokens
Advisory path only.
Observes instability, drift, topology, and research patterns.

Lane 5: RSYNC / Export
Priority Zero.
Export must never be blocked by AI, advisory processing, or heavy analysis.
```

Current architectural posture:

```text
PH6 is held in scientific pre-production status.

The system has working deterministic calibration evidence.
CRAM-PU-LIVE-1.0 has passed fresh-checkout verification.
Failure injection is active.
Hailo integration is deferred because a new Raspberry Pi 5 is required.
The next actionable production-clearance gate is the two-Pi live transfer test.
```

---

## 1. System Architecture & Inventory

| Component                 | PH6 Role                                    | Authority                | Status                  | Infrastructure                                 |
| ------------------------- | ------------------------------------------- | ------------------------ | ----------------------- | ---------------------------------------------- |
| **Sensor / Media Intake** | Captures raw physical-world data            | None                     | Active                  | USB media, camera devices, future sensor buses |
| **CRAM-0**                | Raw intake preservation layer               | Evidence-preserving      | Active / Required       | NVMe-backed storage                            |
| **PSEUDO / CRAM-PU**      | Deterministic adjudication engine           | **Lane 1 Authority**     | Active                  | Python deterministic gates                     |
| **CRAM-A**                | Authoritative accepted evidence store       | Authoritative PASS store | Active / Required       | NVMe CRAM                                      |
| **CRAM-R**                | Rejected evidence vault                     | DROP record store        | Active / Required       | NVMe CRAM                                      |
| **Audit Chain**           | Hash-chained event record                   | Authoritative record     | Active / Required       | `.blake2b`, canonical JSON                     |
| **Replay Engine**         | Reproduces verdicts from preserved evidence | Verification layer       | Active / Required       | Deterministic replay scripts                   |
| **SoSo**                  | Instability and drift observer              | **Authority ZERO**       | Advisory                | MRAM-S only                                    |
| **JEDI**                  | Bounded exploratory swarm/research layer    | **Authority ZERO**       | Advisory / Experimental | Book V / MRAM-S                                |
| **Tokens**                | Advisory continuity/topology memory         | **Authority ZERO**       | Advisory                | `/var/ph6/mram-s/tokens/`                      |
| **RSYNC Export**          | Evidence export and transfer path           | Priority Zero            | Required                | Lane 5                                         |
| **Hailo-8L Node**         | Future AI accelerator support               | Advisory only            | **On Hold**             | Requires new Raspberry Pi 5                    |
| **Two-Pi Live Transfer**  | Production-clearance hardware gate          | Validation gate          | **Next Action**         | Pi-to-Pi live transfer                         |

---

## 2. PH6 Lane Model

| Lane         | Name                         | Function                                    | May Decide PASS/DROP? | May Write CRAM?      | Notes                 |
| ------------ | ---------------------------- | ------------------------------------------- | --------------------- | -------------------- | --------------------- |
| **Lane 0**   | Physical Reality             | Real-world sensor events                    | No                    | No                   | Source of measurement |
| **Lane 0.5** | Smart Spigot / Pre-Admission | Optional DROP-only filtering                | No PASS authority     | Limited / controlled | Cannot create truth   |
| **Lane 1**   | CRAM + PSEUDO                | Preservation and deterministic adjudication | **Yes**               | **Yes**              | Sole authority path   |
| **Lane 2**   | SoSo / JEDI / AI / Tokens    | Advisory observation and research           | **No**                | No CRAM writes       | Authority ZERO        |
| **Lane 5**   | RSYNC / Export               | Evidence export and transfer                | No                    | Export only          | Must never be blocked |

Core invariant:

```text
Preserve first.
Measure deterministically.
Investigate separately.
Advise without authority.
Decide only in Lane 1.
```

---

## 3. Real-Time Performance & Health Metrics

## 3.1 PH6 Scientific Health Summary

| Metric                        | Meaning                                    | Current / Target Status  |
| ----------------------------- | ------------------------------------------ | ------------------------ |
| **Frame Count Validity**      | Test run must meet minimum frame count     | No test under 300 frames |
| **Repeatability**             | Same input produces same metrics/verdicts  | Required                 |
| **Deterministic Mismatches**  | Any difference across repeated runs        | Must be `0`              |
| **CRAM Commit Integrity**     | Atomic write + hash sidecar correctness    | Required                 |
| **Replay Parity**             | Replay output matches original result      | Required                 |
| **RSYNC Non-Blocking**        | Export cannot be starved by analysis       | Required                 |
| **Lane-2 Isolation**          | SoSo/JEDI cannot affect PASS/DROP          | Required                 |
| **Failure Injection Status**  | System rejects known unsafe conditions     | Required                 |
| **Thermal / Power Stability** | No undervoltage or throttling during tests | Required                 |

---

## 4. Current Operational Status

## 4.1 Known Verified Work

```text
USB calibration pipeline: PASS
Files found: 18
Repeat passes: 3
Deterministic: True
Mismatches: 0
Selected/copied: 5
```

Interpretation:

```text
18 media files were detected.
Each was evaluated multiple times.
All repeated readings matched.
No deterministic mismatches occurred.
25% calibration subset was saved to NVMe.
Original USB media was preserved read-only after remount.
```

CRAM-PU-LIVE-1.0 status:

```text
CRAM-PU-LIVE-1.0: LOCKED
Fresh-checkout verification: PASS
Schema validation: PASS
Failure injection: 8/8 PASS
.blake2b sidecars: present for PASS commits
Source drift: none
```

The important difference:

```text
Before:
The system proved it could run.

Now:
The system proves it can reject architectural violations.
```

---

## 5. PH6 Failure Injection Coverage

| Failure Case                 | Expected PH6 Behavior           |
| ---------------------------- | ------------------------------- |
| Missing arrival packet       | Reject / fail validation        |
| Corrupted payload hash       | Reject                          |
| Sequence gap                 | Reject                          |
| Tampered CRAM hash           | Reject                          |
| Lane-2 leakage               | Reject                          |
| Illegal PASS shedding        | Reject                          |
| Unlogged DROP shedding       | Reject                          |
| Broken CRAM hash continuity  | Reject                          |
| RSYNC starvation             | Reject as architectural failure |
| Replay mutation              | Reject                          |
| Authority escalation attempt | Reject                          |

Core rule:

```text
Failure injection is the difference between "it runs" and "it defends the architecture."
```

---

## 6. AI-Consumable PH6 Status Payload

```json
{
  "system_id": "PH6-CRAM",
  "timestamp_utc": "2026-05-06T14:24:00Z",
  "system_class": "deterministic_scientific_evidence_instrument",
  "status": "HELD_PRE_PRODUCTION",
  "release_verdict": "STOP_SHIP_PENDING_PRODUCTION_CLEARANCE",
  "core_invariant": "Preserve first. Measure deterministically. Investigate separately. Advise without authority. Decide only in Lane 1.",
  "authority_model": {
    "lane_1_authority": "PSEUDO_CRAM_PU",
    "pass_drop_authority": "LANE_1_ONLY",
    "lane_2_authority": "ZERO",
    "rsync_priority": "PRIORITY_ZERO"
  },
  "storage_model": {
    "cram_0": {
      "role": "raw_intake_preservation",
      "authoritative": true
    },
    "cram_a": {
      "role": "authoritative_pass_store",
      "commit_marker": ".blake2b",
      "authoritative": true
    },
    "cram_r": {
      "role": "drop_reject_vault",
      "authoritative": true
    },
    "mram_s": {
      "role": "advisory_sidecar_memory",
      "authoritative": false,
      "allowed_writers": ["SoSo", "JEDI", "TOKENS"]
    }
  },
  "determinism_status": {
    "minimum_valid_frame_count": 300,
    "repeatability_required": true,
    "deterministic_mismatches_allowed": 0,
    "canonical_json_required": true,
    "nan_allowed": false,
    "fixed_precision_required": true
  },
  "latest_verified_results": {
    "usb_calibration": {
      "verdict": "PASS",
      "files_found": 18,
      "repeat_passes": 3,
      "deterministic": true,
      "mismatches": 0,
      "selected_25_percent_count": 5,
      "original_media_written": false
    },
    "cram_pu_live_1_0": {
      "status": "LOCKED",
      "fresh_checkout_verification": "PASS",
      "schema_validation": "PASS",
      "failure_injection_passed": 8,
      "failure_injection_total": 8,
      "blake2b_sidecars_present": true,
      "source_drift": false
    }
  },
  "open_items": [
    {
      "id": "OI-01",
      "name": "Hailo wiring",
      "status": "ON_HOLD",
      "reason": "Requires purchase of new Raspberry Pi 5",
      "classification": "hardware_gated_not_proof_defect"
    },
    {
      "id": "OI-03",
      "name": "Two-Pi live transfer",
      "status": "NEXT_ACTIONABLE_GATE",
      "purpose": "production_clearance"
    }
  ],
  "active_incidents": [],
  "forbidden_conditions": [
    "lane_2_pass_drop_authority",
    "ai_threshold_mutation",
    "reverse_authority_path",
    "unlogged_drop_shedding",
    "silent_pass_shedding",
    "rsync_blocking",
    "replay_mutation",
    "hash_chain_break"
  ]
}
```

---

## 7. Architectural Considerations

## 7.1 Observability

PH6 observability should be framed as:

```text
Hash-chained audit events.
Deterministic replay receipts.
Canonical manifests.
Failure-injection reports.
Run summaries.
PostRun coherence reports.
```

OpenTelemetry-style telemetry may exist but must remain non-authoritative.

## 7.2 Resiliency

PH6 resiliency means:

```text
Crash-consistent writes.
Replayable evidence.
Atomic commits.
No silent shedding.
No Lane-2 authority promotion.
No RSYNC starvation.
```

Critical write contract:

```text
write(tmp) → fsync(fd) → rename → fsync(dir)
```

## 7.3 Scalability

PH6 scaling means:

```text
More sensors.
More ingest lanes.
More deterministic workers.
More CRAM storage.
More export capacity.
More replay capacity.
```

Authority must remain narrow:

```text
Scaling compute must not scale authority.
```

---

## 8. Architect Note

```text
Current PH6 posture is stable but not production-cleared.

The system has demonstrated deterministic media calibration, CRAM-PU-LIVE-1.0
fresh-checkout verification, schema validation, failure-injection coverage,
and hash-sidecar generation.

The next meaningful gate is not more doctrine.

The next meaningful gate is live hardware transfer validation:

Sensor / Source Node
  → transfer continuity
  → arrival verification
  → PSEUDO verdict
  → CRAM commit
  → replay proof
  → RSYNC export verification

Hailo integration should remain recorded as ON HOLD until a new Raspberry Pi 5
is available.
```

---

## 9. Final Review Verdict

Structure: **Good** — professional and AI-readable.

Content rule: PH6 must not be framed as a cloud/microservice platform.

PH6 speaks the language of:

```text
scientific evidence preservation
deterministic adjudication
CRAM integrity
Lane-1 authority
Lane-2 advisory isolation
replay parity
failure injection
RSYNC non-blocking export
hardware-gated production clearance
```

```text
This should not be written like a SaaS status page.

It should be written like a deterministic instrument qualification report.
```
