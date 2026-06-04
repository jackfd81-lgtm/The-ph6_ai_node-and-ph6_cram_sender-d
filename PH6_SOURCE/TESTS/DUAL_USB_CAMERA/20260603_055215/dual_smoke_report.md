# PH6 Dual USB Camera — Smoke Test Report
PROPOSED — Lane-2 advisory only. Operator ratification required.

**Verdict**: SMOKE_HOLD
**Both cameras open**: True
**USB bandwidth OK**: True
**Profile**: 640x480@15fps MJPG

### DV20_USB (/dev/video0) — role: smoke_test

| Metric | Value |
|--------|-------|
| Open OK | True |
| Resolution | 640x480 |
| FPS target | 15 |
| FPS achieved | 24.527 |
| Frames attempted | 300 |
| Frames captured | 300 |
| PASS count | 284 |
| DROP count | 16 |
| DROP rate | 5.3% |
| Entropy mean (min/max) | 6.663 (0.010 / 7.032) |
| Laplacian mean (min/max) | 318.1 (0.0 / 493.9) |
| Motion mean (min/max) | 0.0250 (0.0000 / 0.1786) |
| Jitter mean / max (ms) | 40.0 / 52.0 |
| DROP reasons | {'entropy_low': 15, 'blur': 15, 'motion_low': 14} |
| Error | none |

---

### STREAMING_CAM (/dev/video2) — role: smoke_test

| Metric | Value |
|--------|-------|
| Open OK | True |
| Resolution | 640x480 |
| FPS target | 15 |
| FPS achieved | 12.227 |
| Frames attempted | 300 |
| Frames captured | 53 |
| PASS count | 0 |
| DROP count | 300 |
| DROP rate | 100.0% |
| Entropy mean (min/max) | 1.224 (0.000 / 7.040) |
| Laplacian mean (min/max) | 226.2 (0.0 / 1374.3) |
| Motion mean (min/max) | 0.0015 (0.0000 / 0.0096) |
| Jitter mean / max (ms) | 11.7 / 74.8 |
| DROP reasons | {'motion_low': 53, 'read_failure': 247} |
| Error | none |

---
*proposed_by: claude-code-lane2 | ratified_by: null*
