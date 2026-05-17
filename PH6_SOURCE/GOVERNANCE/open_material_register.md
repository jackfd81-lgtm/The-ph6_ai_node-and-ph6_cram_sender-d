# PH6 Open Material Register
Generated: 2026-05-17T07:30:00Z | Post-C13 Whole-System Audit

1,134 raw grep hits classified.

## CRITICAL (1)

**OM-01** — C13 missing from closure_status.json  
**STATUS: FIXED.** C13_24000_VARIABLE_SPEED_INFORMATION_STRESS added as PASS_PENDING_REVIEW in this audit.

## HIGH (2)

**OM-02** — C13 closure_status=OPEN in campaign matrix  
**STATUS: FIXED.** Updated to PASS_PENDING_REVIEW in this audit.

**OM-03 / OM-04** — OI-01 and OI-03 open STOP-SHIP gates  
**STATUS: OPEN. BLOCKED_BY_HARDWARE / BLOCKED_BY_REMOTE_NODE.**  
- OI-01 requires Hailo Pi 5 hardware module  
- OI-03 requires two-Pi network setup and live transfer run  
- These cannot be closed by software campaigns. Human review + hardware required.

## MEDIUM (3)

**OM-05** — LIFE-CRAM-PU-1 not yet run  
Requires live-stream session with real camera and life CRAM runner.

**OM-06** — TOK-LIFE-1 and SOSO-LIFE-1 not yet run  
Require Life CRAM session with live token/SoSo enabled.

**OM-07** — C01-C06 FC01 in matrix as OPEN backlog  
These predate the C07+ active sequence. Not failures. Eligible for human classification as superseded or scheduled.

## LOW (1)

**OM-09** — .tmp files in frame_filter/logs  
`frame_filter/logs/live_run.tmp` and `run_log.tmp` — not deleted pending confirmation. Likely runtime hot-logs from April 2026 frame_filter session.

## INFO (1)

**OM-08** — Three interrupted C13 partial runs preserved  
Committed per doctrine. Do not delete.

## FALSE POSITIVE (1)

**OM-10** — 820+ hits in PH6_SOURCE docs for governance vocabulary terms  
All are prohibition/warning text. Expected.
