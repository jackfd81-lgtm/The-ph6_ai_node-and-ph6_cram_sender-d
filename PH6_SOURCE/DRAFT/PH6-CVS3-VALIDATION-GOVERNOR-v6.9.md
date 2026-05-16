# PH6 CVS-3 Validation Governor

```text
Document ID: PH6-CVS3-VALIDATION-GOVERNOR-1.0
Version:     6.9
Status:      DRAFT
Authority:   Human-authored doctrine. AI may read and apply. AI may not modify.
Created:     2026-05-16
Schema:      ph6.cvs3.doctrine.v1
```

---

## RECLASSIFICATION

| Previous            | Current                        |
| ------------------- | ------------------------------ |
| Validation Suite    | Validation Governor            |
| Test Harness        | Continuous Certification Layer |
| Operational Utility | Governance Subsystem           |

CVS-3 is a PH6 governance subsystem, not a test harness.
Validators are subject to governance, not exempt from it.

---

## CORE VALIDATION LAW

```text
Validators verify truth.
Validators do not create truth.
```

---

## VALIDATION AUTHORITY HIERARCHY (VAH-1.0)

| Layer  | Role                   | Authority      |
| ------ | ---------------------- | -------------- |
| Lane 1 | Operational authority  | PASS/DROP      |
| Lane 2 | Advisory analysis      | NONE           |
| CVS-3  | Verification authority | VERIFY ONLY    |
| Humans | Governance review      | INTERPRET ONLY |

CVS-3 sits outside the Lane 1/Lane 2 authority model.
It observes and reports. It does not adjudicate.

---

## VALIDATOR RULES

Validators MAY:

* observe runtime state
* replay evidence
* verify hashes
* verify schema compliance
* verify replay parity
* verify audit continuity
* emit reports
* emit structured failures
* classify divergence

Validators MUST NOT:

* alter PASS/DROP
* rewrite evidence
* repair corrupted artifacts
* mutate authority state
* rewrite audit chains
* regenerate missing truth
* override runtime evidence
* suppress failures
* auto-heal replay divergence

---

## VALIDATION MODE LOCK (VML-1.0)

### SIMPLE MODE

Purpose: fast operational sanity verification.

Allowed: config checks, schema validation, replay micro-tests, drift scans,
service verification.

Forbidden: stress testing, resource warfare, destructive simulation,
crash injection, endurance campaigns.

---

### NORMAL MODE

Purpose: operational integrity validation.

Allowed: bounded operational load, 300-frame campaigns, replay verification,
RSYNC validation, resource contention tests.

Forbidden: destructive crash injection, thermal assault, power interruption
simulation.

---

### HARD MODE

Purpose: production-lock certification assault.

Allowed: endurance runs, crash simulation, starvation testing, replay torture,
IO warfare, multi-node transfer validation, thermal stress.

Restrictions: authority mutation forbidden; CRAM mutation forbidden;
replay truth may not be altered.

---

## VALIDATOR SELF-GOVERNANCE

Before any validation run:

```text
VERIFY:
- validator hash
- validator schema version
- governance_manifest.json
- schema_lock_registry.json
- forbidden_terms_registry.json
- severity_policy.json
- replay fixture integrity (if applicable)
```

If any fail: VALIDATION RUN INVALID.

Implementation: `ph6/cvs3_preflight.py`

---

## VALIDATOR HASH CONTRACT

Each validator run must emit:

```json
{
  "schema": "ph6.cvs3.preflight.v1",
  "validator_id": "ph6-cvs-<mode>",
  "validator_version": "1.0",
  "validator_hash": "<blake2b-256>",
  "governance_manifest_hash": "<blake2b-256>",
  "schema_registry_hash": "<blake2b-256>",
  "passed": true,
  "failure_count": 0,
  "timestamp_utc": "..."
}
```

---

## REPORT DETERMINISM LAW

Validation reports are authoritative operational artifacts.
Reports must themselves be deterministic.

Reports MUST use:

* canonical JSON (sort_keys=True, separators=(",",":"))
* deterministic field ordering
* UTF-8
* UTC timestamps only
* fixedpoint metrics (scale=10000, ROUND_HALF_EVEN)
* stable field ordering

Reports MUST NOT use:

* locale-sensitive formatting
* unordered maps
* float ambiguity
* machine-specific formatting
* timezone-local timestamps

---

## RUNTIME-DOCUMENT DIVERGENCE (RDD)

Definition: documentation claims a state that runtime evidence does not support.

Rule: runtime evidence is always the authoritative source.

Required RDD failure format (CFC code: G2):

```json
{
  "failure_class": "G2",
  "failure_family": "Governance",
  "severity": "HIGH",
  "authoritative": true,
  "reason": "runtime-document divergence",
  "document_claim": "<what the doc says>",
  "runtime_observation": "<what runtime shows>",
  "authoritative_source": "runtime",
  "timestamp_utc": "..."
}
```

Implementation: `ph6/cfc.make_rdd_failure()`

---

## CANONICAL FAILURE CLASSIFICATION (CFC-1.0)

Implementation: `ph6/cfc.py`

### Failure Families

| Class | Family           | Example codes       |
| ----- | ---------------- | ------------------- |
| G     | Governance       | G1 G2 G3 G4 G5 G6  |
| R     | Replay           | R1 R2 R3 R4 R5 R6  |
| C     | CRAM             | C1 C2 C3 C4         |
| A     | Audit            | A1 A2 A3            |
| S     | Schema           | S1 S2 S3 S4         |
| O     | Operational      | O1 O2 O3 O4         |
| T     | Thermal/Resource | T1 T2               |
| N     | Multi-node       | N1 N2               |
| D     | Determinism      | D1 D2 D3            |

### Severity Levels

```text
CRITICAL > HIGH > MEDIUM > LOW > INFO
```

---

## REPLAY FIXTURE CORPUS (RFC-1.0)

Fixtures are deterministic calibration artifacts.
They must be immutable, hash-locked, and replay-certified.

Required fixture categories:

```text
FIXTURES/
├── entropy_edge/
├── blur_edge/
├── motion_edge/
├── rounding_edge/
├── lowlight_noise/
├── thermal_noise/
├── usb_contention/
├── replay_roundtrip/
├── crash_recovery/
└── multi_node_transfer/
```

Each fixture entry requires:
* content hash (BLAKE2b-256)
* schema_version
* fixture_class
* created_at_utc
* deterministic flag

RFC-1.0 directory structure is registered here as doctrine.
Fixture files are created as evidence runs produce validated artifacts.

---

## TRUE NEXT MILESTONE

The next real PH6 milestone is a validator run whose emitted artifacts
alone can reconstruct authoritative operational truth.

At that point:
* reports become evidence
* replay becomes scientific reproducibility
* governance becomes machine-verifiable
* validator drift becomes detectable
* operational truth becomes reconstructable

That is the transition from:

```text
deterministic system
```

to:

```text
self-auditing deterministic infrastructure.
```

---

## UPDATED PH6 CLASSIFICATION (as of v6.9)

| Area                        | Status        |
| --------------------------- | ------------- |
| Deterministic doctrine      | Strong        |
| Governance maturity         | Strong        |
| Validation architecture     | Strong        |
| Runtime/document separation | Improving     |
| Replay infrastructure       | Medium        |
| Deterministic reporting     | Medium-Strong |
| Validator self-governance   | Emerging      |
| Continuous certification    | Emerging      |
| Self-auditing capability    | Early         |
