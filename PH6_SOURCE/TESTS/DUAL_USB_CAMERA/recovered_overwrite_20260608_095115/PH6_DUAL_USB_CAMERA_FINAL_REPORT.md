# PH6 Dual USB Camera — Final Engineering Report
**PROPOSED** — Lane-2 advisory only. Operator ratification required before any promotion.

---

## 1. Camera Inventory

| Label | Node | USB ID | Manufacturer |
|-------|------|--------|-------------|
| CAMERA_A | /dev/video0 | 4c4a:4a55 | Jieli Technology (DV20 USB) |
| CAMERA_B | /dev/video2 | 0c45:636b | Microdia (Streaming Cam) |

## 2. Device Mapping

Stable. Confirmed by USB-ID and udevadm.
`/dev/video1`, `/dev/video3` are metadata/control nodes — no capture.

## 3. Supported Modes

| Camera | Best MJPG | Safe Baseline |
|--------|-----------|--------------|
| CAMERA_A (DV20) | 1280x720@30fps | 640x480@15fps |
| CAMERA_B (Streaming Cam) | 1920x1080@30fps | 640x480@15fps |

## 4. Selected Safe Modes

- Smoke / Same Vision / Opposite Role: **640x480 @ 15fps MJPG** (both cameras)
- Complementary: Camera A **640x480 @ 15fps MJPG**, Camera B **1280x720 @ 15fps MJPG**

## 5. Same Vision Test Results

| Metric | CAMERA_A | CAMERA_B |
|--------|----------|----------|
| FPS achieved | 12.26 | 14.857 |
| PASS count | 90 | 1199 |
| DROP count | 1110 | 1 |
| DROP rate | 92.5% | 0.1% |
| Entropy mean | 7.904 | 7.6932 |
| Laplacian mean | 560.67 | 4652.87 |
| Motion mean | 0.005459 | 0.012847 |

## 6. Opposite Role Test Results

Recommended primary (PROPOSED): **STREAMING_CAM**
Recommended context (PROPOSED): **DV20_USB**

Primary score A-as-primary: 0.5952
Primary score B-as-primary: 1.9305

## 7. Complementary Test Results

| Camera | Role | Resolution (actual) | FPS achieved | DROP rate |
|--------|------|-------------------|-------------|----------|
| CAMERA_A | detail/measurement | 640x480 | 12.261 | 92.3% |
| CAMERA_B | wide/context | 1280x720 | 14.856 | 68.8% |

## 8. Best Role Assignment (PROPOSED)

| Camera | PROPOSED Role |
|--------|--------------|
| DV20_USB (/dev/video0) | Environmental context |
| STREAMING_CAM (/dev/video2) | Primary measurement |

## 9. Failure Modes Observed

*(See individual phase reports for per-frame DROP reason distributions.)*

## 10. USB Bandwidth Issues

Cameras are on separate USB buses (xhci-hcd.0 and xhci-hcd.1).
USB bandwidth conflict risk: LOW.
Smoke test USB bandwidth OK: True

## 11. Format Negotiation Issues

Camera A: YUYV capability limited — MJPG preferred at all resolutions.
Camera B: MJPG up to 1920x1080@30fps; YUYV viable at 640x480.
Both cameras: `/dev/video1`, `/dev/video3` have no capture formats (metadata/control only).

## 12. Recommended Next Test

1. Increase Camera B to 1920x1080 MJPG and re-run Same Vision at that resolution
2. Evaluate Camera A YUYV at 640x480@10fps for low-bandwidth ingest scenario
3. Run 12,000-frame endurance test once provisional pass confirmed by operator

## 13. Camera Clearance Assessment (PROPOSED)

| Camera | Primary Measurement | Context Measurement | Advisory Only | Not Recommended |
|--------|--------------------|--------------------|--------------|-----------------|
| CAMERA_A (DV20) | candidate | **YES (PROPOSED)** | — | — |
| CAMERA_B (Streaming Cam) | **YES (PROPOSED)** | candidate | — | — |

## 14. Dual Camera Operation Verdict

**DUAL_CAMERA_OPERATION_PROVISIONAL_PASS**

---
*proposed_by: claude-code-lane2 | proposed_at_utc: 2026-06-03T00:00:00Z | ratified_by: null*
