# PH6 Dual USB Camera — Smoke Test Report
PROPOSED — Lane-2 advisory only. Operator ratification required.

**Verdict**: SMOKE_PASS
**Both cameras open**: True
**USB bandwidth OK**: True
**Profile**: 640x480@15fps MJPG

### DV20_USB (/dev/video0) — role: smoke_test

| Metric | Value |
|--------|-------|
| Open OK | True |
| Resolution | 640x480 |
| FPS target | 15 |
| FPS achieved | 12.228 |
| Frames attempted | 300 |
| Frames captured | 300 |
| PASS count | 58 |
| DROP count | 242 |
| DROP rate | 80.7% |
| Entropy mean (min/max) | 7.877 (7.799 / 7.895) |
| Laplacian mean (min/max) | 551.3 (446.5 / 584.8) |
| Motion mean (min/max) | 0.0075 (0.0000 / 0.0329) |
| Jitter mean / max (ms) | 81.5 / 87.4 |
| DROP reasons | {'motion_low': 242} |
| Error | none |

---

### STREAMING_CAM (/dev/video2) — role: smoke_test

| Metric | Value |
|--------|-------|
| Open OK | True |
| Resolution | 640x480 |
| FPS target | 15 |
| FPS achieved | 14.439 |
| Frames attempted | 300 |
| Frames captured | 300 |
| PASS count | 299 |
| DROP count | 1 |
| DROP rate | 0.3% |
| Entropy mean (min/max) | 7.657 (7.437 / 7.724) |
| Laplacian mean (min/max) | 4942.4 (4854.9 / 5383.8) |
| Motion mean (min/max) | 0.0185 (0.0000 / 0.0442) |
| Jitter mean / max (ms) | 66.7 / 70.4 |
| DROP reasons | {'motion_low': 1} |
| Error | none |

---
*proposed_by: claude-code-lane2 | ratified_by: null*
