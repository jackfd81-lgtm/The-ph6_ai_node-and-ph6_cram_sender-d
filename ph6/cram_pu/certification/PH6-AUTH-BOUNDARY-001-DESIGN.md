# PH6-AUTH-BOUNDARY-001-DESIGN

Role: PROPOSED (design artifact, not doctrine, not certification)
Status: PROPOSED — Part 7 only. Parts 1-6 (Phase 1 / Phase 2A) do not exist in this
repository and are not reconstructed here.

## Provenance Notice — Read First

This file did not exist anywhere in `jackfd81-lgtm/the-ph6_ai_node-and-ph6_cram_sender-d`
(checked: full working tree, `git log --all --diff-filter=A` across every branch) before
this pass. The operator's reconciliation-gate prompt assumed an existing artifact with
Phase 1 / Phase 2A findings already in place (AUTHORIZATION PROPOSITION, PSEUDO-A BINDING,
TOK/SOSO/AI BOUNDARY, AUTHORIZATION PROVENANCE, and Dependencies A/B/F). No such prior
artifact was found. Accordingly:

- **Parts 1-6 are absent, not summarized.** This session has never read a Phase 2A source
  document. The finding *names* and their *prior classifications* ("derived minimum,"
  "true by absence of a call path only," etc.) used below are reproduced verbatim from the
  operator's own reconciliation-gate prompt text, not from an independently observed
  artifact. That distinction is preserved throughout — see the "Source of finding text"
  line under each item.
- **Part 7 below is genuinely new work**: every canon citation in it was verified directly
  against the supplied evidence package, quoted below, not inferred or reconstructed from
  the prompt's paraphrase.

## Supplied Canonical Evidence — Provenance Record

Source: `PH6_CANON_SUPPLIED_EVIDENCE_PACKAGE.pdf`, supplied directly by Jack in-session
(44 pages, extracted via pypdf). Per the package's own Provenance Notice (p.1): canonical
status derives from being supplied as doctrine by the sole Lane 1 ratification authority —
**not** from filesystem or repository placement. This file does not copy that PDF into the
repository and does not assert that doing so would confer canonical status.

Contents confirmed present in the supplied package:
1. DOC 0 — PH6 Constitution & Interpretive Control Plane (PH6-DOC0-CONSOLIDATED-1.0), pp.2-14
2. PH6 Consolidated Canon, five-book stack v5.2-RC4 (Book 0 - Book V), pp.15-26
3. Standalone Book 0 - Book V (PH6-BOOK0..V-CONSOLIDATED-1.0), pp.27-44

Note on the outstanding `.docx` gap from the prior pass: `PH6_CONSOLIDATED_CANON.docx`
itself was still not supplied as a `.docx` file, but its content is present in this
package as the "PH6 Consolidated Canon" five-book stack (pp.15-26). Treated here as
**supplied**, sourced from the PDF package rather than the named `.docx`.

Note on DOC 0's internal "DOC 1/DOC 2/DOC 3" reference: DOC 0's own Conflict Rule (p.2)
reads "This document wins over DOC 1, DOC 2, and DOC 3 on all conflicts," and its Reading
Order (p.3, §1.5) names DOC 1 = "instrument and runtime architecture," DOC 2 =
"certification and validation," DOC 3 = "controlled extensions annex." This is a
different numbering scheme than the "Book I-V" naming used by the five-book stack and the
standalone books elsewhere in the same package. The package's top-level Provenance Notice
(p.1) instructs treating the five-book stack and standalone books as the same absorbed
substance under DOC 0, which this reconciliation follows. Flagged here as an unresolved
naming inconsistency in the supplied material itself — not something this pass resolves,
since resolving it is an interpretation of doctrine, which Book 0 §1.1 explicitly reserves
("Book 0 does not create authority. Book 0 governs access to authority").

---

## Part 7 — Canon Reconciliation

### 7.A — DOC 0 Precedence, Verified Against Source Text

Claim to verify: DOC 0 outranks Books I/II/III/IV/V wherever they overlap.

Verified quotes (not paraphrase):

> "Conflict Rule: This document wins over DOC 1, DOC 2, and DOC 3 on all conflicts."
> — DOC 0 header, p.2

> "1.4 Conflict Rules
> • Book doctrine overrides implementation.
> • Lane authority overrides explanatory models.
> • Interpretation may not modify substance.
> • Interpretation may not alter doctrine."
> — DOC 0, Part I §1.4, p.2

> "Sources Absorbed: BOOK0-ICP-1.1, PH6-OSC-2.0, BOOK-IV-CCA-1.1,
> PSEUDO_EXPLICIT_BOUNDARY_PATCH (constitutional sections),
> SIX_ENGINE_SUBJECT_MATTER_UPDATE_FRAME (constitutional sections), PH6-MASTER-v5.2
> Books I-IV"
> — DOC 0 header, p.2

**Finding: CONFIRMED.** DOC 0 states its own precedence over the numbered DOC 1-3 scheme
and separately declares it absorbed the Book I-IV constitutional sections. Combined with
the package's own instruction to treat the five-book stack and standalone books as the
same substance absorbed into DOC 0 (p.1), DOC 0 governs wherever it speaks to the same
substance as Books I/II/IV/V. This is a direct quote, not a derived inference.

### 7.B — Reclassified Findings

For each finding, the "Original classification" line is reproduced from the operator's
reconciliation prompt as given — **this session has not independently seen the Phase 2A
document that classification allegedly came from.** The citation and canon text under each
is independently verified against the supplied PDF.

---

**B1. AUTHORIZATION PROPOSITION**

- Source of finding text: operator prompt only (Phase 2A not observed by this session)
- Original classification (per operator prompt): "derived minimum"
- Reclassified to: "derived AND canon-confirmed at constitutional rank"

Verified citations:

> "4.3 PASS/DROP Vocabulary Lock ... Valid verdict terms: PASS, DROP ... PASS/DROP is
> exclusive to PSEUDO-A in Lane 1. No other system may issue verdicts."
> — DOC 0, Part IV §4.3, p.8

> "4.5 No Authority Widening Rule
> Forbidden at all times:
> • Partition-derived authority
> • Alternate PASS/DROP routes
> • Threshold influence by advisory systems
> • Advisory promotion into Lane 1
> • Swarm governance authority
> • Certification converted into governance"
> — DOC 0, Part IV §4.5, p.8

CANON REQUIREMENT: confirmed at constitutional rank — no route to a PASS/DROP verdict
may exist outside PSEUDO-A, and no advisory-to-authority promotion path may be created,
by name and without exception.
MECHANISM: not addressed by these sections. Neither §4.3 nor §4.5 specifies *how* the
exclusivity is to be enforced in code (e.g. no call-path isolation mechanism, no runtime
guard is named). Canon-mandated, mechanism UNRESOLVED.

---

**B2. PSEUDO-A BINDING**

- Source of finding text: operator prompt only (Phase 2A not observed by this session)
- Original classification (per operator prompt): "UNRESOLVED as enforced property" — kept unchanged
- Addition per this pass: traceable to a constitutional-rank rule, not merely an engineering concern

Verified citations:

> "5.3 PSEUDO-A — Adjudication Subsystem
> • Type: Deterministic adjudication
> • Authority: Sole PASS/DROP authority in Lane 1
> • Functions: Threshold arbitration, deterministic gate evaluation, PASS/DROP issuance,
> reason-code production
> • Rule: PSEUDO-A is the only system that may issue verdicts. No advisory model may
> inherit PSEUDO authority."
> — DOC 0, Part V §5.3, p.9

> "6.3 Verdict Sovereignty Law"
> — DOC 0, Part VI, section title only, p.10 (body text for §6.1-6.4 was not
> individually extractable from the source PDF's table layout — see note below)

CANON REQUIREMENT: confirmed at constitutional rank by §5.3's explicit rule. §6.3's
title ("Verdict Sovereignty Law") is confirmed verbatim as a named constitutional-rank
law; its full body text could not be reliably attributed to §6.3 specifically versus
§6.1/6.2/6.4 due to a PDF text-extraction ordering artifact in that table (headings 6.1-6.4
extracted together, followed by a run of unattributed body lines). This is flagged rather
than guessed at.
MECHANISM: still UNRESOLVED, unchanged from the operator's prior classification. No
supplied document defines an enforcement mechanism (e.g., a binding/attestation scheme
proving a given verdict actually originated from PSEUDO-A). Canon-mandated, mechanism
UNRESOLVED. Status kept exactly as stated in the operator's prompt for this element.

---

**B3. TOK/SOSO/AI BOUNDARY**

- Source of finding text: operator prompt only (Phase 2A not observed by this session)
- Original classification (per operator prompt): "true by absence of a call path only"
- Reclassified to: "canon-mandated by name at constitutional rank, but NOT validated by any positive rejection test"

Verified citation:

> "2.3 Primary Objectives
> PH6 exists to:
> 1. Capture raw physical evidence.
> 2. Preserve evidence through deterministic write discipline.
> 3. Evaluate frames using deterministic PSEUDO logic.
> 4. Separate measurement from interpretation.
> 5. Maintain replayability across hardware and time.
> 6. Export evidence without blocking.
> 7. Prevent AI, SoSo, Kubernetes, or Swarm from gaining evidentiary authority."
> — DOC 0, Part II §2.3, Primary Objective #7, p.6 — verified word for word, including
> the "#7" position.

CANON REQUIREMENT: confirmed unambiguous — AI is named explicitly, alongside SoSo,
Kubernetes, and Swarm, not inferred from Lane-2 category membership as the prior
classification apparently assumed.
MECHANISM / TEST COVERAGE: this pass did not run or locate a positive rejection test
(a test that actively attempts to grant AI/SoSo evidentiary authority and asserts it is
rejected) against this repository's code. That remains a separate, repository-evidence
question this pass did not investigate — consistent with the operator's own instruction
not to conflate "canon requirement confirmed" with "compliance validated." Canon-mandated,
test coverage UNRESOLVED (not investigated this pass).

---

**B4. AUTHORIZATION PROVENANCE / authority_hash collision — DOCTRINE DRIFT**

- Source of finding text: operator prompt only for the framing ("promote to its own
  independent finding"); the underlying code-level divergence was independently
  re-verified by this session directly against repository source (not from the prompt).

Independently verified from this repository (read directly, not from canon or prompt):

> `ph6/cram_pu/ingest_receipt_logger.py:11,18` —
> "authority_hash — BLAKE2b-256 of the authoritative Lane-1 content ... authority_hash is
> the CRAM commit hash for ACCEPTED, or payload_hash for DROPPED / ARRIVED"

> `ph6/ssmt/audit_log.py:47` —
> `"authority_hash": canon_hash(packet_dict)` — a hash of an SSMT/Lane-2 advisory packet
> dict, per CLAUDE.md's own file-placement table (`ssmt/` = Lane-2, zero authority).

Verified canon citation (single-schema requirement):

> "B4 §2 — Schema Contracts
> ...
> • Receipt Schema: (ph6_receipt_v1, monotonic event_seq, event_hash, authority_hash)"
> — Book IV, §2, p.41

> "IV.4 Schema Contracts (Locked)
> All schemas are in ph6_six_engine_pack/schemas/. Schema version strings are locked."
> — DOC 0 / Consolidated Canon, Book IV §IV.4, p.24

CANON REQUIREMENT: confirmed — exactly one Receipt Schema is defined, carrying exactly
one `authority_hash` field, with a locked meaning tied to Lane-1 authoritative content
(the CRAM commit hash / payload hash per `ingest_receipt_logger.py`'s own docstring,
which matches this schema's evident intent).
REPOSITORY FACT: `ph6/ssmt/audit_log.py` — a Lane-2 advisory module — writes a field
named `authority_hash` whose value is `canon_hash(packet_dict)`, a hash of an advisory
object, not of Lane-1 authoritative content.

**Finding: DOCTRINE DRIFT — CONFIRMED.** This is not a naming coincidence; it is a
locked single-schema field name reused with a second, incompatible live meaning inside a
Lane-2 module. Per Book 0 §5 (Drift Prohibition, p.16): "Declare DRIFT_FAIL if any
document, code, annotation, or advisory output: ... Uses PASS/DROP vocabulary outside
Lane 1 adjudication" and the general Boundary Inheritance Law (implementation may refine,
may not relax constraints) — reusing a locked schema field name for a different meaning
in an advisory module is a drift condition against B4 §2's single-schema contract. This
pass does not select a remediation (per the hard freeze, §4 of the operator's prompt) —
only records the drift as confirmed doctrine-vs-code conflict.

Related but distinct, found only in the supplied canon (not previously named in the
operator's prompt at all): DOC 0 / Book IV §IV.5 independently flags a **different**
audit.py defect:

> "IV.5 Implementation Defect — audit.py (Must Patch)
> DEFECT: ph6/audit.py append_audit() does not emit required fields authority_hash or
> event_seq. The ph6.audit_event.v1 schema requires both fields..."
> — p.24

This is a missing-field defect on `ph6/audit.py` (not `ssmt/audit_log.py`), distinct from
the semantic-collision drift above. Noted here for completeness since it surfaced during
citation verification; not investigated further, as investigating `ph6/audit.py`'s current
state was outside this reconciliation's scope.

---

**B5. MINT LEGITIMACY, CAPABILITY INTEGRITY, CONCURRENCY (Dependencies A/B/F)**

- Source of finding text: operator prompt only (Phase 2A not observed by this session)
- Classification: remain UNRESOLVED, unchanged.

Verified against the supplied package's own explicit scope statement:

> "WHAT THIS PACKAGE DOES NOT ESTABLISH
> This package does not define: a Lane-1 commit authorization mint/issuer mechanism, a
> capability object schema, or a concurrency contract for the commit boundary. Absence of
> these in this package is not evidence they exist elsewhere in the repository — that
> determination remains a separate, repository-evidence question (see
> PH6-AUTH-BOUNDARY-001-DESIGN.md)."
> — Package Provenance Notice, p.1

**Confirmed explicitly by the supplied canon's own text, not merely by omission.** No
issuer, capability object, or concurrency contract is defined anywhere in DOC 0, the
five-book stack, or the standalone books. Dependencies A/B/F remain UNRESOLVED. This pass
did not search the repository for a possible implementation of these three items — that
was out of scope for a canon-reconciliation-only pass and is explicitly named as a
separate question by the supplied package itself.

---

### 7.C — Confirmations Required by the Reconciliation Gate

1. No canonical source, production code, test file, test framework logic, or
   certification baseline was modified by this pass. Only this design artifact was
   written (newly created, since no prior version existed in this repository).
2. DOC 0's authority is recorded throughout this document as **supplied canonical
   evidence** (Provenance Notice above), never as "repository-resident canon." The
   supplied PDF was not copied into this repository.
3. Dependencies A/B/F (mint legitimacy, capability integrity, concurrency) remain
   UNRESOLVED, confirmed by the supplied package's own explicit scope statement.
4. The `.docx` gap from the prior pass is resolved as "supplied via PDF package
   instead of the named `.docx`" — not folded into "canon is silent."
5. Two items could not be completed to full verification and are flagged rather than
   guessed: (a) DOC 0 Part VI §6.1-6.4 body-text attribution, due to a PDF table
   extraction ordering artifact; (b) the internal DOC 1/2/3 vs. Book I-V naming overlap
   in DOC 0's own text, flagged in the Provenance Record above, not resolved.

---

## Advisory Disclaimer (Lane 2 Rule)

This document is Lane-2 advisory work product, Authority ZERO. It classifies canon
requirements against previously-named findings and repository code; it does not
implement, select, or endorse any authorization mechanism, and it does not modify any
canonical source, production code, or certification baseline. Nothing in this document
is ratified until Jack states so explicitly, per the Ratification Signal Protocol.

```json
{"proposed_by":"claude-code-lane2","proposed_at_utc":"2026-09-05T13:58:54Z","api_call_log_ref":"session_01AASY1Aw35bJ7Q1wkSvQvxh","ratified_by":null}
```
