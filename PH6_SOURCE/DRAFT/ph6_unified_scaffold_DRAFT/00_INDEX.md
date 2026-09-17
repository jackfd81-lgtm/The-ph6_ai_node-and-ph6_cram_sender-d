Document Type: Unified Scaffold Index
Status: DRAFT — NOT RATIFIED
Version: 0.1
Authority: Lane 2 advisory/build output only
Ratification: NONE

# PH6 Unified Scaffold — Consolidation Report (DRAFT)

This folder is a corrected version of a consolidation roadmap you were shown
by another source. That roadmap contained a fabricated tool reference and
several undisclosed renames/omissions (full list in chat). This version:
fixes what could be fixed with evidence, and flags — rather than guesses at —
what couldn't.

**This is a proposed reorganization. Reorganizing folders is itself a Lane 1
decision; nothing here is ratified by virtue of existing.**

---

## What changed, and evidence for each claim

### Fixed for real (verified by running the tools, not just editing them)

1. **`05_TOOLS/verify_manifest.py`** — path-remapped for the new layout via
   an explicit `PATH_MAP` (old logical names preserved, physical location
   updated). Re-ran it against every moved file:
   `MANIFEST_VALID (SHA-256, paths remapped for unified layout)`, exit 0.
2. **`05_TOOLS/verify_vectors.py`** — same path fix. Re-ran it:
   6/6 golden vectors PASS, `REPLAY_VALIDATION_PASS`, exit 0.
3. **`.github/workflows/policy-gates.yml`** — the old "Fail closed" step was
   a no-op (`echo` + unconditional `exit 0`, never called either verifier).
   This version actually runs `verify_manifest.py` and `verify_vectors.py`.
   `replay-validation.yml` already did this correctly; only `policy-gates.yml`
   needed the fix.
4. **`05_TOOLS/verify_manifest_blake2b.py`** — NEW, additive. Generates
   `03_VERIFICATION_AND_TESTS/blake2b256_manifest_v1.0.json` alongside
   (not replacing) the SHA-256 one. Ran it; output hashes are in that file.
5. **Book V (`BOOK V — EXPERIMENTAL SWARM ANNEX.pdf`) and
   `ph6_consolidation_manifest_v2.json`** — both silently dropped by the
   roadmap you were shown — are present in `01_DOCTRINE_AND_SPEC/`.
6. **All original filenames preserved exactly** — no version-suffix
   stripping, no underscore-renaming of the Book PDFs. The prior roadmap
   proposed both; this scaffold does not, per the "preserve labels exactly"
   rule already stated in `02_CONTROL_PLANE/PH6_AUTHORITY_MODEL_V0.1.md`.
7. **Obsolete Book 0 variant** moved to `99_ARCHIVE/SUPERSEDED_BOOK0/`,
   filename unchanged, with a `NOTICE.md` documenting the size/page/text
   comparison that justifies the flag (23 vs 136 extracted lines — see
   that file for the full table).
8. **`__pycache__`/`.pyc` purged** from the `brain_computer_v2` subsystem
   copy — only source files carried over.

### Explicitly NOT fixed — flagged instead of guessed

0. **RESOLVED BY LANE 1, see `02_CONTROL_PLANE/DECISION_RECORD_2026-09-03.md`**:
   folder renames (`01_CANON_STACK`, `06_AUDIT_LOGS`) — DEFER; `fp()`
   parameters (`FP_SCALE=10,000`, `ROUND_HALF_EVEN`) — PROPOSED only, DO NOT
   IMPLEMENT AS CANONICAL; `JEDI`/`TFH-AK`/`CAM`/`NERO` — NOT PROMOTED.
1. **`verify_vectors.py` still uses raw Python floats**, not `fp()` /
   `ph6.canonjson.v1` — per the decision record above, this stays as-is;
   floats-with-disclosure are the current direction, not a rewrite.
2. **Which hash is actually canonical (SHA-256 vs BLAKE2b-256) is undecided.**
   Both manifests now exist. CI still runs the SHA-256 one. Say which one
   governs and I'll update CI and (if you want) formally supersede the other.
   (Note: `PH6_CONSOLIDATED_CANON.docx` §II.14 states BLAKE2b-256 primary /
   SHA-256 compatibility-only — see item 5 below.)
3. **The old `Six engines pH 6/` Book I/II/III/IV siblings** (same drift
   pattern as the archived Book 0) still live in `PH6_SOURCE_SORTED`,
   untouched — I only pulled the `01_CORE_DOCTRINE`/`02_GOVERNANCE` **v4.0**
   copies into this scaffold. If you want those older siblings formally
   archived too, that's a separate, explicit gate — I didn't do it
   unasked.
5. **UNRESOLVED — RECONCILIATION REQUIRED: `PH6_CONSOLIDATED_CANON.docx`
   vs. this scaffold's active tooling.** Full detail in
   `06_AUDIT_AND_LOGS/UNRESOLVED_canon_vs_scaffold_20260903.md`. Short
   version: that document's locked gate thresholds/logic, golden vector
   suite, and referenced implementation package (`ph6_six_engine_pack`)
   all differ from what's actually in `03_VERIFICATION_AND_TESTS`/`05_TOOLS`
   — reads like a different generation of the measurement subsystem, not
   a typo. Neither side was edited to match the other; Jack's explicit
   call was to record this and decide later.
6. **`md_to_docx.py`** (fabricated in the prior roadmap) is not included.
   `PH6_MASTER_v4.0.docx` and `.pdf` are carried over as originally
   documented in the Canon Stack's own `00_INDEX..md` — editable source +
   readable export — no conversion tool needed unless you want one built
   for real.

---

## Gate sequencing (current)
See `02_CONTROL_PLANE/GATE_LOG_2026-09-03.md`: current gate is
Lineage/Reconciliation (8 evidence-retrieval questions drafted, answers
pending). Gate 003 — Numerical Determinism Contract — is queued behind
it, not started, and explicitly kept separate from lineage findings per
Jack's direction. Gate 004 — Pi Filesystem/Runtime Reconciliation — is a
separate, live-hardware-evidence thread (status PROPOSED / RATIFICATION
OPEN), recorded from Jack's account only; I have not independently
inspected its underlying transcript/report.

---

## Folder map

```
01_DOCTRINE_AND_SPEC/   Books 0–V, PH6_MASTER_v4.0 (.docx+.pdf), consolidation manifest, original index
02_CONTROL_PLANE/       PH6_SOURCE scaffold governance docs (doctrine, authority, gate protocol, etc.) + GOVERNANCE.md
03_VERIFICATION_AND_TESTS/  constants (.json+.bin), golden vectors, both hash manifests
04_SUBSYSTEMS/brain_computer_v2/  real files only, no build cache
05_TOOLS/               verify_manifest.py, verify_vectors.py, verify_manifest_blake2b.py (all re-tested)
06_AUDIT_AND_LOGS/      violations log, cert protocol, reproducibility template, regenerated replay log
.github/workflows/      policy-gates.yml (fixed), replay-validation.yml (path-updated)
99_ARCHIVE/SUPERSEDED_BOOK0/  old Book 0 variant + comparison notice
```

**End of index. This scaffold remains DRAFT — NOT RATIFIED.**
