# PH6 / CRAM Internal System Test Report

**Generated UTC:** 2026-05-28T07:12:00Z
**Node:** jackjack (Pi 5 / 192.168.254.188 / aarch64)
**Repo:** /home/jack
**Test Type:** Internal system test — NO USB / NO CAMERA / NO VIDEO / NO CAN
**Temporary Test Root:** /tmp/ph6_internal_test_20260528T071022Z

---

## Scope

Internal-only test. No USB devices probed. No camera devices opened. No video capture.
No audio/video tests. No CAN HAT. No hardware media capture.

Tested: Pi 5 identity and health, PH6 repo state, governance drift scan, AI preflight,
Python syntax, architecture organization, lane authority / forbidden-field check,
open work / gap review, CRAM PASS-path simulation, CRAM DROP-path simulation,
audit hash-chain simulation, replay parity simulation, local export copy simulation,
Zero 2 W sentinel heartbeat.

Not tested: USB devices, camera/video/audio capture, CAN HAT, MCP2515, full
300-frame evidence validation run.

---

## Locked Rules Confirmed

- Lane 1 remains sole authority.
- Lane 2 remains advisory / Authority ZERO.
- RSYNC/export priority = ABSOLUTE.
- CAN HAT remains deferred.
- Zero 2 W remains active sentinel; Claude not installed.
- SMOKE / INTERNAL ONLY — 2 synthetic frames, not full 300-frame evidence validation.
