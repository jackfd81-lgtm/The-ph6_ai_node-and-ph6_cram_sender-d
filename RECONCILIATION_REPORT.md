# PH6 Constraints-Document Reconciliation Report

```
STATUS: PROPOSED
ACTION: Reconcile externally-supplied "PH6 CRAM SYSTEM DEVELOPMENT & GOVERNANCE
        CONSTRAINTS" document against actual repository state and CLAUDE.md
DETAIL: commit=cafcc3737c branch=main; facts re-verified 2026-09-11 (see re-check
        commands below); no production code touched
NEXT:   Operator decision on the one PROPOSED amendment below and on the two
        Implementation Gaps (secrets.py .gitignore entry; lint/typecheck adoption)
```

```json
{"proposed_by":"claude-code-lane2","proposed_at_utc":"2026-09-11T09:34:14Z","api_call_log_ref":"session_0177a3V4jQW8TmBDZscx3Hzs","ratified_by":null}
```

Governing principle applied throughout: **repository reality → verification →
documentation**, never the reverse. Nothing below treats the constraints
document's wording as evidence that its implementation exists.

---

## Repository Facts

Re-verified this session (commands: `git status --short`, `md5sum CLAUDE.md`,
`find . -maxdepth 1 -iname ".flake8"/"mypy.ini"/"ruff.toml"/".pylintrc"/"tox.ini"`,
`git ls-files | grep -i '\.env'`, `cat pytest.ini`, `git ls-files ph6/esp_s1/`,
`git check-ignore -v ph6/esp_s1/secrets.py`), consistent with the full audit in
`SYSTEM_AUDIT.md` (same session):

- **Test framework/discovery:** `pytest`, configured by top-level `pytest.ini`
  (`pythonpath = ph6/cram_pu`, `testpaths = ph6 ph6_l2_expand frame_filter`).
  345 tests exist across `ph6/ssmt/tests`, `ph6/tok/tests`,
  `ph6/research_agent/tests`, `ph6/hw_hooks/tests`, `ph6/reflection/tests`,
  `ph6/cram_pu/tests`, `ph6_l2_expand/tests`, `frame_filter/test_*.py`.
  `unittest discover` is not used anywhere in the tree.
- **Lint/typecheck configuration:** none exists. No `.flake8`, `ruff.toml`,
  `mypy.ini`, `.pylintrc`, or `tox.ini` anywhere under `/home/jack` (root
  search, repeated this session — still zero hits). `flake8`/`mypy` are not
  installed as part of this project's toolchain.
- **Secrets/configuration mechanism:** no `.env` file is tracked in git
  (`git ls-files | grep -i '\.env'` → empty) and no `.env.example` exists
  anywhere in the repo. The one real credential file in the tree is
  `ph6/esp_s1/secrets.py` (MicroPython, holds a live Wi-Fi SSID/password for
  the ESP32 sensor node) — it is **untracked** and **not covered by any
  `.gitignore` rule** (`git check-ignore -v` exits 1 / no match). This is a
  device-firmware credential, not an application secret, and the repo has no
  environment-variable-based secrets injection pattern anywhere.
- **Evidence/validation directories:** `ph6/cram_pu/validation_runs/` (419,760
  tracked files, raw frame payload binaries) and `frame_filter/frames_*`
  (100,661 files, mostly untracked) hold evidence data. `.git` is 4.1 GB,
  almost entirely from the former. CLAUDE.md's own File Placement table
  already states evidence should not be staged for commit — the current
  tracked state contradicts that existing rule (a pre-existing drift, not
  something introduced by this reconciliation).
- **Audit-record mechanisms:** real and dual-lane. Lane-1: `AuditChain` in
  `ph6/cram_pu/ph6_cram_sim.py` (BLAKE2b-256 hash-chained, GENESIS-rooted,
  verified live this session via `ph6_internal_test.py`'s
  `AUDIT_CHAIN_EVENTS`/`AUDIT_CHAIN_HASH_VERIFY`/`AUDIT_CHAIN_GENESIS`
  checks — all PASS). Lane-2: `ph6/ssmt/hash_chain.py` +
  `ph6/ssmt/audit_writer.py` reimplement the identical canonical-hash +
  atomic-write pattern for advisory data, hard-failing in `__init__` if the
  write root isn't under `/var/ph6/mram-s/swarms/`. No use of Python's
  stdlib `logging` module anywhere in the runtime tree.
- **PH6/CRAM implementation and governance files:** `ph6/cram_pu/` (Lane-1
  deterministic core — capture/gate/CRAM-store/replay), `ph6/governance/`
  (`ph6_governor.py`, `drift_gate.py`, `ph6_functional_validator.py`,
  `ph6_audit.py`), `ph6/ssmt` `ph6/tok` `ph6/research_agent` `ph6/hw_hooks`
  `ph6_l2_expand` (Lane-2, Authority ZERO, isolation enforced by 15+ passing
  tests plus structural `RuntimeError` guards — see `SYSTEM_AUDIT.md` §2.2).
- **CI/verification configuration:** `.github/workflows/governance_scan.yml`
  runs `PH6_SOURCE/TOOLS/ai_preflight_check.py` then
  `PH6_SOURCE/TOOLS/governance_drift_scan.py --scan-root PH6_SOURCE` on every
  push/PR. This is a **governance/doctrine gate**, not a unit-test gate — CI
  does not run `pytest` (or `unittest`) at all today. Re-ran both scripts
  this session: `ai_preflight_check.py` → PASS; `governance_drift_scan.py`
  → PASS, 0 CRITICAL/0 HIGH/0 WARN/27 INFO, matching the CLAUDE.md-documented
  baseline exactly.
- **Files referenced by the constraints document:** `.env` / `.env.example`
  — neither exists; `flake8` / `mypy` configs — neither exists;
  `unittest discover` target — no `unittest`-style test package exists
  (all test files are pytest-style, several import `pytest` fixtures
  directly, e.g. `ph6_l2_expand/tests/conftest.py`).

## Existing CLAUDE.md Rules (currently governing)

Already establishes, and is not contradicted by anything below: Lane-2
Authority ZERO / propose-not-ratify posture; PASS/DROP-only verdict tokens;
`motion_fraction`-only (no `motion_score`); BLAKE2b-256 as sole authority
hash; the 4-step atomic write contract; `.blake2b`-last-on-PASS /
`.blake2b`-forbidden-on-DROP; governance scan target = `PH6_SOURCE/` with an
expected 0/0/0/27 baseline; file-placement table (evidence under
`validation_runs/`, "do not stage for commit"); mandatory
`{"proposed_by":...,"ratified_by":null}` signature on proposed artifacts; a
mandatory `STATUS/ACTION/DETAIL/NEXT` response format. File is currently
**199 lines**, against its own stated **≤200 line** target — i.e., it is
already at its self-imposed budget.

## Constraints Document (as supplied)

Four sections: (1) agent operational behavior — think-first, complete
implementations, no untracked TODOs in `main`; (2) deterministic state/data
contracts — ingress validation with fail-fast, Authority ZERO isolation for
AI/probabilistic layers, `.env`-based secrets management; (3) definition of
done — static checks/linters "enforce zero syntax or typing errors", isolated
test execution "zero regression", logging must capture "failure boundaries
and state transitions"; (4) diagnostic commands — `python -m unittest
discover`, `flake8 .` / `mypy .`, "update evidence or audit manifests where
required."

## Conflicts

| # | Constraint | Conflict with repository / CLAUDE.md |
|---|---|---|
| C1 | Test command: `python -m unittest discover` | Repository uses `pytest` exclusively; no `unittest`-discoverable test package exists. Adopting this literally would require rewriting 345 existing pytest tests for no functional gain. |
| C2 | Lint/typecheck: `flake8 .` / `mypy .` | Neither tool is configured or present. Presenting this as a diagnostic command implies it already works — it does not; running it today would just report "command not found" or scan nothing meaningfully (no configs to bound scope). |
| C3 | Secrets via env vars; commit `.env.example`, never commit `.env` | No `.env` mechanism exists in this codebase's design. The one live credential (`ph6/esp_s1/secrets.py`) is a MicroPython device file, structurally incompatible with a "load from `os.environ`" pattern (it runs on the ESP32 itself, not in a process with an environment to inject into). Adopting this would mean inventing a secrets architecture that doesn't match how the actual secret is consumed. |

## Unresolved / Not-Fully-Verifiable Items

- **"Confirm logging captures failure boundaries and state transitions"**
  (constraints doc §3.3) — classified **UNSUPPORTED as literally worded**:
  the repository has no stdlib `logging` output to check against that
  phrasing. It *is* satisfied in spirit by the hash-chained `AuditChain` /
  `hash_chain.py` mechanisms (every verdict, gate decision, and CRAM
  transition is captured as a durable, tamper-evident structured event) —
  but calling that "logging" would misdescribe the mechanism. Documented as
  a **REDUNDANT-but-differently-implemented** item, not a gap.

## Classification of Every Substantive Constraint

| Constraint | Class | Basis |
|---|---|---|
| Think first / explain structural impact before edits | REDUNDANT | Already the operating norm this session and consistent with CLAUDE.md's PROPOSED-then-surface posture; not a CLAUDE.md line item but not in tension with one either. |
| Complete implementations, no placeholders in critical paths | VERIFIED | `py_compile` clean across all tracked source this session; no stub/placeholder patterns found in `ph6/cram_pu`, `ph6/ssmt`, `ph6/tok`, `ph6_l2_expand` (per `SYSTEM_AUDIT.md` §3.4). |
| No untracked TODOs in merged `main` code | VERIFIED | Only `TODO` occurrences in `ph6/**/*.py` are a `Status.TODO` enum label (planning checklist script) and the literal string inside a *detector* regex — not live debt (§3.4). |
| Ingress validation with explicit schemas, fail-fast on invalid input | VERIFIED | `ph6/cram_pu/schemas/cram_pu_packet.schema.json` (departure/arrival/verdict, all `additionalProperties:false`, `const`-locked discriminators), `ph6/ssmt/schemas/*`, `frame_filter/schemas/*`, `ph6_l2_expand/schemas.py` — all present and enforced (per audit §2.1). |
| Authority ZERO isolation for AI/probabilistic layers, auditable record for verdicts | VERIFIED | 15+ passing isolation tests + structural `RuntimeError` guards (`SYSTEM_AUDIT.md` §2.2); verdicts run through `AuditChain`, not through Lane-2 code, at all. |
| Secrets from env vars; `.env` local-only; never commit `.env`; always commit `.env.example` | CONFLICT (C3) | No `.env` architecture exists; see Conflicts table. The narrower, actually-true statement — "never commit real credentials" — is already true in practice (no secret is in git history) but not via this mechanism. |
| Static checks/linters, zero syntax/typing errors | CONFLICT (C2) / PROPOSED | No linter/typechecker configured today (CONFLICT with "enforce" framing as a definition-of-done item that already runs); adopting one is a reasonable PROPOSED future requirement, not a present fact. |
| Isolated test execution, zero regression | VERIFIED (with a caveat) | 345/345 pytest pass when run against the actual test paths (`ph6/ssmt/tests` etc.) — 4.45s, zero failures, this session. Caveat: the *default* `python3 -m pytest` invocation implied by `pytest.ini`'s own `testpaths` setting does not complete in a reasonable time because it walks the untrimmed evidence directories (`SYSTEM_AUDIT.md` §3.3) — an existing, pre-existing repo issue, not something this constraints document introduced or fixed. |
| Runtime health: logging captures failure boundaries/state transitions | REDUNDANT (differently implemented) | See "Unresolved" above — satisfied by hash-chained audit records, not stdlib logging. |
| Test command: `python -m unittest discover` | CONFLICT (C1) | See Conflicts table. |
| Lint/typecheck: `flake8 .` / `mypy .` | CONFLICT (C2) | See Conflicts table. |
| Update evidence/audit manifests where required by CRAM specifications | VERIFIED (as a principle) | Already how CRAM-A/CRAM-R and `AuditChain` work; already governed by existing CLAUDE.md CRAM-tier rules — no new rule needed. |

## Proposed CLAUDE.md Amendments

One narrow, additive amendment — a factual toolchain pin, so a future
Lane-2 session (or another AI, per CLAUDE.md's own "any model" framing)
doesn't re-import `unittest`/`flake8`/`.env` assumptions from an external
document without checking first. **This pushes CLAUDE.md from 199 to ~207
lines, past its own ≤200-line target** — flagged for operator judgment
rather than silently trimming existing content to make room (see "Changes
NOT To Make").

Insert immediately after the `## GOVERNANCE BASELINE` section, before
`## OPEN ITEMS`:

```markdown
## TOOLCHAIN FACTS (reconciled 2026-09-11 — see RECONCILIATION_REPORT.md)

VERIFIED (current, do not assume otherwise without re-checking):
- Test runner: `pytest` only (`pytest.ini`). No `unittest discover` target exists.
- Lint/typecheck: none configured. No flake8/mypy/ruff config anywhere in repo.
- Secrets: no `.env` mechanism. ESP_S1 Wi-Fi creds live untracked, un-ignored,
  at `ph6/esp_s1/secrets.py` (MicroPython device file, not app config).

PROPOSED (not yet implemented — do not claim these exist):
- Add `ph6/esp_s1/secrets.py` to `.gitignore`.
- Adopt a lint/typecheck gate (tool TBD) if the operator wants one.
```

## Changes NOT To Make

Explicitly rejected, per the "do not migrate the repo to satisfy generic
assumptions" instruction:

- Do **not** replace or wrap `pytest` with `unittest discover` — no
  functional need, and it would require rewriting all 345 existing tests.
- Do **not** create `.flake8` / `mypy.ini` / any lint-tool config merely to
  make the constraints document's diagnostic-commands section true. If the
  operator wants linting, that's a separate, explicit decision with its own
  tool choice (flake8 vs ruff vs mypy strictness level, etc.), not something
  to default into.
- Do **not** invent an `.env`/`.env.example` secrets architecture. The
  existing mechanism (`ph6/esp_s1/secrets.py`, local/untracked) is
  structurally appropriate for a MicroPython device file and should be
  documented as-is, not replaced.
- Do **not** rename, move, or restructure `ph6/cram_pu/validation_runs/` or
  any other evidence directory as part of this reconciliation. The git-bloat
  issue identified in `SYSTEM_AUDIT.md` §3.1 is a separate, already-flagged
  operator decision (git-LFS vs. relocate vs. accept) — resolving it is out
  of scope here and must not be conflated with "cleanup."
- Do **not** delete any evidence, audit record, or historical test artifact.
  Nothing in this reconciliation required or performed a deletion.
- Do **not** trim existing CLAUDE.md content to make room for the new
  section under the 200-line budget — that trade-off is the operator's call,
  not something to resolve unilaterally by cutting rules.

## Implementation Gaps (useful, not yet real — marked PROPOSED, not applied)

1. `ph6/esp_s1/secrets.py` has no `.gitignore` protection — a live
   credential could be committed by a future broad `git add -A` despite the
   repo's own git-safety protocol. Trivial one-line fix; not applied here
   because it constitutes a repository configuration change beyond what was
   authorized for this specific reconciliation task (CLAUDE.md edit only).
2. No lint/typecheck gate exists. If adopted, it should be scoped to the
   actual runtime tree (`ph6/`, `ph6_l2_expand/`, `frame_filter/`) and
   explicitly exclude `ph6/cram_pu/validation_runs/` and `frame_filter/frames_*`
   for the same reason `pytest` collection is slow there (`SYSTEM_AUDIT.md`
   §3.3) — a bare `flake8 .` from repo root would walk the same 500k+ file
   evidence trees.
3. `pytest.ini`'s `norecursedirs` does not exclude
   `ph6/cram_pu/validation_runs` or `frame_filter/frames_*`, so the
   documented default (`python3 -m pytest` from repo root) does not
   complete in practice. Already flagged in `SYSTEM_AUDIT.md` §3.3/§4.3;
   repeated here because it directly undercuts the constraints document's
   "isolated test execution... zero regression" definition-of-done item —
   that item can only be honestly claimed today by scoping pytest to the
   real test paths, not the default invocation.

---

## Verification Run This Session (non-destructive only)

| Check | Result |
|---|---|
| `git status --short` | 1 pre-existing modified file (`ph6_status/status.json`, unrelated to this task) + pre-existing untracked report clutter; nothing touched by this reconciliation |
| `md5sum CLAUDE.md` | `c6c435f0fc838c7f1f866ba261d6625e` (pre-amendment baseline, recorded for the diff below) |
| Lint/typecheck config search | 0 hits (confirmed absent again) |
| `.env` tracked search | 0 hits |
| `ph6/esp_s1/secrets.py` tracked / ignored | untracked, `git check-ignore` exit 1 (not ignored) — unchanged from audit |
| `pytest.ini` contents | unchanged from audit |

No pytest/governance-scan re-run was needed for this task since no code
changed since the prior audit in this same session; those results
(345/345 pass; governance scan 0/0/0/27 PASS; internal-test anchor
reproduced) stand as recorded in `SYSTEM_AUDIT.md`.
