# PH6 Authority Hierarchy

**Schema:** ph6.governance.authority.hierarchy.v1  
**Status:** PROPOSED  
**Proposed by:** claude-code-lane2 | **Ratified by:** null

---

## Authority Levels

| Level | Domain | Contains |
|-------|--------|---------|
| 1 | Legal / Courtroom | Evidentiary rules, FRE 702, chain of custody, court orders |
| 2 | Scientific / Experimental | Validated methods, calibration, reproducibility, uncertainty, ISO 17025 |
| 3 | Engineering | PSEUDO-M, PSEUDO-A, PSEUDO-SCI, CRAM storage lanes, hardware |
| 4 | Software | Runtime code, firmware, drivers, measurement algorithms |
| 5 | Theoretical / Hypothesis | Posits, unvalidated models, simulations |
| 6 | AI Advisory | SoSo, AI review, advisory output — Authority ZERO |
| 7 | Token / Continuity | Token topology, virtual tokens, memory continuity — Advisory only |

Higher number = lower authority. Level 1 is supreme.

PSEUDO-M and PSEUDO-A operate at Level 3 (Engineering).  
CRAM evidence storage operates at Level 3 (Engineering).  
SoSo operates at Level 6 (AI Advisory).  
AI operates at Level 6 (AI Advisory).  
Tokens operate at Level 7 (Token/Continuity).

---

## Core Authority Rule

```
Lane 1 decides.
Lane 2 advises.
AI never adjudicates.
Tokens never override evidence.
CRAM preserves.
PSEUDO measures and adjudicates.
SoSo maps continuity.
Legal Mode overrides all.
```

---

## Lane Authority Map

| Lane | Authority Level | Role |
|------|---------------|------|
| Lane 1 | 2–4 | Deterministic evidence: CRAM-0, PSEUDO-M, PSEUDO-A, CRAM-A, CRAM-R, replay, audit |
| Lane 2 | 6–7 | Advisory: SoSo, AI review, token topology, MRAM-S |
| Lane 3 | 3–4 | Preservation/export: backup, rsync, archive, review bundles |
| Lane 4 | 6–7 | AI learning dataset: certified references, negative corpus, derived artifacts |
| Lane 5 | 1–2 | External/operator review: legal review, scientific review, ratification |

---

## Override Rules

```
Legal (L1) overrides all.
Scientific (L2) overrides Engineering, Software, Theoretical, AI, Tokens.
Engineering (L3) overrides Software, Theoretical, AI, Tokens.
Software (L4) overrides Theoretical, AI, Tokens.
Theoretical (L5) overrides AI and Tokens only.
AI (L6) overrides only its own prior advisory output.
Tokens (L7) override nothing.
```

---

## Non-Negotiable Rules

1. AI may not issue PASS or DROP verdicts.
2. AI may not modify CRAM evidence at any level.
3. SoSo disagreement with PSEUDO does not override PSEUDO.
4. Token topology does not become evidence authority.
5. Theoretical posits require Level 3+ validation before entering evidence chain.
6. Legal Mode cannot be waived by the operator during proceedings.
7. Level 6 and Level 7 outputs are always labeled Advisory / Authority ZERO.

---

## Relationship to CLAUDE.md Governance

The 8-level model in `PH6_AUTHORITY_MODE_HIERARCHY.md` (Level 0=Reality through Level 7=AI) and this 7-level model are compatible. Mapping:

| This doc | PH6_AUTHORITY_MODE_HIERARCHY.md |
|----------|--------------------------------|
| Level 1 (Legal) | Level 1 (Legal) |
| Level 2 (Scientific) | Level 2 / 2A (Scientific / Experimental) |
| Level 3 (Engineering) | Level 3 (PSEUDO) + Level 4 (CRAM) |
| Level 4 (Software) | Level 3–4 implementation layer |
| Level 5 (Theoretical) | Level 5 implicit |
| Level 6 (AI Advisory) | Level 5–7 (SoSo, Tokens, AI) |
| Level 7 (Token) | Level 6 (Tokens) |

---

*Lane-2 advisory document. Operator ratification required.*
