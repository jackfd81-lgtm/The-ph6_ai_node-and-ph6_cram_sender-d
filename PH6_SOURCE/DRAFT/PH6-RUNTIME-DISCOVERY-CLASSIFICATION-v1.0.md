# PH6 RUNTIME DISCOVERY CLASSIFICATION

## PH6-RUNTIME-DISCOVERY-CLASSIFICATION-v1.0

Lane:      2 (Advisory doctrine — no authority path writes)
Authority: ZERO
Status:    DRAFT

---

# 1. PURPOSE AND SCOPE

## Purpose

This document defines the classification semantics for runtime discovery
findings produced by the governance drift scanner operating in
`--discovery` mode against the `ph6/` runtime tree.

It establishes:

* the INFO semantic floor
* the authority-relevance test that gates escalation
* escalation criteria for each severity transition
* certification implications per severity class
* non-escalatable categories (permanent INFO cap)
* governance rules for severity promotion

## What This Document Is Not

This document does not:

* grant any finding authority to block commits
* define new forbidden terms or patterns
* modify the drift scanner or validators
* replace the severity_policy.json definitions
* constitute a seal or certification

All escalation requires explicit human sign-off.
AI may recommend escalation. AI may not promote severity unilaterally.

## Scope

| Target | Coverage |
| ------ | -------- |
| Runtime tree | `ph6/` |
| Scan mode | `--discovery` (INFO-only, exit 0) |
| Doctrine | Lane-2 advisory, Authority ZERO |
| This version | v1.0 — initial classification baseline |

## Why Classification Precedes Escalation

Findings come first; classification criteria come second is the failure mode.

That sequence produces:

* reactive severity inflation
* politically-shaped enforcement
* exception-driven governance
* inconsistent escalation across similar findings

This document inverts the sequence:

* classification semantics defined at baseline
* findings evaluated against stable criteria
* escalation driven by doctrine, not by finding volume or operator frustration

---

# 2. PERMANENTLY INFO-CLASS FINDINGS

## Definition of the Semantic Floor

A finding is permanently INFO-class when it carries:

* no operational consequence
* no authority relevance (see Section 3)
* no replay dependency
* no evidence chain impact

INFO findings are recorded for observability only.
They do not trigger workflow changes.
They do not block commits, merges, or certification runs.
Frequency and persistence do not promote INFO findings.

## INFO Semantic Contract

| Property | Value |
| -------- | ----- |
| Exit code | 0 |
| Validator result | PASS |
| Workflow behavior | Recorded in report only |
| Merge implication | ALLOW |
| Cert implication | INFORMATIONAL — logged, no review obligation |
| Promotable by frequency | NO |
| Promotable by persistence | NO |
| Promotable by AI recommendation alone | NO |

## Examples of Permanently INFO-Class Findings

The following finding types are INFO-class by nature:

| Category | Reason |
| -------- | ------ |
| Comments and inline documentation | No executable authority path |
| TODO / FIXME markers | Observational only; no authority relevance unless adjacent to a violation |
| Test fixture data and validation run artifacts | Non-production evidence paths |
| Disabled or commented-out code blocks | Not reachable at runtime |
| Sample and example configurations | Not authoritative execution paths |
| Advisory metadata in correctly-labeled Lane-2 outputs | Authority ZERO by design |
| Schema fields in schemas not declared in schema_lock_registry | Unregistered schemas carry no canonical authority |
| Optional advisory scripts not on authoritative execution paths | No replay dependency |
| Archived or experimental artifacts in non-production paths | Not in canonical evidence chain |
| Observability-only telemetry formatting differences | No PASS/DROP influence |

---

# 3. AUTHORITY-RELEVANCE TEST

## Purpose

The authority-relevance test is the gate that separates:

* informational observability (INFO)
  from
* governance consequence (WARN and above)

A finding must pass this test before it is eligible for escalation
above INFO. Failing all dimensions means the finding is permanently INFO.

## Test Dimensions

A finding is authority-relevant if it can influence ANY of the following:

| Dimension | Test Question |
| --------- | ------------- |
| Replay | Can this finding indicate a state that would change deterministic replay outcomes? |
| Evidence integrity | Can this finding indicate mutation or contamination of canonical evidence? |
| Authority boundaries | Can this finding indicate Lane-2 code asserting or approaching Lane-1 authority? |
| Certification state | Can this finding indicate a state that would invalidate a certification run? |
| RSYNC sovereignty | Can this finding indicate something conditioning, delaying, or blocking export? |
| Deterministic state | Can this finding indicate non-deterministic behavior in a deterministic execution path? |

## Test Result

| Outcome | Meaning |
| ------- | ------- |
| ANY dimension = YES | Finding is authority-relevant. Eligible for escalation above INFO. Proceed to Section 4. |
| ALL dimensions = NO | Finding is permanently INFO. Check Section 6 for non-escalatable confirmation. |

## Application Rules

* The test is applied per finding, not per check category.
* A check category that produces INFO findings in one context may produce
  escalatable findings in another context.
* The test outcome must be documented when recommending escalation.
* AI must state which dimension triggered authority-relevance when
  recommending promotion.

## Boundary Cases

| Case | Classification |
| ---- | -------------- |
| Finding in Lane-2 path with no Lane-1 adjacency | INFO unless authority dimension triggered |
| Finding in test file that exercises Lane-1 code | Apply test against the tested code path, not the test file |
| Finding that matches a forbidden term in a comment | Likely INFO — apply test; if no dimension triggered, INFO |
| Finding in an archived artifact | INFO unless the artifact is on a live execution path |
| Same forbidden term appearing in both INFO and authority-relevant contexts | Classify each instance independently |

---

# 4. ESCALATION CRITERIA

Escalation always requires:

1. Finding passes the authority-relevance test (Section 3)
2. Finding is not in a non-escalatable category (Section 6)
3. Human sign-off (Section 7)

## INFO → WARN

A finding may be promoted to WARN when:

| Criterion | Requirement |
| --------- | ----------- |
| Authority relevance | At least one dimension triggered in Section 3 |
| Execution reachability | Finding appears in a path reachable at runtime under normal operation |
| Novelty | Pattern has not been previously reviewed and confirmed INFO by a human operator |
| No existing exemption | Finding does not fall under a declared non-escalatable category |

WARN means: governance concern present, human acknowledgement required before merge
in a certification context. Does not block development sessions.

## WARN → HIGH

A finding may be promoted to HIGH when:

| Criterion | Requirement |
| --------- | ----------- |
| Lane adjacency | Finding appears in a Lane-1 adjacent component or on a path that reaches Lane-1 |
| Pattern match | Finding matches a known governance violation pattern at reduced severity |
| Scope | Multiple instances of the same finding across independent runtime paths |
| Canonical replacement | Finding has a defined canonical replacement and the wrong form is in active use |

HIGH means: CERTIFICATION HOLD. Merge blocked until resolved or formally waived.

## HIGH → CRITICAL

A finding may be promoted to CRITICAL only when:

| Criterion | Requirement |
| --------- | ----------- |
| Demonstrated violation | Not theoretical — a concrete instance of the governance violation is present |
| Direct authority path | Finding is on an active Lane-1 execution path or directly conditions Lane-1 behavior |
| Replay or evidence impact | Finding demonstrably affects replay determinism or canonical evidence chain |
| No ambiguity | The violation is unambiguous; it does not require interpretation to identify |

CRITICAL means: STOP-SHIP. Commit blocked. Certification run invalid.
No waiver may suppress a CRITICAL finding — resolution is required.

---

# 5. CERTIFICATION IMPLICATIONS BY CLASS

| Severity | Cert behavior | Review obligation |
| -------- | ------------- | ----------------- |
| INFO | Logged in cert run report | None |
| WARN | Recorded; must be acknowledged before SEALED cert | Human annotation required |
| HIGH | CERTIFICATION HOLD — cert suspended | Resolve or issue governance waiver packet |
| CRITICAL | Cert run invalid — STOP-SHIP | Resolve only; no waiver path |

## Cert Run Validity Rule

A cert run is valid only if:

* `ai_preflight_check.py` exits 0
* `governance_drift_scan.py` exits 0 (no CRITICAL or HIGH)
* All WARN findings reviewed and annotated in the cert run report
* No open STOP-SHIP gates (OI-01, OI-03) unless formally waived

DISCOVERY_PASS findings are informational in cert context.
INFO findings from discovery are logged and require no annotation.

---

# 6. NON-ESCALATABLE CATEGORIES

The following categories are permanently capped at INFO regardless of:

* finding frequency
* finding persistence
* operator frustration
* scan surface expansion

These categories may never be promoted above INFO through escalation
criteria alone. Promotion requires amending this document (Section 7).

## Permanent INFO Cap Categories

| Category | Rationale |
| -------- | --------- |
| Comments, docstrings, inline documentation | No executable path; no authority relevance by definition |
| TODO / FIXME markers (no adjacent violation) | Observational; intent markers are not violations |
| Test fixtures and validation run artifacts | Non-production; excluded from replay chain |
| Disabled or commented-out code | Not reachable; cannot influence authority |
| Sample and example files explicitly marked as non-authoritative | Authority excluded by design |
| Frequency-based promotion of any INFO finding | Count does not change category membership |
| Whitespace, formatting, and style differences | No semantic authority relevance |
| Version string mismatches in non-authoritative metadata | Cosmetic drift only |
| Advisory-only Lane-2 output fields correctly labeled Authority ZERO | ZERO authority is the design contract |
| Findings in files with explicit `# ADVISORY ONLY` / `# NON-AUTHORITATIVE` markers that have been reviewed | Reviewed exemption stands until marker is removed |

## Anti-Alert-Fatigue Control

The purpose of this section is to prevent governance expansion from
filling observability space.

The scanner sees many things.
Only authority-relevant things deserve escalation.
Noise suppression is a governance property, not a scanner failure.

If a non-escalatable category is generating high finding volume:

* DO NOT promote the category
* DO investigate why the scanner is seeing it
* DO consider whether the scanner's scope should be narrowed
* DO NOT treat finding volume as a signal for severity promotion

---

# 7. ESCALATION GOVERNANCE RULES

## Severity Is Not Moral Weight

Severity classification reflects governance consequence.

It does not reflect:

* moral judgment about the finding
* blame assigned to the developer
* assessment of implementation quality
* organizational priority signaling
* emotional response to the finding

| Severity | What it means | What it does NOT mean |
| -------- | ------------- | --------------------- |
| CRITICAL | This finding threatens governance integrity | The developer failed |
| HIGH | This finding requires resolution before certification | This code is bad |
| WARN | This finding requires human acknowledgement | This approach is wrong |
| INFO | This finding is observed and recorded | This is acceptable forever |

This distinction is operationally necessary.

When severity carries moral weight:

* escalation becomes political
* suppression pressure rises from social dynamics instead of governance logic
* demotion becomes motivated by blame avoidance rather than reclassification evidence
* INFO inflation begins as people avoid triggering visible findings

When severity is mechanical:

* escalation follows criteria, not relationships
* suppression requires evidence, not social capital
* cert behavior is stable across teams and sessions
* governance is replayable — the same finding produces the same classification

Severity decisions must be:

* traceable to a specific Section 3 dimension
* documented with a concrete instance
* independent of who wrote the code
* independent of when the code was written
* identical whether the finding appears in your own code or someone else's

If a severity assignment cannot be justified without reference to the
author, the context, or the deadline, the assignment is wrong.

---

## Who May Promote Severity

| Actor | Authority |
| ----- | --------- |
| Human operator | MAY promote severity with documented rationale |
| AI (Claude, Gemini, ChatGPT, local LLM) | MAY recommend promotion; may NOT promote unilaterally |
| Automated tooling | MAY flag as candidate for review; may NOT promote |
| Governance drift scanner | MAY surface findings; may NOT classify above INFO in discovery mode |

Lane-2 Authority ZERO applies to severity promotion as it applies to
evidence and PASS/DROP decisions.

## Required Evidence for Promotion

Any severity promotion recommendation must include:

| Element | Requirement |
| ------- | ----------- |
| Authority-relevance dimension | Which Section 3 dimension triggered, and why |
| Concrete instance | A specific file, line, and content — not a theoretical case |
| Non-escalatable exclusion | Confirmation the finding does not fall in Section 6 |
| Proposed target severity | INFO → WARN, WARN → HIGH, or HIGH → CRITICAL with rationale |

## Required Evidence for HIGH → CRITICAL

Additionally requires:

| Element | Requirement |
| ------- | ----------- |
| Demonstrated replay or evidence impact | Not inferred — shown |
| Direct Lane-1 path | The violation is on an active authoritative execution path |
| Unambiguous violation | No interpretation required to identify the governance breach |

## Mandatory Version Bump Conditions

Any of the following changes to this document require a version bump
and a governance drift scan before the new version is effective:

* Adding or removing an entry from the non-escalatable categories (Section 6)
* Modifying the authority-relevance test dimensions (Section 3)
* Changing escalation criteria thresholds (Section 4)
* Adding a new severity class
* Changing who may promote severity (Section 7)

## Demotion Rules

Demotion (HIGH → WARN, WARN → INFO) follows the same governance process
as promotion:

* Human sign-off required
* Rationale documented
* Not suppressible by AI alone

Demotion is not a waiver. A waiver is a bounded exception for a specific
finding instance. Demotion reclassifies the category itself.

## Escalation as Drift Vector

Escalation governance rules exist because escalation is itself a mutation
path. Without governance, escalation:

* inflates severity to silence inconvenient findings
* suppresses severity to avoid operational consequence
* becomes shaped by the interests of the person proposing it

These rules make escalation auditable, reproducible, and authority-bounded.

---

# STATUS

State:   DRAFT
Version: v1.0
Saved:   2026-05-14
Scope:   ph6/ runtime tree discovery findings
Seal:    Not sealed — requires human review of Section 6 categories and Section 3 dimensions before operational use
Next:    Human review → seal → wire into discovery report annotations
