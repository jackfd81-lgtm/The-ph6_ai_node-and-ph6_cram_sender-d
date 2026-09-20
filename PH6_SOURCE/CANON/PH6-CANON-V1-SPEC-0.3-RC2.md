```
Document ID:     PH6-CANON-V1-SPEC-0.3-RC2
Version:         0.3-RC2
Status:          PROPOSED — Authority ZERO — awaiting operator ratification
Production:      STOP_SHIP — TEST_HARNESS_ONLY
Scope:           ph6.canon.v1 — canonical serialization and hash construction
Companion:       ph6_numeric_encoding_v1_SPEC_DRAFT.md
                 PH6_CANON_V1_TINY_VALIDATOR_REQUIREMENTS.md
Last updated:    2026-06-19
Proposed by:     claude-code-lane2
```

---

# PH6 Canon V1 Specification — 0.3 RC2

## 1. Scope

This document specifies `ph6.canon.v1`: the canonical serialization rule and hash construction procedure for PH6 frame evidence objects.

**In scope:**
- Canonical JSON serialization rules
- BLAKE2b-256 hash construction over canonical bytes
- The `ph6.canon.v1` object schema and `canon_hash` computation

**Out of scope:**
- CRAM tier assignment (CRAM-0 / CRAM-A / CRAM-R / MRAM-S)
- Verdict tokens (PASS / DROP)
- Lane authority assignment
- Chain profile or chain policy
- Numeric encoding detail (see `ph6_numeric_encoding_v1_SPEC_DRAFT.md`)
- Any companion topic not listed above

---

## 2. Canonical JSON Serialization

### 2.1 Rule Set

A PH6 canonical JSON serialization MUST satisfy ALL of the following:

| Property | Requirement |
|----------|-------------|
| Key ordering | Keys sorted lexicographically (Unicode code point order) at every level |
| Separators | Compact — object: `","` and `":"`, no whitespace around delimiters |
| Encoding | UTF-8 byte string |
| NaN/Infinity | FORBIDDEN — raise error on any non-finite float |
| ASCII escape | `ensure_ascii=False` — non-ASCII Unicode characters preserved as UTF-8 |
| Null | `null` (JSON null literal) |
| Boolean | `true` / `false` (lowercase) |
| Integer | Decimal integer digits, no leading zeros beyond the units digit |
| Float | Standard JSON number encoding (non-finite values are forbidden) |

### 2.2 Determinism Guarantee

Given the same input object, canonical JSON MUST produce the same byte sequence on every invocation, on any conforming platform.

### 2.3 Reference Implementation

```python
import json

def canonical_json(obj) -> bytes:
    return json.dumps(
        obj,
        ensure_ascii=False,
        sort_keys=True,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")
```

Source of truth: `ph6/cram_pu/schemas/canonical.py:canonical_json`

---

## 3. BLAKE2b-256 Hash Construction

### 3.1 Algorithm

| Property | Value |
|----------|-------|
| Algorithm | BLAKE2b |
| Digest size | 32 bytes (256 bits) |
| Output encoding | Lowercase hexadecimal, 64 characters |
| Library | Python `hashlib.blake2b(digest_size=32)` |

### 3.2 SHA-256 Status

SHA-256 is a compatibility sidecar only. SHA-256 MAY appear alongside a BLAKE2b-256 hash for interoperability but MUST NOT be used as the primary authority hash for any `ph6.canon.v1` object.

### 3.3 Reference Implementation

```python
import hashlib

def blake2b_256(data: bytes) -> str:
    h = hashlib.blake2b(digest_size=32)
    h.update(data)
    return h.hexdigest()
```

Source of truth: `ph6/cram_pu/schemas/canonical.py:blake2b_256`

---

## 4. The `ph6.canon.v1` Object

### 4.1 Schema

```json
{
  "schema":        "ph6.canon.v1",
  "frame_id":      <integer, minimum 1>,
  "payload_hash":  "<64-char lowercase hex BLAKE2b-256 of payload bytes>",
  "hash_algorithm": "BLAKE2b-256",
  "canon_hash":    "<64-char lowercase hex — see §5>"
}
```

### 4.2 Field Definitions

| Field | Type | Constraint | Description |
|-------|------|------------|-------------|
| `schema` | string | const `"ph6.canon.v1"` | Schema identifier |
| `frame_id` | integer | >= 1 | Monotonically assigned frame identifier |
| `payload_hash` | string | 64-char lowercase hex | BLAKE2b-256 of raw payload bytes |
| `hash_algorithm` | string | const `"BLAKE2b-256"` | Hash algorithm identifier |
| `canon_hash` | string | 64-char lowercase hex | Hash of canonical body (see §5) |

### 4.3 Forbidden Field Values

| Field | Forbidden value | Reason |
|-------|----------------|--------|
| `payload_hash` | uppercase hex | Non-canonical; rejects in validator |
| `hash_algorithm` | anything other than `"BLAKE2b-256"` | Only BLAKE2b-256 is authoritative |
| `frame_id` | 0 or negative | Frame IDs begin at 1 |
| Any numeric field | NaN, Infinity, -Infinity | Non-finite values forbidden in canonical JSON |

---

## 5. Canon Hash Computation Procedure

### 5.1 Body Extraction

The **canonical body** is the `ph6.canon.v1` object with the `canon_hash` field excluded:

```
body = {
    "frame_id":      <frame_id>,
    "hash_algorithm": "BLAKE2b-256",
    "payload_hash":  <payload_hash>,
    "schema":        "ph6.canon.v1",
}
```

Note: keys appear sorted in canonical JSON serialization regardless of insertion order.

### 5.2 Hash Construction

```
canon_hash = BLAKE2b-256( canonical_json(body) )
```

### 5.3 Verification Procedure

A conforming validator MUST:

1. Parse the `ph6.canon.v1` object
2. Validate all required fields are present and conform to §4.2 constraints
3. Extract the canonical body (exclude `canon_hash`)
4. Serialize the body with canonical JSON (§2.1)
5. Compute BLAKE2b-256 of the serialized bytes
6. Compare the computed hash to the provided `canon_hash` field
7. Return outcome `ACCEPT` if equal, `REJECT` if not equal or if any field validation fails

### 5.4 Example (Vector accept_001)

```
payload bytes       : b"ph6_test_payload_frame_001"
payload_hash        : bb7a16998237ac39ba6a2eef66c3d7454f3b867ad2646cb49ffb64e48aa5df2d
canonical body JSON : {"frame_id":1,"hash_algorithm":"BLAKE2b-256","payload_hash":"bb7a...","schema":"ph6.canon.v1"}
canon_hash          : d516198b0de157a19ac0a4103afb39514eece3648518341fabb692a16c377520
```

---

## 6. Outcome Values (Test Vectors Only)

Test vectors use `expected_outcome` — NOT verdict tokens.

| Value | Meaning |
|-------|---------|
| `ACCEPT` | Object is valid; computed canon_hash matches provided value |
| `REJECT` | Object fails one or more validation checks |
| `QUARANTINE` | Object schema version is outside ph6.canon.v1 scope; cannot validate |

These outcome values apply to test vector evaluation ONLY and MUST NOT be used as Lane-1 verdict tokens.

---

## 7. Constraints and Forbidden Patterns

- `canon_hash` MUST NOT be computed over the full object including `canon_hash` itself (circular)
- `payload_hash` MUST be computed over raw payload bytes, not over JSON
- The `hash_algorithm` field is a constant sentinel; its value is `"BLAKE2b-256"` and MUST NOT vary
- No `chain_profile` or chain policy fields belong in `ph6.canon.v1` objects
- No companion topics (verdicts, CRAM tier, RSYNC priority) belong in `ph6.canon.v1` objects

---

## 8. Test Vectors Reference

Location: `PH6_SOURCE/CANON/ph6_canon_v1_vectors/`

| Subset | Count | Purpose |
|--------|-------|---------|
| `accept/` | 4 | Valid objects — expected_outcome: ACCEPT |
| `reject/` | 6 | Invalid objects — expected_outcome: REJECT |
| `quarantine/` | 1 | Unknown schema version — expected_outcome: QUARANTINE |

Manifest: `PH6_SOURCE/CANON/ph6_canon_v1_vectors/manifest.json`

---

## 9. Companion Documents

| Document | Purpose |
|----------|---------|
| `ph6_numeric_encoding_v1_SPEC_DRAFT.md` | Fixed-point numeric encoding detail |
| `PH6_CANON_V1_TINY_VALIDATOR_REQUIREMENTS.md` | Requirements for `tiny_validator.py` |
| `ph6/tiny_validator.py` | Reference implementation (TEST_HARNESS_ONLY) |

---

```json
{
  "proposed_by": "claude-code-lane2",
  "proposed_at_utc": "2026-06-19T00:00:00Z",
  "api_call_log_ref": "session-ph6-canon-rc2-search-h1dq0c",
  "ratified_by": null
}
```
