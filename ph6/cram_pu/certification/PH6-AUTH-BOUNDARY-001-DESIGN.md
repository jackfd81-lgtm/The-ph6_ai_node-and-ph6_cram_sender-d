# PH6-AUTH-BOUNDARY-001 — Lane-1 Authorization Mechanism (Design Proposal)

**Status:** PROPOSED — NOT IMPLEMENTED — NOT CERTIFIED
**Authority:** ZERO (Lane-2 drafted design artifact)
**Root defect addressed:** Lane-1 authoritative commit boundary (`AtomicCRAMCommitter.commit()`) performs no runtime authorization check — confirmed by three independent search passes this session (zero hits for any capability/authorization/permission pattern anywhere in `ph6/`) and one live adversarial test (a call carrying AI-attributed provenance was accepted and stamped `authority: LANE_1`).
**Affected certification findings:** `AI_ADVISORY-003`, `SOSO-SPOOF-001`, `PSEUDO-SEAM-001`
**No canonical PH6 source has been modified to produce this document.**

**REVISION NOTE (design-review pass, 2026-09-05, later session):** this document was hardened per operator gate — a formal self-review, explicit isolation-boundary characterization, sequence/crash/replay semantics, an anti-backdoor requirement, and a formal authority-provenance schema were added (Parts 2-3 below). One material finding surfaced during this pass: **the certification's adversarial test (AI_ADVISORY-003) targeted `AtomicCRAMCommitter` in `cram_pu_atomic_commit.py`, but that is not the commit implementation the actual production pipeline uses.** A second, structurally near-identical implementation, `CRAMWriter` in `crash_replay.py`, is the one imported by `cram_pu_live.py`, `run_4pass_system_test.py`, and every `run_c09`-`run_c13` campaign tool exercised this session for `PSEUDO-FAMILY-001`. `CRAMWriter.commit()` has the exact same defect (no caller-identity check beyond `verdict == "PASS"`). This is documented in Part 2A below as a scope-expanding finding, not silently absorbed into the original design's boundaries. **Status remains PROPOSED — NOT IMPLEMENTED — NOT CERTIFIED. No canonical source was modified during this revision.**

---

## 0. Design constraints from the actual codebase

Before proposing a mechanism, the facts that constrain it:

- PH6's Lane-1/Lane-2 code all runs **in a single Python process**. There is no OS-level process boundary, no network boundary, and no interpreter boundary between `cram_pu`, `ssmt`, `tok`, and `research_agent` — they are modules imported into one process (confirmed by every code path traced this session: `cram_pu_live.py`, `tok_soso_isolation_proof.py`, `run_4pass_system_test.py` all import Lane-1 and Lane-2 modules side by side and call between them directly).
- This means **no in-process mechanism can be a perfect security boundary** in the way a process or network boundary would be. Any design here raises the cost of an unauthorized commit from "zero — call a public function" to "must obtain or forge a specific secret/proof," not to "cryptographically impossible for co-resident code." That distinction is stated explicitly in §6 rather than implied.
- The existing canonical hash primitive is BLAKE2b-256 (CLAUDE.md hard rule 4). BLAKE2b has native keyed-hashing support (`hashlib.blake2b(data, key=secret, digest_size=32)`), so a capability-integrity mechanism can be built entirely from the primitive PH6 already treats as authoritative, without introducing HMAC-SHA256 or any other new cryptographic primitive.

## 1. Candidate mechanisms considered

| Mechanism | Verdict |
|---|---|
| Call-stack / module-origin inspection (my earlier proposal) | **Rejected as final design**, per operator instruction — spoofable by any code placed inside an allowlisted module path; doesn't bind to payload content; provides no replay resistance. Retained only as a *defense-in-depth* supplement (§3), not the primary control. |
| Caller-declared role/lane string (`source="cram_pu"`) | **Rejected** — this is exactly the self-attestation pattern Section 3 of the remediation spec forbids, and is what the current (absent) "check" would degenerate into if implemented naively. |
| OS-level process separation (Lane-1 as a separate service, Lane-2 talks to it only via a narrow RPC/IPC protocol) | **Strongest theoretical option** — genuinely removes co-residency, makes forgery require breaking a real process/network boundary. **Deferred, not chosen**, because it requires re-architecting how `cram_pu_live.py` and every campaign tool invoke the committer (currently direct in-process calls) — a major structural change, not a minimal fix to the discovered defect. Explicitly noted as a natural *next step* if PH6 later needs a stronger boundary: the capability design below is forward-compatible with it (a capability token is exactly what you'd pass across such an RPC boundary too), so this proposal is not wasted work if that path is taken later. |
| **Capability-based authorization, minted only by Lane-1, content-bound via keyed BLAKE2b-256** | **Chosen as primary design.** Detailed below. |

## 2. Authority issuer

**Only `AtomicCRAMCommitter` itself, at the moment `commit()` is legitimately entered from within its own module, may mint a capability for that specific commit.**

Concretely: minting is not a separate public function Lane-2 could call to "ask for" a capability. Minting happens *inside* `commit()`'s own call chain, immediately before the write, using a secret that is never passed as a parameter, never returned, and never importable from outside `cram_pu`'s internal module.

**Why Lane-2 cannot mint it:**
- The signing secret is generated fresh per process (`secrets.token_bytes(32)` at `cram_pu` package initialization) and held in a **closure cell**, not a module attribute. A minting function is constructed once, at init time, capturing the secret in its closure; no name in `cram_pu`'s namespace ever holds the raw secret directly. This defeats the simplest introspection attack (`sys.modules['ph6.cram_pu.X']._SECRET`) — reaching the secret would require `mint_fn.__closure__[...].cell_contents`, which requires an actual reference to the minting function object itself, and that reference is never exported, never assigned to an importable name, and never passed to any Lane-2 code path.
- The secret is **process-lifetime only** — never written to disk, never logged, never included in any evidence artifact. A fresh process (Lane-1 restart) invalidates all previously-issued capabilities, which is correct: capabilities are meant to be minted and consumed within the same short window of the same run, not persisted or handed across runs.
- Residual risk, stated explicitly: code running with equal process privilege (i.e., anything importable in the same interpreter) can in principle reach almost anything via sufficiently determined introspection (`gc.get_referrers`, frame walking, etc.). This design does not claim to defeat a determined attacker with unrestricted introspection rights in the same process — it claims to defeat the actual demonstrated attack (a normal import + direct function call with no special effort), which is what AI_ADVISORY-003 exercised, and to raise the bar substantially above "zero effort."

**PRECISE CHARACTERIZATION (required by design-review gate, Part 2A below expands this — stated here where the mechanism is first introduced so the claim is bounded from the start, not just in a review appendix):**

> A secret held inside a Python closure is an **in-process runtime integrity mechanism**. It is **not a cryptographic isolation boundary** against hostile code executing with equivalent privileges inside the same Python interpreter. It must not be represented, in this document or in any future certification claim, as protection against arbitrary same-process introspection, code injection, or malicious modification of the running interpreter. Any certification claim built on this mechanism is bounded to PH6's intended execution model — legitimate Lane-1/Lane-2 code coexisting in one process, where the demonstrated attack surface is "an unrelated module calls a public function," not "an adversary has arbitrary code-injection or debugger-level access to the live interpreter." Stronger isolation (process-level separation) is a **distinct architectural boundary** and is not implicitly claimed by adopting this design — see the deferred alternative in §1.

## 3. Capability representation

```
LaneOneCommitCapability:
  schema:        "ph6.lane1_capability.v1"
  packet_id:      str        # must exactly match the verdict being committed
  input_hash:     str        # must exactly match verdict["input_hash"]
  verdict:        "PASS"     # capabilities are never minted for DROP (DROP never reaches commit() at all, per existing contract)
  mint_seq:       int        # bound to AtomicCRAMCommitter's own internal _seq counter — a capability is only valid for the NEXT expected sequence number, preventing replay out of order or reuse after a commit has already advanced the chain
  issued_at_ns:   int        # monotonic clock timestamp, process-local — for diagnostic/audit purposes only, NOT used as an expiry (see below)
  mac:            str        # blake2b(canonical_bytes({schema, packet_id, input_hash, verdict, mint_seq}), key=LANE1_SECRET, digest_size=32).hexdigest()
```

**Scope:** single-use, single-payload. The `mac` field cryptographically binds the capability to the *exact* `packet_id` + `input_hash` + `mint_seq` it was minted for. A capability minted for one packet cannot be reused, replayed, or "transplanted" onto a different verdict — changing any bound field invalidates the MAC.

**Lifetime/replay:** rather than wall-clock expiry (which requires clock-trust assumptions this in-process design doesn't need), freshness is enforced by binding to `mint_seq`, which must equal `committer._seq + 1` at verification time. Once a commit succeeds, `_seq` advances, and the consumed capability's `mint_seq` can never satisfy that check again — this gives natural single-use semantics without needing a separate revocation list.

**Provenance vs. authority (Section 3's core distinction):** the capability's fields (`packet_id`, `input_hash`) are provenance — descriptive of *what* is being committed. Authority comes *only* from whether `mac` verifies against the live secret. A forged capability with correct-looking provenance fields but a wrong or absent `mac` is denied exactly the same as one with no fields at all — provenance never substitutes for the integrity check.

## 4. Commit-boundary enforcement

Proposed signature change (design intent, not code):

```
AtomicCRAMCommitter.commit(self, verdict: dict, capability: LaneOneCommitCapability) -> dict
```

`capability` becomes a **required, positional** parameter — no default value. This is deliberate: a required parameter with no default cannot be silently omitted or `None`-defaulted past the check by an unmodified caller; every existing call site must be touched to pass one (see §8, Compatibility).

Enforcement sequence inside `commit()`, **before any file I/O**:

1. Verify `capability.schema == "ph6.lane1_capability.v1"` — reject unknown/absent schema.
2. Verify `capability.packet_id == verdict["packet_id"]` and `capability.input_hash == verdict["input_hash"]` — reject mismatch.
3. Verify `capability.verdict == "PASS" == verdict["verdict"]` — reject anything else (this subsumes and strengthens the existing PASS-only check).
4. Verify `capability.mint_seq == self._seq + 1` — reject stale/replayed/out-of-order capabilities.
5. Recompute `expected_mac` using the live closure-held secret and compare to `capability.mac` using a constant-time comparison (`hmac.compare_digest`) — reject on any mismatch.
6. Only if all five checks pass: proceed to the existing atomic-write sequence unchanged.

Any failure at steps 1-5 raises a new `LaneOneAuthorizationError` **before** `os.open`/`os.write`/`os.replace` are reached — satisfying "authorization occurs before mutation," and satisfying §12's requirement that a denied attempt create no CRAM-A artifact, no partial file, no marker.

## 5. Authority separation — why other objects cannot substitute

| Object | Why it cannot be mistaken for Lane-1 authority under this design |
|---|---|
| AI output / `research_agent` result | Has no path to the closure-held secret; cannot compute a valid `mac` for any payload. |
| SoSo/SSMT `SwarmPacket`, `authority="NONE"` | Different schema entirely (`ph6.ssmt.*` vs `ph6.lane1_capability.v1`); `commit()` does not accept a SwarmPacket as its `capability` argument — a type/schema mismatch, not merely a semantic one. |
| TOK record | Same reasoning — TOK schemas are never `ph6.lane1_capability.v1` and carry no `mac` field bound to the live secret. |
| MRAM-S artifact of any kind | MRAM-S is a *destination*, not a capability source; nothing about being persisted to MRAM-S grants minting rights. |
| A hand-crafted dict with plausible-looking `schema`/`packet_id`/`mac` fields (forgery attempt) | `mac` will not verify against the live secret unless the forger has the actual secret value — guessing a 32-byte keyed BLAKE2b-256 output is computationally infeasible. |
| A capability legitimately minted for a *different* packet | `packet_id`/`input_hash` binding causes step 2 to reject it against the new verdict. |
| A capability from a *previous* commit in the same run | `mint_seq` binding causes step 4 to reject it — sequence already advanced. |

## 6. Attack model

| Attack | Outcome under this design | Notes |
|---|---|---|
| Call `commit()` directly with no capability argument | **DENIED** — `TypeError` (missing required argument) before any check logic even runs, since it's a required parameter. |
| Call `commit()` with a capability object missing fields or wrong schema | **DENIED** at step 1. |
| Forge a capability with correct `packet_id`/`input_hash` but guessed/absent `mac` | **DENIED** at step 5 — cannot produce a valid keyed-BLAKE2b output without the secret. |
| Replay a previously-valid, previously-consumed capability | **DENIED** at step 4 — `mint_seq` no longer matches. |
| Alter provenance fields (`packet_id`) on an otherwise-valid capability, hoping to redirect it to a different packet | **DENIED** at step 2 — MAC no longer matches the altered payload (MAC is computed over these exact fields). |
| Alter `ssmt_version` or other SSMT-side fields | **Out of scope for this mechanism** — handled by §9 (version integrity), a deliberately separate control. |
| Substitute AI/SoSo/TOK/PSEUDO-Predictive/PSEUDO-SCI metadata as if it were authorization | **DENIED** — none of these object types are ever accepted as the `capability` argument; this is a type-level rejection, not a value-level one. |
| Bypass the normal Lane-1 call chain by importing `AtomicCRAMCommitter` from an unrelated script (the exact AI_ADVISORY-003 reproduction) | **DENIED** — the importing script has no reference to the closure-held minting function; it can construct a `LaneOneCommitCapability`-shaped object but cannot produce a valid `mac` for it. |
| Invoke from a separate process (future scenario, not current architecture) | **DENIED** by construction — the secret is process-local and never persisted; a separate process has no way to obtain it at all. |
| Pass a malformed or partially-valid capability (right schema, wrong `mint_seq`) | **DENIED** at step 4. |
| **Residual/accepted risk:** code physically added to a file inside `ph6/cram_pu/` that is executed as part of a legitimate Lane-1 call chain, and thereby gains a real reference to the minting closure | **NOT defended against by this mechanism** — this is a source-integrity/code-review problem (git history, PR review, the existing "never commit without operator approval" rule), explicitly out of scope for a runtime authorization control. Stated here rather than silently assumed away. |
| **Residual/accepted risk:** an attacker with unrestricted Python introspection rights in the same process (frame-walking, `gc` module abuse) reaching the closure cell directly | **Not fully defended against** — no in-process mechanism can be. Raises cost from "zero" to "nontrivial deliberate introspection," does not claim more than that. |

## 7. Version integrity (independent control, per operator instruction — not merged with §2-6)

`ssmt_version` is validated **separately**, at two points, against the existing `SSMT_VERSION` constant (`ssmt/constants.py`, currently `"1.0"`) — no new schema identifier is introduced:

1. **At write** (`ssmt/audit_writer.py::write_packet`): reject (raise, do not silently write) if `packet.ssmt_version != SSMT_VERSION`.
2. **At read/replay** (`ssmt/replay_validator.py` and any consumer of persisted packets, e.g. `ssmt/hash_chain.py` callers): reject if a loaded packet's `ssmt_version` is absent, malformed (not a string matching the expected pattern), or does not match a version this build of `ssmt/` declares support for.

This is a straightforward field-validation control, not a capability system — deliberately simpler than §2-6, because the underlying property being protected (accurate version labeling) is a data-integrity concern, not an authority-escalation concern. Conflating the two, as the operator noted, would have been a mistake.

**Behavior table:**

| Condition | Result |
|---|---|
| `ssmt_version == SSMT_VERSION` | accept |
| absent | DENY (reject write / reject on read) |
| malformed (non-string, wrong shape) | DENY |
| well-formed but unsupported (e.g. a real but unrecognized future version) | DENY, with an explicit "unsupported version" reason distinct from "malformed" |
| mismatched (valid shape, wrong value) | DENY |

## 8. Regression tests required (design-level specification, not yet implemented)

| Test | Requirement |
|---|---|
| `AUTH-BOUNDARY-DENY-001` | Direct `commit()` call with no capability -> `TypeError`, no file created. Reproduces AI_ADVISORY-003's exact scenario. |
| `AUTH-BOUNDARY-DENY-002` | `commit()` call with a hand-forged capability (plausible fields, no valid `mac`) -> `LaneOneAuthorizationError`, no file created. |
| `AUTH-BOUNDARY-DENY-003` | Replay of a previously-consumed valid capability -> `LaneOneAuthorizationError` (mint_seq check). |
| `AUTH-BOUNDARY-DENY-004` | Capability minted for packet A, presented alongside verdict for packet B -> `LaneOneAuthorizationError` (binding check). |
| `SOSO-VERSION-DENY-001` | `write_packet()` with `ssmt_version="99.9.9-SPOOFED"` -> rejected, reproduces SOSO-SPOOF-001. |
| `SOSO-VERSION-DENY-002` | Replay/read path presented with a persisted packet carrying a mismatched version -> rejected. |
| `PSEUDO-SEAM-DENY-001` | Same as `AUTH-BOUNDARY-DENY-001/002`, invoked from a script positioned to simulate the PSEUDO-seam path -> denied identically, confirming the fix closes the seam from both the AI-side and PSEUDO-side framing (these were always the same underlying defect viewed from two angles). |
| `AUTH-BOUNDARY-POSITIVE-001` | The legitimate flow — PSEUDO-A adjudicates PASS, `commit_pass_verdicts()` mints and immediately consumes a capability within the real call chain -> commit succeeds, CRAM-A file + `.blake2b` marker written exactly as today, byte-for-byte compatible record shape (plus the new capability having been consumed, which is not persisted into the CRAM-A record itself — see §9). |
| Full existing suite | All 242 currently-passing pytest tests, `ph6_internal_test.py`, `tok_soso_isolation_proof.py`, and the C10/C11/C12 PSEUDO-family campaigns re-run and confirmed still passing post-change — regression, not just new-test-passing. |

## 9. Compatibility — what this touches

**Breaking change, requires updating every legitimate call site:**
- `cram_pu/tools/cram_pu_atomic_commit.py` — `commit()` signature, `commit_pass_verdicts()` (must mint internally before calling `commit()`)
- `cram_pu/cram_pu_live.py` — wherever it invokes the committer
- `cram_pu/run_4pass_system_test.py`, `run_two_pi_transfer_test.py`, `evc01_crash_simulation.py`, `evc02_long_run.py`, `evc04_payload_replay.py`, `evc04_live_payload_replay.py` — each constructs/calls a committer or equivalent commit path
- `cram_pu/tools/run_c10_c11_c12_absorption_campaigns.py`, `run_c13_variable_speed_information_stress.py`, `run_c09_12000_frame_campaign.py` — campaign tools that commit frames
- `cram_pu/tests/test_vrc.py`, `cram_pu/tests/test_crash_replay.py`, `cram_pu/tests/test_closure_patches.py`, and other tests constructing an `AtomicCRAMCommitter` fixture
- `ph6_internal_test.py`'s CRAM stage checks — needs a test-support minting path (see below)

**Not touched:** TOK internals, SSMT/SoSo internals (their own MRAM-S writes are unaffected — this mechanism only guards the CRAM-A/R commit direction), the schema files themselves (`cram_pu_packet.schema.json`, `cram_pu_receipt.schema.json` — the *committed record's own shape* is unchanged; only the *act of committing* gains a precondition), `governance/`, `tok/`, `research_agent/` (none of these currently call `commit()` — that's the point).

**Open design question flagged for operator, not resolved silently:** `ph6_internal_test.py` needs *some* way to exercise the commit path for its self-test (CRYPTO-001/STORAGE-001 depend on this). Two options: (a) it runs the real, full legitimate call chain (PSEUDO-A mints, hands off, commits) rather than constructing `AtomicCRAMCommitter` standalone — preferred, since it tests the real path; or (b) a separate, clearly-named test-support minting function exists in a module never imported by any production Lane-2-reachable path. Option (a) is recommended; (b) is flagged as a risk (test-mode backdoors have a way of leaking into production reachability) and would need explicit justification if chosen.

## 10. Migration — no corruption of existing evidence

- Capabilities are checked only at **mint/write time for new commits going forward**. Nothing about `_load_last_hash()`/`_load_last_seq()` (which only *read* existing `cram_*.json` files to continue the hash chain) needs to know about capabilities — old records are read exactly as today.
- No backfill, no re-signing, no re-hashing of existing CRAM-A/CRAM-R evidence is required or proposed.
- The chain-continuity guarantee (`prev_cram_hash`) is unaffected — capabilities gate *whether* a new commit happens, not *what* the committed record's chain-hash contains. Record shape is unchanged (capability metadata is consumed for the check, not persisted into the record) — meaning `.blake2b` markers and downstream replay/parity tooling that reads committed records see no format change.

## 11. Certification — evidence required to move FAIL -> PASS

Per the operator's fresh-certification rule (no historical evidence carried forward as current):

1. §8's full test table executed fresh, all DENY-classified tests actually denying, all POSITIVE tests actually succeeding.
2. Full existing mandatory registry (32 global tests + 22 family tests) re-run in full — not just the three previously-failing tests — to confirm zero regression, per the operator's explicit "no PASS may be inferred merely because the change is small" instruction.
3. `AI_ADVISORY-003`, `SOSO-SPOOF-001`, `PSEUDO-SEAM-001` re-classified PASS only if their respective fresh adversarial re-executions (not the original pre-remediation ones) show DENIED.
4. A new receipt (`PH6-CERTIFICATION-RECEIPT-POST-AUTH-BOUNDARY-REMEDIATION.json`) generated per the remediation spec's §16, referencing this design document, the pre-remediation frozen snapshot, and the fresh execution evidence — the frozen pre-remediation receipt is never overwritten.
5. `CRYPTO-003`, `SCHEMA-002`, `AI_ADVISORY-001`, `HRG9-001` remain exactly as they are (UNRESOLVED) — this remediation does not touch them, and the fresh receipt must show them unchanged, not silently dropped.

---

# PART 2 — DESIGN HARDENING (review pass, no source modified)

## 2A. Scope-expanding finding: two commit implementations, not one

Tracing the actual call graph for this review surfaced a fact the original design did not account for. There are **two structurally near-identical atomic-commit classes**, not one:

| | `AtomicCRAMCommitter` (`cram_pu/tools/cram_pu_atomic_commit.py`) | `CRAMWriter` (`cram_pu/crash_replay.py`, lines ~617-690) |
|---|---|---|
| Schema | `ph6.cram_commit.v1` | `ph6.cram_commit.v1` (same schema string) |
| Check performed | `verdict["verdict"] != "PASS"` -> raise | `verdict_record.get("verdict") != "PASS"` -> raise |
| Atomic sequence | tmp write+fsync -> rename -> marker tmp+fsync -> rename -> dir fsync | identical sequence, same order |
| Actually used by production | Only `cram_pu/tests/test_canonical_schemas.py` and its own `commit_pass_verdicts()`/CLI | `cram_pu_live.py`, `run_4pass_system_test.py`, `run_two_pi_transfer_test.py`, `evc02_long_run.py`, `run_c09_12000_frame_campaign.py`, `run_c10_c11_c12_absorption_campaigns.py`, `run_c13_variable_speed_information_stress.py`, `life_cram_lcc_01_live_camera.py`, `cram_pu_fi_suite.py`, `cram_pu/tests/test_closure_patches.py`, `cram_pu/tests/test_vrc.py` |

**Consequence:** `CRAMWriter`, not `AtomicCRAMCommitter`, is the commit boundary the actual production pipeline and the C10-C13 campaigns (the ones fresh-executed this session for `PSEUDO-FAMILY-001`, all PASS) go through. `CRAMWriter.commit()` has the identical defect — no caller-identity check beyond the PASS-only guard. AI_ADVISORY-003's adversarial test, as originally run, demonstrates the defect class exists in this codebase, but it exercised the *less-used* of the two implementations.

**This is recorded as an UNRESOLVED design dependency, not silently folded in:** the design in Part 1 must be understood to apply to **both** classes, or a prior decision must be made to consolidate them into one before implementation. Applying the capability check to only one class (whichever the original design assumed) while leaving the other unguarded would produce a **false-positive certification** — tests would show DENIED against the tested class while the actual, more heavily used production path remains exactly as exploitable as before. This is exactly the "declared ≠ observed ≠ validated" trap the certification's own epistemic rule exists to prevent.

**Recommendation for the eventual implementation phase (not authorized now):** consolidate to a single commit class before or as part of introducing the capability check, rather than duplicating the check into two parallel implementations — duplication is how this gap was able to hide in one of the two classes in the first place. This is a design recommendation, not a decision made unilaterally here.

## 2B. Sequence binding, crash, replay, and atomicity semantics

State-transition contract, reconciled against the actual existing code (both classes share this structure; described once, applies to both):

```
AUTHORIZE  →  RESERVE/VALIDATE SEQUENCE  →  COMMIT ATOMICALLY  →  CHAIN UPDATE  →  RECEIPT
```

Mapped onto real code (`AtomicCRAMCommitter.commit()` / `CRAMWriter.commit()`, both read this way from the actual source):

1. **When `_seq` is allocated:** in-memory, `self._seq += 1`, as the *first* statement in `commit()` — before any I/O, before the record dict is even built. (Note: `CRAMWriter` does not maintain a `_seq` counter at all in the current code — it only tracks `_prev_hash`; sequence numbering as such is `AtomicCRAMCommitter`-specific today. This is itself a reconciliation gap: the proposed capability's `mint_seq` binding (Part 1 §3-4) has no existing `_seq` counterpart to bind against in `CRAMWriter`. **Recorded as UNRESOLVED** — the capability design's sequence-binding mechanism must be re-specified once 2A's consolidation question is settled, since it currently only maps cleanly onto one of the two classes.)
2. **When the capability would be minted relative to `_seq`:** proposed to happen *before* step 1's increment is trusted — i.e., mint against `self._seq + 1` computed at call time, matching Part 1 §3's design. Not yet reconciled with `CRAMWriter`'s absence of `_seq` (see above).
3. **When the capability would be validated:** proposed as the very first action inside `commit()`, before the PASS-only check even runs (Part 1 §4, steps 1-5) — i.e., authorization gates entry to the function body, before any existing logic executes.
4. **When artifact content is validated:** unchanged from today — the existing PASS-only check (Part 1 §4 step 3 folds this in).
5. **When the artifact write occurs:** unchanged — `tmp` file open, `json.dump`/`os.write`, `f.flush()`, `os.fsync(f.fileno())`, all in-memory-to-tmp-file, nothing durable yet.
6. **When the atomic commit becomes durable:** at `os.replace(tmp, final)` — this is the actual durability point for the payload (POSIX rename is atomic within a filesystem; the preceding `fsync` on the tmp file's fd ensures its content is durable *before* the rename makes it visible under the final name).
7. **When "ChainIndex" is updated:** **there is no separate ChainIndex structure in the current codebase** (confirmed by exhaustive repo-wide search this session and in the original certification pass — zero hits for `ChainIndex` under any name, anywhere in `ph6/`). The "chain" that exists is the `prev_cram_hash`/`cram_hash` linkage embedded *directly inside each committed record*, written as part of the *same* atomic payload write in step 5-6 — there is no separate chain-update step or window. This is a **reconciliation, not a gap**: the design's abstract "CHAIN UPDATE" phase collapses into "COMMIT ATOMICALLY" for this codebase's actual architecture. Stated explicitly rather than inventing a ChainIndex that doesn't exist to make the abstract model fit.
8. **When the sequence advances:** the in-memory `self._prev_hash = record["cram_hash"]` assignment happens *after* the durable write (both renames + dir fsync) completes, at the very end of `commit()`. (`AtomicCRAMCommitter`'s `self._seq` was already incremented in-memory at step 1, before the write — see the crash analysis below for why this ordering is still safe.)
9. **When the receipt is generated:** **no per-commit "receipt" object exists at this layer in either class.** `commit()` returns the `record` dict to its caller; nothing writes a separate receipt file per commit. Receipt-like artifacts (`PH6_4_PASS_SYSTEM_REPORT.md`, `tok_soso_isolation_receipt.json`) are generated later, by higher-level tools, after a batch of commits — not 1:1 with each individual commit. **Recorded as UNRESOLVED**: the abstract model's "RECEIPT" phase has no exact existing analog at the commit-boundary layer; the design must either treat the returned `record` as the de facto receipt, or explicitly scope "RECEIPT" out of this control's boundary and leave it to the existing higher-level reporting tools, which are unaffected by this proposal either way.
10. **Recoverable state after each crash point:**

| Crash point | Recoverable state | Evidence |
|---|---|---|
| Before `_seq`/sequence reservation | Nothing to recover — no side effect occurred. | By construction (in-memory only, first statement). |
| After in-memory `_seq += 1`, before any write | The increment is lost with the process. On restart, `_load_last_seq()` recomputes from `len(cram_dir.glob("cram_*.json"))` — the same count as before the crash (no file was written) — so the *same* sequence number is issued again on the next attempt. No gap, no duplicate, self-healing by recomputation from disk state rather than trusting the dead in-memory counter. | `cram_pu_atomic_commit.py::_load_last_seq` (read this session). |
| During tmp payload write (before `os.replace`) | An orphaned `filename.tmp` is left on disk. `_load_last_seq()`/`_load_last_hash()` glob only `cram_*.json` (not `*.tmp`), so the orphan is invisible to sequence/chain recovery — again self-healing for chain purposes. **Existing gap, not introduced by this proposal:** nothing in the traced code actively cleans up orphaned `.tmp` files; `check_torn_files()` in `crash_replay.py` *detects* them (`rglob("*.tmp")`) but I found no corresponding cleanup/repair call site in this session's trace. Flagged as a pre-existing condition this design neither fixes nor worsens. |
| After payload durable (`os.replace` for `final` succeeded), before marker write/replace | A `cram_*.json` file exists **without** its `.blake2b` marker — an intermediate state explicitly anticipated by CLAUDE.md hard rule 8 ("`.blake2b` marker on PASS path: written LAST"). `check_cram_integrity()` in `crash_replay.py` verifies `cram_hash`/`prev_cram_hash` linkage across payload files, but **I did not find marker-presence verification inside `check_cram_integrity()` itself** — marker-order logic exists only inside the writer classes' own write sequence, not as an independent post-hoc detector. **Recorded as UNRESOLVED**: whether an existing tool detects "payload present, marker absent" after the fact (as opposed to preventing it during a live write) could not be confirmed from the code traced this session; this must be established, not assumed, before implementation claims this state is detectable. |
| During marker tmp write/replace | Same class of orphaned `.tmp` as above, for the marker file this time. Same self-healing-for-chain-purposes property (sequence/chain recovery ignores `.tmp` files); same pre-existing gap regarding cleanup. |
| After marker durable, before parent-directory `fsync` | Existing code already closes this window deliberately — a single `os.fsync(dir_fd)` after *both* renames is already present in both classes' current implementations. Nothing for this design to add here; noted for completeness of the crash-point enumeration, not as a finding. |
| After full durability, before in-memory chain-state (`self._prev_hash`) update | The in-memory value is lost with the process, but it is reconstructed correctly on restart by `_load_last_hash()`, which reads the *last file on disk* (already durable) — not the dead in-memory value. No corruption. |
| After receipt generation (N/A at this layer per item 9) | Not applicable at the commit-boundary layer — see item 9. |
| Replay after any of the above | The existing replay/crash-recovery tooling (`crash_replay.py`'s `CrashReplayValidator`, `check_torn_files`, `check_cram_integrity`, and `cram_pu/tools/cram_pu_replay_verify.py`) already operates by re-deriving state from durable files on disk, never from in-memory counters — this property is **preserved, not altered**, by the proposed capability check, since the capability check only gates *entry* to `commit()` and does not touch the read/recovery paths at all. |
| Duplicate capability use | Denied by `mint_seq` binding (Part 1 §4 step 4) for `AtomicCRAMCommitter` — **unresolved for `CRAMWriter`** per item 1 above, since it has no `_seq` counter to bind against today. |
| Stale capability use | Same as duplicate — covered for one class, unresolved for the other pending 2A's consolidation decision. |
| Sequence collision / concurrent commit attempts | **Not established from the repository.** I found no locking, no `multiprocessing`/`threading` synchronization primitive, and no evidence either class is ever called concurrently from more than one thread/process in the traced code — every call site traced this session is single-threaded, sequential. Whether concurrent invocation is a scenario PH6 needs to defend against at all (versus being excluded by the deployment model) **could not be established from existing contracts** and is recorded here as UNRESOLVED rather than assumed either way. If concurrent invocation is possible in some deployment this session did not trace, the current code (both classes) has no race protection today, independent of this proposal, and the proposed capability mechanism would not introduce one either (minting and validating are not shown to be atomic with respect to `_seq` reservation under concurrent callers). |

**Conclusion for 2B:** the proposed mechanism does not weaken any *existing* atomic-write, chain, or crash-recovery guarantee — it adds a precondition check *before* the existing sequence, does not alter steps 4 onward. However, it is **not yet fully specified** for `CRAMWriter` (no `_seq` to bind to) and depends on an unresolved consolidation decision (2A) before it can be implemented identically across both commit classes. HRG9 itself is unaffected structurally (HRG9-001 remains a separate, UNRESOLVED certification finding for unrelated reasons — see the frozen baseline; this design does not touch HRG9's own algorithm or evidence).

## 2C. Anti-backdoor requirement — `ph6_internal_test.py` and all future test code

This design **explicitly prohibits**, for the eventual implementation phase (none of this is implemented now):

- `if TEST_MODE:` or any equivalent conditional bypass
- a separate `_internal_test_commit()` or similarly-named alternate entry point
- test-only capability constructors that produce a capability without going through the real minting closure
- any authority-check bypass function, however named
- environment-variable overrides of the authorization decision
- monkey-patching the authorization check in test setup/fixtures
- alternate "test commit" APIs that skip validation
- fixtures that disable or circumvent the production authorization boundary
- hidden test credentials, or any static/well-known secret standing in for the process-generated one

**Requirement:** `ph6_internal_test.py` (and `test_canonical_schemas.py`, `test_vrc.py`, `test_closure_patches.py`, and any other test currently constructing a committer directly) must, once implemented, exercise the **real** legitimate chain: mint (inside the real minting closure, triggered by the real call path) → validate (inside the real `commit()`) → commit (the real, unmodified write sequence). No shortcut path may exist in production code that a determined caller could also reach — a test-only bypass is, by construction, also a production-reachable bypass, since Python does not distinguish "test code" from "production code" at the import-system level. This principle is stated here as a binding requirement for the implementation phase; it changes nothing in this pass, since no code is being written now.

## 2D. Authority provenance schema — formal field classification

Expanding Part 1 §3's capability table with the explicit classification the review requires:

| Field | Semantic meaning | Authority significance | Authenticated? | Bound to this commit? | Replay-sensitive? | Attacker-controlled? | Classification |
|---|---|---|---|---|---|---|---|
| `capability_version` (was `schema`) | Format identifier (`ph6.lane1_capability.v1`) | None on its own | No (not covered by MAC unless included in the signed payload — **must be included in the MAC input, corrected from Part 1's original table which listed it but should be made explicit here**) | Indirectly (via MAC, once included) | No | Yes, trivially — attacker can claim any version string | **IDENTITY** (format self-description) — never AUTHORITY by itself |
| `authority_domain = LANE_1` | Declares which lane this capability claims to authorize | **Would be AUTHORITY-bearing only because the MAC covers it** — the string itself is meaningless without a valid MAC | Yes, via MAC | Yes | No (constant) | Yes (attacker can write this string into a forged object) | **PROVENANCE**, elevated to **AUTHORITY** only in combination with a verified MAC — never trust this field in isolation |
| `packet_id` | Which packet this authorizes | None on its own | Yes, via MAC | Yes (exact match required, Part 1 §4 step 2) | Yes (binding prevents reuse against a different packet) | Yes (attacker can write any value) | **CONTENT/PROVENANCE**, authority only via MAC |
| `input_hash` | Which payload content this authorizes | None on its own | Yes, via MAC | Yes | Yes | Yes | **CONTENT**, authority only via MAC |
| `commit_sequence` (was `mint_seq`) | Which position in the commit chain this authorizes | None on its own | Yes, via MAC | Yes (exact match to live `_seq + 1`, Part 1 §4 step 4) | **Yes — this is the primary replay defense** | Yes (attacker can write any integer) | **SEQUENCE**, authority only via MAC + live-state comparison |
| `issued_for` (new, requested by review — not in Part 1's original table) | Declares the specific call site/component this was minted for, for audit/diagnostic purposes | None — explicitly NOT a security check; see below | Optional — may be included in MAC for tamper-evidence, but even if authenticated, **must never be used as the authorization decision itself** | Diagnostic only | No | Yes | **PROVENANCE ONLY** — this field exists so a human reviewing logs/receipts can see what the capability was minted for; it must not be read by `commit()`'s own logic as a basis for allow/deny, which would reintroduce exactly the self-attestation pattern §3 forbids (a field merely *saying* "cram_pu_live" is not proof of anything, MAC or not — the MAC proves the *fields as a whole* weren't altered post-mint, it does not prove `issued_for`'s claim was true when set, since the minting closure itself does not currently verify its own caller either. **Recorded as UNRESOLVED**: the minting closure's own caller-legitimacy is established only by 2A (it's reachable only from within `commit()`'s real call path today) — `issued_for` cannot add authority beyond that. |
| `capability_mac` (was `mac`) | Proof of authenticity of every other field in this table | **This is the entire authority of the capability — every other field is inert without it** | N/A (it *is* the authentication mechanism) | N/A | N/A | No — cannot be forged without the closure-held secret (bounded per Part 1's isolation-boundary characterization, and 2A above) | **AUTHENTICATION** |

**Summary distinction required by the review, stated explicitly:** every field above except `capability_mac` is **provenance or content description** — informative, not authoritative. `capability_mac` is the **sole source of authority** in this design; it is what converts an otherwise-inert, fully attacker-forgeable set of claims into something `commit()` can trust, and only because it cannot be produced without access the design argues (with stated limits, §2 isolation-boundary language) Lane-2 code does not have.

## 2E. Explicit capability-substitution denials

Stated directly, for adversarial-test derivation during the (not-yet-authorized) implementation phase:

- **TOK ≠ Lane-1 Capability.** A TOK record's schema is never `ph6.lane1_capability.v1`; `commit()`'s proposed signature does not accept a TOK object as its `capability` argument. Type/schema mismatch, not a value-level check that could be fooled by a well-formed-looking TOK.
- **SoSo artifact ≠ Lane-1 Capability.** Same reasoning — `SwarmPacket`'s schema and shape are structurally different; no `capability_mac` field exists on a `SwarmPacket`, and even if one were added by an attacker, it could not be produced against the real Lane-1 secret.
- **AI provenance ≠ Lane-1 Capability.** Anything `research_agent` produces has no path to the minting closure (confirmed absence of any `cram_pu` import in `research_agent/`, this session's earlier finding, unchanged by this review).
- **PSEUDO result ≠ Lane-1 Capability.** A `PSEUDO-M`/`PSEUDO-A` measurement or verdict is *input* to a legitimate mint (the verdict being committed), not itself a capability — the verdict dict and the capability object are proposed as two separate, independently-required arguments to `commit()` (Part 1 §4), so possessing a valid PSEUDO-A verdict alone is insufficient without also holding a matching, MAC-valid capability.
- **MRAM-S artifact ≠ Lane-1 Capability.** MRAM-S is a write *destination*, not a capability source or holder — nothing about an artifact's presence in MRAM-S confers minting rights, and no code path reads MRAM-S to construct a capability.
- **Ordinary metadata ≠ Lane-1 Capability.** Any freeform dict key (`source`, `issued_by`, etc. — the exact fields used in the original AI_ADVISORY-003 adversarial test) carries no authority under this design; only `capability_mac` does, and metadata fields are never substituted for it.
- **Version strings ≠ Lane-1 Capability.** `ssmt_version` and `capability_version` are both plain strings with no cryptographic binding on their own — neither is ever treated as proof of authority; see 2D's field-by-field table.
- **Caller-supplied authority labels ≠ Lane-1 Capability.** This is the exact pattern Part 1 §3 already forbids ("caller says LANE_1 -> system trusts caller") and remains forbidden.
- **Serialized provenance claims ≠ Lane-1 Capability.** A JSON blob that merely *describes* a legitimate-sounding provenance chain (e.g., a forged `issued_for` history) is not authority — only a verified `capability_mac` is, per 2D.

Each of the above is intended to become one negative regression test at implementation time (per Part 1 §8 and this section) — not implemented now.

---

# PART 3 — FORMAL DESIGN SELF-REVIEW

## 3.1 Crash / Replay Semantics

**STATUS:** UNRESOLVED
**EVIDENCE:** Section 2B traces every crash point against the actual code for `AtomicCRAMCommitter`. Existing atomicity (tmp-write-fsync-rename-fsync), the embedded (not separate) chain-hash mechanism, and existing recovery tooling (`check_torn_files`, `check_cram_integrity`) are all preserved by the proposed design *for that one class*. However: (a) `CRAMWriter` — the actually-used production path — has no `_seq` counter for the proposed `commit_sequence` binding to attach to, so replay/duplicate-use defense is unspecified for the class that matters most in practice; (b) whether any existing tool detects "payload present, marker absent" post-hoc (as opposed to preventing it live) could not be confirmed from the code traced; (c) concurrent/racing commit attempts are not addressed by either existing code or this proposal, and whether that scenario is even in-model for PH6 could not be established from existing contracts.
**DESIGN CONSEQUENCE:** The design cannot yet claim "preserves all existing atomicity/replay/chain guarantees" as a blanket statement — it can only claim this for `AtomicCRAMCommitter` specifically, which is not the class the certification's own PSEUDO-family evidence (C10-C13) actually exercises.
**IMPLEMENTATION REQUIREMENT:** Before implementation, resolve 2A (consolidate commit classes, or explicitly design the sequence-binding mechanism for `CRAMWriter`'s actual state — it would need a `_seq`-equivalent added, which is itself a source change requiring its own review). Confirm or build the missing marker-presence-after-payload detector. Make an explicit, documented decision on whether concurrent invocation is in-scope; if it is, the capability mechanism as specified does not yet address it and would need a reservation step that is atomic with respect to `_seq`/`commit_sequence` allocation (e.g., a compare-and-swap style check), not yet designed.

## 3.2 Capability Substitution Attacks

**STATUS:** PASS
**EVIDENCE:** 2D and 2E enumerate every existing PH6 artifact type this session has directly examined (TOK, SoSo/SwarmPacket, AI/research_agent output, PSEUDO result, MRAM-S artifact, plain metadata dict, version strings, caller-declared labels) and, for each, identify the specific structural reason (schema mismatch, missing MAC field, no path to the minting secret) it cannot satisfy the proposed authorization boundary. None of these object types share `ph6.lane1_capability.v1`'s schema or could produce a valid `capability_mac` without the closure-held secret.
**DESIGN CONSEQUENCE:** No accidental satisfaction of the boundary by an existing artifact type is identified. This status is scoped to "no *accidental* substitution" — it does not claim the mechanism is unbreakable (see 3.1's residual risks and Part 1 §2's stated isolation-boundary limits, which are a *deliberate*-attack question, not an *accidental*-substitution one).
**IMPLEMENTATION REQUIREMENT:** Each denial in 2E becomes an explicit negative regression test (Part 1 §8) at implementation time — this PASS is a design-level claim, not yet execution-backed, and must not be treated as certification evidence (design ≠ implementation ≠ certification, per the evidence-discipline rule).

## 3.3 Sequence Race Conditions

**STATUS:** FAIL
**EVIDENCE:** 2B's crash-point table explicitly states: "I found no locking, no `multiprocessing`/`threading` synchronization primitive, and no evidence either class is ever called concurrently... Whether concurrent invocation is a scenario PH6 needs to defend against at all... could not be established from existing contracts." Neither the existing code nor this proposal has any defense against a genuinely concurrent/racing commit attempt (two threads/processes both reading `self._seq`, both incrementing, both attempting to mint/write against overlapping sequence numbers).
**DESIGN CONSEQUENCE:** This is marked FAIL rather than UNRESOLVED because it is not merely undetermined — it is a **known, unaddressed gap** in both the existing code and the proposed design, whenever concurrent invocation occurs. If PH6's deployment model genuinely never calls these classes concurrently (plausible, given every traced call site is sequential), this FAIL is inert in practice — but the design cannot claim to have solved it, and marking it PASS or UNRESOLVED would understate a real, identified weakness.
**DESIGN CONSEQUENCE (implementation-blocking):** the capability mechanism as currently specified does not add race protection — minting reads `self._seq`/`self._prev_hash` and validating compares against a possibly-stale live value, with no atomic reservation step. Two racing callers could both mint valid-looking capabilities against the same `_seq + 1` before either commits.
**IMPLEMENTATION REQUIREMENT:** Either (a) establish from operator/architecture knowledge that concurrent invocation is out of PH6's deployment model entirely (a documented assumption, not a code fix), or (b) add an explicit atomic reservation primitive (e.g., a lock around mint+validate+commit as one critical section) before implementation — not designed here, since it wasn't part of the original proposal's scope and needs its own review once (a) is answered.

## 3.4 Authority Provenance

**STATUS:** PASS, with one bounded caveat
**EVIDENCE:** 2D's field-by-field table classifies every proposed capability field as IDENTITY, PROVENANCE, CONTENT, SEQUENCE, or AUTHENTICATION, and states explicitly that only `capability_mac` (AUTHENTICATION) constitutes authority — every other field, including `authority_domain = LANE_1` itself, is inert without it. This directly satisfies "unambiguously identifies who/what is authorized... without confusing provenance metadata with actual authority," which was the original design's central claim (Part 1 §3) and is now formally categorized rather than asserted narratively.
**DESIGN CONSEQUENCE:** The design correctly avoids the trap of treating any self-declared field as authority. The bounded caveat: the capability proves *the fields as signed weren't altered post-mint* and *the minter held the secret* — it does not, and cannot, independently prove the minting closure's own invocation was itself legitimate beyond what 2A/3.1 already establish (i.e., authority is only as good as "only reachable from within `commit()`'s real call chain today," which is a call-graph property, not a cryptographic one, for the *minting* step specifically — the MAC protects the capability's integrity after minting, not the legitimacy of the mint event itself against an attacker who has otherwise gained the ability to trigger minting).
**IMPLEMENTATION REQUIREMENT:** None beyond what 3.1/3.3 already require — this dimension is otherwise ready to carry into implementation once those two are resolved.

---

# PART 4 — CONSOLIDATED UNRESOLVED DESIGN DEPENDENCIES

1. **(2A)** Two separate commit implementations (`AtomicCRAMCommitter`, `CRAMWriter`) exist; the design must be extended to cover both, or a consolidation decision made, before implementation.
2. **(2B item 1)** `CRAMWriter` has no `_seq` counter — `commit_sequence` binding is unspecified for the class production actually uses.
3. **(2B item 9)** No per-commit "receipt" object exists at this layer in either class — the abstract state machine's RECEIPT phase has no exact analog; must be explicitly scoped in or out.
4. **(2B crash table, row 3)** Whether any existing tool detects "payload durable, marker absent" post-hoc could not be confirmed from code traced this session.
5. **(3.3)** No race/concurrency protection exists in current code or this proposal; whether concurrent invocation is in-model for PH6 is undetermined from existing contracts.
6. **(2D, `issued_for`)** A minting closure's own caller-legitimacy is currently established only by call-graph reachability (2A), not cryptographically — this is a property of the *minting* step, distinct from the *validation* step's cryptographic guarantee, and should be stated plainly to whoever reviews this next rather than left implicit.

None of these are guessed at or resolved by invention in this pass, per the evidence-discipline rule (§8 of the operator's remediation spec, still binding here).

---

---

# PART 5 — PHASE 2 EVIDENCE RESOLUTION (no architecture invented, no source modified)

## 5A. Scope

**This investigation resolves:** whether the repository contains sufficient authoritative evidence to define an *existing* Lane-1 authorization/capability boundary — i.e., is there something already there to enforce, reuse, or reconcile with.

**This investigation explicitly does NOT resolve:** what PH6 *should* implement. No capability object, minting authority, signing protocol, caller-identity mechanism, registry, schema, golden vector, receipt field, concurrency semantic, or crash guarantee was invented, designed further, or implemented in this pass. Where evidence is absent, the conclusion is `UNRESOLVED`, not a proposed fix.

## 5B. Existing boundary — both commit paths, traced

Confirmed unchanged from the prior design-hardening pass, now traced further:

**Path 1 (the one AI_ADVISORY-003's adversarial test exercised):**
`cram_pu/tools/cram_pu_atomic_commit.py :: AtomicCRAMCommitter.commit()` — reached via `commit_pass_verdicts()` in the same file, or directly (as the adversarial test did). Production callers: only `cram_pu/tests/test_canonical_schemas.py` and its own CLI (`if __name__ == "__main__"`).

**Path 2 (the one production actually uses):**
`cram_pu/crash_replay.py :: CRAMWriter.commit()`. Full upstream chain traced this pass:
```
DepartureLogger.log()  →  ArrivalLogger.log()  →  VerdictLogger.log()  →  CRAMWriter.commit()
(cram_pu/departure_logger.py)  (cram_pu/arrival_logger.py)  (cram_pu/verdict_logger.py)  (cram_pu/crash_replay.py)
```
Each stage (`DepartureLogger`, `ArrivalLogger`, `VerdictLogger`) appends to its own JSONL log (`_append_jsonl`) and computes its own BLAKE2b-256 hash of its stage's content — none of these three stages perform any caller-identity or authorization check on their own inputs either; they are content-hashing/logging wrappers, not gates. `VerdictLogger` contains the actual `_pseudo_verdict()` adjudication logic (PSEUDO-A's real decision function) before handing the verdict to `CRAMWriter.commit()`.

**`EvidencePacket` / `ChainIndex` — re-confirmed absent as implementations, present only as prose:** a fresh, targeted search this pass found the terms only inside comments and docstrings (`tok/validators.py:9`, `tok/audit_writer.py:10`, `cram_pu/tools/run_c10_c11_c12_absorption_campaigns.py:138`, `governance/ph6_governor.py:223,231`) — every occurrence is a *reference to a forbidden-mutation target* ("No EvidencePacket mutation") or a *status-report label*, never a class, schema, or data structure. This is a clean **DECLARED, not OBSERVED, not VALIDATED** case (§5D).

## 5C. Evidence Matrix

| Dependency | Status | Evidence | Validation | Remaining ambiguity |
|---|---|---|---|---|
| **A — Mint legitimacy** | **UNRESOLVED** | Exhaustive search (three passes across two sessions: broad term search, function/class/decorator pattern search, this pass's re-confirmation) for any issuer/minting/authorization component: zero hits anywhere in `ph6/`. `PH6_SOURCE/SCHEMAS/ph6_ai_authority_request_v1.schema.json` and `ph6_authority_response_v1.schema.json` exist as *contract text* but have zero implementing code (confirmed, `AI_ADVISORY-001`). | No executable mint-legitimacy mechanism exists to validate. | Whether an issuer concept is intended to exist (per the schemas) but was never built, versus never intended to be a runtime mechanism at all, cannot be determined from repository evidence alone. |
| **B — Capability integrity** | **UNRESOLVED** | No authority-bearing capability/token/object of any kind exists anywhere in `ph6/` to trace representation, serialization, hashing, or validation for. `authority_hash` (see 5C detail below) is a *content* hash, not a capability. | N/A — nothing to validate. | The question "can integrity be proven" presupposes an object; none exists, so the question cannot be answered in the affirmative or negative — it is moot, which is itself the finding. |
| **C — Receipt/provenance binding** | **UNRESOLVED** (partially characterized) | `authority_hash` traced precisely: in `cram_pu/ingest_receipt_logger.py:11,18,125,140`, it is defined as "BLAKE2b-256 of the authoritative Lane-1 content... the CRAM commit hash for ACCEPTED" records. `cram_pu/vrc.py:136-143` verifies this field *matches* the corresponding CRAM file's own `cram_hash` — a **content-integrity check** (does the receipt accurately describe a commit that exists), not an authorization check. Separately, `ssmt/audit_log.py:47` uses the *same field name* `"authority_hash"` for `canon_hash(packet_dict)` on a Lane-2 advisory `SwarmPacket` — a naming collision worth flagging: the field name implies authority in both places, but only carries any Lane-1 meaning in `ingest_receipt_logger.py`'s context. `event_seq`/`event_hash`/`prev_event_hash` (`ssmt/hash_chain.py::chain_event`, `ssmt/audit_log.py`, `ssmt/forensic_closure.py`, `cram_pu/vrc.py`) establish event identity and predecessor linkage (tamper-evidence chaining) for whichever log they're written into — they prove *an entry wasn't altered after being chained*, not *who was authorized to add it*. | `vrc.py`'s Step B check is executable and was traced to real code (not merely documented). | None of these fields establish capability identity, capability integrity (of a Lane-1 authorization object — none exists), or issuer legitimacy. They establish content/chain integrity only. This is a precise, evidence-backed negative finding, not an assumption. |
| **D — Both commit paths** | **RESOLVED** (as to *existence and structure* of both paths; **UNRESOLVED** as to whether either has authorization) | Both paths fully traced this pass — see 5B. Both share the identical structural defect: a PASS-only content check, zero caller-identity/authorization check. | Both classes' source read directly, line ranges cited in 5B and in Part 2A. | Whether the two paths were intended to be one (later diverged) or are deliberately parallel could not be established from repository evidence — no comment, changelog, or doc addresses the duplication. |
| **E — Crash recovery / atomicity** | **RESOLVED** | `cram_pu/tests/test_crash_replay.py` contains 9 test classes (`TestTornFiles`, `TestContinuity`, `TestPassLoss`, `TestDropShedding`, `TestAdvisoryIsolation`, `TestCRAMIntegrity`, `TestRSYNCHealth`, `TestCRAMWriter`, `TestCrashReplayValidator`) — part of the 114/114 currently-passing `cram_pu/tests/` suite (executed this session, prior pass). `TestCRAMWriter` specifically targets **Path 2**, the class production actually uses. `ph6_internal_test.py`'s `ATOMIC_WRITE_CONTRACT` check (executed this session: PASS) independently confirms write+overwrite byte-exactness. | Executed, not merely documented: `python3 -m pytest cram_pu/tests/test_crash_replay.py` (prior session pass, part of the 242-test full-suite run). | Atomicity/crash-recovery for the *content* of a commit is validated. This says nothing about authorization — a crash-safe write of an *unauthorized* commit is exactly as crash-safe as an authorized one; the two properties are orthogonal, and E resolving RESOLVED does not touch A/B/C's UNRESOLVED status. |
| **F — Concurrency** | **UNRESOLVED** (for the actual commit boundary) | Zero locks, mutexes, `threading`, `multiprocessing`, or file-locking primitives found anywhere in `cram_pu/` (searched this pass). A real concurrency test **does exist**, but for a different boundary: `ssmt/failure_injection.py::concurrent_writes()` (uses `threading.Lock`/`threading.Barrier`/`threading.Thread`) and `ssmt/tests/test_failure_injection.py::test_fi04_concurrent_runs_*` test the **SSMT/SoSo advisory scheduler**, not the CRAM-A commit boundary. No concurrent-commit test exists for `AtomicCRAMCommitter` or `CRAMWriter`. | `FI-SSMT-04` is executed, real, and part of the passing suite — but scoped to a different component. | Whether the Lane-1 commit boundary is ever invoked concurrently in any real deployment could not be established from repository evidence (every traced call site is sequential); if it is, no protection exists today, independent of this proposal. |

## 5D. Declared vs Observed vs Validated

- **DECLARED only** (documentation/prose, no executable correlate found): `EvidencePacket`, `ChainIndex` as named concepts; `PH6_SOURCE/SCHEMAS/ph6_ai_authority_request_v1.schema.json`/`ph6_authority_response_v1.schema.json` as an authorization *contract* with no implementation; the four corpus documents named in the operating prompt (`BOOK I — OPERATIONAL SOURCE CONSTITUTION.pdf`, `00_PH6_CONSTITUTION_INTERPRETIVE_CONTROL.pdf`, `BOOK IV — CERTIFICATION PROOF PACK.pdf`, `PH6_CONSOLIDATED_CANON.docx`) — **searched for by exact and partial filename across all of `PH6_SOURCE`; none exist in this repository.** The only filename matches found were unrelated documents that happen to share the word "CONSTITUTION" (`NODE_ASSIGNMENTS/FLEET_CONSTITUTION_v1.md`, `03_SCIENTIFIC_INSTRUMENT/FAST_CRAM_CONSTITUTIONAL_MODEL.md`, `03_SCIENTIFIC_INSTRUMENT/CONSTITUTIONAL_ENGINEERING_PRINCIPLES.md`) — these were not substituted for the requested documents or treated as answering the corpus-reconciliation requirement; the requested documents are simply **absent from this repository**, stated plainly rather than worked around.
- **OBSERVED** (executable behavior traced and read, not yet independently re-verified by a fresh run in this pass): the exact structure of both commit paths (5B); the `authority_hash`/`event_seq` field semantics (5C); the naming collision on `authority_hash` between Lane-1 and Lane-2 contexts.
- **VALIDATED** (reproducible executed test or authoritative invariant, confirmed by actual execution either this session or the immediately prior one, not merely read): `test_crash_replay.py`'s 9 test classes (114/114 `cram_pu/tests/` passing, executed this session); `ph6_internal_test.py`'s `ATOMIC_WRITE_CONTRACT` (executed this session, PASS); `ssmt/tests/test_failure_injection.py::test_fi04_*` (part of the 52/52 `ssmt/tests/` passing, executed this session) for SSMT-scheduler concurrency specifically, not CRAM commit concurrency.

## 5E. Existing certification findings — confirmed, not reweighted

| Finding | Confirmed / Revised | Evidence |
|---|---|---|
| `AI_ADVISORY-003` | **CONFIRMED**, evidence traced to Path 1 (`AtomicCRAMCommitter`) specifically. The finding is not weakened by Path 2's existence — if anything, 5B's tracing shows the *same* defect exists in the *more heavily used* path (`CRAMWriter`), which strengthens rather than narrows the finding's real-world relevance, without this Phase-2 pass rerunning any remediation code to re-demonstrate it (not permitted this phase). | Original adversarial test (prior session): direct call to `AtomicCRAMCommitter.commit()` with AI-attributed provenance succeeded, stamped `authority: LANE_1`. |
| `SOSO-SPOOF-001` | **CONFIRMED**, unchanged. `ssmt/audit_writer.py::write_packet` performs no version check; `ssmt/replay_validator.py` source contains zero references to `ssmt_version` (confirmed again this pass, no new contradicting evidence found). | Original adversarial test (prior session): spoofed `ssmt_version="99.9.9-SPOOFED"` written and accepted with no rejection/detection/recording. |
| `PSEUDO-SEAM-001` | **CONFIRMED**, and now more precisely located: the "seam" is the same Path 1/Path 2 commit boundary that `VerdictLogger`'s `_pseudo_verdict()` (the real PSEUDO-A adjudication) hands off to — the seam is not in PSEUDO-A's own decision logic (which is clean, per `PSEUDO-A-001` PASS evidence), it is entirely in the commit function PSEUDO-A's output is passed to next, which is identical to `AI_ADVISORY-003`'s root cause viewed from the other calling direction. | Prior session's adversarial test plus this pass's confirmation that `VerdictLogger → CRAMWriter.commit()` is the real call chain, with no authorization check anywhere in it. |

The common conclusion the certification evidence indicates — `Lane-2/AI → Lane-1 commit API → accepted` — is **confirmed by this pass's repository tracing**, not weakened (the current call graph not exercising the path in normal production does not change that the function itself, on both paths, accepts the call when it is made) and not strengthened beyond what was demonstrated (no new adversarial execution was run this phase; this is a static-evidence confirmation of a previously-executed finding, not a new data point).

## 5F. Architectural gaps (evidence-established only — no proposed fixes here)

1. No authorization/capability/minting mechanism exists anywhere in `ph6/` (A, B).
2. Two structurally duplicate commit implementations exist, both equally unauthorized (D).
3. `authority_hash` and `event_hash`/`event_seq` chains provide content/tamper integrity, not authorization provenance — and the field name `authority_hash` is reused across Lane-1 and Lane-2 contexts with different actual meaning, which is itself a documentation-hygiene gap independent of the authorization question (C).
4. No concurrency protection exists for either commit path; a concurrency test exists but for an unrelated component (F).
5. The four corpus documents the operating prompt named for canonical reconciliation do not exist in this repository (5D).

## 5G. Decisions requiring operator authority

1. Whether to consolidate the two commit implementations (Path 1, Path 2) before any authorization mechanism is designed further, or design for both independently.
2. Whether an authorization/capability mechanism should be built at all given none currently exists (this is the design already proposed in Parts 1-2, still unimplemented, still requiring separate authorization to build).
3. Whether the `authority_hash` naming collision between `ingest_receipt_logger.py` and `ssmt/audit_log.py` should be resolved (rename one), independent of the authorization-mechanism question.
4. Whether concurrent invocation of the commit boundary is a scenario PH6's deployment model needs to defend against at all.
5. Where to locate/obtain the four named corpus documents, if they exist outside this repository and should inform this design, or whether their absence here means they are not authoritative for this repository's certification.

## 5H. Non-decisions — explicitly not made this phase

- No capability token, minting authority, signing protocol, or caller-identity mechanism was designed further or implemented.
- No registry, schema, or golden vector was created.
- No receipt field was added to any existing receipt mechanism.
- No concurrency semantics were defined or implemented.
- No crash guarantee was added or altered.
- `AtomicCRAMCommitter.commit()`, `CRAMWriter.commit()`, PSEUDO, SoSo, TOK, CRAM, MRAM-S: none modified.
- No certification result was changed to remove or soften a blocker.
- The `authority_hash` naming collision (5F item 3) was identified, not resolved.

```json
{"proposed_by":"claude-code-lane2","proposed_at_utc":"2026-09-05T14:20:00Z","api_call_log_ref":"session_01Er4uEgGZE7jhVVrQcnSh6S","ratified_by":null,"revision":"phase-2-evidence-resolution"}
```

---

# PART 6 — PHASE 2A: LANE-1 COMMIT AUTHORIZATION SEMANTICS CONTRACT

**Mode: DESIGN CONTRACT RESOLUTION ONLY. Implementation FROZEN. Certification FROZEN. No mechanism selected. No source modified.**

## 6.1 Purpose

Define the *proposition* the Lane-1 commit boundary must be able to prove before permitting an irreversible commit — not the mechanism that proves it. Mechanism selection is explicitly out of scope for this gate (§6.15 only enumerates requirements a mechanism would need to satisfy; it does not choose one).

## 6.2 Governing invariant

**DESIGN REQUIREMENT DERIVED FROM ACCEPTED ARCHITECTURE** (accepted per the operator's Phase 2A framing, not independently re-derived here):

```
PSEUDO-A VERDICT AUTHORITY  ≠  COMMIT EXECUTION AUTHORIZATION  ≠  PHYSICAL CRAM PERSISTENCE
```

This is stated as accepted architecture per §1 of the operating prompt, not as something this pass proves from repository evidence — it is the frame this contract works within.

## 6.3 Authority proposition

**UNRESOLVED as a canon-defined proposition; RESOLVED as a derived minimum, stated explicitly as derived, not discovered.**

No canon-tier document (`PH6_SOURCE/CANON/`, `PH6_SOURCE/GOVERNANCE/`) states an explicit proposition for what must be true before a Lane-1 commit is authorized. Searched this pass: zero hits for "commit authorization," "execution identity," "trust boundary," "authorization boundary," or "single-writer" in either tree. The only "authoriz*" hits in `GOVERNANCE/` are incidental — status-report conclusions ("no unauthorized closed states," `whole_system_architect_search_summary.md:12`) or scanning-infrastructure artifacts (`forbidden_terms_registry.json`, `governance_manifest.json`) that use the word without defining it. **This is a DECLARED-absence finding, not an inference of what the proposition should be.**

In the absence of a canon-defined proposition, the minimum proposition *derivable from the accepted governing invariant (§6.2) and the traced call graph (Phase 2, §5B)* — stated as **derived, not discovered** — is:

> **"This specific commit request originated from the specific, unaltered output of a real PSEUDO-A adjudication for this specific payload, and no other code path constructed or altered the commit request in between."**

This is the narrowest proposition that would actually close `AI_ADVISORY-003`/`SOSO-SPOOF-001`/`PSEUDO-SEAM-001` as demonstrated (all three exploit exactly the gap between "a dict that looks like a verdict" and "the dict `VerdictLogger.log()` actually produced" — see §6.5). Whether PH6 governance wants a *broader* proposition (e.g., involving process identity, hardware attestation, operator sign-off) is explicitly **UNRESOLVED** and flagged as an operator decision (§6.17), not decided here.

## 6.4 Authority subject

**RESOLVED, from repository evidence — with a distinction the repository itself does not currently make.**

Traced from `cram_pu/verdict_logger.py::VerdictLogger.log()` (read this pass, full body quoted): the verdict record's `verdict` field is computed **fresh, inside `log()`, from `_pseudo_verdict(metrics)`** — it is not caller-supplied. This makes **the execution of `VerdictLogger.log()` itself** — not an abstract "PSEUDO-A" identity, not "a Lane-1 process" in general — the actual authority subject *for the verdict content*.

However: **the repository does not distinguish, anywhere, between "a dict that was produced by executing `VerdictLogger.log()`" and "a dict that merely has the same shape."** `record` is a plain Python `dict`; nothing about it is bound to the code that built it. `AI_ADVISORY-003`'s adversarial test never touched `VerdictLogger` at all — it built an equivalent-shaped dict from scratch and handed it directly to `commit()`. **This is the precise evidence-grounded gap**: the authority subject *should be* (per §6.3's derived proposition) "the execution of `VerdictLogger.log()`," but the *actual, currently observable* authority subject accepted by `commit()` is **"any caller in the process holding a dict with `verdict == 'PASS'`"** — i.e., no subject distinction is currently enforced at all.

Do not equate "PSEUDO-A" (a conceptual adjudication role) with "the caller invoking commit()" (an unconstrained set today) — repository evidence establishes these are currently the same only by convention/absence-of-abuse, never by enforcement.

## 6.5 Mint legitimacy semantics

**UNRESOLVED.** Reconfirmed from Phase 2 (§5C, Dependency A) with no new contradicting evidence this pass: no issuer, issuance-condition, issuance-provenance, scope, lifetime, replay, revocation, or delegation semantic exists anywhere in `ph6/`. `PH6_SOURCE/SCHEMAS/ph6_ai_authority_request_v1.schema.json`/`ph6_authority_response_v1.schema.json` remain DECLARED contract text with zero implementing code. No issuer is invented here.

## 6.6 Capability integrity semantics

**UNRESOLVED as to what must be proven, because no capability object exists to define this against; the *predicate list* below is derived from §6.3's proposition, not discovered in the repository, and is labeled as such.**

**DESIGN REQUIREMENT DERIVED FROM §6.3** (not canon, not observed): whatever object eventually represents "proof of the §6.3 proposition" would need to allow verification of:
- authenticity (was this produced by a real `VerdictLogger.log()` execution, not forged)
- integrity (has it been altered since production)
- binding to the specific commit request (not replayable against a different payload)
- freshness (not replayable against a later, different commit attempt for the same or different payload)

**No selection of a cryptographic primitive is made here.** Whether cryptography is required at all, versus some other mechanism, is explicitly deferred to §6.15 — and even §6.15 only lists requirements, not a chosen mechanism, per this gate's scope.

## 6.7 PSEUDO-A binding semantics

**UNRESOLVED as an enforced property; RESOLVED as a precisely characterized gap.**

Real evidence, traced this pass: `VerdictLogger.log()` produces `record` with `schema: "ph6.pseudo_verdict.v2"`, a freshly-computed `verdict`, and a **self-declared `"authority": "LANE_1"` field written into the record by the function's own code** — i.e., even the "legitimate" path bakes in a plain-string authority claim with no enforcement that only `VerdictLogger.log()` can produce a dict containing that string. `record` is then returned as an ordinary dict; the call chain from there to `CRAMWriter.commit()`/`AtomicCRAMCommitter.commit()` (`cram_pu_live.py`, `run_4pass_system_test.py`, campaign tools) passes this dict by ordinary Python reference, with no binding mechanism of any kind between "the dict commit() receives" and "the specific `VerdictLogger.log()` call that (in the legitimate case) produced it."

This is precisely why `AI_ADVISORY-003` succeeded: the adversarial script did not need to defeat any binding — none exists to defeat. The contract requirement, stated as **derived, not discovered**: authorization evidence must be bound to *the specific execution of the adjudication step*, not merely to *a dict shaped like its output* — otherwise "authorization" would just become a second, parallel PASS/DROP-shaped check with the identical spoofing weakness as the field it's meant to protect (the operator's explicit warning in §6/D of the operating prompt: "Authorization must not become a second PASS/DROP authority").

## 6.8 Authorization provenance semantics

**UNRESOLVED**, per Phase 2's Dependency C, reconfirmed with no new evidence this pass. Restated precisely: `authority_hash` (`cram_pu/ingest_receipt_logger.py:11,18,125,140`) is "BLAKE2b-256 of the authoritative Lane-1 content" — it proves a receipt accurately describes an existing CRAM record (content/tamper integrity, verified by `vrc.py:136-143`'s Step B), not that the record's *creation* was authorized. `event_seq`/`event_hash`/`prev_event_hash` (`ssmt/hash_chain.py::chain_event`) establish chain-tamper-evidence for whichever log they appear in, not issuer legitimacy.

**Naming collision, restated as required by §11/E of the operating prompt:** the identical field name `authority_hash` is used in `cram_pu/ingest_receipt_logger.py` (Lane-1, means "hash of the authoritative Lane-1 content") and in `ssmt/audit_log.py:47` (Lane-2, means `canon_hash(packet_dict)` — an ordinary content hash of an advisory SSMT packet, `authority=NONE` per that packet's own contract). **This is more than terminology** — a field literally named "authority_hash" existing on a Lane-2 advisory object, when that object's own contract states `authority=NONE`, is a documentation/naming hazard that could mislead a future reader (human or AI) into treating the SSMT-side field as authority-bearing when it explicitly is not. Flagged as requiring architectural resolution (§6.17), not resolved here (renaming would be a source modification, prohibited this gate).

**No CRAM evidence-record provenance field currently carries any authorization-specific data at all** — `record` in `cram_pu_atomic_commit.py`/`crash_replay.py` contains `schema`, `commit_seq`/`frame_id`, `payload_hash`, `verdict`, `authority` (self-declared string), `prev_cram_hash`, `timestamp_utc`, `cram_hash` — no field represents "proof this commit was authorized," because no such proof is produced anywhere today.

## 6.9 Both commit-path contract

**RESOLVED as to identification and required scope; UNRESOLVED as to whether the two paths can/should share one contract.**

| | Path 1: `AtomicCRAMCommitter.commit()` (`cram_pu/tools/cram_pu_atomic_commit.py`) | Path 2: `CRAMWriter.commit()` (`cram_pu/crash_replay.py`) |
|---|---|---|
| Entry point | `commit(self, verdict: dict)` | `commit(self, frame_id: int, payload_hash: str, verdict_record: dict)` |
| Caller (production) | `commit_pass_verdicts()` (same file); test suite | `VerdictLogger.log()` output, passed by `cram_pu_live.py`, `run_4pass_system_test.py`, campaign tools (see 5B) |
| Existing PASS/DROP validation | `verdict["verdict"] != "PASS"` -> raise | `verdict_record.get("verdict") != "PASS"` -> raise |
| Proposed §6.3 proposition applies? | Yes — same defect class, same operating prompt's "AI_ADVISORY-003" evidence | Yes — same defect class, "PSEUDO-SEAM-001" evidence, and this is the path production actually uses |
| Evidence available at the boundary | `verdict` dict only — no reference to *how* it was produced | `frame_id`, `payload_hash` (separate args, not embedded in `verdict_record`), plus `verdict_record` — marginally more context (payload_hash is passed independently, meaning a future binding check *could* cross-verify it against `verdict_record["input_hash"]`, which is not done today) |
| Required denial behavior | Not yet defined — deferred to implementation (§6.16, out of scope here) | Same |

**Can both paths share one authorization contract?** The proposition (§6.3) and the binding requirement (§6.7) apply identically to both — nothing about either path's structure makes the proposition path-specific. **Whether one *implementation* could serve both, or whether Path 1/Path 2 should first be consolidated (Phase 2's open question, §5G item 1), remains UNRESOLVED** and is explicitly an operator decision, not resolved by this contract. This document states the semantics apply to *both*, not that a single mechanism instance must serve both.

## 6.10 Crash / atomicity relationship

**RESOLVED**, reusing Phase 2's Dependency E finding (114/114 `cram_pu/tests/` passing, including `test_crash_replay.py`'s `TestCRAMWriter` — not redemonstrated this pass, per the instruction not to redesign proven durability).

**DESIGN REQUIREMENT DERIVED FROM §6.2/§6.3** (not a new crash semantic — a placement requirement for where an authorization check would sit relative to the *already-proven* atomic sequence): authorization must be established **before** the existing atomic-write sequence begins (before the first `os.open`/`tmp` write in either class), not interleaved with it and not after. This does not modify the proven sequence (tmp-write-fsync-rename-marker-fsync-rename-dir-fsync, per Phase 2 §5B/2B) — it only requires that whatever check exists must gate *entry* to that sequence, so that a denied request produces zero filesystem side effects, consistent with the existing guarantee that a `commit()` call either fully succeeds or (per the PASS-only check today) raises before any I/O. This placement requirement is derived by analogy to the *existing* PASS-only check's placement (which already gates *before* I/O) — not invented from nothing.

## 6.11 Concurrency applicability

**UNRESOLVED.** Reconfirmed this pass, no new evidence: no lock, mutex, `threading`, `multiprocessing`, or file-locking primitive exists in `cram_pu/`. Every traced production call site (Phase 2 §5B, this session's fresh executions of `run_c10_c11_c12_absorption_campaigns.py`, `ph6_internal_test.py`, `tok_soso_isolation_proof.py`) invokes the commit boundary sequentially, single-threaded. **Per the operating prompt's explicit instruction, `ssmt/failure_injection.py::concurrent_writes()`/`FI-SSMT-04` is not used as evidence here** — it tests the SSMT scheduler, a different component, and is excluded from this determination rather than cited as adjacent support. No deployment-architecture document (searched `PH6_SOURCE/CANON`, `GOVERNANCE`, and the fleet/node documents referenced in memory this session) states single-writer semantics explicitly enough to resolve this. **CONCURRENCY APPLICABILITY = UNRESOLVED**, per the operating prompt's own instruction for this exact case.

## 6.12 Version-integrity relationship

**RESOLVED as to current behavior (reused from `SOSO-SPOOF-001`, not redemonstrated this pass); UNRESOLVED as to whether version identity is part of the §6.3 authorization proposition.**

Current behavior, restated precisely with the three-way distinction the operating prompt requires:
- **DECLARED version:** whatever `SSMT_VERSION` (`ssmt/constants.py`, `"1.0"`) or a packet's own `ssmt_version` field claims.
- **OBSERVED version:** `ssmt/audit_writer.py::write_packet` writes whatever `ssmt_version` string the caller's `SwarmPacket` object carries, with no comparison to `SSMT_VERSION` anywhere in that function (read this session, prior pass).
- **VALIDATED version:** none — `ssmt/replay_validator.py`'s source contains zero references to `ssmt_version` (confirmed this session), so no read-path check exists either. Nothing about a packet's version is ever validated, only declared and observed-as-written.

**Whether version identity should be part of the Lane-1 commit authorization proposition (§6.3) at all is UNRESOLVED** — `ssmt_version` today is exclusively an SSMT/Lane-2 concept (SoSo-side packets), and no repository evidence connects it to the CRAM-A commit boundary's `verdict`/`input_hash` fields, which have no version field of their own at all (traced `record` shape in §6.8 — no version field present). Treating `SOSO-SPOOF-001` and `AI_ADVISORY-003`/`PSEUDO-SEAM-001` as requiring one unified fix would not be supported by evidence — they are different fields on different objects at different boundaries, consistent with the operator's earlier explicit instruction that these remain independently testable controls.

## 6.13 TOK / SoSo / AI boundary

**RESOLVED**, reusing this session's already-executed evidence rather than re-deriving:

- **SoSo is advisory, confirmed executable, not merely declared:** `ssmt/tests/test_soso_contract.py` (9/9 PASS, this session) + `tok_soso_isolation_proof.py`'s `soso_has_authority_zero`, `soso_does_not_emit_pass_drop`, `soso_does_not_mutate_cram`, `soso_does_not_change_thresholds` (all PASS, this session, real production-shaped 300-frame runs).
- **TOK is advisory, confirmed executable:** `tok/tests/test_tok_boundaries.py::test_tok_declares_authority_zero` (PASS, this session) + isolation proof's `tokens_have_authority_zero`, `tokens_do_not_emit_pass_drop`, `token_promotion_fails_closed` (PASS, this session — `token_promotion_fails_closed` is the single strongest existing piece of evidence that TOK-asserted authority is already rejected somewhere in the current system, though not at the specific commit boundary this contract concerns — it is evidence the *principle* is already enforced in at least one place, not evidence the commit boundary itself enforces it).
- **AI is advisory, confirmed by absence of capability, not by a positive check:** `research_agent/` has zero import path to `cram_pu` (confirmed this session, multiple passes) — AI's advisory-only status at the commit boundary is currently true *only because no code connects them*, not because any check would reject an attempt (this is `AI_ADVISORY-003`'s exact finding, restated in this frame).
- **PSEUDO-A is the authoritative PASS/DROP decision-maker:** confirmed via `PSEUDO-A-001` (fresh execution, 0 violations, this session) and `pseudo_family_boundary_audit.md`'s historical governance audit — PSEUDO-A's *decision logic* is clean; the gap is entirely downstream of it (§6.7).

**What the authorization contract must reject when advisory-layer provenance is presented as Lane-1 authority — derived requirement, not yet implemented or tested against a real authorization mechanism (none exists):** a capability/proof object (§6.6) must be rejected if it is, or is derived from, a TOK record, `SwarmPacket`, AI/research_agent output, or any object whose own contract declares `authority: NONE`/`authority_zero`. This restates Part 2E's substitution-denial list from the prior design pass, now framed as a requirement on the *proposition* rather than a property of one specific proposed mechanism.

## 6.14 Failure / denial semantics

**UNRESOLVED as canon; RESOLVED as a derived minimum taxonomy, labeled as derived.**

No existing PH6 doctrine defines a denial-state taxonomy for commit authorization specifically (searched this pass, no hits beyond the incidental ones noted in §6.3). The taxonomy below is **derived from the states the certification evidence this session actually demonstrated or could construct**, not invented freely:

| State | Evidence this session establishes it's a real, distinguishable case |
|---|---|
| valid PASS + valid authorization | Not demonstrable — no authorization mechanism exists to be valid. |
| valid PASS + missing authorization | **This is exactly what `AI_ADVISORY-003`'s adversarial test demonstrated** — a real, valid-shaped PASS verdict, zero authorization object of any kind, accepted. |
| valid PASS + invalid/forged authorization | Not demonstrable today (no authorization object exists to forge) — but directly anticipated by the Part 1/2 design's attack-model table (§6 of the prior design pass), not re-derived here. |
| valid PASS + unverifiable authorization (e.g., object present but wrong schema) | Same as above — anticipated, not yet demonstrable. |
| DROP + authorization presented | Not applicable under the existing PASS-only contract — `commit()` already rejects non-PASS verdicts unconditionally (`AtomicCRAMCommitter`/`CRAMWriter`'s existing check); this state is structurally excluded before an authorization check would even run. |
| advisory-layer assertion presented as authorization | Not directly demonstrated by an executed test this session, but §6.13's TOK/SoSo `authority=NONE` contract evidence makes this the natural adversarial case a future test would construct — anticipated, not executed. |
| malformed authorization | Anticipated (Part 2's attack-model table), not executed. |
| stale/replayed authorization | Anticipated (Part 2's attack-model table, `mint_seq`/replay discussion), not executed — and Phase 2's Dependency A/B finding that no authorization object exists means "stale" cannot even be defined yet (staleness requires a lifetime concept, itself UNRESOLVED per §6.6). |
| authorization for wrong commit/context | Anticipated (Part 2's `packet_id`/`input_hash` binding discussion), not executed. |

**These states are not collapsed** — each is listed distinctly per the operating prompt's requirement, with an honest marker for which are executed-evidence-backed versus anticipated-but-undemonstrated.

## 6.15 Minimum mechanism requirements (requirements only — no mechanism selected)

**DESIGN REQUIREMENT DERIVED FROM §6.3-6.14, explicitly not a mechanism choice:**

Any eventual mechanism must be able to:
1. Bind proof-of-authorization to the specific execution of the adjudication step (§6.7), not merely to a dict shape.
2. Be unforgeable by code that has not executed that adjudication step, to a degree bounded honestly (the prior design pass's isolation-boundary characterization — in-process integrity, not cryptographic isolation against equal-privilege code — applies here as a *constraint on what any mechanism can claim*, not a chosen implementation).
3. Distinguish the denial states of §6.14 rather than collapsing them.
4. Gate entry *before* the existing, already-proven atomic-write sequence (§6.10), without modifying that sequence.
5. Apply to both commit paths (§6.9), whether via one shared instance or two path-specific ones — undetermined.
6. Explicitly refuse TOK/SoSo/AI-provenanced objects (§6.13).
7. Leave open, not silently resolve, the concurrency (§6.11) and version-binding (§6.12) questions — a mechanism must not implicitly assume single-writer semantics or version-inclusion without those being separately decided.

No token, credential, cryptographic primitive, or API shape is selected. The prior design pass (Parts 1-2) already sketched one candidate (capability-based, keyed-BLAKE2b) satisfying requirements 1-2-4-6 as illustration — it is not re-endorsed or re-rejected here; this section states requirements only, per this gate's explicit scope limit.

## 6.16 Evidence classification summary (every material claim above, indexed)

| Claim | Classification |
|---|---|
| §6.2 governing invariant | DESIGN REQUIREMENT DERIVED FROM ACCEPTED ARCHITECTURE (stated as accepted per operating prompt, not repository-derived) |
| §6.3 authority proposition (canon-defined) | DECLARED-absent — UNRESOLVED |
| §6.3 authority proposition (derived minimum) | DESIGN REQUIREMENT DERIVED, explicitly not canon |
| §6.4 authority subject (VerdictLogger execution) | OBSERVED (source read, this pass) |
| §6.4 authority subject (currently enforced) | OBSERVED — "any caller holding a PASS-shaped dict" (confirmed by executed adversarial test, prior session — VALIDATED) |
| §6.5 mint legitimacy | UNRESOLVED (exhaustive search, three passes) |
| §6.6 capability integrity predicates | DESIGN REQUIREMENT DERIVED, not observed or declared |
| §6.7 PSEUDO-A binding gap | VALIDATED (AI_ADVISORY-003's executed test demonstrates the gap directly) |
| §6.8 authority_hash / event_hash semantics | OBSERVED (source read) + VALIDATED (`vrc.py` Step B is executable, traced) |
| §6.8 naming collision | OBSERVED |
| §6.9 both paths' structure | OBSERVED (source read, both files) |
| §6.9 shared-vs-separate contract | UNRESOLVED |
| §6.10 crash/atomicity durability | VALIDATED (114/114 test suite, this session) |
| §6.10 authorization placement requirement | DESIGN REQUIREMENT DERIVED (by analogy to existing check placement) |
| §6.11 concurrency | UNRESOLVED |
| §6.12 version current behavior | OBSERVED + VALIDATED (`SOSO-SPOOF-001`'s executed test) |
| §6.12 version-in-authorization-proposition | UNRESOLVED |
| §6.13 SoSo/TOK/PSEUDO-A advisory-vs-authoritative status | VALIDATED (executed tests, this session, cited individually) |
| §6.13 AI advisory status | OBSERVED (absence of import path) — not VALIDATED as a positive-rejection test, since none exists |
| §6.14 denial taxonomy | DESIGN REQUIREMENT DERIVED, individually marked executed-evidence vs. anticipated |
| §6.15 mechanism requirements | DESIGN REQUIREMENT DERIVED — no mechanism selected |

## 6.17 Explicit unresolved questions requiring operator decision

1. Does PH6 governance want the derived minimum proposition (§6.3), or a broader one (process identity, hardware attestation, operator sign-off)? Not decided here.
2. Should the `authority_hash` naming collision (§6.8) be resolved (rename), independent of the authorization question?
3. Should Path 1 and Path 2 (§6.9) be consolidated before or as part of implementing any authorization mechanism, or should both be addressed independently?
4. Is concurrent invocation of the commit boundary (§6.11) ever going to occur in PH6's actual deployment model? No document or test settles this.
5. Should `ssmt_version`/SoSo-side version identity ever become part of the Lane-1 authorization proposition (§6.12), or do these remain permanently separate controls as previously instructed?
6. Where do the four named corpus documents (`BOOK I`, `00_PH6_CONSTITUTION_INTERPRETIVE_CONTROL`, `BOOK IV`, `PH6_CONSOLIDATED_CANON.docx`) actually exist, if anywhere, and should they supersede or inform this contract once located? Confirmed absent from this repository across two search passes.

## 6.18 Implementation prerequisites (not authorized, listed for the eventual gate)

Before implementation could begin, per this contract: §6.17's five questions need operator answers; the mechanism-requirement list (§6.15) needs to be checked against whichever mechanism is eventually chosen; §6.9's path-consolidation question needs an answer since it affects whether one or two code changes are needed; §6.14's anticipated-but-undemonstrated denial states need to become concrete negative tests once a mechanism exists to test them against.

## 6.19 Phase 2A disposition

**COMPLETE.** The authorization proposition is stated as a derived minimum, explicitly labeled as derived rather than discovered, because no canon-tier proposition exists. All required semantic dimensions (§6.4-§6.14) are resolved to the extent repository evidence permits, with every UNRESOLVED item traceable to a specific, exhausted search rather than an unexamined gap. No mechanism was selected. No source was modified.

```json
{"proposed_by":"claude-code-lane2","proposed_at_utc":"2026-09-05T14:35:00Z","api_call_log_ref":"session_01Er4uEgGZE7jhVVrQcnSh6S","ratified_by":null,"revision":"phase-2a-authorization-semantics-contract"}
```
