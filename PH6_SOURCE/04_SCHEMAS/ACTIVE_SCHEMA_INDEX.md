# Active Schema Index

```text
Document ID:    PH6-ACTIVE-SCHEMA-INDEX-1.0
Status:         ACTIVE
Source:         PH6_SOURCE/GOVERNANCE/schema_lock_registry.json
Hash algorithm: BLAKE2b-256
SHA256:         COMPATIBILITY_ONLY
```

All schemas below are LOCKED. Version bump required for any change.

---

## Lane 0 — Origin / Transit (no authority)

| Schema ID | Version | Authority | Notes |
|-----------|---------|-----------|-------|
| `ph6.raw_departure.v1` | 1 | NONE | Sensor departure packet |
| `ph6.raw_arrival.v1` | 1 | NONE | Sensor arrival packet |
| `ph6.governance.manifest.v1` | 1 | GOVERNANCE | Machine-readable authority source |

---

## Lane 1 — Authority (PASS/DROP)

| Schema ID | Version | Authority | Notes |
|-----------|---------|-----------|-------|
| `ph6.pseudo_verdict.v1` | 1 | LANE_1 | PSEUDO deterministic verdict |
| `ph6.cram_commit.v1` | 1 | LANE_1 | CRAM atomic commit |
| `ph6.drop_shedding.v1` | 1 | LANE_1 | DROP shedding record |
| `ph6.cram_audit.v1` | 1 | LANE_1 | Audit chain — atomic, fsync-guaranteed |
| `ph6.cram_pu.receipt.v1` | 1 | LANE_1 | CRAM-PU run receipt |

---

## Lane 2 — Advisory (Authority ZERO)

| Schema ID | Version | Authority | Notes |
|-----------|---------|-----------|-------|
| `ph6.audit_event.v1` | 1 | NONE | Lane-2 advisory audit; authority_hash = 64 zeros |
| `ph6.mram_s.advisory.v1` | 1 | NONE | MRAM-S advisory output |
| `ph6.ssmt.audit_event.v1` | 1 | NONE | SSMT advisory audit |
| `ph6.tok.advisory_event.v1` | 1 | NONE | TOK advisory |
| `ph6.soso.advisory.v1` | 1 | NONE | SoSo-family advisory output |

---

## Lane 2 — Governance Reporting

| Schema ID | Version | Authority | Notes |
|-----------|---------|-----------|-------|
| `ph6.governance.drift_report.v1` | 1 | NONE | Output of governance_drift_scan.py |
| `ph6.governance.preflight_report.v1` | 1 | NONE | Output of ai_preflight_check.py |

---

## Lane 5 — Export (Priority Zero)

| Schema ID | Version | Authority | Notes |
|-----------|---------|-----------|-------|
| `ph6.rsync_queue.v1` | 1 | EXPORT_SOVEREIGN | RSYNC Priority Zero |

---

## Universal Forbidden Fields

```text
motion_score
motion_decay_score
```

These must not appear in any schema output regardless of lane.

---

## Lane 2 Forbidden Fields

```text
verdict
result  (when implying authority)
```

`advisory_result` is the required substitute for Lane 2 outputs.

---

## Authority Sentinel

```text
Lane 2 authority_hash value = 0000000000000000000000000000000000000000000000000000000000000000
(64 zeros — marks Authority ZERO, not a hash of content)
```

---

## Source Registry

```text
PH6_SOURCE/GOVERNANCE/schema_lock_registry.json
```
