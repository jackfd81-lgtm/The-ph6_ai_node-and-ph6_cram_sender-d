Document Type: Terminology Reference Note
Status: PROPOSED / SOURCE-REFERENCE-ONLY / NOT RATIFIED
Version: 0.1
Authority: Lane 2 advisory — Authority ZERO
Ratification: NONE

# SoSo / JEDI terminology lineage — with verification status

## My verification status on this (Claude, this session)
I did not produce the lineage map below — it was supplied to me already
written, citing five sources: `cli.py`, `__init__.py`, `AI Cognitive Drift
Governance Research 2.pdf`, `PH6-SOSO-JEDI-RESEARCH-GAP-MAP-v1.2.md`, and
`SoSo Definition Update.txt`. I checked what I actually have access to:

- **`AI Cognitive Drift Governance Research 2.pdf`** — CONFIRMED PRESENT,
  at `PH6_SOURCE_SORTED/10_ARCHIVE/EXACT_DUPLICATES/Master cram Jack/` (and
  a primary copy without the "2" elsewhere in `03_ARCHITECTURE`). Real file.
- **`cli.py` / `__init__.py` defining `SoSo`/`JEDI` classes and
  `soso-status`/`jedi-status` commands** — NOT FOUND anywhere in the three
  uploaded zips. The only `__init__.py` I actually have (in
  `brain_computer_v2`) exports `BrainComputerV2`/`PerplexityAdapter`, not
  SoSo/JEDI.
- **`SoSo Definition Update.txt`** and **`PH6-SOSO-JEDI-RESEARCH-GAP-MAP-v1.2.md`**
  — NOT FOUND by exact name anywhere uploaded.
- I opened the one folder that looked like the obvious candidate —
  `PH6_SOURCE_SORTED/.../Mram/Jedi/` (RTF + HTML files) — and extracted
  their text directly. Result: one file mentions "SoSo" ~25 times but zero
  "JEDI"; the other mentions neither the lineage terms nor "Cognitive
  Drift" nor "Source Steward". **These files do not substantiate the
  lineage claims below**, despite living in a folder literally named
  "Jedi".

**Net: 1 of 5 cited sources confirmed real; the other 4 are either absent
from what's been uploaded to me, or (for the one folder I could check)
don't contain the claimed content.** This doesn't mean the lineage below
is wrong — it may well exist in material I haven't been given — it means
I can't independently corroborate most of it this session.

## The lineage claim itself, as supplied (unverified by me except as noted above)

There are at least two distinct SoSo-JEDI meanings claimed in the corpus:

| Form | Function | Authority |
|---|---|---|
| SoSo (software) | Continuity/advisory: observations, token deltas, chains | ZERO / Lane 2 |
| JEDI (software) | Cognitive-stability: epistemic state, drift, falsification tests | ZERO / Lane 2 |
| SoSo-JEDI (research architecture) | Cognitive drift, observability, continuity, swarm defense | ZERO / Lane 2 |
| SoSo-JEDI v1.1 → v1.2 | Research-gap program; v1.2 adds MRAM-S constraint, black-box schema, novelty-claim demotion | ZERO / Lane 2 |
| SoSo-JEDI — Source Steward (later definition) | Archive/provenance/reconstruction/continuity steward | ZERO / Lane 2 |

Proposed reading: "SoSo-JEDI" is not one architecture across the corpus —
it names at minimum (A) a cognitive-stability research program and (B) a
later, functionally different source/provenance/continuity steward
concept, plus underlying separate `SoSo` and `JEDI` software components
that preceded the combined term.

## Standing per the existing decision record
Consistent with `DECISION_RECORD_2026-09-03.md`: `JEDI` (and by extension
`SoSo-JEDI` in any form) remains **NOT PROMOTED**. This note does not
change that. Its own stated status —
`PROPOSED / SOURCE-REFERENCE-ONLY / Authority ZERO` — agrees with, rather
than conflicts with, the existing decision to not promote these terms
merely because they recur across drafts.

## A third, distinct form: the future AI-mediator SoSo
See `PROJECT_CHARTER_SOSO_AI_MEDIATOR.md`. Jack has explicitly confirmed
this is a **separate, future, not-started** project — a SoSo variant
acting as a deterministic mediation boundary between AI and PH6 — and
that it is not to be confused with, or treated as inheriting authority
from, either the cognitive-stability research SoSo-JEDI (A) or the
source-steward SoSo-JEDI (B) above. Whatever `JEDI` means in that project
is explicitly TBD, not assumed equal to either existing definition.

## Open item
If the actual `cli.py`/`__init__.py`/`SoSo Definition Update.txt`/
`PH6-SOSO-JEDI-RESEARCH-GAP-MAP-v1.2.md` files exist somewhere not yet
uploaded to this conversation, sharing them would let me verify this
directly rather than relying on a secondhand summary.
