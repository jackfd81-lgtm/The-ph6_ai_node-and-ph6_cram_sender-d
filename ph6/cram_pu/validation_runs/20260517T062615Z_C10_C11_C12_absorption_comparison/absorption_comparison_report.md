# PH6 C10/C11/C12 — Absorption-Rate PSEUDO Family Comparison

Generated: 2026-05-17T06:26:15Z

## Summary Table

| Campaign | Frames | Target FPS | Actual FPS | Bytes/Frame | Bytes/Sec | PASS | DROP | Replay | RSYNC | Lane2 | PSEUDO-M | PSEUDO-A | PSEUDO-Pred | PSEUDO-SCI |
|----------|-------:|----------:|-----------:|------------:|----------:|-----:|-----:|--------|-------|-------|----------|----------|-------------|------------|
| C10 | 6000 | 15 | 15.0 | 1200 | 18003 | 4114 | 1886 | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| C11 | 6000 | 30 | 30.0 | 600 | 18003 | 4114 | 1886 | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| C12 | 3000 | 50 | 50.0 | 300 | 15004 | 2057 | 943 | PASS | PASS | PASS | PASS | PASS | PASS | PASS |

## Absorption Analysis

- C10 (15 FPS): **18003 bytes/s** — 1200 bytes/frame — 7,200,000 bytes total
- C11 (30 FPS): **18003 bytes/s** — 600 bytes/frame — 3,600,000 bytes total
- C12 (50 FPS): **15004 bytes/s** — 300 bytes/frame — 900,000 bytes total
- **Best absorption rate**: C10 at 18003 bytes/s

## PSEUDO Family Stability

- PSEUDO family **STABLE** across all absorption regimes

## PASS/DROP Distribution

- C10: 4114 PASS / 1886 DROP (68.6% pass rate)
- C11: 4114 PASS / 1886 DROP (68.6% pass rate)
- C12: 2057 PASS / 943 DROP (68.6% pass rate)

## Replay Parity by Campaign

- C10: `PASS` — hash `blake2b256:b3c2d6ea0f8bc76f...`
- C11: `PASS` — hash `blake2b256:b3c2d6ea0f8bc76f...`
- C12: `PASS` — hash `blake2b256:f86a81f8c50bfe36...`

## Recommended Next Action

All three absorption campaigns passed. PSEUDO family verified deterministic, bounded, replayable, and isolated across 15/30/50 FPS regimes. Next gate: OI-03 real Pi-to-Pi transfer evidence.
