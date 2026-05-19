================================================================================
PH6 DOCUMENTATION GOVERNANCE DOCTRINE
================================================================================
Classification : CANON -- Book II / Book III
Authority      : FULL
Version        : DGD-1.0
Scope          : All PH6 canon files, governance documents, certification
                 artifacts, and AI-ingest corpus materials
================================================================================

================================================================================
PREAMBLE
================================================================================

PH6 canon is not merely documentation.

It is simultaneously:
  - engineering specification
  - constitutional governance
  - AI-ingest corpus
  - retrieval substrate
  - certification reference
  - drift-control system
  - institutional memory layer

That changes how language must be engineered.

This doctrine governs how PH6 documentation is written, structured, and
maintained. Adherence is required for all new canon files and for revisions
to existing canon.

================================================================================
PRINCIPLE 1 -- AFFIRMATIVE DOCTRINE IS STRONGER THAN NEGATIVE DOCTRINE
================================================================================

Negative wording defines prohibition.
Affirmative wording defines invariant purpose.

WEAK FORM (negative only):
  FORBIDDEN: motion_score

STRONG FORM (affirmative + rationale):
  MOTION FIELD DOCTRINE
  - motion analysis is REQUIRED
  - canonical field: motion_fraction
  - noncanonical names: motion_score, motion_decay_score
  - motion analysis itself is permitted and required

The strong form preserves:
  - engineering intent
  - rationale for the constraint
  - certification logic
  - deterministic philosophy
  - future reconstructability

The weak form preserves only restriction.

Second example:

WEAK FORM:
  thresholds must not change at runtime

STRONG FORM:
  thresholds fixed at design time -- replay-stable

The strong form encodes WHY (replay equivalence, audit stability) not just WHAT.

Affirmative doctrine is superior for PH6 because doctrine must survive:
  - partial retrieval
  - AI summarization
  - context fragmentation
  - onboarding compression
  - long-term archival drift

Future engineers must be able to reconstruct WHY a rule exists,
not merely observe that it exists.

================================================================================
PRINCIPLE 2 -- SECTION NAMING CONTROLS INTERPRETATION
================================================================================

Headers are semantic governance gates.

A section title determines the interpretive frame before the content is read.

Example:

  HEADER: FORBIDDEN FIELDS
  -> implied meaning: dangerous concepts, suppress motion analysis
  -> reader inference: motion analysis may itself be forbidden

  HEADER: MOTION FIELD DOCTRINE
  -> implied meaning: governed subsystem with defined boundaries
  -> reader inference: motion analysis exists, has rules, is extensible

The second header creates:
  - operational framing
  - subsystem legitimacy
  - bounded governance
  - extensibility expectation

The first creates fear framing and semantic suppression.

Therefore:
  document topology = governance topology

Meaning: hierarchy, ordering, section names, emphasis, terminology,
and grouping all influence future system interpretation.

For PH6 this is critical because AI systems ingest structure before nuance.

Rule: name sections by what they govern, not by what they forbid.

================================================================================
PRINCIPLE 3 -- CANONICAL FIELDS MUST BE DISTINGUISHED FROM CONCEPTUAL SPACE
================================================================================

A canonical serialized field is not the same thing as its conceptual subsystem.

Example:
  motion_fraction = canonical authority field + replay-stable serialization primitive

It is NOT the totality of motion analysis.

The conceptual subsystem may legitimately include:
  - velocity estimation
  - persistence
  - continuity
  - temporal topology
  - multi-frame analysis
  - deterministic tracking
  - bounded classification

Doctrine must distinguish three layers:

  Layer 1 -- canonical fields       stable serialized authority
  Layer 2 -- runtime analytics      derived deterministic computation
  Layer 3 -- advisory ontology      interpretive / non-authoritative models

This separation prevents premature ontology lock-in and allows subsystem
growth without schema drift.

Rule: when introducing a field name, explicitly assign it to one of the
three layers above.

================================================================================
PRINCIPLE 4 -- CONSTITUTIONAL LANGUAGE BEATS IMPLEMENTATION LANGUAGE
================================================================================

WEAK (implementation):
  don't do X

STRONG (constitutional):
  X violates replay equivalence

The strong form encodes:
  - the invariant
  - the rationale
  - the system philosophy
  - certification implications
  - architectural boundaries

PH6 should prefer constitutional explanations.

Additional examples:

  WEAK:   don't mutate sealed evidence
  STRONG: post-seal mutation destroys chain-of-custody integrity

  WEAK:   use BLAKE2b
  STRONG: BLAKE2b-256 provides authority-marker stability across replay cycles

Rule: when stating a constraint, include the invariant it protects.

================================================================================
PRINCIPLE 5 -- DRIFT-RESISTANT DOCTRINE MUST BE MACHINE-STABLE
================================================================================

PH6 doctrine must survive:
  - markdown stripping
  - terminal rendering
  - AI chunk retrieval
  - OCR
  - plain text export
  - partial quoting
  - context truncation

Required formatting properties:
  - explicit section labels (not implied by indentation)
  - stable ASCII structures (==== dividers, not markdown # headers)
  - deterministic terminology (no synonyms for canonical terms)
  - low-ambiguity sectioning (one concept per section)
  - replay-safe wording (meaning preserved if section read in isolation)

Preferred constructs:
  ==== dividers             survive all renderers
  fixed-width columns       survive markdown stripping
  vertical ASCII flowcharts survive indentation collapse
  -> instead of Unicode ->  survives ASCII-only terminals
  -- instead of Unicode --  survives ASCII-only terminals

Avoid:
  indentation-dependent meaning
  markdown pipe tables as sole structure
  Unicode arrows in pipelines
  nested bullet hierarchies more than two levels deep

Rule: structure must be meaningful in plain text. Markdown is cosmetic only.

================================================================================
PRINCIPLE 6 -- DOCTRINE MUST PRESERVE HONEST UNCERTAINTY
================================================================================

PH6 gains credibility by explicitly distinguishing observed from sealed.

That same principle applies to documentation.

Doctrine must clearly separate:

  PROVEN INVARIANT       constitutionally stable -- part of sealed canon
  OPERATIONAL GUIDANCE   current best practice -- may evolve
  FUTURE ONTOLOGY        deferred -- not yet canon
  ADVISORY CONCEPT       noncanonical -- Lane 2 level
  EXPERIMENTAL IDEA      non-authoritative -- must not enter canon paths

This prevents accidental canon inflation.

Rule: every statement in a canon document must carry an implicit or explicit
classification from the table above. Unclassified assertions are drafts,
not canon.

================================================================================
SUMMARY TABLE
================================================================================

  Principle   Rule
  ---------   ----------------------------------------------------------------
  P1          Affirmative form -- include the why, not only the what
  P2          Name sections by what they govern, not what they forbid
  P3          Separate canonical fields from conceptual subsystem space
  P4          Encode invariants, not just restrictions
  P5          Structure must survive markdown stripping and terminal rendering
  P6          Classify every assertion -- no unclassified canon statements

================================================================================
ARCHITECTURAL INSIGHT
================================================================================

PH6 is evolving toward:

  A deterministic constitutional runtime
  whose documentation is itself part of the runtime governance system.

The canon is not merely describing the system.

The canon actively:
  - constrains interpretation
  - controls drift
  - shapes implementation
  - governs certification
  - limits authority leakage
  - stabilizes AI ingestion behavior

At that point:
  documentation engineering = systems engineering

================================================================================
END -- DOCUMENTATION GOVERNANCE DOCTRINE DGD-1.0
================================================================================
