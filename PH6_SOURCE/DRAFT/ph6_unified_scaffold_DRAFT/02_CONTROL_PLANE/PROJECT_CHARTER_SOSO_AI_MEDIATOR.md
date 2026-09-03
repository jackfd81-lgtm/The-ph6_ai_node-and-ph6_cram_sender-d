Document Type: Project Charter
Status: FUTURE PROJECT — NOT STARTED
Version: 0.1
Authority: PROPOSED / ADVISORY — Authority ZERO
Ratification: NONE

# PH6 — Future SoSo/JEDI AI-Mediator Project (Charter)

## Status block (verbatim from Jack's brief)
```
STATUS: FUTURE PROJECT
IMPLEMENTATION: NOT STARTED
HARDWARE: NOT INSTALLED
RASPBERRY PI: NOT YET CONFIGURED
VERIFICATION: NONE
VALIDATION: NONE
PRODUCTION STATUS: NONE
AUTHORITY: PROPOSED / ADVISORY
```

## What this is — and is explicitly not
This is **not** the existing SoSo-JEDI archive/provenance/continuity project
documented in `TERMINOLOGY_NOTE_SOSO_JEDI.md`. It is a distinct, new,
future role for a SoSo variant: a deterministic mediation boundary between
AI and PH6's deterministic systems.

```
AI  →  SoSo (deterministic mediator)  →  PH6 deterministic interfaces
```

AI does not talk to CRAM, PSEUDO, storage, hardware, sensors, or
authoritative state directly. AI talks to SoSo; SoSo — per its own
deterministic rules — decides what's permitted to pass through to PH6's
permitted interfaces. Neither AI nor this SoSo variant acquires authority
by virtue of sitting in that path.

## Relationship to the existing SoSo-JEDI terminology note
The existing "Source Steward" SoSo-JEDI definition remains **reference
material**, not the thing being built. What this project inherits from it
(if anything) — provenance handling, deterministic organization,
Authority ZERO posture — is itself an open question, not assumed. `JEDI`
in this project is explicitly **not** assumed identical to the existing
SoSo-JEDI archive definition; what it means here is TBD.

## Development sequence (mandatory order, per Jack's brief)
```
Concept → Requirements → Architecture → Interfaces →
Deterministic contracts → Implementation → Tests → Evidence → Verification
```
Nothing downstream of "Concept" has started. No code, no Raspberry Pi
setup, no interface design has been done as of this charter.

## Open investigation list (Jack's 17 items, unstarted)
1. What this SoSo variant actually is
2. How it differs from existing SoSo variants
3. What JEDI means in this implementation
4. AI↔SoSo communication model
5. SoSo↔PH6 communication model
6. What AI may request
7. What AI is prohibited from accessing directly
8. How SoSo enforces the boundary
9. Deterministic request representation
10. Deterministic response representation
11. Provenance preservation
12. Interaction logging
13. Failure handling
14. Replay/audit
15. Local/edge operation
16. Raspberry Pi implementation path
17. Testing/verification path

## Standing rule for this project
Do not describe any part of this as operational, installed, tested,
validated, or production-ready until it actually is. This charter records
intent and scope — nothing more.
