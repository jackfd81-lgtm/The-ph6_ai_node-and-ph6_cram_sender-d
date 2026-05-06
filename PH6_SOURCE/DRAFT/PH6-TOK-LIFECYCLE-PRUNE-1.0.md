# TOK-1.0 — Corrected Token Lifecycle + Pruning Implementation

## PH6 / CRAM Advisory Layer Patch

```text
Document ID: TOK-LIFECYCLE-PRUNE-1.0
Version: TOK-LIFECYCLE-PRUNE-1.0
Classification: LANE-2 / MRAM-S / AUTHORITY ZERO
Status: DRAFT / ACTIVE DEVELOPMENT REFERENCE
Primary Home: Book V — SoSo, JEDI, Tokens, Living Observation
Cross-Links: Book III (containment), Book IV (replay exclusion)
Implementation: ph6/tok/lifecycle.py
```

---

## 1. Review Verdict

| Area            | Issue                                      | Correction                                                           |
| --------------- | ------------------------------------------ | -------------------------------------------------------------------- |
| Audit           | `pruning.log` was plain text               | Must be append-only JSONL with hash chain                            |
| Determinism     | `datetime.now()` and unordered dict writes | Use deterministic timestamps passed in + sorted canonical JSON       |
| Hashing         | SHA/hash support missing                   | Use `BLAKE2b-256`                                                    |
| Atomicity       | `shutil.move()` is not enough              | Use write → fsync → rename → fsync(dir)                              |
| Authority       | `authority_hash` naming is risky           | Keep but clarify it is CRAM reference hash, not authority permission |
| Replay          | Token deletes lacked rebuild record        | Every genesis/update/promotion/prune must be logged                  |
| Manual override | Unsafe wording                             | Replace with audited protection request                              |

---

## 2. Canonical Doctrine Block

```text
TOK-1.0 manages advisory token topology.

TOK-1.0 is Lane-2 only.
TOK-1.0 has Authority ZERO.
TOK-1.0 writes only to MRAM-S.
TOK-1.0 may never modify CRAM, PSEUDO, PASS/DROP, thresholds, replay verdicts,
or RSYNC behavior.

Live token materializations may be pruned.
Historical token events may not be erased.

Valid deterministic rebuild source:

CRAM references
+ token genesis events
+ token update events
+ token promotion events
+ token protection events
+ token prune events
+ advisory audit chain
→ rebuilt TOK state
```

---

## 3. Implementation

See `ph6/tok/lifecycle.py` for full corrected implementation.

Key corrections applied:
- `pruning.log` → append-only JSONL hash chain (`tok_advisory_audit.jsonl`)
- `datetime.now()` → deterministic `timestamp_ms` passed in
- Unordered dict writes → sorted canonical JSON (`sort_keys=True`)
- `shutil.move()` → `write(tmp) → fsync(fd) → rename → fsync(dir)`
- `authority_hash` field → `cram_ref_hash` field (advisory reference only)
- Token deletes without rebuild record → every genesis/update/promotion/prune logged to audit
- "Manual override" wording → `protect_vlt()` as audited protection request, Authority ZERO

---

## 4. Corrected File Outputs

```text
/var/ph6/mram-s/tokens/
  live_tokens.json          ← atomic-written, rebuildable
  tok_advisory_audit.jsonl  ← append-only JSONL hash chain, never deleted
  archive/
    vlt_<token_id>.<timestamp_ms>.json  ← archived VLTs before prune
```

Allowed writes:

```text
MRAM-S only
```

Forbidden writes:

```text
/var/ph6/cram-0
/var/ph6/cram-a
/var/ph6/cram-r
/var/ph6/export
PSEUDO configs
threshold configs
PASS/DROP records
```

---

## 5. Final Canonical Summary

```text
TOK-1.0 token pruning is live-state management, not evidence deletion.

RTs are permanent CRAM reference anchors.

VDTs are short-lived hypotheses and may be aggressively pruned.

VLTs are reinforced advisory topology and may be conservatively pruned or archived.

Every token creation, promotion, protection request, and prune event must be
written to the append-only advisory audit chain.

Live token files may be deleted or compacted.

Audit history may not be deleted.

Rebuild must remain deterministic.

Authority remains ZERO.

CRAM remains sovereign.
```

---

## Integration Correction: PH6-TOK-COMMIT-CORRECTION-1.0

This lifecycle implementation is accepted only under the following integration constraints:

1. TOK is Lane-2 only.
2. TOK has Authority ZERO.
3. TOK writes only to MRAM-S.
4. TOK may prune live advisory materializations.
5. TOK may not erase historical advisory audit events.
6. TOK may not write CRAM.
7. TOK may not alter PSEUDO.
8. TOK may not influence PASS/DROP.
9. TOK may not block RSYNC.
10. TOK may not become replay dependency.

Smoke test interpretation:

`PROMOTED: <vlt_id> / PRUNED: 0` is valid when VDTs are consumed into a VLT and the VLT
has not exceeded pruning thresholds.

Final interpretation:

```text
TOK may explain continuity.

TOK may never decide truth.
```
