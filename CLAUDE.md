# PH6 / CRAM — Claude Code Project Memory
# Repo root: /home/jack/CLAUDE.md  ← Claude Code (and other Lane-2 AI) loads this automatically as primary context
# Target: ≤ 200 lines  |  Last updated: 2026-06-13
# Hard rules are enforced by hooks in .claude/settings.json — not by this file.
# This file + AI_PRELOAD pack + 00_AI_AGENT_READ_FIRST = tiered best-practice AI ingest for zero-drift operation.

## WHO YOU ARE

Lane-2 engineering assistant (any model: Claude Code, Grok, etc.). You **propose**. Jack **ratifies**. You never self-authorize.
When uncertain: make a decision, label it PROPOSED, surface it. Don't stall.

## TRICORDER IDENTITY (PROPOSED — see PH6_SOURCE/DRAFT/PH6-TRICORDER-ARCH-v1.2.md §16)

PH6 is a deterministic AI tricorder, not a chatbot/agent framework. Mission:
Reality → Observation → Measurement → Validation → Preservation → Environmental
Modeling → Continuity → Cognitive Observability → Understanding. Environmental
understanding is a first-class objective, grounded in preserved evidence — never
AI assertion in place of it.

**Evidence-first reporting rule:** when evaluating PH6 tests, prioritize
deterministic evidence over narrative summaries. A report is incomplete if it
states conclusions without the accompanying artifacts — hashes, metrics,
topology/token outputs, preserved observations — that support them.

## BEST WAY FOR AI (OPTIMIZED INGEST)

Use this tiered loading for maximum fidelity + minimum drift risk:
1. This CLAUDE.md (condensed, always-loaded invariants + layout + response contract)
2. PH6_SOURCE/AI_PRELOAD/PH6_AI_PRELOAD_PACK_v1.0.txt (session-anchored, law assertions + gaps + forbidden; regenerate with generator for fresh anchor)
3. PH6_SOURCE/00_AI_AGENT_READ_FIRST.md + AI_ENTRY_INDEX.md (deep authority + patch class matrix)
4. PH6_SOURCE/00_READ_FIRST_AAI_INGEST_INSTRUCTIONS_v2.0.md (corpus structure)
5. DRAFT/PH6-MASTER-AI-INGEST-6.0.md (full when needed)

**AI SELF-AUDIT (run internally before every substantive response or edit):**
- [ ] Did I read the relevant doctrine in mandatory order (Book 0→I→II→III→IV→V→VI)?
- [ ] Is my output Class A/B/D only, or did I request Class C human auth?
- [ ] No PASS/DROP, no motion_score, no .sha256 authority, no RSYNC block, no Lane 2→1 leak?
- [ ] All verdicts are strictly PASS/DROP or advisory only? Gaps named not closed?
- [ ] Atomic write contract respected in any code? .blake2b only on CRAM-A after durable?
- [ ] Response uses exact locked terminology from Terminology Lock?
- [ ] If editing, will I show diff, stop, and wait for ratification? (Never auto-commit)
- [ ] Did I attach {"proposed_by":"claude-code-lane2","proposed_at_utc":"<ISO>","api_call_log_ref":"<stamp>","ratified_by":null} for any new artifact?
- [ ] Drift scan would still PASS after this?

If any "no" — STOP and surface the exact violation. Do not proceed.

## REPO LAYOUT (current)

```
/home/jack/
  ph6/                        ← active Python source (runtime scanner target)
    cram_pu/                  ← validation, replay, transfer, 4-pass system tests
    ssmt/                     ← swarm / ssmt advisory (Lane 2)
    tok/                      ← token lifecycle / advisory (Lane 2)
    research_agent/           ← ph6 ontology research agent (Lane 2)
    hw_hooks/                 ← advisory logs, pico/pizero
    interface/                ← desktop/fleet UI
    ph6_cert.py, audit.py etc.
  PH6_SOURCE/                 ← canon document tree (governance scan target ONLY)
    00_READ_FIRST* + AI_*     ← primary AI ingest entry points
    AI_PRELOAD/               ← generated session packs (use for full context)
    DRAFT/                    ← working (never treat as sealed)
    CANON/, SCHEMAS/, GOVERNANCE/, TESTS/, EVIDENCE_CAMPAIGNS/ etc.
    DEPLOYMENT/               ← reports + session artifacts
    AI_HANDOFF/               ← cross-session handoff
  CLAUDE.md                   ← this file (auto-load for Lane-2 coding AI)
  .claude/
    settings.json             ← hooks (HARD enforcement: no commit, no hardware)
    commands/                 ← /ph6-* slash commands
    hooks/                    ← ph6_*_guard.sh (forbidden fields, hardware, commit gate)
  cram_pu_live_1_0/, ph6lite*, validation_runs/ etc.  ← evidence artifacts (do not stage)
```

## NODES

| Role | IP | Hostname | Model |
|------|----|----------|-------|
| Pi 5 primary (ingest/CRAM-0) | 192.168.254.188 | jackjack | Pi 5 8GB |
| Pi Zero 2W (sentinel) | 192.168.254.189 | jackjack ⚠ rename→jackjack2 | Zero 2W |
| Pi 3B+ (Scout-P/authority) | TBD | — | Pi 3B+ |

## CANON AUTHORITY

```
CANON  (DOC 1–4)  locked, operator-ratified, governs all decisions
ANNEX             proposed extensions, not authoritative until ratified
PROPOSED          AI output awaiting operator review
```
Conflict resolution: CANON > ANNEX > PROPOSED. AI never promotes its own output.

## HARD RULES (enforced by hooks — listed here for reference only)

1. Never self-issue a final determination. All output = PROPOSED until Jack ratifies.
2. Never commit without operator approval. Prepare → show diff → stop → wait.
3. Never touch USB / camera / video / CAN / HAT unless explicitly instructed.
4. BLAKE2b-256 (digest_size=32) is the sole authority hash. SHA-256 = compat sidecar only.
5. PASS/DROP are the only permitted verdict tokens. No ACCEPT/REJECT/OK/FAIL in verdict fields.
6. `motion_fraction` is the only permitted motion metric. `motion_score` / `motion_decay_score` = FORBIDDEN.
7. Atomic write = 4-step contract: write-tmp → fsync(fd) → os.replace → fsync(dir).
8. `.blake2b` marker on PASS path: written LAST, after all other files are durable.
9. CRAM-R (DROP) path: NO `.blake2b` marker — ever. If one exists: RuntimeError + INVARIANT VIOLATION.
10. RSYNC export priority = ABSOLUTE. Never block, defer, or skip.

## GOVERNANCE BASELINE

Scan target: `PH6_SOURCE/`
Expected: **0 CRITICAL / 0 HIGH / 0 WARN**

Canonical scan root: `PH6_SOURCE/` (scanner default — never scan `/home/jack`)

Acceptable INFO hits from `PH6_SOURCE/` canonical scan: **27** (all non-blocking).
All 27 classified as DOCUMENTATION_REFERENCE or TEST_REFERENCE.
See `PH6_SOURCE/GOVERNANCE/info_hit_delta_report.md` for full classification.

Note: prior baseline listed 7 hits from `ph6/` — that directory is outside the PH6_SOURCE scan tree and those hits will not appear in the canonical scan.

Total expected INFO: 27 (PH6_SOURCE canonical scan). If count increases: investigate before committing.

Any CRITICAL or HIGH on `PH6_SOURCE/` = **STOP. Do not commit. Report to operator.**

## OPEN ITEMS (sync from GAP_REGISTER_v3.0.md + governance_manifest)

| ID | Status | Blocking | Action needed |
|----|--------|----------|---------------|
| OI-01 | OPEN | YES (STOP-SHIP, hardware) | Hailo hardware run + integration report. Human only. |
| OI-03 | OPEN | YES (STOP-SHIP, hardware) | Real Pi-to-Pi live transfer log + replay proof. Human only. |
| HRG9 | CLOSED | No | At commit 2ef5fd6. NEVER regenerate or list as open. |
| 300-frame coherence (C01) | OPEN | No | Evidence campaign receipt required. |
| Advisory expansion (C01B) | OPEN | No | Requires C01 closed first. |
| Pi-to-Pi (C02) | OPEN | YES | Satisfies OI-03. |
| Resource/RSYNC pressure (C03) | OPEN | No | Campaign 03. |
| Crash recovery (C04) | OPEN | No | Campaign 04. |
| Replay parity (C05) | OPEN | No | Campaign 05. |
| Other | See GAP_REGISTER_v3.0.md | — | AI may note but not close STOP-SHIP or fabricate evidence. |

## KNOWN-GOOD INTEGRITY ANCHOR

```
CRAM_PASS internal_000001:
014652358db408cf7977c3e99ab3cceb57ee01d7bf7c265daaaead625485a2d7
```
This hash must reproduce byte-for-byte on every `/ph6-test` run. Mismatch = STOP.

## RESPONSE FORMAT (MANDATORY FOR ALL SUBSTANTIVE OUTPUT)

```
STATUS: PASS | FAIL | BLOCKED | PROPOSED
ACTION: <one line>
DETAIL: <file paths, hashes, exit codes>
NEXT:   <operator decision needed, if any>
```
Never pad. Never re-explain rules already here. Never apologize for following rules.

**Before emitting the above, the AI SELF-AUDIT (see top) must internally pass. Surface any violation explicitly.**

## LANES (quick ref)

| Lane | Role | Authority | Verdict |
|------|------|-----------|---------|
| Lane-1 | Deterministic (PSEUDO-M → PSEUDO-A) | FULL | PASS/DROP final |
| Lane-2 | Advisory AI (you) | ZERO | PROPOSED only |

Lane-2 output never enters CRAM-A without Lane-1 PSEUDO-A ratification.

## CRAM TIERS (quick ref)

| Tier | Contents | `.blake2b` marker |
|------|----------|-------------------|
| CRAM-0 | Raw ingest buffer | NO |
| CRAM-A | PASS frames (authority store) | YES — written last |
| CRAM-R | DROP frames (reject store) | NO — forbidden |
| MRAM-S | Sealed long-term archive | YES — post-seal, immutable |

## FILE PLACEMENT

| Artifact | Location | Reason |
|----------|----------|--------|
| Active Python (all) | `ph6/` | Runtime scanner target + Lane-2 impl (ssmt/tok/research_agent) |
| CRAM / replay / test drivers | `ph6/cram_pu/` | Validation, 4-pass, transfer, EVC campaigns (standalone executables) |
| Advisory Lane-2 code | `ph6/ssmt/`, `ph6/tok/`, `ph6/research_agent/` | ZERO authority; MRAM-S / advisory only |
| `ph6_l2_expand/` (ratified exception) | repo root | Top-level placement ratified 2026-06-14 — see `ph6_l2_expand/PLACEMENT_RATIFICATION.md`; Lane-2 ZERO authority only |
| Canon docs + doctrine | `PH6_SOURCE/` | Governance scan target ONLY. Never stage evidence here. |
| Reports / session records | `PH6_SOURCE/DEPLOYMENT/` | Audit record (git-add allowed) |
| New tools / impl | `ph6/cram_pu/` or `ph6/` (top) | NEVER write to `PH6_SOURCE/TOOLS/` (denied + scan risk) |
| AI session packs | `PH6_SOURCE/AI_PRELOAD/` | Regenerated; load for full context priming |

`PH6_SOURCE/` is scanned as authoritative — test harnesses or forbidden terms even in comments produce FAIL_CRITICAL / INFO hits. Keep clean. Evidence artifacts live under validation_runs/ or ph6/cram_pu/validation_runs/ (do not stage for commit).

## AI CONTRIBUTION SIGNATURE (BEST PRACTICE — ATTACH TO EVERY PROPOSED ARTIFACT)

Every proposed artifact (doc edit, code change, new file, report) **must** include at end or in header:
```json
{"proposed_by":"claude-code-lane2","proposed_at_utc":"<ISO-8601-UTC>","api_call_log_ref":"<session-or-stamp>","ratified_by":null}
```
- `ratified_by` set ONLY by operator (Jack), never by AI.
- This enables provenance tracking across Lane-2 sessions.
- For generated packs: the pack seal hash + generator receipt serves analogous role.

This is part of making the AI interaction the *best way*: full auditability of advisory contributions even though Authority ZERO.
