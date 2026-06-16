# PH6 Scientific Evidence Instrument Doctrine

**Schema:** ph6.governance.scientific.instrument_doctrine.v1  
**Status:** PROPOSED  
**Proposed by:** claude-code-lane2 | **Ratified by:** null

---

## 1. Instrument Definition

PH6 is not merely a software system, embedded system, or scientific computing stack.

**PH6 is a scientific evidence instrument.**

Its purpose is to observe reality, capture measurements, preserve evidence, validate results, certify replay, and allow AI to learn from the environment without corrupting the original evidence chain.

---

## 2. Mandatory Observation Chain

This order is mandatory. No step may be skipped or reordered.

```
Observation
  → Measurement
  → Preservation
  → Validation
  → Certification
  → Audit
  → Replay
  → Review
```

No optimization, AI process, compression method, token mapping, or UI convenience may violate this order.

---

## 3. Non-Negotiable Properties

Every PH6 measurement must satisfy all eight:

```
1. Determinism      — same input + same config = same output, always
2. Auditability     — every decision has a traceable record
3. Replayability    — any evidence packet can be replayed to produce the same result
4. Chain of custody — unbroken record from capture to review
5. Authority isolation — AI advisory is never mixed with deterministic verdict
6. Evidence immutability — CRAM evidence is never mutated after preservation
7. Measurement sovereignty — sensor output is not automatically measurement truth
8. Replay certification — replay match is required before evidence is certified
```

If any property cannot be satisfied, the measurement is not PH6-grade evidence.

---

## 4. Runtime Architecture

```
Reality
  ↓
Sensors
  ↓
CRAM-0           (raw intake — preserve before interpret)
  ↓
PSEUDO-M         (deterministic measurement)
  ↓
PSEUDO-A         (deterministic PASS / DROP adjudication)
  ↓
CRAM-A           (accepted PASS evidence — immutable)
CRAM-R           (rejected DROP evidence — immutable)
  ↓
PSEUDO-SCI       (scientific metric extension, certification, repeatability)
  ↓
SoSo             (continuity mapping, drift, context)
  ↓
MRAM-S           (advisory memory — authority ZERO)
  ↓
RSYNC / Export / Review
```

Each layer operates at or above the layer that produced its input. No layer may modify a prior layer's output.

---

## 5. Sensor Sovereignty

Sensor output is not automatically measurement truth.

Sensor output may contain: noise, drift, bias, saturation, compression artifacts, focus errors, exposure errors, temperature effects, environmental distortion, firmware artifacts, and hardware timing defects.

Required chain:

```
Reality → Sensor → Normalization → Measurement → Interpretation → Adjudication → Preservation
```

**A sensor may observe. A measurement system must measure. An adjudication system must judge. An AI system may only advise.**

---

## 6. Evidence Classes

| Class | Description | Authority |
|-------|-------------|----------|
| CRAM-E | Original CRAM evidence | Lane 1 — highest |
| CRAM-D | Derived evidence | Lane 1 secondary |
| CRAM-H | Hypothesis evidence | Lane 1 candidate — requires validation |
| CRAM-R | Negative/rejected evidence | Lane 1 — immutable DROP record |
| MRAM-S | Advisory memory | Lane 2 — authority ZERO |
| TOKEN-G | Token topology graph | Lane 2 — advisory reference only |
| REPLAY-C | Replay certification output | Lane 1 — required for certification |

---

## 7. Replay Certification Rule

```
Same evidence
Same config
Same code (same hash)
Same thresholds
Same sensor profile
Same normalization
Same replay engine

Must produce:
  same metrics
  same verdict
  same hashes
  same audit record class
```

Replay failure is not ignored. It creates: CRAM-R record, audit warning, certification failure, operator review requirement, and gap register entry.

---

## 8. Relationship to Legal Review

PH6 CRAM evidence + PSEUDO verdict + replay certification constitute the candidate chain for FRE 702 review.

AI advisory output (Lane 2, MRAM-S, SoSo) supports review but is never a FRE 702 candidate independently.

The chain must answer:
```
What was measured?
How was it measured?
What method was used?
What is the error rate?
How was it validated?
Where does interpretation begin?
Who controlled the instrument?
Is the record unmodified?
Can it be replayed?
```

---

*Lane-2 advisory document. Operator ratification required.*
