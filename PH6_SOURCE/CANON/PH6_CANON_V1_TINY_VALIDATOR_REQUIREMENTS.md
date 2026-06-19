```
Document ID:   PH6-CANON-V1-TINY-VALIDATOR-REQUIREMENTS
Version:       0.3-RC2
Status:        PROPOSED — Authority ZERO — awaiting operator ratification
Production:    STOP_SHIP — TEST_HARNESS_ONLY
Scope:         Requirements for tiny_validator.py (ph6.canon.v1)
Parent spec:   PH6-CANON-V1-SPEC-0.3-RC2.md
Last updated:  2026-06-19
Proposed by:   claude-code-lane2
```

---

# PH6 Canon V1 Tiny Validator Requirements

## 1. Purpose

This document specifies the requirements for `tiny_validator.py` — the reference test-harness implementation for validating `ph6.canon.v1` canonical objects against the specification in `PH6-CANON-V1-SPEC-0.3-RC2.md`.

The tiny validator is a single-file, zero-dependency (stdlib-only) Python script. It is **TEST_HARNESS_ONLY** and has **Authority ZERO**. It MUST NOT be used in any Lane-1 authority path.

---

## 2. Validator Scope

The validator validates only the following:
- Canonical JSON serialization correctness (§2 of parent spec)
- BLAKE2b-256 hash construction (§3 of parent spec)
- `ph6.canon.v1` object field constraints (§4 of parent spec)
- Canon hash computation procedure (§5 of parent spec)

The validator MUST NOT:
- Assign CRAM tier
- Emit PASS or DROP verdict tokens
- Interact with any hardware path
- Modify any file outside its output report
- Perform network operations
- Claim production authority

---

## 3. Required Checks

For each `ph6.canon.v1` vector object, the validator MUST perform checks in this order:

| # | Check | Failure action |
|---|-------|----------------|
| REQ-01 | All required fields present: `schema`, `frame_id`, `payload_hash`, `hash_algorithm`, `canon_hash` | Return REJECT with `missing_required_fields` error |
| REQ-02 | `schema` == `"ph6.canon.v1"` | Return QUARANTINE if schema is a different known-pattern value; REJECT if malformed |
| REQ-03 | `hash_algorithm` == `"BLAKE2b-256"` | Return REJECT with `WRONG_HASH_ALGORITHM` error |
| REQ-04 | `frame_id` is an integer >= 1 | Return REJECT with `INVALID_FRAME_ID` error |
| REQ-05 | `payload_hash` matches `^[0-9a-f]{64}$` (64 lowercase hex chars) | Return REJECT with `INVALID_PAYLOAD_HASH_FORMAT` error |
| REQ-06 | `canon_hash` matches `^[0-9a-f]{64}$` (64 lowercase hex chars) | Return REJECT with `INVALID_CANON_HASH_FORMAT` error |
| REQ-07 | Recompute `canon_hash` per §5 of spec; compare to provided value | Return REJECT with `CANON_HASH_MISMATCH` error if not equal |
| REQ-08 | (Cross-check) Second independent implementation matches Implementation A | Log `impl_match: false` if mismatch; this is a validator internal error |

---

## 4. Outcome Definitions

| Outcome | Condition | Notes |
|---------|-----------|-------|
| `ACCEPT` | All REQ-01 through REQ-07 pass; computed canon_hash matches | Object is valid per ph6.canon.v1 |
| `REJECT` | Any of REQ-01, REQ-03 through REQ-07 fail | Object fails validation; `errors` list populated |
| `QUARANTINE` | REQ-02 fails because `schema` != `"ph6.canon.v1"` but has recognizable format | Object is outside validator scope; cannot determine validity |

These outcomes apply to TEST VECTOR EVALUATION ONLY and are NOT Lane-1 verdict tokens.

---

## 5. Output Format

The validator MUST output a JSON object to stdout with this structure:

```json
{
  "schema": "ph6.canon.v1.validator_run",
  "validator_version": "0.3-RC2",
  "authority": "ZERO",
  "production_status": "TEST_HARNESS_ONLY",
  "total_vectors": <int>,
  "vectors_matched": <int>,
  "vectors_mismatched": <int>,
  "all_match": <bool>,
  "results": [
    {
      "vector_file": "<relative path>",
      "expected_outcome": "ACCEPT|REJECT|QUARANTINE",
      "actual_outcome": "ACCEPT|REJECT|QUARANTINE",
      "match": <bool>,
      "errors": ["<error string>", ...],
      "impl_match": <bool|null>
    }
  ]
}
```

Per-vector result fields:

| Field | Required | Description |
|-------|----------|-------------|
| `vector_file` | YES | Relative path to the vector file |
| `expected_outcome` | YES | Value from vector's `expected_outcome` field |
| `actual_outcome` | YES | Outcome computed by validator |
| `match` | YES | `true` if expected == actual |
| `errors` | YES | List of error strings (empty for ACCEPT) |
| `impl_match` | YES | `true` if Impl-A hash == Impl-B hash; `null` if not computed |

---

## 6. Two-Implementation Requirement

The validator MUST contain two independent implementations of canonical_json + BLAKE2b-256:

| Implementation | Requirement |
|---------------|-------------|
| Implementation A | May use Python stdlib `json.dumps` with appropriate parameters |
| Implementation B | MUST independently produce identical bytes without calling Implementation A |

Both implementations MUST produce the same `canon_hash` for every valid object. Any mismatch between A and B MUST be logged as a validator internal error and reported in `impl_match: false`.

This two-implementation check serves as the cross-language/cross-implementation match proof required by §7 of the RC2 artifact chain.

---

## 7. Test Vector Protocol

1. Locate the `ph6_canon_v1_vectors/` directory
2. Process subdirectories in order: `accept/`, `reject/`, `quarantine/`
3. For each `*.json` file in each subdirectory, run REQ-01 through REQ-08
4. Compare `actual_outcome` to the vector's `expected_outcome` field
5. Report `match: true` if they agree, `match: false` if they differ
6. Exit code: `0` if `all_match` is `true`, `1` otherwise

---

## 8. Implementation Location

```
ph6/tiny_validator.py
```

Rationale: active Python implementations live in `ph6/`. The validator is a test harness, not a production tool, but it is still executed Python code and therefore belongs in `ph6/` per the file placement rules in `CLAUDE.md`.

---

```json
{
  "proposed_by": "claude-code-lane2",
  "proposed_at_utc": "2026-06-19T00:00:00Z",
  "api_call_log_ref": "session-ph6-canon-rc2-search-h1dq0c",
  "ratified_by": null
}
```
