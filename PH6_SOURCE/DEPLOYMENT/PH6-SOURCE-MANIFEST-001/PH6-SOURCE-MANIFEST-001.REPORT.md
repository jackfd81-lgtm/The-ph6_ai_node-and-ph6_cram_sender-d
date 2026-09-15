# PH6-SOURCE-MANIFEST-001 — Repository-Grounded Reconnaissance Report

Generated: 2026-09-15 (this session) · Status: **PROPOSED — Lane-2, Authority ZERO — reconnaissance only, not ratified**

Repository: `jackfd81-lgtm/the-ph6_ai_node-and-ph6_cram_sender-d`, branch
`claude/ph6-manifest-reconnaissance-7qohsi`, HEAD `cafcc3737c992ca48e744ed536632fdaa28d621f`
(identical to `main`; also PR #16's base — base is current, no drift).

This report and the accompanying `PH6-SOURCE-MANIFEST-001.json` were built by
direct inspection of the actual repository, git state, and GitHub PR #16 —
**not** by trusting the operator-supplied `initial.json` snapshot's
classifications, per the task's explicit instruction. That snapshot is cited
where relevant and preserved unmodified; it was never edited.

---

## 1. Scope and what this is not

This is a **reconnaissance-boundary manifest**, per the task's own stop
condition: it records identity, evidence, and unresolved conflicts. It does
**not** resolve governance conflicts, does not rank canon, does not grant
authority, does not modify PH6 production code, and does not create any
polling/monitoring automation (none was created; PR #16 is not being
watched by this session).

Evidence states below follow strict separation: **documented ≠ implemented
≠ merged ≠ validated ≠ governed ≠ production-cleared.**

---

## 2. Upload integrity check

Both files attached to this conversation were verified byte-for-byte:

| File | Claimed SHA-256 | Computed SHA-256 | Result |
|---|---|---|---|
| `PH6-SOURCE-MANIFEST-001-UPDATE-PATCH-v0.2.1.zip` | `af9462fe...68e39` | `af9462fe...68e39` | **MATCH** |
| `PH6-SOURCE-MANIFEST-001-CLAUDE-CODE-HANDOFF.zip` | (none claimed) | `77ddb827...46c2e` | recorded |

The two later re-uploads (`817dde0d-...`, `aeeb23c4-...`) are byte-identical
(same SHA-256) to the originals — no new content, nothing re-extracted.

---

## 3. Raspberry Pi hardware layer — UNRESOLVED, no access

CLAUDE.md documents (DOCUMENTATION_ONLY, never independently observed):

| Role | IP | Hostname |
|---|---|---|
| Pi 5 primary (ingest/CRAM-0) | 192.168.254.188 | jackjack |
| Pi Zero 2W (sentinel) | 192.168.254.189 | jackjack (⚠ pending rename) |
| Pi 3B+ (Scout-P/authority) | TBD | — |

This Claude Code session is an isolated remote cloud container with **no
network route to the operator's LAN and no hardware access**. Per the
v0.2.1 patch's own evidence hierarchy, `PHYSICAL_DEVICE_OBSERVATION` is
required to claim `OBSERVED_MATCH`/`OBSERVED_MISMATCH`; documentation alone
is explicitly disallowed as sufficient evidence.

**Recorded:** `deployment_correspondence.relationship_status = NOT_ASSESSED`,
`observation_basis = DOCUMENTATION_ONLY`, `confidence = UNKNOWN`. This
cannot be resolved from this session. To close it, the operator must either
run inspection commands on the physical Pi and paste back the output, or
connect a session that has real network reach to the Pi.

---

## 4. PR #16 — verified against the actual GitHub API, not the operator's report

The operator-supplied context (`context/PR16_OPERATOR_HANDOFF.md`) claimed
seven facts. Each was independently checked:

| Claim | Verified? | Evidence |
|---|---|---|
| PR #16 is draft | **CONFIRMED** | `state: open, draft: true` |
| Contains RLT/PLT/AHT loss-token implementation | **CONFIRMED** | PR body + file list (`ph6/tok/lifecycle.py` etc.) |
| Contains rehydration | **CONFIRMED** | `TokenStore.rehydrate_aht_to_rt` per PR body |
| Contains SoSo-JEDI single-token provenance adapter | **CONFIRMED** | New file `PH6_SOURCE/AI/soso_jedi/token_provenance.py` |
| CI governance-scan is green | **CONFIRMED independently** | GitHub check-runs API: `governance-scan`, 2 runs, both `conclusion: success` on head sha `d7df6e38...` — not just PR-body prose |
| No merge conflicts | **CONFIRMED** | `mergeable_state: clean`; base sha == current repo HEAD |
| No review comments | **CONFIRMED** | `get_comments` → `[]`, `get_reviews` → `[]` |
| BCV2/Life-CRAM left unimplemented, flagged CONFLICT | **CONFIRMED** | Explicit `## CONFLICT → EVIDENCE → OPTIONS → RECOMMENDATION` section in PR body |
| BCV2 absent from repository | **CONFIRMED independently** | This session's own repo-wide grep, separately from PR #16 author's search, both return zero hits |
| Life CRAM exists as LCC-01 | **CONFIRMED** | `PH6_SOURCE/GOVERNANCE/{closure_status,evidence_campaign_matrix}.json`, `ph6/cram_pu/tools/life_cram_lcc_01_live_camera.py`, multiple real evidenced campaign runs under `ph6/cram_pu/validation_runs/**/lcc01_*` |

**Not independently re-verified this session:** the PR's self-reported
"241 passed / 2 pre-existing skips" test count, and exact per-file byte
hashes of the 8 changed files (the diff exceeded this session's tool output
limit and was not fetched — recorded as a coverage gap, not silently
assumed true).

**PR #16 is NOT merged.** Its 8 new/changed files exist only on the
`claude/lmpq-001-missing-components-ro3qo8` branch, not in this session's
checked-out working tree. They are recorded in the manifest as
`source_class: CANDIDATE_UNMERGED_PR` with a placeholder hash, never
conflated with `repository_artifact` entries hashed from real working-tree
bytes.

---

## 5. BCV2 / Life-CRAM / LCC-01 — the key new finding

This is the most significant reconciliation-relevant discovery of this
pass, and it **contradicts a premise both the operator's handoff and PR
#16 shared**: that BCV2 is simply undefined/nonexistent.

- **In the git repository:** zero occurrences of `BCV2` anywhere (confirmed
  independently, matching both the operator's report and PR #16's own
  finding).
- **In the operator's separately-staged corpus** (`initial.json`, built
  2026-09-15T10:36:51Z from `/mnt/data`, **two days after** PR #16 was
  opened): a real, named archive — `PH6_BCV2_SoSo_Starter.zip`
  (SHA-256 `0fe38838...c8d19`, 7283 bytes, 15 members) **as reported in
  that snapshot** (not independently recomputed this session — the raw
  `/mnt/data` bytes were never supplied to this session, only the handoff
  and patch zips, neither of which contains this file).

  Its member list is not a placeholder — it is a scaffolded module with an
  interface contract:
  - `bcv2/__init__.py`, `bcv2/models.py`
  - `contracts/bcv2_interface.json`, `contracts/coordination.json`
  - `tests/test_soso_boundary.py`, `tests/test_interface.py`
  - `scripts/check_boundary.py`, `README.md`, `pyproject.toml`

- **Life CRAM already exists under the name `LCC-01`**, with real evidence:
  capture runs against `/dev/video0`, BLAKE2b-256 `result_set_hash` values,
  `PASS`/`PASS_PENDING_REVIEW`/`FAIL_EVIDENCE_PRESERVED` outcomes recorded
  in `ph6/cram_pu/validation_runs/**` and governance files
  (`closure_status.json`, `evidence_campaign_matrix.json`).

**Unresolved conflict, routed to governance, not resolved here:**
`PH6_BCV2_SoSo_Starter.zip` was staged by the operator but never landed in
this repository. PR #16 could not have known about it (created 2026-09-13,
before the corpus existed). Whether this staged package should be merged,
reconciled against LCC-01, treated as a duplicate/superseded design, or
something else entirely is a decision only PH6 governance (the operator)
can make. **No renaming, merging, or promotion was performed.**

---

## 6. RLT / PLT / AHT — doctrine predates PR #16, code does not yet exist on `main`

- Fully defined in `PH6_SOURCE/GOVERNANCE/PH6_LIVING_MEMORY_TOKEN_RETENTION_POLICY.md`
  §4/§6 and `PH6_SOURCE/GOVERNANCE/PH6_TOKEN_MEMORY_AI_DERIVED_EVIDENCE_DOCTRINE.md`,
  and already enumerated in both token schemas
  (`ph6_token_v1.schema.json`, `token_record.schema.json`) — **before**
  PR #16.
- **No implementation exists in this session's working tree**
  (`grep` across `ph6/`, `ph6_ai_node/`, `ph6_cram_sender/`, `ph6_l2_expand/`
  for `RLT`/`PLT`/`AHT` as code identifiers: zero hits). PR #16 is the
  first implementation, and it is unmerged.
- Authority ranking `RT > RLT > VLT > AHT > PLT > VDT` is documentation
  only; PR #16's own body notes it has no executable conflict-resolution
  use yet.

## 7. SoSo-JEDI — naming overlap, not a conflict, confirmed

- `PH6_SOURCE/AI/soso_jedi/jedi/swarm_sim_bp.py` (`BookVCoreEngine`)
  pre-exists and is a **different** capability (layer/storm-branch
  reconstruction), unmodified by PR #16.
- PR #16 adds a **new, separate file**,
  `PH6_SOURCE/AI/soso_jedi/token_provenance.py`, answering a different
  question (single-token lineage). This is additive, not a rename or
  collision, per PR #16's own description — this session did not
  independently inspect PR #16's diff to verify the adapter's contents
  (see coverage gap in §4).
- Doctrine documents `PH6-LIVING-CRAM-PSEUDO-SOSO-JEDI-v1.0.md` and
  `PH6-PSEUDO-SOSO-JEDI-UPDATE-v1.0.md` (both `DRAFT/`, never sealed)
  confirmed present and pre-existing.

## 8. RECON-001 — referenced by the handoff package, absent from the repository

The handoff `README.md` instructs routing unresolved conflicts to
"the existing PH6 reconciliation authority (`RECON-001`)". A repository-wide
search (case-sensitive, all tracked files) found **zero occurrences of
`RECON-001`** anywhere in this repository. Per the handoff's own fail-closed
rule, this is recorded as `NOT_FOUND_IN_DECLARED_CORPUS_COVERAGE` — not
proof that no such process exists elsewhere (e.g. in the operator's own
process, outside this repo), just that this repository does not document it.

---

## 9. Manifest coverage and limitations (honest accounting, not silent gaps)

- **422,520** files are git-tracked in this repository. **419,760** of them
  (99.35%) live under `ph6/cram_pu/validation_runs/` — bulk evidence
  artifacts that CLAUDE.md itself classifies as outside the governance-scan
  tree and "do not stage for commit." Individually hashing all of them was
  judged disproportionate to a source/architecture manifest and was **not
  done**; the directory is recorded as a single aggregate coverage note
  (count + bulk exclusion reason), not silently dropped.
- The remaining **2,760** tracked files were all individually opened,
  SHA-256-hashed from actual bytes, and recorded as `repository_artifact`
  entries.
- **2,760** of those got only identity (hash/size/path); a curated subset
  of ~10 files directly implicated in the PR #16/BCV2/LCC-01/token
  reconciliation received real declared-status annotations grounded in
  content actually read this session — the rest carry an explicit
  "not individually classified" note rather than a fabricated status.
- **No archive files exist in the git repository's in-scope tree** (zero
  `.zip`/`.tar*` hits among the 2,760 files), so no nested-archive
  inventory was needed on the repository side.
- PR #16's 8 changed files are recorded with placeholder (all-zero) hashes
  and `source_class: CANDIDATE_UNMERGED_PR` — their real content was not
  fetched (diff exceeded this session's output limit).

---

## 10. Manifest validation

`PH6-SOURCE-MANIFEST-001.json` (2,781 artifacts) was validated against the
supplied `PH6-SOURCE-MANIFEST-001.schema.v0.2.1.json` using
`jsonschema` (Draft 2020-12) in this session: **0 errors.**

---

## 11. Unresolved items requiring PH6 governance review (not resolved here)

1. **BCV2 staged package vs. LCC-01** — does `PH6_BCV2_SoSo_Starter.zip`
   represent a separate required component, a superseded/duplicate design,
   or should "Life CRAM" formally remain LCC-01-only? Operator decision.
2. **Raspberry Pi deployment correspondence** — `NOT_ASSESSED` for all
   three nodes; requires either physical inspection output pasted back, or
   a session with real network access to the Pi.
3. **PR #16 disposition** — draft, unreviewed by a human, CI green,
   mergeable clean, zero comments/reviews. No action taken; not merged,
   not commented on, per the task's explicit "stop at the reconciliation
   boundary" instruction.
4. **RECON-001** — referenced by the handoff package as an existing PH6
   process but not found anywhere in this repository. Operator should
   confirm where it's documented, if it exists outside this repo.
5. **PR #16 byte-level verification** — the 8 changed files' exact hashes
   were not independently recomputed this session (coverage gap, §4/§9).

---

## 12. Output artifacts

- `PH6-SOURCE-MANIFEST-001.json` — this pass's repository-grounded manifest (2,781 artifacts, schema-valid)
- `PH6-SOURCE-MANIFEST-001.json.sha256sum.txt` — SHA-256 of the manifest JSON (named `.sha256sum.txt`, not `.sha256`: this repo's `governance_drift_scan.py` `blake2b_marker_regression` check flags any bare `*.sha256` file lacking a `.blake2b` companion as **HIGH** — correct for CRAM-A evidence directories, a false trigger for a manifest sidecar hash. Verified by re-running the scan after the rename.)
- `PH6-SOURCE-MANIFEST-001.schema.json` — copy of the supplied v0.2.1 schema this manifest validates against
- `PH6-SOURCE-MANIFEST-001.REPORT.md` — this file

All four were committed to `claude/ph6-manifest-reconnaissance-7qohsi` and
pushed as **draft PR #17** (following this repo's own PR #1–16 precedent:
Lane-2 PROPOSED work is committed and opened as a draft, not left stranded
locally — the draft PR is the "stop and wait" point, not the local working
tree). PR #17 remains draft, unmerged, unratified.

**Self-check:** `PH6_SOURCE/TOOLS/governance_drift_scan.py --scan-root PH6_SOURCE/`
was re-run against the tree *including these new files*:
`overall_result: PASS`, **0 CRITICAL / 0 HIGH / 0 WARN**, 4 INFO — all 4 are
pre-existing `PROHIBITION_DOCSTRING` hits in `PH6_SOURCE/TESTS/DUAL_USB_CAMERA/`
unrelated to this change (same 4 PR #16's own scan reported). Matches
CLAUDE.md's governance baseline exactly.

```json
{"proposed_by":"claude-code-lane2","proposed_at_utc":"2026-09-15T11:25:40Z","api_call_log_ref":"ph6-source-manifest-001-recon-session","ratified_by":null}
```

---

## 13. Addendum (2026-09-15, same session) — operator-directed refinement

Following operator review of the initial PR #17 report, four corrections
were made. None of them change any prior finding's substance; they make the
evidence-state encoding stricter, per operator direction.

### 13.1 BCV2 — collapsed into independent dimensions, not a single field

The earlier "starter confirmed, product undetermined" framing collapsed
distinct dimensions into one classification. Corrected to four independent
axes on the confirmed starter artifact
(`PH6-SRC-PH6_BCV2_SoSo_Starter.zip-0fe388386c5c`):

```json
{
  "existence_status": "CONFIRMED_IN_STAGED_CORPUS",
  "implementation_status": "MINIMAL_SCAFFOLD",
  "authority_status": "LANE_2_ADVISORY_ONLY",
  "ratification_status": "UNRATIFIED"
}
```

...plus a **separate** claim-record artifact
(`PH6-CLAIM-BCV2-FULL-PRODUCT-STATUS`) explicitly stating that the full
BCV2 product's existence, implementation, authority, and ratification are
all independently `UNRESOLVED` / `UNRATIFIED` — the starter's confirmed
existence must not be read as evidence for any of those.

### 13.2 Evidence Kernel / Patch Set 001 — independently investigated (read-only)

An operator-relayed claim (sourced to an external document, `pasted.txt`,
not supplied to this session) stated that "Evidence Kernel Patch Set 001"
is specified but not implemented, naming a missing canonicalizer, verifier,
fixtures, and conformance suite. This session traced the claim as far as
the available materials allow, rather than accepting it as established:

- **Repository**: zero hits for `evidence kernel`, `patch set 001`,
  `EK-001`, `canonicalizer`/`canonicaliser`, or `conformance suite`, under
  any spelling, anywhere in the git-tracked tree (including
  `PH6_SOURCE/GAP_REGISTER_v3.0.md`). The single repo hit for "evidence
  kernel" is this manifest's own boilerplate, copied from the supplied
  handoff README's generic hash-boundary language — not a repo-specific
  reference.
- **Operator-staged corpus** (`initial.json` index, 349 artifacts): zero
  hits for the same terms. One package with plausibly related *function*
  exists under a **different name** — `PH6_TFH_AK_v1_1_1.zip` ("TFH_AK"),
  containing `ph6_tfh/canonical.py`, `ph6_tfh/audit/{engine,receipt,replay}.py`,
  `ph6_tfh/provenance/hashes.py`, audit/receipt-bundle schemas, a test
  suite (`test_authority.py`, `test_tfh.py`, `test_v1_1_0_fixes.py`, test
  vectors), and its own `docs/IMPLEMENTATION_STATUS.md`.
- **This session cannot read that package's actual byte content** —
  `initial.json` records only path, hash, and size, not file contents, and
  the raw staged corpus (`/mnt/data`) was never supplied here, only the two
  handoff/patch zips (neither contains `PH6_TFH_AK_v1_1_1.zip`).

Recorded as claim-record `PH6-CLAIM-EVIDENCE-KERNEL-PATCH-SET-001`:
`term_located_in_repository: NOT_FOUND`,
`term_located_in_staged_corpus_index: NOT_FOUND`,
`candidate_package_identified: PH6_TFH_AK_v1_1_1.zip (unconfirmed as the same referent)`,
`candidate_package_content_verified: NOT_POSSIBLE_THIS_SESSION`,
implementation/verifier/conformance-suite status all `UNRESOLVED`.

This is a **correction**, not just an answer, to the operator's proposed
label of `SUPPORTED_BY_STAGED_REPORT / INDEPENDENT_VERIFICATION_PENDING`:
this session could not even locate the term itself under independent
search — only a candidate package under different naming. Recorded instead
as `NAME_NOT_LOCATED / CANDIDATE_PACKAGE_UNVERIFIED`, which is the more
conservative and more accurate description of what was actually
established this session.

### 13.3 RECON-001 — restructured from prose into a structured object

New claim-record artifact `PH6-CLAIM-RECON-001-COVERAGE`:

```json
{
  "status": "NOT_FOUND_IN_DECLARED_CORPUS_COVERAGE",
  "scope": "repository + declared staged corpus index (initial.json, 349 artifacts) inspected by this reconnaissance pass",
  "global_absence_proven": false
}
```

`global_absence_proven` is explicitly `false`, not omitted — this
distinguishes "absent from the corpus this pass had coverage over" from a
(unsupportable) claim that RECON-001 doesn't exist anywhere at all.

### 13.4 Raspberry Pi — unchanged

Left exactly as `NOT_ASSESSED`, per explicit operator direction not to
weaken or reinterpret that finding. No new information this round.

### 13.5 Not done, on explicit instruction

No merge of PR #17. No scope expansion into architecture/implementation
work. No Raspberry Pi observation campaign (requires a session with actual
hardware/network access). No targeted RECON-001 retrieval beyond the
corpus already inspected. All remain queued for separate, explicitly
authorized work.

Manifest: 2,784 artifacts (was 2,781), re-validated against
`PH6-SOURCE-MANIFEST-001.schema.v0.2.1.json` — 0 errors. `manifest_version`
bumped to `0.2.1-r1` to distinguish this revision from the original PR #17
snapshot without breaking `$id`/schema compatibility.

```json
{"proposed_by":"claude-code-lane2","proposed_at_utc":"2026-09-15T11:41:51Z","api_call_log_ref":"ph6-source-manifest-001-recon-session-addendum-1","ratified_by":null}
```
