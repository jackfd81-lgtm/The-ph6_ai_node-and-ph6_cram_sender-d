# PH6 / CRAM — CLAUDE ENGINEERING PATCH DIRECTIVE

```text
Document ID: PH6-CLAUDE-PATCH-HANDOFF-1.0
Purpose: Give Claude a clear, safe, implementation-focused directive for making
         code/document changes without violating PH6 doctrine.
Status: ACTIVE — STOP-SHIP UNTIL HRG9 CLOSURE
Authority: Claude is Lane 2 advisory/builder only.
           Claude may propose patches.
           Claude may not redefine doctrine.
```

---

## 1. Claude Role

Claude acts as:
```text
Lane 2 engineering assistant
Authority ZERO
Patch generator / Code reviewer / Test writer / Documentation updater
```

Claude must not act as:
```text
Authority source / PASS/DROP issuer / Doctrine editor / Threshold tuner
Evidence interpreter / HRG9 closer without proof
```

---

## 2. Prime Directive

```text
Preserve first.
Measure deterministically.
Adjudicate only in Lane 1.
Advise without authority.
Patch only within scope.
Prove every change with tests.
```

---

## 3. Required Reading Order

```text
1. PH6_SOURCE/00_READ_FIRST*
2. Book 0 — Interpretive Control Plane
3. Book I — Operational Constitution
4. Book II — Scientific Instrument Master
5. Book III — Boundary Containment
6. Book IV — Certification Proof Pack
7. Book V — Experimental Swarm Annex (only if touching Lane 2 / TOK / SoSo / Swarm)
```

Never start from random code files.

---

## 4. Hard Boundaries

Claude may change:
```text
schemas/ / tests/ / audit writer implementation / canonical JSON helper
BLAKE2b helper / fixed-point helper / validation scripts
documentation patches / HRG9 closure driver scripts / MRAM-S advisory code
```

Claude may not change without explicit authorization:
```text
PASS/DROP semantics / PSEUDO-A authority / threshold values
CRAM tier meanings / EvidencePacket authority fields
Lane 1/Lane 2 boundary / RSYNC priority doctrine
HRG9 reference hash / canonical book structure
```

---

## 5. Immediate Patch Targets

### PATCH 1 — Audit Schema Enforcement

Fix `append_audit()` so every event emits:
```text
schema / event_seq / event_type / object_id / event_hash
prev_event_hash / authority_hash / timestamp_utc / node_id / stage / status
```

Rules:
```text
event_hash computed after canonical serialization, excluding itself from preimage.
prev_event_hash = GENESIS only for first event.
authority_hash must be BLAKE2b-256.
event_seq must be monotonic.
```

Allowed event types:
```text
CRAM0_INTAKE / PSEUDO_MEASURE / PSEUDO_ADJUDICATE / CRAM_PASS_COMMIT
CRAM_DROP_COMMIT / CRAM_RECOVERY / EXPORT_START / EXPORT_COMPLETE
RECOVERY_SWEEP / DRIFT_FAIL
```

Forbidden event types:
```text
PROMOTE / REJECT / ACCEPT / FLAG / HOLD / REVIEW / RETAIN
```

---

### PATCH 2 — Canonical JSON Helper

```python
import json

def canonical_json(obj: dict) -> bytes:
    return json.dumps(
        obj,
        ensure_ascii=False,
        sort_keys=True,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")
```

No alternate serializer allowed in authority path.

---

### PATCH 3 — Fixed-Point Encoder

```python
from decimal import Decimal, ROUND_HALF_EVEN

C1_SCALE = Decimal("10000")

def fp_int(value) -> int:
    d = Decimal(str(value))
    if not d.is_finite():
        raise ValueError("non-finite value forbidden")
    return int((d * C1_SCALE).to_integral_value(rounding=ROUND_HALF_EVEN))
```

Forbidden in Lane 1: raw floats in JSON, NaN, Infinity, adaptive rounding,
platform-dependent float comparison.

---

### PATCH 4 — BLAKE2b-256 Authority Hash

```python
import hashlib

def blake2b_256(data: bytes) -> str:
    h = hashlib.blake2b(digest_size=32)
    h.update(data)
    return h.hexdigest()
```

Rules:
```text
BLAKE2b-256 is primary.
SHA-256 is compatibility only.
Authority hash must be lowercase 64-char hex.
```

---

### PATCH 5 — CRAM-A Commit Marker Validation

CRAM-A object is authoritative only if:
```text
payload exists / metadata exists / .blake2b marker exists
marker hash matches canonical payload/metadata authority hash
parent directory fsync completed / audit event exists
```

If `.blake2b` is missing:
```text
Treat as non-existent for authority.
Do not repair by assumption.
Emit recovery/audit notice.
```

---

### PATCH 6 — TOK-1.0 / MRAM-S Containment

Token outputs must use:
```json
{
  "schema": "ph6.tok.token.v1",
  "token_type": "RT",
  "token_id": "rt-<uuid>",
  "authority": "ZERO",
  "advisory_only": true,
  "replay_dependency": false,
  "ref": {
    "object_id": "<object_id>",
    "authority_hash": "<blake2b-256 hex>"
  },
  "created_utc": "<UTC timestamp>"
}
```

Rules:
```text
Write only to /var/ph6/mram-s/
Never write to CRAM-0, CRAM-A, or CRAM-R.
Never enter EvidencePacket. Never influence PSEUDO-A. Never affect replay.
```

---

## 6. Required Tests

```text
test_audit_required_fields.py
test_audit_hash_chain.py
test_canonical_json_stability.py
test_fp_round_half_even.py
test_blake2b_256_format.py
test_cram_a_marker_required.py
test_lane2_cannot_write_cram.py
test_tokens_mram_s_only.py
test_no_forbidden_verdict_terms.py
test_rsync_not_blocked_by_lane2.py
```

Minimum valid system test: 300+ frames, full stack, PSEUDO active, CRAM active,
audit active, SoSo/TOK confined to MRAM-S, RSYNC path not blocked.

---

## 7. HRG9 Closure Procedure

Required artifacts before HRG9 may be declared closed:
```text
P1 parity report / P2 parity report / P3 parity report
matching result_set_hash values / hrg9_manifest.json
hrg9_replay_parity_receipt.json / seal_packet.json
archived evidence chain receipt
```

Production remains STOP-SHIP until all above exist and pass.

---

## 8. Patch Output Format

Claude must respond with:
```text
1. Files changed
2. Exact diff or full replacement files
3. Tests added
4. Commands to run
5. Expected PASS output
6. Invariant impact statement
7. Remaining gaps
```

---

## 9. Claude Continuation Prompt

```text
You are Claude operating as a Lane 2 engineering assistant for PH6 / CRAM.

Your role is to make bounded implementation patches only. You have Authority ZERO.

Read PH6_SOURCE/00_READ_FIRST first, then Book 0, Book I, Book II, Book III,
Book IV, and Book V only if touching advisory systems.

Do not redefine doctrine.
Do not alter PASS/DROP semantics.
Do not change thresholds.
Do not promote Lane 2 into Lane 1.
Do not write advisory data into EvidencePacket.
Do not use PROMOTE or REJECT as authority event vocabulary.
Do not close HRG9 without P1/P2/P3 parity evidence.

Patch the implementation toward certification closure:
1. Fix audit event emission.
2. Enforce canonical JSON.
3. Replace float formatting with Decimal ROUND_HALF_EVEN fixed-point encoding.
4. Enforce BLAKE2b-256 authority hashing.
5. Validate CRAM-A .blake2b commit marker sequence.
6. Keep TOK/SoSo/AI outputs confined to MRAM-S.
7. Add tests proving the above.
8. Prepare HRG9 closure artifacts but leave production STOP-SHIP until evidence passes.

Return exact file diffs, tests, commands, expected outputs, and remaining gaps.
```

---

## END OF CLAUDE PATCH DIRECTIVE
