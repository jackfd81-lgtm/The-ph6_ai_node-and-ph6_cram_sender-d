# Camera B USB Hardware Fault — Diagnostic Report
**PROPOSED** — Lane-2 advisory only. Operator ratification required.

## Summary

Camera B (Microdia Streaming Cam, 0c45:636b, `/dev/video2`) experienced repeated USB hardware
resets during the dual-camera smoke test and is no longer enumerated by the OS.

**Fault class**: `CAMERA_B_USB_HARDWARE_FAULT`
**Dual-camera verdict impact**: `DUAL_CAMERA_OPERATION_HOLD`

---

## Timeline of Events

| Time (kernel uptime) | Event |
|---------------------|-------|
| ~4328s | Camera B USB reset triggered |
| ~4329s | `device not accepting address 13, error -22` |
| ~4330s | `"Cannot enable. Maybe the USB cable is bad?"` — kernel message |
| ~4330s | Camera B disconnects (device 13 gone) |
| ~4331s | Camera B re-enumerates as device 14 |
| ~4530s | Camera B disconnects again (device 14 gone) |
| ~4531s | Camera B re-enumerates as device 16 |
| ~4538s | Camera B disconnects again (device 16 gone) |
| ~4539s | Enumeration attempt device 17 — fails |
| ~4541s | `"Cannot enable. Maybe the USB cable is bad?"` |
| ~4541s | Kernel attempts power cycle |
| ~4542s | `"unable to enumerate USB device"` — terminal failure |

## Key Kernel Messages

```
usb 1-1: reset high-speed USB device number 13 using xhci-hcd
usb 1-1: device not accepting address 13, error -22
usb usb1-port1: Cannot enable. Maybe the USB cable is bad?
usb 1-1: USB disconnect, device number 13
...
usb usb1-port1: attempt power cycle
usb usb1-port1: Cannot enable. Maybe the USB cable is bad?
usb usb1-port1: unable to enumerate USB device
```

## Probable Root Causes (in priority order)

1. **USB cable marginal quality or damaged** — most likely given kernel's own message.
   Camera B is on `xhci-hcd.0 / bus 1 / port 1`. The repeated EINVAL (error -22) on
   address assignment is consistent with a cable that is marginal at high-speed (480Mbps).
   Camera B was capturing MJPEG at 1920x1080 rated — its sustained bandwidth demand is higher
   than Camera A.

2. **USB power delivery insufficient at bus 1 port 1** — Pi 5 USB 2.0 ports are shared
   off the PCIe bus. With Camera A also active on `xhci-hcd.1`, total USB power draw
   may exceed what the Pi 5 PSU delivers under the combined camera load.

3. **Camera B firmware instability under concurrent capture** — the 53 frames captured
   in smoke test before the first reset suggests the camera was working initially, then
   reset when it hit a firmware buffer overrun or USB timeout.

## Camera A Status (post-failure)

Camera A (DV20 USB, 4c4a:4a55, `/dev/video0`) is fully operational after Camera B's failure.
Solo verification: **99/100 PASS, 24.6fps, drop_rate=1.0%**.
Camera A is on a separate USB controller (`xhci-hcd.1 / bus 3`).

## Camera B Current State

```
lsusb: Camera B NOT present (post-test)
v4l2-ctl --list-devices: /dev/video2 NOT present
/dev/video2 NOT present in /dev/video*
```

Camera B requires physical investigation before any further testing.

## Operator Action Items (PROPOSED)

1. **Physically inspect USB cable** for Camera B — replace with a known-good data+power cable.
2. **Test Camera B solo** (no Camera A connected) after cable replacement.
3. **Verify USB power** — consider powered USB hub for Camera B if cable replacement doesn't resolve.
4. **Re-run dual smoke test** only after Camera B passes 300-frame solo test.

## Clearance Impact

| Camera | Clearance | Blocker |
|--------|-----------|---------|
| CAMERA_A (DV20) | `CAMERA_A_RECOMMENDED_PRIMARY` (PROPOSED, pending operator ratification) | None — solo PASS |
| CAMERA_B (Streaming Cam) | `CAMERA_B_USB_HARDWARE_FAULT` | USB cable/power hardware issue |
| Dual Operation | `DUAL_CAMERA_OPERATION_HOLD` | Camera B fault |

---
*proposed_by: claude-code-lane2 | proposed_at_utc: 2026-06-03T00:00:00Z | ratified_by: null*
