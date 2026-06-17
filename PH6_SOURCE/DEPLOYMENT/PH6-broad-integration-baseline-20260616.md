# PH6 Broad Integration Baseline — 2026-06-16

timestamp_utc: 2026-06-16T23:10:00Z
authority: ZERO
classification: BROAD_INTEGRATION_BASELINE_20260616_PENDING_AUDIT
verification_worktree: /home/jack/PH6_MAIN_VERIFY_20260616

## Origin/Main State

| Field | Value |
|-------|-------|
| Commit | `7b5e0434eea83bfeba3bc3092c45e96e8c4f3c35` |
| Subject | Merge pull request #3 from jackfd81-lgtm/ph6/er1a-mram-soso-tokens-pr-20260616T213958Z |
| Date | 2026-06-16T18:03:19-0500 |
| PR #4 (clean ER-1) merge commit | `c8122ee9edd74498159f611f9d85602ce549aa9d` |
| PR #3 (broad integration) merge commit | `7b5e0434eea83bfeba3bc3092c45e96e8c4f3c35` |

## Merge Sequence

1. **PR #4** merged at 23:00:52Z — 2 commits, 4 files, +1101/-0 (clean ER-1A/ER-1B scope)
2. **PR #3** merged at 23:03:19Z — 13 commits, 202 files, +24463/-36 (broad integration)

PR #3 is the current tip of main. PR #4's clean ER-1 commits are subsumed within the PR #3 merge.

## Operator Decision

**DO NOT REVERT PR #3.**

Reason: PR #3 contained required infrastructure that ER-1A/ER-1B depends on:
- `CLAUDE.md` — governance anchor file loaded automatically by Claude Code
- Full `ph6_l2_expand` package (`__init__.py`, `schemas.py`, `token_types.py`, `topology_mapper.py`, etc.)
- `PH6_SOURCE/GOVERNANCE/` — core doctrine documents
- `PH6_SOURCE/SCHEMAS/` — core schema files

A `git revert -m 1` of PR #3's merge commit was attempted and abandoned. It would have deleted all of the above, leaving ER-1 tests broken and CLAUDE.md absent from main.

## Critical File Verification (from origin/main @ 7b5e0434ee)

| File | Present | SHA256 |
|------|---------|--------|
| CLAUDE.md | YES | — |
| ph6/tok/lifecycle.py | YES | `0171ea0b98cb4bbab58d8e322a08f715abf1daa3227989296117e0a72b081e27` |
| ph6_l2_expand/topology_reconstruct.py | YES | `d5c40ebe9b144ede7c0ae1d1f896dbb1caa9cb91c7de6ccad4838911ee5324c0` |
| ph6_l2_expand/tests/test_er1a_proof.py | YES | `b0b21ed22f58d997f11617fefec0e9ef59948b6a7eb50d089a1e8220d97726f0` |
| ph6_l2_expand/tests/test_er1b_proof.py | YES | `bbcb61c082c3b4d94613ef4c905c0dd983c11002dc1d00b1179476fa2029ae44` |

## Test Results (verified from /home/jack/PH6_MAIN_VERIFY_20260616)

```
python -m pytest ph6_l2_expand/tests/test_er1a_proof.py ph6_l2_expand/tests/test_er1b_proof.py -v
  8/8   ER-1A proof tests: PASS
  9/9   ER-1B proof tests: PASS
  17/17 combined: PASS

python -m pytest ph6_l2_expand/tests/ -q
  63/63 PASS

python -m pytest ph6/tok/ -q
  12/12 PASS
```

## Classification

```
main: BROAD_INTEGRATION_BASELINE_20260616_PENDING_AUDIT
ER-1A: MERGED_TO_MAIN
ER-1B: MERGED_TO_MAIN
PR #3: ACCEPTED (contains required infrastructure — cannot be reverted cleanly)
PR #4: MERGED (clean ER-1 scope; commits subsumed by PR #3 merge)
ER-1C: SNAPSHOT CACHE DEFERRED
ER-1D-LITE: CLEARED TO BEGIN (post-merge tests all PASS)
```

## Governance Constraints Confirmed

- Lane 2 / Authority ZERO boundaries remain active
- No Lane-1 imports in ER-1 files
- No CRAM-A/CRAM-R writes from ER-1 path
- No PASS/DROP verdict fields in ER-1 code
- No mean_confidence emitted or used in ER-1B
- Any future cleanup must be surgical (file-by-file PR), not full PR revert
- Snapshot cache (ER-1C) remains deferred pending temporal policy decision

## Pending Audit

PR #3 carried 202 changed files from multiple integration areas:
- sei architecture
- SoSo JEDI runtime
- desktop Class 3 manager
- dual-camera fixes
- hardware hooks
- reflection schemas
- research agent
- desktop registry / camera threshold calibration

These have not been individually reviewed. A future audit PR may apply surgical removals
if specific files are found to violate governance boundaries.

## Worktree Cleanup Note

Temporary worktrees created during this session:
- `/home/jack/PH6_ER1_CLEAN` — clean cherry-pick worktree (source of PR #4)
- `/home/jack/PH6_MAIN_VERIFY_20260616` — this verification worktree (detached HEAD)

Both may be removed with `git worktree remove <path>` when no longer needed.

{"proposed_by":"claude-code-lane2","proposed_at_utc":"2026-06-16T23:10:00Z","api_call_log_ref":"session-20260616T224321Z","ratified_by":null}
