Document Type: Decision Record
Status: RECORDED — ISSUED BY LANE 1 (Jack)
Version: 1.0
Authority: LANE 1 — this file records a Lane 1 decision, not Lane 2 advisory output
Ratification: These specific decisions ARE Jack's explicit direction. This does
  not ratify any canon document, terminology, or code as CANON — it ratifies
  the *process decision* to defer/not-implement/preserve, below.

# Decision Record — 2026-09-03 — Folder naming, fp(), terminology promotion

## Context
Two independently-produced governance documents (a migration protocol and a
master governance spec) both proposed renaming `01_DOCTRINE_AND_SPEC` →
`01_CANON_STACK` and `06_AUDIT_AND_LOGS` → `06_AUDIT_LOGS`, and the second
supplied candidate `fp()` parameters (`FP_SCALE = 10,000`, `ROUND_HALF_EVEN`).
Both were flagged back to Jack as open Lane 1 decisions rather than acted on.

## Decision

| Item | Decision |
|---|---|
| `01_DOCTRINE_AND_SPEC` → `01_CANON_STACK` | **DEFER** — not renamed |
| `06_AUDIT_AND_LOGS` → `06_AUDIT_LOGS` | **DEFER** — not renamed |
| `FP_SCALE = 10,000` | **PROPOSED** — candidate value only |
| `ROUND_HALF_EVEN` | **PROPOSED** — candidate value only |
| Fixed-point `fp()` implementation in `verify_vectors.py` | **DO NOT IMPLEMENT AS CANONICAL** |
| Existing repository layout (`01_DOCTRINE_AND_SPEC`, `06_AUDIT_AND_LOGS`, etc.) | **PRESERVE** |
| Unresolved numerical semantics (rounding point, division, sqrt algorithm, entropy/log implementation, rolling-window accumulation, threshold-comparison semantics, overflow/range, fixed-point serialization, cross-platform replay) | **FAIL CLOSED / RECORD UNRESOLVED** |
| `JEDI`, `TFH-AK`, `CAM`, `NERO` | **NOT PROMOTED.** Repetition across drafts establishes the terms exist in the corpus. It does NOT establish definition, authority, or normative behavior. |

## Rationale (Jack's own words, recorded verbatim)
> Agreement between drafts does not override the observed repository state.
> ... a float implementation is actually safer if the verifier explicitly
> labels itself as provisional rather than pretending either representation
> is canonical.

## Effect on this scaffold
- No folders renamed this session.
- `verify_vectors.py` remains on raw floats; its existing header comment
  already discloses this — no further code change made against this
  decision.
- Next scaffold operation, per Jack's direction: **preservation and
  evidence reconciliation**, not further speculative rename or numerical
  rewrite.

**This record itself is the ratification of the decision to defer/not-implement/
preserve. It is not a ratification of `01_CANON_STACK`, `06_AUDIT_LOGS`,
`FP_SCALE=10,000`, `ROUND_HALF_EVEN`, or any of the four terminology items —
those remain exactly as unresolved/proposed as stated above.**
