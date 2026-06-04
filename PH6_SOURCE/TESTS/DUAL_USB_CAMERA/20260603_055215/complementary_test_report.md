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
| FPS achieved | 24.922 |
| Frames attempted | 1200 |
| Frames captured | 1200 |
| PASS count | 1199 |
| DROP count | 1 |
| DROP rate | 0.1% |
| Entropy mean (min/max) | 6.893 (6.609 / 6.909) |
| Laplacian mean (min/max) | 375.4 (155.6 / 393.0) |
| Motion mean (min/max) | 0.0287 (0.0000 / 0.0307) |
| Jitter mean / max (ms) | 40.1 / 53.5 |
| DROP reasons | {'motion_low': 1} |
| Error | none |

---

## Camera B — Wide / Context

### STREAMING_CAM (/dev/video2) — role: wide_context

| Metric | Value |
|--------|-------|
| Open OK | False |
| Resolution | 1280x720 |
| FPS target | 15 |
| FPS achieved | 0.0 |
| Frames attempted | 0 |
| Frames captured | 0 |
| PASS count | 0 |
| DROP count | 0 |
| DROP rate | 0.0% |
| Entropy mean (min/max) | 0.000 (0.000 / 0.000) |
| Laplacian mean (min/max) | 0.0 (0.0 / 0.0) |
| Motion mean (min/max) | 0.0000 (0.0000 / 0.0000) |
| Jitter mean / max (ms) | 0.0 / 0.0 |
| DROP reasons | {} |
| Error | failed to open /dev/video2 |

---
*proposed_by: claude-code-lane2 | ratified_by: null*
