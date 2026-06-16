# PH6 Dual USB Camera — Opposite Role Test Report
PROPOSED — Lane-2 advisory only. Operator ratification required.

**Profile**: 640x480@15fps MJPG | **Frames**: 1200 per camera per pass

## Role Recommendation (PROPOSED)

| | Score | Recommended Role |
|-|-------|-----------------|
| DV20_USB as primary | 0.5952 | CONTEXT |
| STREAMING_CAM as primary | 1.9305 | PRIMARY |

**PROPOSED PRIMARY**: STREAMING_CAM
**PROPOSED CONTEXT**: DV20_USB

> Advisory note: PROPOSED role assignment — Lane-2 advisory only; Lane-1 authority not exercised

## Pass 1: A=primary, B=context

### DV20_USB (/dev/video0) — role: primary_measurement

| Metric | Value |
|--------|-------|
| Open OK | True |
| Resolution | 640x480 |
| FPS target | 15 |
| FPS achieved | 12.261 |
| Frames attempted | 1200 |
| Frames captured | 1200 |
| PASS count | 21 |
| DROP count | 1179 |
| DROP rate | 98.2% |
| Entropy mean (min/max) | 7.881 (7.802 / 7.914) |
| Laplacian mean (min/max) | 560.9 (474.3 / 581.9) |
| Motion mean (min/max) | 0.0051 (0.0000 / 0.0976) |
| Jitter mean / max (ms) | 81.5 / 92.3 |
| DROP reasons | {'motion_low': 1179} |
| Error | none |

---

### STREAMING_CAM (/dev/video2) — role: environmental_context

| Metric | Value |
|--------|-------|
| Open OK | True |
| Resolution | 640x480 |
| FPS target | 15 |
| FPS achieved | 14.857 |
| Frames attempted | 1200 |
| Frames captured | 1200 |
| PASS count | 1189 |
| DROP count | 11 |
| DROP rate | 0.9% |
| Entropy mean (min/max) | 7.698 (7.290 / 7.737) |
| Laplacian mean (min/max) | 4797.3 (4515.6 / 4982.3) |
| Motion mean (min/max) | 0.0150 (0.0000 / 0.0439) |
| Jitter mean / max (ms) | 66.7 / 78.2 |
| DROP reasons | {'motion_low': 11} |
| Error | none |

## Pass 2: A=context, B=primary

### DV20_USB (/dev/video0) — role: environmental_context

| Metric | Value |
|--------|-------|
| Open OK | True |
| Resolution | 640x480 |
| FPS target | 15 |
| FPS achieved | 12.261 |
| Frames attempted | 1200 |
| Frames captured | 1200 |
| PASS count | 54 |
| DROP count | 1146 |
| DROP rate | 95.5% |
| Entropy mean (min/max) | 7.872 (7.783 / 7.887) |
| Laplacian mean (min/max) | 555.3 (458.4 / 579.5) |
| Motion mean (min/max) | 0.0047 (0.0000 / 0.0251) |
| Jitter mean / max (ms) | 81.5 / 96.5 |
| DROP reasons | {'motion_low': 1146} |
| Error | none |

---

### STREAMING_CAM (/dev/video2) — role: primary_measurement

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
| Entropy mean (min/max) | 7.735 (7.199 / 7.775) |
| Laplacian mean (min/max) | 4765.7 (4594.4 / 4942.9) |
| Motion mean (min/max) | 0.0169 (0.0000 / 0.0454) |
| Jitter mean / max (ms) | 66.7 / 77.8 |
| DROP reasons | {'motion_low': 1} |
| Error | none |

---
*proposed_by: claude-code-lane2 | ratified_by: null*
