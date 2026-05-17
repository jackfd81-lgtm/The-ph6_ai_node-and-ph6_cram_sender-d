# PH6 C13 — Variable-Speed / Variable-Information Stress Campaign

## Executive Result

**Overall:** `PASS`  **State:** `PASS_PENDING_REVIEW`  **Closed:** `false`

Total: 24000/24000 frames | Duration: 1057.6s | Overall FPS: 22.7 | Total bytes: 32,400,000

## Phase Table

| Phase | Name | Frames | Target FPS | Actual FPS | Sustain | bytes/frame | bytes/s | IDI_avg | PASS | DROP | replay | RSYNC | Lane2 |
|-------|------|-------:|----------:|-----------:|---------|------------:|--------:|-------:|-----:|-----:|--------|-------|------:|
| A | slow_high_info | 4000 | 15 | 15.0 | OK | 1200 | 18001 | 0.366 | 2743 | 1257 | PASS | OK | 0 |
| B | fast_medium_high_info | 4000 | ∞ | 126.1 | OK | 900 | 113489 | 0.366 | 2743 | 1257 | PASS | OK | 0 |
| C | regular_baseline | 4000 | 30 | 30.0 | OK | 600 | 18004 | 0.366 | 2743 | 1257 | PASS | OK | 0 |
| D | max_fast_max_info | 2000 | ∞ | 107.3 | OK | 2400 | 257605 | 0.366 | 1372 | 628 | PASS | OK | 0 |
| E | slowest_max_info | 2000 | 5 | 5.0 | OK | 2400 | 12006 | 0.366 | 1372 | 628 | PASS | OK | 0 |
| F | regular_recovery | 4000 | 30 | 30.0 | OK | 600 | 18004 | 0.366 | 2743 | 1257 | PASS | OK | 0 |
| G | 60fps_max_info | 4000 | 60 | 60.0 | OK | 2400 | 144022 | 0.366 | 2743 | 1257 | PASS | OK | 0 |

## Stress Comparisons

- A (slow/high-info) vs E (slowest/max-info) FPS: A=15.0 → E=5.0
- C (regular baseline) vs F (regular recovery) FPS: C=30.0 → F=30.0
- B (fast/medium-high) vs D (max-fast/max-info) bytes/frame: B=900 → D=2400
- D (max-fast) vs G (60fps/max-info) bytes/s: D=257605 → G=144022
- Endurance: first 12K FPS=27.8 vs last 12K FPS=16.7 (DEGRADED)

## PSEUDO Family

- Overall: `PASS`
- All deterministic: `True`
- All bounded: `True`
- All replayable: `True`
- All isolated: `True`

## Governance Status

- State: `PASS_PENDING_REVIEW`
- Closed: `false`
- Production clearance: NOT DECLARED
