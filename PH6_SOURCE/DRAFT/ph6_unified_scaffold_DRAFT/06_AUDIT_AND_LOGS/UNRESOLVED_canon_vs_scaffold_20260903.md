Document Type: Reconciliation Record
Status: UNRESOLVED — RECONCILIATION REQUIRED
Version: 0.1
Authority: Lane 2 advisory/build output only — records a finding, resolves nothing
Ratification: NONE

# UNRESOLVED — PH6_CONSOLIDATED_CANON.docx vs. active scaffold tooling

## Decision on record
Jack explicitly chose **not** to edit `PH6_CONSOLIDATED_CANON.docx` to match
the scaffold, and not to edit the scaffold to match the document. Per his
own words: *"leave the document as-is, record as explicit
UNRESOLVED — RECONCILIATION REQUIRED item, decide later which one
governs."* This file is that record. No content was changed on either
side to produce it.

## Source document
`01_DOCTRINE_AND_SPEC/PH6_CONSOLIDATED_CANON.docx` — self-declared header:
`Classification: CANON`, `Status: Development-operational / Production
STOP-SHIP / HRG9 OPEN`, `Version: v5.2-RC4 consolidated April 2026`.

## What conflicts, specifically

1. **Gate logic and thresholds.** Document §II.5 locks a single-frame,
   no-persistence veto model: Shannon entropy 3.5–7.5, Laplacian variance
   ≥60.0, motion fraction 0.05–0.95; any one veto → DROP. The scaffold's
   `03_VERIFICATION_AND_TESTS/constants_v1.0.json` and `05_TOOLS/verify_vectors.py`
   implement a different model entirely: different threshold values, plus
   a consecutive-frame persistence counter (`ENTROPY_PERSISTENCE`,
   `MOTION_WINDOW`) and a rolling z-score anomaly check the document
   doesn't mention.

2. **Different golden vector suites, testing different things.** The
   document's `C1-001`…`C1-012` + `C1-R001`–`R003` vectors test
   `fp_int(value, scale=10000)` — fixed-point conversion, rounding,
   NaN/Infinity rejection. The scaffold's
   `03_VERIFICATION_AND_TESTS/golden_vectors/golden_vectors_v1.0.json`
   (`GV-001`…`GV-006`) tests frame-verdict sequences. Not two versions of
   the same test — two tests of two different subsystems.

3. **Different implementation package referenced.** The document names
   `ph6_six_engine_pack/ph6/audit.py` and five schema files
   (`audit_event.schema.json`, `evidence_packet.schema.json`,
   `lane1_verdict.schema.json`, `replay_manifest.schema.json`,
   `soso_token.schema.json`). None of these exist anywhere in this
   scaffold. `05_TOOLS/` only contains `verify_manifest.py`,
   `verify_vectors.py`, `verify_manifest_blake2b.py`.

## What this does NOT mean
This is not necessarily an error in either artifact. The pattern (locked
fixed-point contract with real golden vectors, a named implementation
package, different gate math) reads like a **different generation or
branch** of the PH6 measurement subsystem than the one in
`ph6_repo_skeleton_v2` that this scaffold was built from — not a typo in
one or the other.

## What this DOES mean, procedurally
Per the "no silent fallback" / "reconcile, don't guess" principle already
on record in this project: **neither `constants_v1.0.json`/`verify_vectors.py`
nor `PH6_CONSOLIDATED_CANON.docx`'s §II.5/§IV.3 should be treated as
settled relative to the other** until Jack decides which generation
governs, or whether both need to coexist as explicitly versioned,
separately-scoped subsystems.

## What's resolved from this document, unaffected by the above
Two things from this document were treated as resolved-in-your-favor
already, and stand independent of the conflict above:
- `BLAKE2b-256` as primary hash / `SHA-256` as compatibility-only (§II.14) —
  first real source confirmation this session, not affected by the
  gate/vector mismatch.
- `Lane 5 = RSYNC / evidence export / Priority Zero` — resolves the
  previously-flagged undefined "Lane 5" reference.

## Still open
`fp_int(scale=10000, ROUND_HALF_EVEN)` is closer to complete (real golden
vectors now exist for it) but still doesn't define sqrt, division, or
entropy/log implementation — per Jack's own standing list of what's
missing, this remains **PROPOSED**, not implemented in
`verify_vectors.py`.

## Addendum — 2026-09-03, source-availability finding (Jack)

Jack checked the file library rather than assuming `ph6_six_engine_pack`
was absent. Finding, as reported:

| Evidence | State |
|---|---|
| Consolidated doctrine | Available |
| Six-book canon | Available |
| Manifest | Available |
| Historical references to implementation pack | Available |
| `ph6_six_engine_pack/ph6/audit.py` actual source | Not available |
| Five actual schema files | Not available |
| Byte-level implementation comparison | Blocked |
| Actual runtime lineage verification | Blocked |
| Paper/spec lineage analysis | Possible |

Cited support: `PH6_CONSOLIDATED_CANON.docx` names
`ph6_six_engine_pack/ph6/audit.py` as authoritative and the five schemas
under `ph6_six_engine_pack/schemas/` as locked, and states the standalone
`08_IMPLEMENTATION_SOURCE/audit.py` is stale/superseded by the pack's
version — I confirmed these specific claims directly against the docx
already in this scaffold. Jack additionally cites
`PH6_SMI1_COMPLIANCE_REPORT.md` as independently recording the same
`ph6_six_engine_pack/ph6/audit.py` defect.

**Verification note:** `PH6_SMI1_COMPLIANCE_REPORT.md` has not been
uploaded to me and isn't in this scaffold. That citation is taken on
trust from Jack's report, not independently inspected — the same
"reference is not evidence" standard applied to `ph6_six_engine_pack`
itself applies here too, for consistency.

**Gate state: lineage/reconciliation PARTIALLY ENABLED.** Paper-level
comparison between the canon's stated expectations and this scaffold's
actual tooling remains possible and already partly done (see mismatches
above). Implementation-level verification — whether any actual code ever
conformed to either spec — stays BLOCKED until `ph6_six_engine_pack`'s
real source is recovered. No canon or scaffold content changed by this
addendum; source-availability finding only.
