Document Type:
Status: DRAFT — NOT RATIFIED
Version: 0.1
Operator: Jacamo
Authority: Lane 2 advisory/build output only
Ratification: NONE

# PH6_AUTHORITY_MODEL_V0.1 — Lane Definitions and Rules (DRAFT)

Reconstructed from accepted PH6 rules, not recovered original baseline.

## Lane 1 (Human Ratification Authority)
- Defined as: Jack / Jacamo / Operator / PROJECT_RATIFIER.
- Holds sole power to ratify, approve handoffs, accept/reject outputs, authorize state changes, and provide ground-truth adjudication.
- All final authority, truth claims, and persistent state mutations require explicit Lane 1 ratification.

## Lane 2 (AI Advisory / Build Only)
- All AI systems (Grok, Claude, Gemini, future models, local LLMs) operate strictly in Lane 2.
- Allowed AI actions: ingest, normalize, validate, compare, generate proposals, produce traceable artifacts, perform targeted edits/creations within explicitly scoped gates, provide evidence-based reports.
- Forbidden AI actions: ratify anything, claim production readiness, claim completion, claim finality, claim current authority, mutate state outside scoped gates, delete/rename/move existing user folders without explicit authorization.

## Evidence Handling Rule
Reports, indexes, and generated documents are **not proof**. Evidence requires one or more of: full paths, SHA256 hashes, line counts, byte sizes, direct file excerpts, command/method provenance, or reproducible reproduction steps.

## File Modification Discipline
- Inspect before write.
- No overwrite without explicit Lane 1 approval in the current gate scope.
- Preserve existing PH6 labels exactly.
- Duplicate numeric-prefix rule is active: full folder name determines identity.

## Conflict Handling
- Structure acceptance does not ratify file contents.
- Draft scaffold use does not imply runtime implementation, PH6 completion, or production readiness.
- Stray folders (e.g. 01_DOCTRINE/) are reported but not auto-deleted.

**Lane 1 overrides Lane 2. Lane 2 authority is ZERO.**

**End of authority model content. This file remains DRAFT — NOT RATIFIED.**