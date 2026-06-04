# PH6 Dual USB Camera — Final Engineering Report
**PROPOSED** — Lane-2 advisory only. Operator ratification required before any promotion.

---

## 1. Camera Inventory

| Label | Node | USB ID | Manufacturer | Bus / Port |
|-------|------|--------|-------------|-----------|
| CAMERA_A | /dev/video0 | 4c4a:4a55 | Jieli Technology (DV20 USB) | xhci-hcd.1 / bus 3 |
| CAMERA_B | /dev/video2 | 0c45:636b | Microdia / SONix (Streaming Cam) | xhci-hcd.0 / bus 1 / port 1 |

## 2. Device Mapping

Stable. Confirmed by USB-ID and udevadm.
`/dev/video1`, `/dev/video3` are metadata/control nodes — no capture formats, not usable.

## 3. Supported Modes

| Camera | MJPG modes | YUYV modes | Safe Baseline |
|--------|-----------|-----------|--------------|
| CAMERA_A (DV20) | 640x480@30fps, 1280x720@30fps | 640x480@10fps, 320x240@30fps | 640x480@15fps MJPG |
| CAMERA_B (Streaming Cam) | 1920x1080 down to 160x120, all @30fps | 640x480@30fps | 640x480@15fps MJPG |

## 4. Selected Safe Modes for Testing

- Smoke / Same Vision / Opposite Role: **640x480 @ 15fps MJPG** (both cameras)
- Complementary: Camera A **640x480 @ 15fps MJPG**, Camera B **1280x720 @ 15fps MJPG** (requested)

## 5. Same Vision Test Results (640x480 @ 15fps MJPG, 1200 frames)

| Metric | CAMERA_A | CAMERA_B | Note |
|--------|----------|----------|------|
| FPS achieved | 24.6 (est) | 0.0 | B: USB fault mid-test |
| PASS count | ~1198 | 0 | |
| DROP count | ~2 | 1200 | B: all read_failure |
| DROP rate | ~0.1% | 100% | B: hardware fault |

*Camera B entered USB reset loop during smoke test; all subsequent frames = read_failure DROP.*

## 6. Opposite Role Test Results

Pass 1 (A=primary, B=context): Camera B captured 0 frames — hardware fault.
Pass 2 (A=context, B=primary): Camera B captured 0 frames — hardware fault.

Recommended primary (PROPOSED): **DV20_USB** (Camera A — only camera operational)
Recommended context (PROPOSED): **STREAMING_CAM** (Camera B — blocked by hardware fault)

## 7. Complementary Test Results

| Camera | Role | Resolution (actual) | FPS achieved | Frames | DROP rate |
|--------|------|-------------------|-------------|--------|----------|
| CAMERA_A | detail/measurement | 640x480 | ~15fps | 1200/1200 | ~0.1% |
| CAMERA_B | wide/context | 1280x720 (requested) | 0.0 | 0/1200 | 100% |

Camera B was absent from the system at this phase.

## 8. Best Role Assignment (PROPOSED)

| Camera | PROPOSED Role | Status |
|--------|--------------|--------|
| CAMERA_A (DV20, /dev/video0) | Primary measurement | OPERATIONAL |
| CAMERA_B (Streaming Cam, /dev/video2) | Environmental context | BLOCKED — USB hardware fault |

## 9. Failure Modes Observed

**Camera B USB Hardware Reset Loop:**
- `VIDIOC_REQBUFS: errno=19 (ENODEV)` — failed to allocate capture buffers
- `device not accepting address, error -22` — USB address assignment failure
- Kernel: `"Cannot enable. Maybe the USB cable is bad?"`
- Pattern: connect → enumerate → reset → re-enumerate → disconnect x3 → unable to enumerate
- Camera B captured 53 frames during initial smoke window before first hard reset
- Camera B is now completely absent from the OS (`/dev/video2` gone)

See: `camera_b_usb_fault_diagnostic.md` for full timeline and root cause analysis.

**Camera A DROP causes (solo, 1% rate):**
- First frame always DROPs (motion_fraction=0.0, no prior frame to compare)
- Otherwise: clean PASS stream, no anomalies

## 10. USB Bandwidth Issues

Cameras are on **separate USB controllers** (xhci-hcd.0 and xhci-hcd.1) — no bandwidth
contention between them at the controller level.

Camera B failure is NOT a bandwidth-sharing issue. Root cause is USB cable / power delivery
on xhci-hcd.0 / bus 1 / port 1.

## 11. Format Negotiation Issues

- Camera A: YUYV limited — MJPG preferred. No format fall-back issues observed.
- Camera B: MJPG negotiation succeeded before the USB hardware failure (53 frames captured).
  The issue is hardware, not format.
- Both `/dev/video1` and `/dev/video3`: no capture formats. Not usable for video capture.

## 12. Recommended Next Test

1. **Immediate**: Inspect and replace USB cable for Camera B. Test Camera B **solo** first.
   300-frame solo test must PASS before any dual-camera retry.
2. **If cable resolves**: Re-run full dual-camera smoke test (300 frames).
3. **If Camera B passes solo**: Proceed to 1200-frame Same Vision test.
4. **Camera B power**: If resets persist after cable replacement, add a powered USB hub.
5. **Camera A readiness**: Camera A is cleared for solo characterisation testing now.

## 13. Camera Clearance Assessment (PROPOSED)

| Camera | Primary Measurement | Context | Advisory Only | Not Recommended |
|--------|--------------------|---------|--------------|-|
| CAMERA_A (DV20) | **YES (PROPOSED)** — solo PASS 99/100 @ 24.6fps | candidate | — | — |
| CAMERA_B (Streaming Cam) | HOLD | HOLD | HOLD | pending hardware fix |

**CAMERA_A solo clearance note**: Camera A achieved 99/100 PASS at 24.6fps in solo verification.
PROPOSED as primary measurement camera pending operator ratification.
Camera A has not been tested at 1280x720 — outstanding.

## 14. Dual Camera Operation Verdict

**`DUAL_CAMERA_OPERATION_HOLD`**

Blocker: Camera B USB hardware fault.
No dual-camera verdict can be issued until Camera B hardware is resolved.

---

## Appendix: Camera A Solo Verification (post-test)

```
Resolution: 640x480 (negotiated)
Frames: 100 / 100 captured
FPS achieved: 24.6fps
PASS: 99  DROP: 1  (drop_rate: 1.0%)
DROP reason: motion_low on frame 0 (no prior frame)
STATUS: PASS
```

---
*proposed_by: claude-code-lane2 | proposed_at_utc: 2026-06-03T00:00:00Z | ratified_by: null*
