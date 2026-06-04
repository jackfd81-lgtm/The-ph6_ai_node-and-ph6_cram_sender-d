# PH6 Dual USB Camera — Opposite Role Test Report
PROPOSED — Lane-2 advisory only. Operator ratification required.

**Profile**: 640x480@15fps MJPG | **Frames**: 1200 per camera per pass

## Role Recommendation (PROPOSED)

| | Score | Recommended Role |
|-|-------|-----------------|
| DV20_USB as primary | 0.8060 | PRIMARY |
| STREAMING_CAM as primary | 0.0000 | CONTEXT |

**PROPOSED PRIMARY**: DV20_USB
**PROPOSED CONTEXT**: STREAMING_CAM

> Advisory note: PROPOSED role assignment — Lane-2 advisory only; Lane-1 authority not exercised

## Pass 1: A=primary, B=context

### DV20_USB (/dev/video0) — role: primary_measurement

| Metric | Value |
|--------|-------|
| Open OK | True |
| Resolution | 640x480 |
| FPS target | 15 |
| FPS achieved | 24.923 |
| Frames attempted | 1200 |
| Frames captured | 1200 |
| PASS count | 1199 |
| DROP count | 1 |
| DROP rate | 0.1% |
| Entropy mean (min/max) | 6.884 (6.593 / 6.909) |
| Laplacian mean (min/max) | 364.3 (148.3 / 384.4) |
| Motion mean (min/max) | 0.0281 (0.0000 / 0.0297) |
| Jitter mean / max (ms) | 40.1 / 54.2 |
| DROP reasons | {'motion_low': 1} |
| Error | none |

---

### STREAMING_CAM (/dev/video2) — role: environmental_context

| Metric | Value |
|--------|-------|
| Open OK | False |
| Resolution | 640x480 |
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

## Pass 2: A=context, B=primary

### DV20_USB (/dev/video0) — role: environmental_context

| Metric | Value |
|--------|-------|
| Open OK | True |
| Resolution | 640x480 |
| FPS target | 15 |
| FPS achieved | 24.938 |
| Frames attempted | 1200 |
| Frames captured | 1200 |
| PASS count | 1199 |
| DROP count | 1 |
| DROP rate | 0.1% |
| Entropy mean (min/max) | 6.886 (6.598 / 6.911) |
| Laplacian mean (min/max) | 370.5 (148.7 / 389.9) |
| Motion mean (min/max) | 0.0284 (0.0000 / 0.0298) |
| Jitter mean / max (ms) | 40.1 / 46.6 |
| DROP reasons | {'motion_low': 1} |
| Error | none |

---

### STREAMING_CAM (/dev/video2) — role: primary_measurement

| Metric | Value |
|--------|-------|
| Open OK | False |
| Resolution | 640x480 |
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
