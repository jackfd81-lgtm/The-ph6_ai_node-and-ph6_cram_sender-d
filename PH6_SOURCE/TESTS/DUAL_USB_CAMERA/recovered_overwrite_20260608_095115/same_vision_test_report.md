# PH6 Dual USB Camera — Same Vision Test Report
PROPOSED — Lane-2 advisory only. Operator ratification required.

**Profile**: 640x480@15fps MJPG | **Frames**: 1200 per camera

## Stability Delta (A vs B)

| Metric | Delta |
|--------|-------|
| FPS diff | 2.596 |
| DROP rate diff | 95.9% |
| Entropy mean diff | 0.1585 |
| Laplacian mean diff | 4283.4 |

## Camera A

### DV20_USB (/dev/video0) — role: same_vision

| Metric | Value |
|--------|-------|
| Open OK | True |
| Resolution | 640x480 |
| FPS target | 15 |
| FPS achieved | 12.261 |
| Frames attempted | 1200 |
| Frames captured | 1200 |
| PASS count | 48 |
| DROP count | 1152 |
| DROP rate | 96.0% |
| Entropy mean (min/max) | 7.881 (7.801 / 7.905) |
| Laplacian mean (min/max) | 552.2 (443.3 / 583.9) |
| Motion mean (min/max) | 0.0046 (0.0000 / 0.0226) |
| Jitter mean / max (ms) | 81.5 / 88.6 |
| DROP reasons | {'motion_low': 1152} |
| Error | none |

## Camera B

### STREAMING_CAM (/dev/video2) — role: same_vision

| Metric | Value |
|--------|-------|
| Open OK | True |
| Resolution | 640x480 |
| FPS target | 15 |
| FPS achieved | 14.857 |
| Frames attempted | 1200 |
| Frames captured | 1200 |
| PASS count | 1199 |
| DROP count | 1 |
| DROP rate | 0.1% |
| Entropy mean (min/max) | 7.723 (7.425 / 7.792) |
| Laplacian mean (min/max) | 4835.6 (4547.7 / 5242.1) |
| Motion mean (min/max) | 0.0153 (0.0000 / 0.0326) |
| Jitter mean / max (ms) | 66.7 / 77.3 |
| DROP reasons | {'motion_low': 1} |
| Error | none |

---
*proposed_by: claude-code-lane2 | ratified_by: null*
