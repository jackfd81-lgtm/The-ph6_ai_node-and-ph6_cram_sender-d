# PH6 Acquisition Provenance Schema — v1

```text
Schema ID:        ph6.acquisition.provenance.v1
Version:          1
Lane:             1 (preserved with CRAM-A authoritative evidence)
Authority:        MEASUREMENT_PROVENANCE
Status:           LOCKED
Hash algorithm:   BLAKE2b-256
Doctrine source:  PH6_SOURCE/03_SCIENTIFIC_INSTRUMENT/PH6-SCIENTIFIC-INTEGRITY-EXPANSION-v2.1.md
                  § 2.6 Observer Contamination Doctrine
                  § Environmental Boundedness Law
```

---

## Purpose

This schema formally binds the scientific doctrine established in the Scientific
Integrity Expansion Patch v2.1 to a machine-verifiable, drift-enforceable record
structure.

Without this schema, the epistemic hierarchy is philosophy.
With this schema, the epistemic hierarchy becomes enforceable.

The acquisition provenance record captures the conditions under which a measurement
was taken, alongside the measurement itself. It is a mandatory replay-critical
companion to every CRAM-A authoritative evidence record.

The governing question this schema answers:

> "Under what acquisition conditions was this measurement physically taken,
> and which of those conditions may have influenced what was measured?"

---

## Constitutional Basis

From Observer Contamination Doctrine (§ 2.6):

> PH6 therefore records sensor mode, processing state, timing state,
> synchronization source, illumination state, and acquisition conditions
> as part of evidentiary provenance.

From Environmental Boundedness Law:

> Environmental state is considered part of evidentiary context.

From Replay-Reproducible vs Replay-Stable Interpretation (§ 5.4):

> Preserved measurements, timestamps, deterministic metrics, hashes,
> sequencing, provenance, and audit continuity must remain stable under replay.

---

## Schema Definition

```json
{
  "schema_version": "ph6.acquisition.provenance.v1",
  "sensor_id": "<string — unique sensor identifier>",
  "firmware_id": "<string — sensor or capture firmware version>",
  "sensor_mode": "<string — e.g. continuous | triggered | burst | single>",
  "processing_state": "<string — raw | compressed | enhanced | none>",
  "illumination_state": "<string — ambient | IR | controlled | mixed | unknown>",
  "timing_source": "<string — system_clock | NTP | PPS | GPS | unknown>",
  "sync_source": "<string — local | network | external | none>",
  "capture_timestamp_utc": "<ISO 8601 UTC string>",
  "operational_envelope_id": "<string — identifies characterized operating envelope>",
  "transformation_disclosure": ["<list of named transforms applied before measurement, e.g. gamma_correction>"],
  "observer_contamination_flags": ["<list of known contamination sources, e.g. IR_illumination_active>"],
  "provenance_hash": "<blake2b256 of canonical JSON of this record excluding provenance_hash>"
}
```

---

## Required Fields

All fields below are required. Omitting any constitutes a provenance failure.

| Field | Type | Description |
|-------|------|-------------|
| `schema_version` | string | Must be exactly `"ph6.acquisition.provenance.v1"` |
| `sensor_id` | string | Unique, stable sensor identifier |
| `firmware_id` | string | Firmware/driver version at capture time |
| `sensor_mode` | string | Operating mode of the sensor at capture |
| `processing_state` | string | Transform state of the signal at capture |
| `illumination_state` | string | Illumination conditions at capture |
| `timing_source` | string | Source of the capture timestamp |
| `sync_source` | string | Synchronization authority for the timestamp |
| `capture_timestamp_utc` | string | UTC acquisition timestamp (ISO 8601) |
| `operational_envelope_id` | string | ID of the characterized operating envelope |
| `transformation_disclosure` | array | Named transforms applied; empty list if none |
| `observer_contamination_flags` | array | Known contamination sources; empty list if none |
| `provenance_hash` | string | BLAKE2b-256 of canonical JSON of this record (without this field) |

---

## Forbidden Fields

```text
motion_score
motion_decay_score
verdict
result
advisory_result
```

This record describes acquisition conditions, not measurement verdicts. Verdict
fields have no meaning in provenance context.

---

## Replay Contract

The `provenance_hash` is computed as:

```python
blake2b256(canonical_json({all fields except provenance_hash}))
```

where `canonical_json` is `json.dumps(obj, sort_keys=True, separators=(",", ":"))`.

This makes each provenance record self-verifying: any replay pass can recompute
the hash from the stored fields and confirm the record has not been altered.

The `provenance_hash` must be computed last and written atomically with the record.

---

## Operational Envelope

The `operational_envelope_id` is a stable string identifier that references a
characterized operating environment. Examples:

```text
indoor_controlled_lab_v1
outdoor_daylight_uncharacterized
indoor_low_light_IR_active_v1
uncharacterized_field_conditions
```

If the operating envelope has not been formally characterized, use:
`uncharacterized_field_conditions`

This is not a STOP-SHIP condition, but it must be disclosed.

---

## Observer Contamination Flags

`observer_contamination_flags` is a required array. It may be empty but must be
present. Known flag values:

```text
IR_illumination_active
active_autofocus_engaged
compression_applied
AI_enhancement_active
sensor_polling_contention
multi_sensor_crosstalk
```

Custom flags are permitted. The absence of this field is a schema violation.
An empty array means no contamination is known — which is itself a disclosed claim.

---

## Transformation Disclosure

`transformation_disclosure` is a required array. It may be empty but must be
present. Known transform names:

```text
gamma_correction
white_balance
noise_reduction
sharpening
demosaic
HDR_merge
color_space_conversion
```

Any processing applied to the signal before measurement must appear here.
Undisclosed transforms violate replay determinism.

---

## Integration with CRAM-A

The acquisition provenance record accompanies every CRAM-A evidence object:

```text
CRAM-A object:
  <object_id>_raw.bin              — raw sensor data
  <object_id>_meta.json            — CRAM metadata (ph6.cram.meta.v1)
  <object_id>_provenance.json      — acquisition provenance (this schema)
  <object_id>.sha256               — SHA-256 compat sidecar
  <object_id>.blake2b              — BLAKE2b-256 authority marker (written LAST)
```

The `provenance_hash` in the provenance record and the `authority_hash` in the
CRAM metadata are distinct:

- `authority_hash` = hash of raw measurement + metrics (verdict authority)
- `provenance_hash` = hash of acquisition conditions (provenance integrity)

Both must be preserved and replay-verifiable independently.

---

## Schema Maturation Pipeline

```text
§ 2.6 Observer Contamination Doctrine  →  this schema
Environmental Boundedness Law          →  operational_envelope_id field
§ 5.4 Replay-Stable Interpretation     →  provenance_hash + transformation_disclosure
Epistemic Hierarchy (§ 0.1)            →  required field ordering (physical → semantic)
```

This schema is the machine-verifiable bridge between the v2.1 scientific
doctrine and the PH6 drift enforcement layer.
