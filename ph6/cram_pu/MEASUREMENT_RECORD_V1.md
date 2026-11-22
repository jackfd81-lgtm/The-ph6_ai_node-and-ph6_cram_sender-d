# MEASUREMENT_RECORD_V1 candidate — operator notes

PROPOSED codex-lane2, 2026-09-29; ratified_by=None.

Read [ADR-MR1-20260929](ADR-MR1-20260929.md) for authority, format and recovery decisions.
**Lineup:** Reality → CRAM-0 → PSEUDO-M → PSEUDO-A → CRAM-A/CRAM-R →
one-way membrane → TOK / SoSo / AI → MRAM-S (Authority ZERO).

Structural formats are registered in `schemas/MEASUREMENT_V1_REGISTRY.json`.
Structural JSON Schema validation alone is insufficient: `read_measurements(root)`
replays the original pixels, metrics, disposition, encoding and measurement chain.

The measurement record embeds its acquisition commitment. Required facts map to:

| Requested binding | Field |
|---|---|
| Measurement identity and order | `measurement_id`, `sequence_number` |
| Acquisition clocks | `acquisition.context.timestamp_utc`, `wall_time_ns`, `monotonic_timestamp_ns` |
| Instrument and capture settings | `acquisition.context.sensor`, `capture_configuration` |
| Original image dimensions, pixel format and layout | `acquisition.dimensions`, `pixel_format`, `layout` |
| Original acquisition hash | `acquisition.acquisition_byte_hash`, `hash_algorithm` |
| PSEUDO version, thresholds and numerical versions | `pseudo.version`, `configuration`, `configuration_hash`, `library_versions` |
| Metric inputs and results | `pseudo.inputs`, `pseudo.metrics` |
| Host thermal and I/O observations | `acquisition.context.thermal_state`, `io_state` |
| Authoritative disposition | `disposition`, `reasons` |
| Derived JPEG bytes and encoding | `encoded_payload` |
| Chain | `previous_record_hash`, `record_hash` |

Create each camera campaign in a **new empty directory**. Use `--advisory-socket`
to select a separate campaign socket. An absent socket is acceptable for capture;
it is recorded as failed admission and discovery can recover committed PASS records.
Do not register a store by sending a hint: the worker requires explicit `--cram-store`.

After stopping the Lane-1 owner, `MeasurementWriter(root)` validates the full existing
namespace and resumes only a structurally valid pending tail. This is a write-capable
Lane-1 recovery operation. To inspect without recovery, use `read_measurements(root)`.
Neither operation should be applied to migrate a legacy evidence namespace.

An isolated worker can use the existing entry point:

```sh
python3 -B -m ph6.ssmt.worker --require-limits \
  --socket /run/user/1000/ph6-mr1-test/input.sock \
  --root /var/ph6/mram-s/swarms/new-candidate-namespace \
  --cram-store /path/to/new/capture/cram_store
```

The SSMT writer requires an output namespace beneath `/var/ph6/mram-s/swarms/`;
an arbitrary home-directory output correctly fails its existing write-boundary check.
Run that command only inside the established advisory resource cage. The example
is not an instruction to change the installed service. The delivery report includes
the exact isolated campaign configuration that was exercised.

Consumers must inspect coverage health as well as token count. A historical RT may
remain in an immutable advisory audit after its source becomes unavailable; its
existence is not a current provenance validation or permission to change CRAM.
