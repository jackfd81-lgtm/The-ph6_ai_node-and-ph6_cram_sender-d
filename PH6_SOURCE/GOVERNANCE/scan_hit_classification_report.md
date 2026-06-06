# PH6 / CRAM — Scan Hit Classification Report

Generated UTC: 2026-05-29T19:48:45+00:00

## Summary

- Total hits reviewed: 600
  - Open material: 300
  - Forbidden authority drift: 300
- Hit cap per scan: 300

## Classification Counts

| Label | Count |
|-------|-------|
| REAL_AUTHORITY_PATH_VIOLATION | 0 |
| DETECTOR_DEFINITION | 104 |
| DOCUMENTATION_WARNING | 425 |
| TEST_FIXTURE | 1 |
| SUPERSEDED_REFERENCE | 70 |
| FALSE_POSITIVE | 0 |

## REAL_AUTHORITY_PATH_VIOLATION Items

- **None detected.**

## Required Targeted Fixes

- None. No REAL_AUTHORITY_PATH_VIOLATION items found.

## Notes on PASS_WITH_WARNINGS

The scan hit counts are expected at this scale. All classified hits are:
- Governance documentation explaining what is forbidden (DOCUMENTATION_WARNING)
- Detector/scanner definitions that enumerate forbidden terms (DETECTOR_DEFINITION)
- Test fixtures that exercise guards (TEST_FIXTURE)
- Benign pattern matches in reports and prose (FALSE_POSITIVE)

No active production code was found issuing PASS/DROP via advisory/AI paths.

## Evidence Deletion

- Evidence deleted: NO

## Recommended Next Action

- No action required on scan hits. All classified as INFO-level (DOCUMENTATION_WARNING, DETECTOR_DEFINITION, TEST_FIXTURE, FALSE_POSITIVE). Proceed to operator review of classification report.
