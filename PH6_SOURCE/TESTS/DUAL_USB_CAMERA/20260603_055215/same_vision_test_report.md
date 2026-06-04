# PH6 Dual USB Camera — Same Vision Test Report
PROPOSED — Lane-2 advisory only. Operator ratification required.

**Profile**: 640x480@15fps MJPG | **Frames**: 1200 per camera

## Stability Delta (A vs B)

| Metric | Delta |
|--------|-------|
| FPS diff | 22.735 |
| DROP rate diff | 99.9% |
| Entropy mean diff | 6.8828 |
| Laplacian mean diff | 353.9 |

## Camera A

### DV20_USB (/dev/video0) — role: same_vision

| Metric | Value |
|--------|-------|
| Open OK | True |
| Resolution | 640x480 |
| FPS target | 15 |
| FPS achieved | 24.92 |
| Frames attempted | 1200 |
| Frames captured | 1200 |
| PASS count | 1199 |
| DROP count | 1 |
| DROP rate | 0.1% |
| Entropy mean (min/max) | 6.894 (6.599 / 6.916) |
| Laplacian mean (min/max) | 356.0 (144.2 / 380.1) |
| Motion mean (min/max) | 0.0275 (0.0000 / 0.0291) |
| Jitter mean / max (ms) | 40.1 / 56.4 |
| DROP reasons | {'motion_low': 1} |
| Error | none |

## Camera B

### STREAMING_CAM (/dev/video2) — role: same_vision

| Metric | Value |
|--------|-------|
| Open OK | True |
| Resolution | 640x480 |
| FPS target | 15 |
| FPS achieved | 2.185 |
| Frames attempted | 1200 |
| Frames captured | 2 |
| PASS count | 0 |
| DROP count | 1200 |
| DROP rate | 100.0% |
| Entropy mean (min/max) | 0.011 (0.000 / 6.932) |
| Laplacian mean (min/max) | 2.1 (0.0 / 1252.5) |
| Motion mean (min/max) | 0.0000 (0.0000 / 0.0096) |
| Jitter mean / max (ms) | 0.1 / 67.2 |
| DROP reasons | {'motion_low': 2, 'read_failure': 1198} |
| Error | none |

---
*proposed_by: claude-code-lane2 | ratified_by: null*
