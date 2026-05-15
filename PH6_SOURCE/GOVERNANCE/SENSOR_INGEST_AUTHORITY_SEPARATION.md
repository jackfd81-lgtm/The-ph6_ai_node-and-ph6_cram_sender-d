# PH6 Doctrine: Sensor Ingest Degradation vs Authority Logic Failure

```text
Document ID: PH6-GOVERNANCE-SENSOR-INGEST-SEPARATION-1.0
Status:      ACTIVE
Created:     2026-05-15
Authority:   Human-authored doctrine. AI may read and apply. AI may not modify.
Derived from: GAP-16 evidence campaign — AV contention + isolation test
```

---

## Core Principle

```text
Sensor ingest degradation shall not be classified as an authority failure unless
it causes Lane 1 to issue a non-deterministic verdict, corrupt CRAM state,
violate replay parity, alter PASS/DROP semantics, or permit Lane 2 authority leakage.

Degraded sensor input must be recorded, flagged, and preserved as degraded-quality
evidence. Lane 1 remains valid if it records the degradation explicitly and applies
the same deterministic rules during replay.
```

---

## Definitions

### Lane 0 / Sensor Ingest Degradation

Lane 0 is the physical sensor layer — camera hardware, microphone, USB transport,
frame timing. Failures here are **input quality problems**.

Examples:
```text
- USB camera FPS drops from ~30 FPS to ~20 FPS under bus load
- Audio RMS rises or clips (peak = 32767) under simultaneous USB capture
- Camera disconnects from USB bus
- USB device disappears from lsusb
- Frame timing becomes unstable or irregular
- Audio overruns from driver buffer contention
```

This affects the **quality, completeness, or reliability of incoming sensor data**.
It does **not automatically mean PH6 made a wrong decision**.

### Lane 1 / Authority Logic

Lane 1 is the deterministic CRAM + PSEUDO path. Failures here are **authority defects**.

Examples:
```text
- PASS/DROP verdict logic becomes non-deterministic
- CRAM write contract violated (missing .blake2b marker, torn file, hash mismatch)
- Hash chain broken
- Replay parity lost
- Authority boundary crossed (Lane 2 influencing PASS/DROP)
- SoSo advisory containing verdict, result, pass, or drop fields
```

---

## The Separation Rule

```text
Sensor ingest degradation = Lane 0 / measurement-condition problem

It becomes a Lane 1 authority problem only if PH6:
  1. Hides the degradation from the evidence record
  2. Misclassifies degraded input as nominal-quality input
  3. Lets degradation change deterministic verdict rules during replay
  4. Corrupts CRAM state as a result of degraded input
  5. Breaks replay parity because degradation was not recorded
  6. Allows Lane 2 / SoSo / AI to influence PASS/DROP in response to degradation
```

---

## Required Response to Sensor Ingest Degradation

When Lane 0 degradation is detected, the system **must**:

1. Record actual observed metrics (FPS, RMS, peak, overruns, disconnect timestamp)
2. Not assume nominal values — never apply default FPS or default audio quality
3. Classify the evidence packet with its actual measured quality
4. Preserve degraded-quality packets in CRAM-0 with degradation metrics intact
5. Allow Lane 1 to apply the same deterministic verdict rules to degraded input
6. Flag degraded packets distinctly from nominal packets in CRAM-A or CRAM-R

---

## Evidence Basis

This doctrine is derived from GAP-16 (Microdia USB AV Contention):

```text
GAP-16A confirmed: simultaneous AV causes ~33% FPS drop and audio clipping.
GAP-16B confirmed: disconnects occur under AV load, not under video-only load.

In all cases:
  Lane 1 / PSEUDO / SoSo authority: UNAFFECTED
  CRAM write contract:               UNAFFECTED
  Hash chain:                        UNAFFECTED
  Replay parity:                     UNAFFECTED
  PASS/DROP semantics:               UNAFFECTED

The sensor hardware degraded.
PH6 authority logic did not fail.
```

---

## Glossary Additions (pending GLOSSARY_LOCK update)

| Term | Definition |
|---|---|
| **Lane 0** | Physical sensor layer — camera, microphone, USB transport, frame timing. Not an authority layer. Failures here are sensor ingest degradation, not authority defects. |
| **Sensor ingest degradation** | Reduction in sensor data quality, completeness, or reliability at Lane 0. Must be recorded; does not automatically constitute an authority failure. |
| **Degraded-quality evidence** | A CRAM packet where observed metrics fall outside nominal ranges. Preserved as-is; Lane 1 verdict applies same rules. |
