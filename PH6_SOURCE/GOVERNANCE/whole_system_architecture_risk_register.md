# PH6 Whole-System Architecture Risk Register
Generated: 2026-05-17T07:30:00Z | Post-C13 Whole-System Audit

Production clearance status: **NOT DECLARED**

## Risk Summary

| ID | Category | Title | Severity | Status |
|---|---|---|---|---|
| RSK-01 | Evidence Closure | C13 missing from closure_status.json | CRITICAL | **FIXED** |
| RSK-02 | Governance State | C13 OPEN in campaign matrix | HIGH | **FIXED** |
| RSK-03 | Hardware-Gated | OI-01 Hailo STOP-SHIP | HIGH | OPEN |
| RSK-04 | OI-03 Cross-Node | OI-03 Pi-to-Pi STOP-SHIP | HIGH | OPEN |
| RSK-05 | Life CRAM | Life CRAM campaigns not run | MEDIUM | OPEN |
| RSK-06 | Evidence Closure | C08 older artifact schema | MEDIUM | OPEN |
| RSK-07 | Evidence Closure | C07-C13 awaiting reviewer sign-off | MEDIUM | OPEN |
| RSK-08 | Doc/Canon Drift | C01-C06 FC01 as OPEN backlog | LOW | OPEN |
| RSK-09 | Tooling | .tmp files not deleted | LOW | PENDING |
| RSK-10 | PSEUDO Family | PSEUDO boundary PASS C08-C13 | INFO | CLOSED_INFO |
| RSK-11 | Production Clearance | OI-01 + OI-03 block clearance | HIGH | OPEN |

## Fixed This Audit

- **RSK-01**: C13 added to closure_status.json as PASS_PENDING_REVIEW
- **RSK-02**: C13 updated to PASS_PENDING_REVIEW in evidence_campaign_matrix.json

## Blocked by Hardware/Remote

- **RSK-03 OI-01**: Hailo hardware integration — requires Hailo Pi 5 module
- **RSK-04 OI-03**: Pi-to-Pi live transfer — requires two-Pi network setup
- **RSK-11**: Production clearance cannot be declared until OI-01 and OI-03 are closed

## Eligible for Human Review

- C07 through C13 (all PASS_PENDING_REVIEW): reviewer sign-off required
- C08 older schema: confirm schema evolution is acceptable
- C01-C06 FC01: classify as superseded or schedule

## Not to Close

- OI-01, OI-03, HRG9 (already closed — do not regenerate)
- Any PASS_PENDING_REVIEW campaign without complete reviewer metadata
