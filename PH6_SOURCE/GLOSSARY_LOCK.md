# PH6 / CRAM — Glossary Lock

```text
Document ID: PH6-GLOSSARY-LOCK-1.0
Status: ACTIVE
Purpose: Lock canonical terminology. Synonyms and paraphrases are forbidden
         in authority paths and doctrine documents.
```

---

## Canonical Terms

| Term | Definition | Forbidden Synonyms |
|------|-----------|-------------------|
| **CRAM** | Crash RAM / Cold RAM — the write-first crash-consistent evidence preservation system | memory, cache, store, database |
| **CRAM-0** | Raw intake buffer — first write destination, preserved arrival truth | raw store, intake queue |
| **CRAM-A** | Authoritative PASS evidence store — immutable after commit | PASS store, accepted store |
| **CRAM-R** | DROP reject vault — authoritative negative-result corpus | reject store, failed store |
| **MRAM-S** | Advisory shadow storage — Lane-2 only, Authority ZERO | advisory store, sidecar memory, AI memory |
| **PSEUDO** | Deterministic measurement and adjudication engine | AI judge, ML model, classifier |
| **PSEUDO-M** | Pseudo Mathematics — measurement subsystem, no verdicts | PSEUDO measurement, metrics engine |
| **PSEUDO-A** | Pseudo Assembly Theory — sole PASS/DROP authority | PSEUDO adjudicator, verdict engine |
| **PSEUDO-SCI** | Scientific sideband observability — advisory only | PSEUDO science, SCI layer |
| **Lane 1** | Authority path: CRAM + PSEUDO. Only Lane 1 may produce authoritative truth | authoritative lane, primary lane |
| **Lane 2** | Advisory path: TOK / SoSo / JEDI / AI / Swarm. Authority ZERO | advisory layer, AI lane, secondary lane |
| **Lane 5** | RSYNC export — Priority Zero, must never be blocked | export lane, transfer lane |
| **PASS** | Sole positive verdict from PSEUDO-A | accept, approve, OK, valid, positive |
| **DROP** | Sole negative verdict from PSEUDO-A | reject, fail, deny, negative, invalid |
| **Authority ZERO** | No verdict authority. Cannot issue PASS or DROP | advisory authority, limited authority |
| **SoSo** | Lane-2 drift and instability observer | stability monitor, drift engine, AI observer |
| **JEDI** | Lane-2 bounded research coordinator | research engine, hypothesis engine |
| **TOK** | Token system — Lane-2 advisory continuity objects (RT, VDT, VLT) | token memory, advisory tokens |
| **RT** | Reference Token — CRAM continuity anchor, Authority ZERO | reference, anchor, pointer token |
| **VDT** | Virtual Drift Token — short-lived advisory hypothesis, Authority ZERO | drift token, hypothesis token |
| **VLT** | Virtual Longevity Token — reinforced advisory continuity, Authority ZERO | longevity token, persistence token |
| **AVLT** | Archived Virtual Longevity Token — retired VLT, historical advisory only | archived token, old token |
| **timestamp_utc** | ISO 8601 UTC timestamp string (e.g. `2026-05-06T14:24:00Z`) | timestamp, time, epoch, unix_time |
| **.blake2b marker** | Authoritative commit marker — object is CRAM-A authoritative only when marker exists | sidecar, hash file, checksum file |
| **canonical JSON** | `sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(",",":")` | JSON, serialized, encoded |
| **fixed-point** | Integer metric encoding at scale 10000, using Decimal ROUND_HALF_EVEN | float metric, decimal metric |
| **EvidencePacket** | Sealed authoritative boundary object — Lane-2 data may never enter | evidence record, verdict packet |
| **DRIFT_FAIL** | Architectural violation state — halt and audit | failure, error, mismatch |
| **HRG9** | The production-clearance hardware replay evidence gate — OPEN until all artifacts pass | hardware gate, replay gate |
| **STOP-SHIP** | Production is not cleared. Do not deploy. | held, pending, not ready |

---

## Forbidden Authoritative Event Types

These must never appear in Lane-1 or CRAM audit event logs:

```text
PROMOTE
REJECT
ACCEPT
FLAG
HOLD
REVIEW
RETAIN
```

Allowed event types:

```text
CRAM0_INTAKE
PSEUDO_MEASURE
PSEUDO_ADJUDICATE
CRAM_PASS_COMMIT
CRAM_DROP_COMMIT
CRAM_RECOVERY
EXPORT_START
EXPORT_COMPLETE
RECOVERY_SWEEP
DRIFT_FAIL
```

---

## Fixed-Point Field Names (canonical)

| Metric | Canonical Field Name | Old (forbidden in authority path) |
|--------|----------------------|-----------------------------------|
| Mean brightness | `mean_brightness_fp` | `mean_brightness` |
| Laplacian variance | `laplacian_var_fp` | `laplacian_var` |
| Motion fraction | `motion_fraction_fp` | `motion_fraction` |
| Byte variance | `byte_variance_fp` | `byte_variance` |
| Entropy | `entropy_fp` | `entropy` |

---

## Timestamp Convention

```text
Authority paths:   timestamp_utc  (ISO 8601 UTC string, e.g. "2026-05-06T14:24:00Z")
Non-authoritative: may use float epoch only if clearly labeled non-authoritative
Forbidden mix:     timestamp: time.time() in any schema-facing authority record
```
