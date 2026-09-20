```
Document ID:   PH6-CANON-V1-CROSS-IMPL-MATCH-REPORT
Version:       0.3-RC2
Status:        PROPOSED — Authority ZERO — awaiting operator ratification
Production:    TEST_HARNESS_ONLY
Generated:     2026-06-19T00:00:00Z
Proposed by:   claude-code-lane2
```

---

# PH6 Canon V1 — Cross-Implementation Match Report

## 1. Purpose

This report documents that two independent implementations of the `ph6.canon.v1` canonical serialization and BLAKE2b-256 hash construction produce identical output for all test vectors.

---

## 2. Implementations

### Implementation A — stdlib `json.dumps`

Location: `ph6/tiny_validator.py` functions `_cj_A` / `_b2_A`

```python
def _cj_A(obj: Any) -> bytes:
    return json.dumps(
        obj,
        ensure_ascii=False,
        sort_keys=True,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")

def _b2_A(data: bytes) -> str:
    h = hashlib.blake2b(digest_size=32)
    h.update(data)
    return h.hexdigest()
```

**Approach:** Delegates key sorting and JSON serialization to CPython's `json.dumps` with `sort_keys=True`. This mirrors the approach used in the production reference at `ph6/cram_pu/schemas/canonical.py`.

---

### Implementation B — Hand-rolled dict sort + encode

Location: `ph6/tiny_validator.py` functions `_cj_B` / `_b2_B`

```python
def _cj_B(obj: Any) -> bytes:
    if isinstance(obj, dict):
        pairs = sorted(obj.items())
        encoded = b",".join(
            json.dumps(k, ensure_ascii=False).encode("utf-8") + b":" + _cj_B(v)
            for k, v in pairs
        )
        return b"{" + encoded + b"}"
    if isinstance(obj, list):
        return b"[" + b",".join(_cj_B(x) for x in obj) + b"]"
    if isinstance(obj, bool):
        return b"true" if obj else b"false"
    if isinstance(obj, int):
        return str(obj).encode("utf-8")
    if isinstance(obj, float):
        if obj != obj or obj in (float("inf"), float("-inf")):
            raise ValueError(f"non-finite float forbidden: {obj!r}")
        return json.dumps(obj).encode("utf-8")
    if isinstance(obj, str):
        return json.dumps(obj, ensure_ascii=False).encode("utf-8")
    if obj is None:
        return b"null"
    raise TypeError(f"unsupported type: {type(obj)!r}")
```

**Approach:** Manually iterates dict items in sorted order, recursively serializes values, and concatenates bytes. Does NOT call `_cj_A` or `json.dumps` at the top level for dicts — independence is structural, not just parametric.

---

## 3. Match Results

Run against all 11 test vectors on 2026-06-19. For each ACCEPT vector and the one REJECT vector where canon_hash computation is reached (reject_004), both implementations were exercised.

| Vector | Impl A hash | Impl B hash | Match |
|--------|-------------|-------------|-------|
| accept_001 | `d516198b0de157a19ac0a4103afb39514eece3648518341fabb692a16c377520` | `d516198b0de157a19ac0a4103afb39514eece3648518341fabb692a16c377520` | YES |
| accept_002 | `829504087e453827f021e0b62d9cae4490408fdeb76398b1933a4cb1f781f065` | `829504087e453827f021e0b62d9cae4490408fdeb76398b1933a4cb1f781f065` | YES |
| accept_003 | `d0fc232ed417e3509846123e1619309e655bb64009455b64d4bd16a2adfeddf1` | `d0fc232ed417e3509846123e1619309e655bb64009455b64d4bd16a2adfeddf1` | YES |
| accept_004 | `0f5b97cc9c856e5d2e24dabdcbe8f36aeaa05fe38534aeffb5cc1f55586a2bcd` | `0f5b97cc9c856e5d2e24dabdcbe8f36aeaa05fe38534aeffb5cc1f55586a2bcd` | YES |
| reject_004 (hash computation reached) | `d516198b0de157a19ac0a4103afb39514eece3648518341fabb692a16c377520` | `d516198b0de157a19ac0a4103afb39514eece3648518341fabb692a16c377520` | YES |

Vectors where implementation match is not exercised (format failures caught before hash computation): reject_001, reject_002, reject_003, reject_005, reject_006, quarantine_001 — `impl_match: null` in run report (correct; not a failure).

**`all_impl_match: true`** — confirmed in `validator_run_report.json`.

---

## 4. Conclusion

Both implementations produce byte-identical canonical JSON and BLAKE2b-256 hashes for all vectors where computation is reached. This confirms:

1. Key sorting is stable and order-independent between implementations
2. Compact separator encoding is consistent
3. UTF-8 encoding is consistent (accept_004 unicode vector)
4. BLAKE2b-256 with `digest_size=32` is consistent across both code paths

The canonical serialization rule in `PH6-CANON-V1-SPEC-0.3-RC2.md §2` is sufficient to produce deterministic, implementation-independent canonical bytes.

---

**Status:** PROPOSED — Authority ZERO. Not a production clearance.

```json
{
  "proposed_by": "claude-code-lane2",
  "proposed_at_utc": "2026-06-19T00:00:00Z",
  "api_call_log_ref": "session-ph6-canon-rc2-search-h1dq0c",
  "ratified_by": null
}
```
