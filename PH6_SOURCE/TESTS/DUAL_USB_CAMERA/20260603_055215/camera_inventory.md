# PH6 Dual USB Camera Inventory
PROPOSED — Lane-2 advisory only.

## Device Mapping

| Label | Node | USB ID | Manufacturer | Max MJPG | Safe Baseline |
|-------|------|--------|-------------|----------|--------------|
| CAMERA_A | /dev/video0 | 4c4a:4a55 | Jieli Technology (DV20 USB) | 1280x720@30fps | 640x480@15fps MJPG |
| CAMERA_B | /dev/video2 | 0c45:636b | Microdia (Streaming Cam) | 1920x1080@30fps | 640x480@15fps MJPG |

## Stable Mapping Note

Mapping confirmed by USB-ID and udevadm.
`/dev/video1` and `/dev/video3` are metadata/control nodes (no capture formats).
`/dev/video0` and `/dev/video2` are the real capture streams.

## Camera A — DV20 USB (Jieli Technology 4c4a:4a55)

**MJPG**: 640x480@30fps, 1280x720@30fps
**YUYV**: 640x480@10fps, 320x240@30fps
**Note**: Limited YUYV capability; MJPG preferred.

## Camera B — Streaming Cam (Microdia 0c45:636b)

**MJPG**: 1920x1080, 1280x1024, 1280x960, 1280x720, 1024x768, 848x480, 800x600, 640x480, 320x240, 176x144, 160x120 — all @30fps
**YUYV**: 640x480@30fps (5fps at high res)
**Note**: Highly capable; both USB buses are separate (no shared bandwidth contention).

---
*proposed_by: claude-code-lane2 | ratified_by: null*
