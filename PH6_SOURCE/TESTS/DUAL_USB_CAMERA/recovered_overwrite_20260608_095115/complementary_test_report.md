# PH6 Dual USB Camera — Complementary Test Report
PROPOSED — Lane-2 advisory only. Operator ratification required.

**Camera A**: 640x480@15fps MJPG (detail/measurement)
**Camera B**: 1280x720@15fps MJPG (wide/context)
**Resolution note**: Camera B negotiated: 1280x720 (requested 1280x720)

> Camera B advisory metrics do NOT influence Camera A PASS/DROP. Each camera runs its own PSEUDO-A lane independently.

## Camera A — Detail / Measurement

### DV20_USB (/dev/video0) — role: detail_measurement

| Metric | Value |
|--------|-------|
| Open OK | True |
| Resolution | 640x480 |
| FPS target | 15 |
| FPS achieved | 12.261 |
| Frames attempted | 1200 |
| Frames captured | 1200 |
| PASS count | 92 |
| DROP count | 1108 |
| DROP rate | 92.3% |
| Entropy mean (min/max) | 7.875 (7.783 / 7.906) |
| Laplacian mean (min/max) | 570.6 (437.5 / 617.7) |
| Motion mean (min/max) | 0.0056 (0.0000 / 0.0622) |
| Jitter mean / max (ms) | 81.5 / 133.5 |
| DROP reasons | {'motion_low': 1108} |
| Error | none |

---

## Camera B — Wide / Context

### STREAMING_CAM (/dev/video2) — role: wide_context

| Metric | Value |
|--------|-------|
| Open OK | True |
| Resolution | 1280x720 |
| FPS target | 15 |
| FPS achieved | 14.856 |
| Frames attempted | 1200 |
| Frames captured | 1200 |
| PASS count | 375 |
| DROP count | 825 |
| DROP rate | 68.8% |
| Entropy mean (min/max) | 7.589 (6.879 / 7.636) |
| Laplacian mean (min/max) | 1622.7 (1533.7 / 1801.0) |
| Motion mean (min/max) | 0.0097 (0.0000 / 0.0268) |
| Jitter mean / max (ms) | 66.7 / 154.9 |
| DROP reasons | {'motion_low': 825} |
| Error | none |

---
*proposed_by: claude-code-lane2 | ratified_by: null*
