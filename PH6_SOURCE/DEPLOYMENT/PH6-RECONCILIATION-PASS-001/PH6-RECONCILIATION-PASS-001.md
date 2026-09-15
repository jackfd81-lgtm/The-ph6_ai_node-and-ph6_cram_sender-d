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
