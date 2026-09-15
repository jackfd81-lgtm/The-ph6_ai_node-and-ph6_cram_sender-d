# PH6-RECONCILIATION-PASS-001

Status: **PROPOSED — Lane-2, Authority ZERO — reconnaissance/investigation only, not ratified**

Follows on from PR #17 (`PH6-SOURCE-MANIFEST-001`), which is left untouched by
this pass per explicit operator direction ("PR #17 has reached its proper
stopping point"). This is a **separate** deliverable on its own branch, not an
addendum to #17.

Scope executed this pass, per operator-approved sequence:
1. Evidence Kernel / Patch Set 001 — exhaustive trace.
2. RECON-001 — exhaustive trace.
3. First-pass repository implementation inventory (the "Repository says" /
   "Implementation" columns of the requested reconciliation matrix).
4. Observe-only Raspberry Pi audit — **prepared, not executed** (still no
   hardware/network access from this session).

Explicitly **not** done this pass (per operator's phased plan): merging PR
#17, executing the Pi audit, writing/building anything, or making
KEEP/HARDEN/REUSE/BUILD determinations (that's Phase 6, gated on the three
items above — this pass only produces their inputs).

---

## 1. Evidence Kernel / Patch Set 001 — exhaustive trace, still not located

The prior finding (PR #17 addendum) searched the main working tree, the
operator-staged corpus index, and `PH6_SOURCE/GAP_REGISTER_v3.0.md`. This
pass extended that to **every branch that exists in this GitHub repository**:

- Fetched and `git grep`'d all 19 branches (`main`, this session's own 2
  branches, and all 16 other `claude/`, `ph6/`, and `copilot/` branches
  corresponding to PRs #1–16 plus one branch with no open PR).
- Searched commit messages and file-content history across all refs
  (`git log --all --grep`, `git log --all -S`) for `evidence kernel`,
  `RECON-001`, `canonicalizer`, `EK-001`, `conformance suite`.

**Result: zero hits anywhere, under any spelling, on any branch.** The only
matches in the entire search are this session's own PR #17 manifest/report
text, which is not a repository-canon reference.

### Closest candidate found: PH6 Canon V1 (PR #9, unmerged, stale)

`claude/ph6-canon-rc2-search-h1dq0c` (PR #9, opened 2026-06-19, **still open,
draft, never merged**, diverged from `main` at `e23749a1d0` — i.e. it predates
roughly a dozen commits now on `main` and was never rebased) contains a
structurally complete canonicalization/verification chain:

| Evidence Kernel concept (as described in the operator-relayed claim) | PR #9 artifact |
|---|---|
| Canonicalizer | `PH6_SOURCE/TOOLS/canon_compiler/canon_compiler.py`, `PH6_SOURCE/CANON/PH6-CANON-V1-SPEC-0.3-RC2.md` (canonical JSON + BLAKE2b-256 hash construction spec) |
| Verifier | `ph6/tiny_validator.py` — dual-implementation (Impl-A stdlib `json.dumps`, Impl-B hand-rolled) |
| Fixtures | `PH6_SOURCE/CANON/ph6_canon_v1_vectors/{accept,reject,quarantine}/*.json` — 11 vectors (4 ACCEPT, 6 REJECT, 1 QUARANTINE) |
| Conformance suite / result | `PH6_SOURCE/DEPLOYMENT/validator_run_report.json` — an actual executed run, self-reported (not independently re-run this pass) as 11/11 vectors matched, `all_impl_match: true` |

**None of these files exist on `main`** — confirmed by direct path check
against this session's checkout. They exist only on PR #9's unmerged branch.

**This is not a confirmed identity claim.** PH6 Canon V1 and "Evidence
Kernel Patch Set 001" are two different names, and no artifact anywhere
establishes they refer to the same thing. What can be said: if "Evidence
Kernel" refers to *some* canonicalizer+verifier+fixtures+conformance-suite
capability for PH6, PR #9 is the only real, executed, passing candidate
implementation of that shape found anywhere in this repository's full
branch history — and it is six months stale and was never merged. Recorded
as a finding to route to the operator, not resolved.

**Separately, the operator-staged corpus** (searched previously, not
re-searched this pass) contains `PH6_TFH_AK_v1_1_1.zip` — real
audit/canonical/provenance/replay code under a third, different name
(`TFH_AK`), whose byte content remains unavailable to this session. That
finding is unchanged from the PR #17 addendum.

So there are now **three distinct, non-identical candidates** for whatever
"Evidence Kernel" is supposed to name: PH6 Canon V1 (unmerged branch, in
repo), TFH_AK v1.1.1 (staged corpus, not in repo), and no artifact anywhere
literally named "Evidence Kernel." Reconciling which (if any) of these is
the intended referent is a governance/naming decision, not something this
session can infer.

---

## 2. RECON-001 — exhaustive trace, still not located

Same exhaustive method as above (19 branches, commit messages, content
history, operator-staged corpus index): **zero hits, anywhere, under the
literal string `RECON-001`.**

```json
{
  "status": "NOT_FOUND_IN_DECLARED_CORPUS_COVERAGE",
  "scope": "all 19 branches in jackfd81-lgtm/the-ph6_ai_node-and-ph6_cram_sender-d (commit messages + full content history) + operator-staged corpus index (initial.json, 349 artifacts) + both supplied handoff/patch zip packages",
  "global_absence_proven": false
}
```

This is a stronger evidence base than the PR #17 finding (which covered only
the main working tree and the staged-corpus index), but the conclusion is
unchanged, and `global_absence_proven` remains explicitly `false`: this does
not prove RECON-001 doesn't exist somewhere entirely outside what this
session has access to (an external document, a different repository, the
operator's own notes). No reconstruction from memory or inference was
performed.

---

## 3. First-pass repository implementation inventory

Requested reconciliation matrix, populated only where this pass found real
evidence. `Source says` reflects CLAUDE.md/doctrine already read in the PR
#17 pass; `Hardware` is `N/A` throughout (no domain here has a hardware
component except the Pi row) or `NOT_ASSESSED` for the Pi row itself. This
is a **first pass, not exhaustive** — several rows note where deeper
tracing was out of scope for this pass's effort budget.

| Domain | Source says | Repository says | Implementation | Status |
|---|---|---|---|---|
| Lane-1 authority (PSEUDO-A) | Deterministic, sole PASS/DROP authority (CLAUDE.md) | Referenced pervasively across `ph6/cram_pu/` (`canonical.py`, `tok_soso_isolation_proof.py`, `evc02_long_run.py`, campaign tools) | No single dedicated "PSEUDO-A" module located in this pass's search depth — authority logic appears distributed rather than centralized in one file. **Needs a dedicated follow-up pass**, not concluded here. | PARTIAL_TRACE |
| CRAM-A / CRAM-R | Authority store (PASS, `.blake2b` last) / reject store (DROP, no marker) | `class CRAMWriter` found at `ph6/cram_pu/crash_replay.py:617` | Exists and is referenced by PR #16 as "untouched, still refuses non-PASS verdicts" (self-reported by that PR, not independently re-verified this pass) | REPO_PRESENT_NOT_DEEPLY_VERIFIED |
| MRAM-S | Sealed advisory archive | Referenced across `ph6/ssmt/`, `ph6/hw_hooks/`, `ph6/cram_pu/` (`errors.py`, `live_sidecar.py`, `advisory_log.py`, `vrc.py`, `crash_replay.py`) | Present, multi-file; not traced to one canonical implementation in this pass | REPO_PRESENT_NOT_DEEPLY_VERIFIED |
| SoSo (Lane-2 advisory) | Advisory, Authority ZERO | Substantial implementation: `ph6/ssmt/{execution_graph,errors,audit_writer,replay_receipt,audit_log,tok_index,hash_chain,temporal_decay,closure}.py` and more | Implemented, multi-module | KEEP_CANDIDATE (pending deeper test/validation check) |
| Tokens: RT / VDT / VLT | Token lifecycle doctrine | `class RT`, `class VDT`, `class VLT` confirmed in `ph6/tok/lifecycle.py` on `main` | Implemented | KEEP_CANDIDATE |
| Tokens: RLT / PLT / AHT | Same doctrine, §4/§6 of `PH6_LIVING_MEMORY_TOKEN_RETENTION_POLICY.md` | Doctrine only on `main`; implementation exists solely on unmerged PR #16 | `IMPLEMENTED_ON_UNMERGED_BRANCH` (see PR #17 manifest) | HUMAN_REVIEW_PENDING (PR #16) |
| NERO | Advisory topology component (per staged corpus naming) | **Zero occurrences anywhere in the git repository** (`ph6/`, `PH6_SOURCE/`, all 19 branches) | Not implemented in repo. **Exists only in the operator-staged corpus**: `PH6_SOSO_NERO_CONTROL_PACKAGE_V0_1_ADVISORY_DRAFT.zip` (schemas, a validator script, a bootstrap README, a commands shell script) and a second reference in `PH6_SOSO_SYSTEM_scaffold.zip::.../05_NERO/`. **Same pattern as BCV2**: named, real, staged, never landed. | UNRESOLVED_STAGED_ONLY |
| BCV2 | Candidate memory substrate | Starter confirmed in staged corpus only (see PR #17 manifest, `PH6-CLAIM-BCV2-FULL-PRODUCT-STATUS`) | `MINIMAL_SCAFFOLD`, staged only | UNRESOLVED_STAGED_ONLY |
| Evidence Kernel | Claimed/relayed, not independently sourced | Not found under that name anywhere (see §1) | Closest candidate: PH6 Canon V1 (PR #9, unmerged, stale) — different name, unconfirmed identity | UNRESOLVED — see §1 |
| SoSo-JEDI | Proposed specialist layer | `PH6_SOURCE/AI/soso_jedi/jedi/swarm_sim_bp.py` (`BookVCoreEngine`) confirmed present; `PH6_SOURCE/AI/soso_jedi/token_provenance.py` added by unmerged PR #16 | Base engine implemented on `main`; provenance adapter unmerged | KEEP_CANDIDATE (base) / HUMAN_REVIEW_PENDING (adapter, via PR #16) |
| Certification | Defined tests/certification process | `PH6_SOURCE/SCHEMAS/replay/replay_certification_record.schema.json` confirmed present. The `PH6_SOURCE/CERTIFICATION/audit_patched.py` path referenced by `PH6_SOURCE/DEPLOYMENT/PH6_REPO_CLEANUP_CLASSIFICATION.md` **was not found at that path** in the current tree — possible drift between that classification doc and actual repo state; not resolved this pass. | Schema present; the named audit tool's actual location is unconfirmed | NEEDS_FOLLOW_UP |
| Raspberry Pi deployment | Documented node roles (CLAUDE.md) | N/A | Not assessed on hardware | NOT_ASSESSED — see §4 |

### 3.1 A broader pattern worth naming explicitly

BCV2 and NERO are not isolated cases. The operator-staged corpus contains
**13 top-level packages**, none of which exist in this git repository
(confirmed in the PR #17 pass: zero archive files anywhere in the tracked
working tree). This pass only closely inspected two of them (BCV2, and
partially TFH_AK). The other ten —
`PH6-SoSo-Agent-Reasoning-Core-v0.1.zip`,
`PH6_CANON_STACK_v4.0_SOURCE_SET 3.zip`,
`PH6_SOSO_SOURCE_DOCUMENT_SET.zip`, `PH6_SOSO_SYSTEM_scaffold.zip`,
`PH6_SOURCE_SCAFFOLD_DRAFT_HANDOFF.zip` (+ `_v2`),
`PH6_STORAGE_LIBRARY_SOURCE_PACKAGE_SCAFFOLD.zip`, `ph6_closure_code.zip`,
`tri_ph6_cram_ORGANIZED.zip`, and one oddly-named loose text file
(`corpus contains a much stronger PH6 constitutional, implementation,
boundary, to.txt`) — have **not** been individually traced this pass. This
is flagged, not investigated further here, since it's a materially larger
piece of work than the two named priorities (Evidence Kernel, RECON-001)
and would need its own scoped pass.

---

## 4. Raspberry Pi observe-only audit — PREPARED, NOT EXECUTED

This session still has no network route to the operator's LAN and no
hardware access. Nothing below was run. This is a command list only, for
the operator (or a future session with actual reach) to execute and paste
back — read-only, no installation, no configuration changes, no service
modifications, no writes to any PH6 evidence directory.

```
# Identity
cat /proc/device-tree/model 2>/dev/null; uname -a

# Storage / mounts
lsblk; findmnt; df -h

# Network
ip addr; hostname; hostname -I

# Camera
ls -l /dev/video* 2>/dev/null; v4l2-ctl --list-devices 2>/dev/null

# Thermal / throttling
vcgencmd measure_temp 2>/dev/null; vcgencmd get_throttled 2>/dev/null

# Services
systemctl list-units --type=service --state=running | grep -i ph6

# PH6 directories (read-only listing only)
ls -la /var/ph6 2>/dev/null
find / -maxdepth 4 -iname "*ph6*" -not -path "/proc/*" -not -path "/sys/*" 2>/dev/null

# Permissions on anything found above
stat <path-from-above>
```

Once run, the results should be compared against CLAUDE.md's node table
(§NODES) per artifact, per the v0.2.1 patch's `deployment_correspondence`
schema already validated in PR #17 — producing `OBSERVED_MATCH`,
`OBSERVED_MISMATCH`, `VARIANT`, or staying `UNRESOLVED`, never inferred from
this document alone.

---

## 5. What this pass explicitly did not do

- Did not touch, amend, or comment on PR #17.
- Did not merge or approve any PR.
- Did not execute the Pi audit (no access) or fabricate its results.
- Did not modify any PH6 production code (`ph6/`, `ph6_ai_node/`,
  `ph6_cram_sender/`, `ph6_l2_expand/`).
- Did not attempt KEEP/HARDEN/REUSE/BUILD classification — that requires
  the three items above to actually resolve first, per the operator's own
  phased sequence.
- Did not individually trace the remaining ~10 staged corpus packages
  named in §3.1.

```json
{"proposed_by":"claude-code-lane2","proposed_at_utc":"2026-09-15T11:54:16Z","api_call_log_ref":"ph6-reconciliation-pass-001-session","ratified_by":null}
```

---

## 6. Addendum (same session) — Evidence Kernel identity reconciliation + 2 more staged packages

Per operator authorization to run a structured identity reconciliation
(not "which candidate is real" but "what is each one, and how do they
relate") across the three Evidence Kernel candidates, plus inspect two
more Priority-1 staged packages.

### 6.1 Naming correction, stated plainly

The operator's suggested Priority 2 list named `PH6_RULES_PACKAGE` and
`PH6_CONSOLIDATED_MATERIAL_PACKET`. **Neither exists** among the actual 13
top-level staged-corpus package names recorded in `initial.json`. The real
list is: `PH6-SoSo-Agent-Reasoning-Core-v0.1.zip`, `PH6_BCV2_SoSo_Starter.zip`,
`PH6_CANON_STACK_v4.0_SOURCE_SET 3.zip`,
`PH6_SOSO_NERO_CONTROL_PACKAGE_V0_1_ADVISORY_DRAFT.zip`,
`PH6_SOSO_SOURCE_DOCUMENT_SET.zip`, `PH6_SOSO_SYSTEM_scaffold.zip`,
`PH6_SOURCE_SCAFFOLD_DRAFT_HANDOFF.zip` (+ `_v2`),
`PH6_STORAGE_LIBRARY_SOURCE_PACKAGE_SCAFFOLD.zip`, `PH6_TFH_AK_v1_1_1.zip`,
`ph6_closure_code.zip`, `tri_ph6_cram_ORGANIZED.zip`, and one oddly-named
loose text file. This isn't pedantry: silently substituting a plausible-
sounding name for the real one is exactly the kind of drift this whole
exercise exists to prevent, so it's corrected here rather than quietly
followed.

### 6.2 Evidence Kernel identity reconciliation

| Field | Candidate A — PR #9 "PH6 Canon V1 RC2" | Candidate B — TFH_AK v1.1.1 | Candidate C — "Evidence Kernel Patch Set 001" |
|---|---|---|---|
| Artifact identity | Canonical JSON serialization spec + dual-impl validator + golden vectors + conformance report | Audit/canonicalization/provenance/replay Python package with its own CLI, schemas, systemd unit | No artifact located under this name anywhere searched |
| Branch | `claude/ph6-canon-rc2-search-h1dq0c` (open PR #9) | N/A — not in this git repository at all; staged corpus only | N/A |
| Commit | `86b473c9af231ac6d18e7d2d493bcbcbdbe42e45` | N/A (zip, not a commit) | N/A |
| Date | 2026-06-19T11:34:26Z (commit); `SHA256SUMS.json` says `generated_at_utc: 2026-06-19T00:00:00Z`; `governance_manifest.json` inside it is dated `2026-06-06` (older, bundled from an earlier pass) | Unknown — `initial.json` only records the staging snapshot time (2026-09-15), not the package's own creation date; its internal `MANIFEST.yaml`/`CHANGELOG.md` presumably has one but this session cannot read staged-corpus byte content | N/A |
| Status | Open, draft, **never merged**, base diverged from `main` at `e23749a1d0` — roughly a dozen commits behind current `main` | Not applicable to git status; exists only in the operator's separately-staged `/mnt/data` corpus | Not found |
| Specification | `PH6_SOURCE/CANON/PH6-CANON-V1-SPEC-0.3-RC2.md` — canonical JSON + BLAKE2b-256 hash construction | `PH6_TFH_AK_v1_1_1/docs/PH6-TFH-001.md` (path confirmed, content not read this session) | None |
| Canonicalizer | `PH6_SOURCE/TOOLS/canon_compiler/canon_compiler.py` (real, in-repo-on-branch bytes read) | `ph6_tfh/canonical.py` (path only, content unread) | N/A |
| Verifier | `ph6/tiny_validator.py`, dual implementation (Impl-A/B) | No file path suggesting a standalone "verifier" distinct from the audit engine (`ph6_tfh/audit/engine.py`) | N/A |
| Fixtures | 11 vectors: `ph6_canon_v1_vectors/{accept×4,reject×6,quarantine×1}` | `tests/vectors/{clear_translation,provenance_break,scope_drift}.json` — 3 vectors, different domain (translation/scope, not accept/reject/quarantine) | N/A |
| Conformance | `PH6_SOURCE/DEPLOYMENT/validator_run_report.json` — self-reported 11/11 matched, `all_impl_match: true` (not independently re-run this session) | `tests/{test_authority,test_tfh,test_v1_1_0_fixes}.py` exist (paths only; pass/fail status unknown, content unread) | N/A |
| Hash profile | SHA-256 **and** BLAKE2b-256 recorded per-file in `SHA256SUMS.json` (both algorithms, explicitly labeled "BLAKE2b-256 (PH6 authority hash)") | `ph6_tfh/provenance/hashes.py` exists (path only; algorithm unconfirmed) | N/A |
| Schema | `ph6.canon.v1.rc2.sha256sums`, `authority: "ZERO"`, `production_status: "TEST_HARNESS_ONLY"` | `schemas/{audit,receipt_bundle,representation,translation_contract}.schema.json` (paths only) | N/A |
| Authority | Explicitly `ZERO` / `TEST_HARNESS_ONLY` (self-declared in `SHA256SUMS.json`) | `ph6_tfh/governance/{drift_gate,policy,registry}.py` suggest it has its own governance/authority model, distinct from PH6's Lane-1/Lane-2 split — unconfirmed without reading content | N/A |
| Relationship to BCV2/TFH/CRAM | No reference to BCV2, TFH, or CRAM found in the file names/paths available | Name itself ("AK" = plausibly "Audit Kernel") suggests audit/evidence framing; no confirmed link to BCV2 or Canon V1 | N/A |
| Supersession | Nothing on `main` derives from or supersedes it (see 6.3) | Unknown | N/A |
| Currentness | **Not current** — corrected finding, see 6.3 below | Not in repo at all — not current by definition | N/A — nothing to be current with |

**Outcome: `IDENTITY_UNRESOLVED` for all three pairwise relationships.**
None of `CONFIRMED_SAME_REFERENT`, `CONFIRMED_PREDECESSOR`,
`CONFIRMED_SUCCESSOR`, `RELATED_BUT_DISTINCT`, or `UNRELATED` can be
established from evidence available to this session. What can be said:
Candidate A is real, in-repo (on an unmerged branch), executed, and
self-reported passing. Candidate B is real but access-limited (staged
corpus, no byte content available). Candidate C's literal name is
unlocated anywhere. They are three different names with three different
evidence profiles, not three descriptions of one thing.

### 6.3 Correction to this session's own earlier "currentness" check

Initial grep for `canon_compiler` against `main` returned a hit:
`PH6_SOURCE/TOOLS/guard_scanner/canon_compiler_guard.py`. Read in full,
that file's own docstring states: *"PH6CRAM Canon Guard Scanner — checks
all Python modules enforce if-main execution guards. **Separate from
canon_compiler.py (manifest generator)**."* It was added to `main` by a
different, earlier commit (`621a959258`, `"sei: integrate PH6 scientific
evidence instrument architecture"`) that predates this session's initial
20-commit `git log` window and was not otherwise investigated. The file
explicitly disclaims any relationship to PR #9's `canon_compiler.py` — so
this is **not** evidence that Candidate A is current on `main`; it's a
coincidental name match in an unrelated file, correctly self-labeled by
the file itself. Corrected in the table above rather than left standing.

Flagging without investigating further: that `sei:` commit references a
**"PH6 scientific evidence instrument architecture"** — a component name
not previously encountered in this reconciliation pass or PR #17's
manifest, and not covered by the 11-domain matrix in §3. Out of scope for
this addendum; noted so it isn't lost.

### 6.4 Two more Priority-1 staged packages — structural inventory only (index-only, no byte access)

Same access limitation as every other staged-corpus finding in this and
the PR #17 pass: `initial.json` records path + hash + size only, never
file contents. What follows is member-path structure, not code review.

**`PH6-SoSo-Agent-Reasoning-Core-v0.1.zip`** (SHA-256 `7fa81d1d...45a1a`,
45285 bytes, 23 members) — a substantial, separate SoSo implementation:
`soso_controller.py`, `soso_reasoner.py`, `soso_reasoning_core.py`,
`soso_mram_s.py`, and a `soso/` package with `boundary/guard.py`,
`provenance/analyzer.py`, `reasoning/{context,contracts,orchestrator}.py`,
`relationships/mapper.py`, `source/identity.py`, `run_vertical_slice.py`.
This is structurally distinct from (not obviously the same as) the SoSo
implementation actually on `main` (`ph6/ssmt/*.py`, listed in §3). Whether
this staged package is a predecessor, an alternate design, or unrelated
research is **unresolved** — same "staged, never landed" pattern as
BCV2/NERO, now confirmed for a third domain.

**`ph6_closure_code.zip`** (SHA-256 `128a968b...d2d253`, 6804 bytes, 9
members) — `ph6/canon.py`, `ph6/audit.py`, `ph6_cert/hrg9.py`,
`ph6_cert/validate_run.py`, `build_hrg9_manifest.py`. The `hrg9` naming is
notable: CLAUDE.md records `HRG9` as **CLOSED at commit `2ef5fd6`, "NEVER
regenerate or list as open."** This package is very plausibly the
historical source of that closure — but this is an inference from naming,
not confirmed from content, and per CLAUDE.md's own explicit instruction
this is **not being reopened or investigated further**. Noted for the
record only.

### 6.5 What this addendum still does not do

- Does not resolve `IDENTITY_UNRESOLVED` for the Evidence Kernel
  candidates — that's the operator's call once actually needed.
- Does not touch HRG9 (explicitly closed, never to be regenerated).
- Does not investigate the newly-surfaced "SEI" (scientific evidence
  instrument) component.
- **Count correction (caught on operator review, not by this session
  unprompted):** this section originally said "6 remain." That was wrong.
  13 total top-level staged packages minus the 5 actually examined
  (`BCV2`, `NERO`, `TFH_AK`, `PH6-SoSo-Agent-Reasoning-Core-v0.1`,
  `ph6_closure_code`) leaves **8** remaining, not 6:
  `PH6_CANON_STACK_v4.0_SOURCE_SET 3`, `PH6_SOSO_SOURCE_DOCUMENT_SET`,
  `PH6_SOSO_SYSTEM_scaffold`, `PH6_SOURCE_SCAFFOLD_DRAFT_HANDOFF` (v1
  *and* v2 — counted separately, both real distinct package entries),
  `PH6_STORAGE_LIBRARY_SOURCE_PACKAGE_SCAFFOLD`, `tri_ph6_cram_ORGANIZED`,
  and the one loose text file. See §7 — all 8 are now inventoried.
- Does not build the full machine-readable "PH6 Implementation & Source
  Reconciliation Matrix" schema — deliberately held for a dedicated pass
  once staged-package inventory is further along, per the operator's own
  recommended ordering.

```json
{"proposed_by":"claude-code-lane2","proposed_at_utc":"2026-09-15T11:59:41Z","api_call_log_ref":"ph6-reconciliation-pass-001-session-addendum-1","ratified_by":null}
```

---

## 7. Addendum 2 (same session) — remaining 8 staged packages, index-only

Per operator authorization to complete the controlled inventory before
starting the reconciliation matrix. Same access limitation throughout:
`initial.json` records path + hash + size, never file bytes. **No nested
archive was extracted** (several packages below contain their own nested
`.zip`/`.tar.gz` members — those are listed by path only, per explicit
instruction not to extract without separate, controlled authorization).
No filename is treated as establishing identity by itself.

### 7.1 SEI correction

§6.3 characterized "SEI" (scientific evidence instrument) as "newly-
surfaced" and "previously unnoticed." That was imprecise. A repo-wide
search this round found it's actually already documented on `main`:
`PH6_SOURCE/GOVERNANCE/scientific/PH6_SCIENTIFIC_EVIDENCE_INSTRUMENT_DOCTRINE.md`,
referenced across several `PH6_SOURCE/DRAFT/PH6-*-INGEST-*` files. It was
outside the 11-domain list this pass was originally scoped to (§3), not
actually hidden or undocumented. Corrected here rather than left standing.

### 7.2 The 8 packages

**`PH6_CANON_STACK_v4.0_SOURCE_SET 3.zip`** (SHA-256 `f565c6e7...c6e05`,
471,759 bytes, 11 members) — a "Books 0–V" canon stack: `BOOK 0 —
INTERPRETIVE CONTROL PLANE`, `BOOK I — OPERATIONAL SOURCE CONSTITUTION`,
`BOOK II — SCIENTIFIC INSTRUMENT MASTER`, `BOOK III — BOUNDARY CONTAINMENT
ANNEX`, `BOOK IV — CERTIFICATION PROOF PACK`, `BOOK V — EXPERIMENTAL SWARM
ANNEX` (all PDF), plus `PH6_MASTER_v4.0.pdf`/`.docx`,
`ph6_consolidation_manifest_v2.json`, `00_INDEX..md`, `text.txt`. **Book
II's title plausibly relates to the SEI doctrine in §7.1** — unconfirmed,
content unread (PDF, not extracted). File names in this package are
UTF-8-mis-decoded in the index (`ΓÇö` = a corrupted em dash "—") — a
staging/encoding artifact, not meaningful data, noted so it isn't
misread. This is "v4.0" of canon; the actual repo's own canon material
(`PH6_SOURCE/CANON/`, `PH6_SOURCE/DRAFT/`) uses different version markers
throughout (Canon V1 on PR #9, `PH6-MASTER-AI-INGEST-6.0.md` on main) —
whether "v4.0" here is an ancestor, a parallel numbering scheme, or
unrelated is **unresolved**, flagged for possible byte-level follow-up
given its apparent scope (six "books").

**`PH6_SOSO_SOURCE_DOCUMENT_SET.zip`** (SHA-256 `bbf13382...8434e96`,
79,726 bytes, 64 members) — a large, internally-numbered SoSo doctrine set
(`DOCUMENT_000` through `DOCUMENT_050`), covering doctrine, `AUTHORITY_ZERO`,
`SEVEN_IRON_LAWS`, lane definitions, governance architecture, a JSON
schema (`ph6_soso_step3_record_v0_2_candidate.schema.json`), a validator
(`validators/procedural_validator_scaffold.py`), and example fixtures
(valid/invalid JSON records). **Notably, it contains its own internal
supersession bookkeeping**: `DOCUMENT_044_HISTORICAL_ARTIFACT_REGISTRY.md`,
`DOCUMENT_045_SUPERSEDED_DOCUMENT_REGISTRY.md`,
`DOCUMENT_046_DEPRECATED_DOCUMENT_REGISTRY.md`,
`DOCUMENT_047_SOURCE_MATERIAL_LINEAGE_MAP.md`. Also contains
per-provider AI advisory review documents (`DOCUMENT_040`–`043`: Claude,
Gemini, Perplexity, Grok). **Flagged as high-value for a future
byte-level pass**: if this package's own registries are readable, they
may directly answer some of this reconciliation's open questions (e.g.
whether some staged material is already self-declared superseded) without
this session having to infer it. Not read this pass — index only.

**`PH6_SOSO_SYSTEM_scaffold.zip`** (SHA-256 `2fe975a1...bcded53ba`, 26,801
bytes, 47 members) — a complete numbered doctrine+test scaffold
(`00_INDEX` through `11_BOOTSTRAPS`). `00_INDEX/SUPERSEDED_CLAIMS.md` and
`00_INDEX/CURRENT_ACCEPTED_MODEL.md` are the same self-bookkeeping pattern
as the document set above. **New finding: `03_TOKENS/{MIT,PIT,SIT}.md`
name three token types not seen anywhere else this pass** — distinct from
the six already known (`RT`/`VDT`/`VLT` implemented on `main`;
`RLT`/`PLT`/`AHT` doctrine + PR #16 unmerged implementation). A repo-wide
search this round for `MIT`/`PIT`/`SIT` as token-family terms (not the
MIT license) found **zero hits anywhere in the git repository** — these
three exist only in this one staged package. `07_CRAM_PSEUDO_BOUNDARY/`
contains `PASS_DROP_AUTHORITY.md` and `PSEUDO_A_VALIDATION_BOUNDARY.md` —
doctrine-level material that may bear on §3's `PARTIAL_TRACE` finding for
Lane-1/PSEUDO-A (no single dedicated module was found in the actual repo
code); unread this pass, flagged for follow-up. `09_TESTS/` contains
actual test files (`test_lane2_no_pass_drop.py`,
`test_vlt_not_confirmed_identity.py`, etc.) — a fourth "staged, never
landed" implementation-adjacent package, same pattern as BCV2/NERO/
SoSo-Agent-Reasoning-Core.

**`PH6_SOURCE_SCAFFOLD_DRAFT_HANDOFF.zip`** (v1, SHA-256
`0719714f...335a81c`, 17,684 bytes) and **`_v2.zip`** (SHA-256
`540608d9...ce94447`, 17,666 bytes) — both 9 members, same 9 relative
paths (`PH6_SOURCE/{00_INDEX,01_CORE_DOCTRINE,02_GOVERNANCE×3,
03_ARCHITECTURE,04_REQUIREMENTS,08_HANDOFFS,09_PROMPTS}/*_V0.1.md`), a
"v0.1" doctrine baseline scaffold. **Member-level hash comparison, done
this pass**: 8 of 9 files are byte-identical between v1 and v2; only
`PH6_SOURCE/00_INDEX/PH6_INDEX_V0.1.md` differs. So v2 is a narrow,
confirmed, single-file index update over v1 — not a full rewrite. This is
about the only place in this whole reconciliation pass where a
version-to-version delta could be established with certainty rather than
inferred.

**`PH6_STORAGE_LIBRARY_SOURCE_PACKAGE_SCAFFOLD.zip`** (SHA-256
`6057b73a...5c6fc9386`, 8,474,298 bytes, 4 members) — a wrapper directory
(`PH6_STORAGE_LIBRARY/SOURCE_PACKAGES/PH6_CRAM_ORGANIZED_SOURCE_PACKAGE/`)
containing a manifest, two README-style markdown files, and **a nested
`tri_ph6_cram_ORGANIZED.zip`**. **Hash comparison, done this pass**: this
nested zip's SHA-256 (`65dbe824...21a6f3442`) is **byte-identical** to the
standalone top-level `tri_ph6_cram_ORGANIZED.zip` entry below. Confirmed
duplicate staging — the same 8.4MB archive is catalogued twice in the
corpus (once wrapped, once standalone), not two different versions.

**`tri_ph6_cram_ORGANIZED.zip`** (SHA-256 `65dbe824...21a6f3442`,
8,458,815 bytes, 85 members) — by far the largest and most historically
dense package: dozens of PDFs under `01_Reference_Docs/` (multiple
numbered/duplicate-suffixed variants of "PH6 CRAM Master Documentation
Package," "PH6-CRAM-PSEUDO Universal Build Doctrine," canon v0.1.0/v2.1
packets, a "PH6 Time Machine" doc), markdown doctrine
(`CANONICAL_DOCTRINE.md`, `SEVEN_IRON_LAWS.md`, `VOCABULARY_LOCKED.md`,
`HARDWARE_ROLES.md`, `LANE_MODEL.md`, `STORAGE_TOPOLOGY.md`,
`UNIVERSE_FREEZE_PROCEDURE.md`), Word docs, and — **not extracted, listed
by path only** — six more nested archives under `04_Archives/`:
`PH6_CANON_v0.1.0_bundle.zip`, `PH6_CRAM_DOCUMENT_PACKAGE.zip`,
`ph6_cert_final.tar.gz` (+ a `-1.zip` variant), `ph6_cert_suite_v2.tar.gz`,
`ph6_certification_suite.tar.gz`, `ph6_complete_with_config.tar.gz` (+ a
`courtroom_v1` variant and its own `-4` suffix). This is the deepest,
oldest-looking layer of the whole corpus — filenames alone (`(1)`, `(2)`,
`(3)` suffixes; "Combine February 20, 2026"; a screenshot;
`ORGANIZATION_REPORT.md`) suggest an already-deduplicated archival effort
by the operator predating this reconciliation work, not raw unsorted
material. **This is the single most likely place for a genuinely
superseded or historical-only implementation to be hiding, and the least
practical to hand-inventory further without extraction** — flagged
explicitly as the top candidate for a controlled, separately-authorized
byte-level pass, not attempted here.

**`corpus contains a much stronger PH6 constitutional, implementation,
boundary, to.txt`** (SHA-256 `bd1ecabb...c368d4e`, 32,015 bytes, plain
text, not an archive) — the filename itself reads as a truncated sentence
fragment, not a normal artifact name. This is flagged as a **naming
anomaly**, not treated as meaningful. Content unread (plain text, but
still staged-corpus-only, no byte access this session).

### 7.3 Overlaps and contradictions identified (not resolved)

- Four separate "staged, never landed" implementation-adjacent packages
  now confirmed: BCV2, NERO, `PH6-SoSo-Agent-Reasoning-Core-v0.1`, and
  `PH6_SOSO_SYSTEM_scaffold`. This is a pattern, not a coincidence, but
  *why* four independent SoSo-adjacent efforts exist unlanded is not
  something this session can determine from paths alone.
- Two internally self-documenting packages
  (`PH6_SOSO_SOURCE_DOCUMENT_SET`, `PH6_SOSO_SYSTEM_scaffold`) each carry
  their *own* supersession/deprecation registries. These registries were
  not read this pass. They may already contain authoritative answers to
  some of this reconciliation's open questions — reading them is
  identified as the highest-value next step, not performed here.
- `MIT`/`PIT`/`SIT` token types exist only in one staged package, absent
  from the repository and from every other staged package inspected.
- Confirmed exact duplicate: `tri_ph6_cram_ORGANIZED.zip` is staged twice
  (nested + standalone), byte-identical.
- Confirmed exact near-duplicate: `PH6_SOURCE_SCAFFOLD_DRAFT_HANDOFF`
  v1/v2 differ in exactly one file.
- `PH6_CANON_STACK_v4.0`'s "Book II — Scientific Instrument Master" may
  relate to the SEI doctrine already on `main` (§7.1) — unconfirmed.

### 7.4 What this addendum still does not do

- Does not extract any nested archive (7 further nested archives now
  identified: 1 inside `PH6_STORAGE_LIBRARY_SOURCE_PACKAGE_SCAFFOLD`, 6+
  inside `tri_ph6_cram_ORGANIZED`).
- Does not read any package's internal registry, doctrine, or schema
  content beyond file/path names already present in the index.
- Does not modify `main` or PR #17.
- Does not reopen HRG9.
- Does not build the reconciliation matrix — all 13 staged packages are
  now inventoried at the index level (13/13), which is the checkpoint the
  operator asked to reach before that next step.

```json
{"proposed_by":"claude-code-lane2","proposed_at_utc":"2026-09-15T12:05:46Z","api_call_log_ref":"ph6-reconciliation-pass-001-session-addendum-2","ratified_by":null}
```

---

## 8. Addendum 3 (same session) — Provenance investigation: BLOCKED on missing input

The operator authorized the next phase: a content-level provenance/
supersession investigation, starting with `PH6_SOSO_SOURCE_DOCUMENT_SET`'s
own index/manifest and its four registry documents (`DOCUMENT_044`
historical-artifact, `045` superseded-document, `046` deprecated-document,
`047` source-material-lineage-map), to determine whether they establish
real relationships among BCV2, NERO, the two other SoSo-adjacent staged
implementations, the Evidence Kernel candidates, and other inventoried
artifacts.

**This session cannot perform that investigation.** Verified this pass:
the only files ever uploaded to this session are
`PH6-SOURCE-MANIFEST-001-CLAUDE-CODE-HANDOFF.zip` and
`PH6-SOURCE-MANIFEST-001-UPDATE-PATCH-v0.2.1.zip` (each re-uploaded once,
byte-identical both times — 4 files total, 2 distinct). Neither contains
`PH6_SOSO_SOURCE_DOCUMENT_SET.zip` or any of the other 12 staged packages.
Everything reported about all 13 packages in §3–7 of this document — every
member path, every hash, every size — comes from `initial.json`
(path + hash + size index only). **No file inside any of the 13 staged
packages has ever been opened by this session.** That includes the
`manifest.json`, `DOCUMENT_INDEX.md`, and all four registry documents this
phase specifically needs to read.

Attempting the requested output sections (A–G) without those bytes would
require inventing plausible-sounding registry content — supersession
declarations, dates, version numbers — which is exactly the fabrication
this entire operation exists to prevent. That is not done here.

### 8.1 What can honestly be reported against the requested output sections

- **A. Provenance sources examined**: none — no source content was
  readable this pass.
- **B. Relationship findings**: none established. No new table rows.
- **C. Supersession/deprecation findings**: none established.
- **D. Evidence Kernel update**: **unchanged** — `IDENTITY_UNRESOLVED`
  stands for Candidates A/B/C, explicitly because no new evidence was
  available to examine, not because new evidence was weighed and found
  insufficient.
- **E. SoSo implementation lineage**: **unchanged** — BCV2, NERO,
  `PH6-SoSo-Agent-Reasoning-Core-v0.1`, and `PH6_SOSO_SYSTEM_scaffold`
  remain four independent, unrelated-by-evidence staged artifacts.
- **F. Unresolved identity questions**: all questions from §6/§7 of this
  document remain open, plus one new one: whether
  `PH6_SOSO_SOURCE_DOCUMENT_SET`'s registries actually resolve any of them
  — genuinely unknown, since they haven't been read.
- **G. Extraction candidates**: none identified — establishing a candidate
  requires reading the registries first, which requires the missing input.

### 8.2 What would unblock this

`PH6_SOSO_SOURCE_DOCUMENT_SET.zip` uploaded to this session (or the
operator's broader `/mnt/data` staged corpus, if the other 12 packages are
also meant to be readable at content level going forward). Once supplied,
this phase can run exactly as specified: index/manifest first, only the
four registry documents next, no further extraction without a specifically
identified, reported reason.

```json
{"proposed_by":"claude-code-lane2","proposed_at_utc":"2026-09-15T12:09:44Z","api_call_log_ref":"ph6-reconciliation-pass-001-session-addendum-3-blocked","ratified_by":null}
```
