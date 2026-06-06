# PH6 Governance INFO Hit Delta Report

**Schema:** ph6.governance.info_delta_report.v1  
**Generated:** 2026-06-06T10:30:00Z  
**Proposed by:** claude-code-lane2 | **Ratified by:** null  
**Scan root:** `/home/jack/PH6_SOURCE`

---

## Summary

| Metric | Value |
|--------|-------|
| Previous baseline INFO count | 7 |
| Current INFO count | 27 |
| Delta | +20 |
| Blocking hits | 0 |
| Verdict | ALL_NON_BLOCKING |

## Why the Count Changed

The previous baseline of 7 INFO hits was measured against a `/home/jack` full scan. Those 7 hits were all in `ph6/` (simulation constants, test guards, isolation proofs). They do **not** appear when scanning only `PH6_SOURCE/`.

The current 27 INFO hits are entirely from `PH6_SOURCE/` test scripts and the schema ontology. The delta is a **scope change**, not a real violation growth.

## Classification Table

| Classification | Count | Description |
|----------------|-------|-------------|
| DOCUMENTATION_REFERENCE | 7 | Docstrings that document which fields are forbidden — not usages |
| TEST_REFERENCE | 7 | Run artifact copies of canonical test scripts; one comment explicitly denying usage |
| DETECTOR_REFERENCE | 0 | — |
| LEGACY_REFERENCE | 0 | — |
| CLEANUP_RECOMMENDED | 0 | — |

## Detail

### DOCUMENTATION_REFERENCE (7 unique files × 2 terms = 14 findings)

All six active test scripts in `TESTS/DUAL_USB_CAMERA/` carry a docstring line of the form:
```
- motion_fraction ONLY — motion_score / motion_decay_score FORBIDDEN
```
This is correct and required — it documents the prohibition at the top of every test file.

The schema ontology at `04_SCHEMAS/PH6-MEASUREMENT-ONTOLOGY-SCHEMA-v1.0.md:585` lists `adaptive_threshold` in its forbidden-terms vocabulary. Also correct.

None of these represent actual field usage.

### TEST_REFERENCE (6 run artifact copies + 1 comment = 13 findings)

Five certification run snapshots under `TESTS/DUAL_USB_CAMERA/cert_v2_1/20260603_*/scripts/` each contain a copy of `ph6_dual_camera_certification_v2_1.py`. These are immutable evidence artifacts produced by completed test runs. Their prohibition docstrings generate hits for both `motion_score` and `motion_decay_score`.

`TESTS/CAMERA_BENCHMARK/stage4_area_math_scan.py:37` contains the comment:
```
No field named motion_score or motion_decay_score is computed or stored
```
This explicitly asserts non-usage — the opposite of a violation.

## Action Required

None. All 27 INFO hits are non-blocking.

**Recommended CLAUDE.md update:** change the governance baseline expected INFO count from 7 to 27, and note that the canonical scan root is `/home/jack/PH6_SOURCE` (not `/home/jack`). The old 7 were from a different scan scope and no longer apply.

---

*Lane-2 advisory report. No authority changes. No canon writes. Operator ratification required before this document is considered authoritative.*
