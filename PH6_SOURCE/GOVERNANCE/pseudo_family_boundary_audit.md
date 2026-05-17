# PH6 PSEUDO Family Boundary Audit
Generated: 2026-05-17T07:30:00Z | Post-C13 Whole-System Audit

## Authority Law

**Only PSEUDO-A may issue PASS/DROP.**

## Overall Result: PASS

All 6 campaigns (C08-C13) verified: pseudo_m_violations=0, pseudo_a_violations=0, lane2_violation_count=0.

## Family Boundaries Verified

| Member | Role | Issues PASS/DROP | Mutates Authority Path | Result |
|---|---|---|---|---|
| PSEUDO-M | Deterministic metric computation | NO | NO | PASS |
| PSEUDO-A | PASS/DROP gate authority | YES (only member) | NO | PASS |
| PSEUDO-Predictive | Advisory/diagnostic only | NO | NO | PASS |
| PSEUDO-SCI | Observability sideband | NO | NO | PASS |

## PSEUDO-M Fields (All Fixed-Point Integers)

- `entropy_fp`
- `laplacian_var_fp`
- `motion_fraction_fp`

Schema: `ph6.metrics.fixedpoint.v1`. Verified across all C08-C13 phase receipts.

## Forbidden Term Hits in Code — All False Positives

| Location | Term | Classification |
|---|---|---|
| `ph6/ssmt/` models, schemas, tests | `confidence_fp` | FALSE_POSITIVE — Lane 2 swarm internal metric, Authority ZERO |
| `ph6/tok/lifecycle.py` | `confidence` | FALSE_POSITIVE — Token VDT/VLT lifecycle threshold, Authority ZERO |
| `ph6/cram_pu/cram_pu_live.py:68` | `confidence=0.0` | FALSE_POSITIVE — _TokSidecar RT constructor, never surfaces to Lane 1 |
| `ph6/cram_pu/vrc.py:214` | `confidence probability ai_verdict` | DETECTOR_DEFINITION — VRC forbidden-field scanner list |

No contamination from Lane 2, tokens, or SoSo into PSEUDO-A verdict path.
