# PH6 Certification — Phase 1 Reconciliation Map (v1)

STATUS: PROPOSED — Lane-2, Authority ZERO. Reconciliation only. No test has been executed.
Scope: response to full-topology certification directive (TOK/SoSo/PSEUDO/AI-advisory expansion),
2026-09-05. Supersedes the CRAM-PU-only preflight from the prior session.

Method: `grep`/`find` over `/home/jack/ph6` (excluding `__pycache__`, `validation_runs/`, `runtime/`)
plus targeted checks of `/home/jack/PH6_SOURCE/SCHEMAS` and `/home/jack/PH6_SOURCE/HRG9_CLOSURE`
for contract text. No file content was assumed from documentation alone — every row below is
backed by a file:line or file-existence check actually run this session.

| Domain | Canonical location | Status | Evidence |
|---|---|---|---|
| CRAM-PU | `ph6/cram_pu/` — `cram_pu_live.py`, `verdict_logger.py`, `schemas/canonical.py`, `tools/cram_pu_replay_verify.py`, `tools/cram_pu_atomic_commit.py` | CANONICAL | multiple files, package imports clean (see prior preflight) |
| PSEUDO | No standalone class. Canonical stage names `PSEUDO_MEASURE` / `PSEUDO_ADJUDICATE` defined in `cram_pu/schemas/canonical.py:23-24`. Gate logic (deterministic measure → PASS/DROP-only adjudicate, no weighting/confidence) distributed across `verdict_logger.py` and campaign tools `tools/run_c10_c11_c12_absorption_campaigns.py` (explicit asserts), `tools/run_c13_variable_speed_information_stress.py` | CANONICAL (distributed, not centralized) | `cram_pu/schemas/canonical.py:23-24`; `cram_pu/tools/run_c10_c11_c12_absorption_campaigns.py:14-15,233,239` |
| TOK | `ph6/tok/` — `validators.py`, `geometry.py`, `lifecycle.py`, `token_store.py`, `rebuild.py`, `audit_writer.py`, `reconstruct.py`, `scheduler.py`, `BOUNDARY.md`, `tests/test_tok_boundaries.py` | CANONICAL | directory listing, full module set present with its own test suite |
| SoSo | **Not a separate module.** Implemented as `ph6/ssmt/` under contract label `PH6-SOSO-FAMILY-CONTRACT-v1.0`. `ssmt/tests/test_soso_contract.py` imports `ph6.ssmt.models.SwarmInput`, `ph6.ssmt.scheduler.SwarmScheduler`, `ph6.ssmt.replay_validator.ReplayValidator`, `ph6.ssmt.constants` | CANONICAL — name reconciled: SoSo == SSMT | `ssmt/tests/test_soso_contract.py:1-11` (docstring names the contract explicitly) |
| AI / advisory agent | `ph6/research_agent/` — `ph6_agent.py`, `ph6_common.py`, `atomic.py`, `hashing.py`, `ph6_ontology.yaml`, `tests/test_research_agent_contract.py` | CANONICAL (implementation exists) | directory listing |
| MRAM-S | Write roots: `ssmt/constants.py` → `SSMT_WRITE_ROOT="/var/ph6/mram-s/swarms/"`, `TOK_READ_ROOT="/var/ph6/mram-s/tokens/"`. Separate namespaced writer: `hw_hooks/advisory_log.py` (`MRAM_S_ADVISORY_SUBPATH`, path-escape guarded) | CANONICAL — multiple legitimate namespaced writers under one root | `ssmt/constants.py:5-6`; `hw_hooks/advisory_log.py:12,20-21` |
| EvidencePacket | Referenced (as term/dict key, not class) in `tok/validators.py`, `tok/audit_writer.py`, `cram_pu/tools/run_c10_c11_c12_absorption_campaigns.py`, `governance/ph6_governor.py`. `grep -rn "^class EvidencePacket"` → zero hits anywhere in `ph6/` | **MISSING** | no defining file found this session |
| ChainIndex | `grep -rn "ChainIndex"` → zero hits anywhere in `ph6/`, under any name | **MISSING** | no hits |
| Registry / capability enforcement | `grep` for `class .*Registry`/`capability` → zero hits in `ph6/`. Contract *schemas* exist only in `PH6_SOURCE/SCHEMAS/`: `ph6_ai_authority_request_v1.schema.json`, `ph6_authority_response_v1.schema.json`, `ph6_ai_transform_record_v1.schema.json`, `ph6_ai_decision_review_v1.schema.json`. No runtime code enforces them. | **UNRESOLVED** — per operator decision 2026-09-05: report as UNRESOLVED, do not fabricate; follow-on spec drafted separately (see `PROPOSED_registry_capability_enforcement_spec_v1.md`) | `PH6_SOURCE/SCHEMAS/*.json` present; zero `ph6/` code hits |
| Atomic write | Two distinct, non-duplicate implementations by authority layer: **Lane-1** `cram_pu/tools/cram_pu_atomic_commit.py` (`AtomicCRAMCommitter`, `commit_pass_verdicts`); **Lane-2** `research_agent/atomic.py` (`atomic_write`) | CANONICAL (both — not a conflict) | `cram_pu/tools/cram_pu_atomic_commit.py:29,108`; `research_agent/atomic.py:11` |
| Replay | `cram_pu/crash_replay.py`, `cram_pu/tools/cram_pu_replay_verify.py`, `cram_pu/tools/replay_parity_proof.py`, `cram_pu/evc04_payload_replay.py`, `cram_pu/evc04_live_payload_replay.py`, `ssmt/replay_validator.py`, `ssmt/replay_receipt.py` | CANONICAL | directory/grep listing |
| HRG9 | Code: `ssmt/closure.py`, `ssmt/forensic_closure.py` ("HRG9-compatible closure rule validator", "Full HRG9-compatible forensic closure for SSMT-1.0"). Sealed evidence: `/home/jack/PH6_SOURCE/HRG9_CLOSURE/*.json` — tracked, git-clean, closure commit `ce1cc1f303`, refresh `2ef5fd66dd` ("HRG9_STATUS = CLOSED", replay parity PASS, 1400/1400 marker integrity). Source run: `cram_pu/validation_runs/20260506T111731Z/{pass_1..pass_4}` present on disk. | **CANONICAL, CLOSED** — per operator decision 2026-09-05: harness verifies against sealed evidence only (VERIFIED_AGAINST_SEAL), never re-opens or re-executes as a fresh gate. Actual replay-verify run against the sealed evidence is **NOT_EXECUTED** yet — requires mapping `pass_1`/`pass_2` outputs to `cram_pu_replay_verify.py`'s `--verdict-log`/`--payloads-json`/`--cram-dir` args. | `PH6_SOURCE/HRG9_CLOSURE/hrg9_replay_parity_receipt.json`; commit `2ef5fd66dd` |
| Schemas | `ph6/cram_pu/schemas/` — `canonical.py`, `cram_pu_packet.schema.json`, `cram_pu_receipt.schema.json`, `audit.py` | CANONICAL | directory listing |
| `ph6.canonjson.v1` (as literally named) | Zero hits anywhere. Nearest real artifacts use different schema names (`ph6.ssmt.manifest.v1`, `ph6.hrg9.replay_parity_receipt.v1`) | **MISSING (naming)** | prior-session grep; nothing found under this exact name |

## Open items carried into Phase 2

1. **EvidencePacket / ChainIndex** — genuinely absent from the codebase under any name found. Certification tests that depend on these contracts (§18 provenance chain, §11 Lane-1 authoritative state) will be marked UNRESOLVED until either the operator identifies where they actually live, or confirms they were never implemented (doctrine only).
2. **Registry/capability enforcement** — UNRESOLVED per operator decision; blocks §9 effective-capability tests. Follow-on spec is separate work, not part of this certification run.
3. **HRG9** — sealed/closed; harness will verify-against-seal only, per operator decision.
4. **`frame_filter`** — separate git repo at `/home/jack/frame_filter/`, imports cleanly once its own directory is on `sys.path` (depends on sibling `cram_writer.py`). Per §21, intentionality/supply-chain boundary not yet established — carried as UNRESOLVED into the TOPOLOGY test domain.

```json
{"proposed_by":"claude-code-lane2","proposed_at_utc":"2026-09-05T12:15:00Z","api_call_log_ref":"session_01Er4uEgGZE7jhVVrQcnSh6S","ratified_by":null}
```
