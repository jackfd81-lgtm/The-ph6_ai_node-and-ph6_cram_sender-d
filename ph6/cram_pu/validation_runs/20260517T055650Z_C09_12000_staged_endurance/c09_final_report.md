# PH6 C09 — 12,000-Frame Staged Endurance + Throughput Campaign

## Executive Result

**Overall:** `PASS`  **Campaign State:** `PASS_PENDING_REVIEW`  **Closed:** `false`

Total frames: 12000/12000 | Duration: 67.6s | FPS: 177.5

## Phase Table

| Phase | Mode | Frames | Duration | FPS | Avg ms | P95 ms | P99 ms | PASS | DROP | Errors | Result |
|-------|------|-------:|---------:|----:|-------:|-------:|-------:|-----:|-----:|-------:|--------|
| A | FAST | 2000 | 11.1s | 180.0 | 5.55 | 7.70 | 10.27 | 1372 | 628 | 0 | PASS |
| B | REGULAR_CRAM | 2000 | 10.9s | 183.7 | 5.44 | 7.57 | 8.91 | 1372 | 628 | 0 | PASS |
| C | FAST_CRAM | 2000 | 10.8s | 185.2 | 5.40 | 7.38 | 8.55 | 1372 | 628 | 0 | PASS |
| D | FAST | 2000 | 10.8s | 185.3 | 5.39 | 7.43 | 8.54 | 1372 | 628 | 0 | PASS |
| E | REGULAR_CRAM | 2000 | 10.8s | 185.0 | 5.40 | 7.36 | 8.06 | 1372 | 628 | 0 | PASS |
| F | FAST_CRAM | 2000 | 10.8s | 184.4 | 5.42 | 7.45 | 8.43 | 1372 | 628 | 0 | PASS |

## Throughput Comparison

| Mode | Avg FPS |
|------|--------:|
| FAST | 182.7 |
| REGULAR_CRAM | 184.4 |
| FAST_CRAM | 184.8 |

- FAST vs REGULAR_CRAM delta: **-0.9%**
- FAST_CRAM vs REGULAR_CRAM delta: **+0.2%**
- FAST_CRAM vs FAST delta: **+1.2%**

## Endurance Analysis (First vs Second 6,000 frames)

- First 6,000 FPS: **182.9**
- Second 6,000 FPS: **184.9**
- Degradation: **NO** (stable or faster)

## Validation Results

- Replay parity: `PASS` — hash parity: `MATCH`
- RSYNC non-blocking: `PASS`
- Lane 2 isolation: `PASS`
- Failure register entries: `0`

## Governance Status

- Campaign state: `PASS_PENDING_REVIEW`
- Closed: `false`
- HRG9: candidate evidence only
- Production clearance: NOT DECLARED

## Recommended Next Action
Human review of C09 artifacts, then pursue OI-03 real Pi-to-Pi transfer.
