```
Document ID:   PH6-NUMERIC-ENCODING-V1-SPEC-DRAFT
Version:       0.1-DRAFT
Status:        PROPOSED — Authority ZERO — awaiting operator ratification
Production:    STOP_SHIP — TEST_HARNESS_ONLY
Scope:         ph6.canon.v1 numeric field encoding rules
Parent spec:   PH6-CANON-V1-SPEC-0.3-RC2.md
Last updated:  2026-06-19
Proposed by:   claude-code-lane2
```

---

# PH6 Numeric Encoding V1 — SPEC DRAFT

## 1. Purpose

This document specifies how numeric values are encoded in `ph6.canon.v1` canonical objects. It is a companion to `PH6-CANON-V1-SPEC-0.3-RC2.md` and covers fixed-point encoding, JSON number representation, and rounding rules.

**In scope:** numeric encoding for `ph6.canon.v1` fields only.
**Out of scope:** verdict logic, CRAM tier assignment, chain policy.

---

## 2. Fixed-Point Encoding

### 2.1 Motivation

Floating-point representation is platform-dependent and cannot guarantee identical bit patterns across implementations. PH6 Canon V1 uses a fixed-point integer representation for any numeric measurement field to ensure deterministic canonical JSON.

### 2.2 Scale Factor

```
C1_SCALE = 10000  (4 decimal places of precision)
```

A real-valued measurement `v` is encoded as:

```
fp_integer = round(v * C1_SCALE, ROUND_HALF_EVEN)
```

The `fp_integer` value is stored as a JSON integer in the canonical object.

### 2.3 Examples

| Real value | Fixed-point integer | Canonical JSON |
|-----------|--------------------|-|
| `0.0` | `0` | `0` |
| `1.0` | `10000` | `10000` |
| `3.5` | `35000` | `35000` |
| `12.3456` | `123456` | `123456` |
| `20.0` | `200000` | `200000` |
| `235.0` | `2350000` | `2350000` |

### 2.4 Reverse Conversion

```
real_value = fp_integer / C1_SCALE
```

This yields a `Decimal` with 4 decimal places.

---

## 3. Rounding Rule

### 3.1 ROUND_HALF_EVEN (Banker's Rounding)

All fixed-point conversions MUST use `ROUND_HALF_EVEN` (also called banker's rounding or round-half-to-even). This avoids systematic rounding bias in large datasets.

| Input | Raw product | Rounded |
|-------|-------------|---------|
| `0.00005` | `0.5` | `0` (even) |
| `0.00015` | `1.5` | `2` (even) |
| `0.00025` | `2.5` | `2` (even) |
| `0.00035` | `3.5` | `4` (even) |

### 3.2 Reference Implementation

```python
from decimal import Decimal, ROUND_HALF_EVEN

C1_SCALE = Decimal("10000")

def fp_int(value) -> int:
    d = Decimal(str(value))
    if not d.is_finite():
        raise ValueError(f"non-finite value forbidden: {value!r}")
    return int((d * C1_SCALE).to_integral_value(rounding=ROUND_HALF_EVEN))
```

Source of truth: `ph6/cram_pu/schemas/canonical.py:fp_int`

---

## 4. Forbidden Values

The following values are FORBIDDEN in any numeric field of a `ph6.canon.v1` canonical object:

| Forbidden | Reason |
|-----------|--------|
| `NaN` | Non-canonical; not representable in canonical JSON |
| `Infinity` | Non-canonical; not representable in canonical JSON |
| `-Infinity` | Non-canonical; not representable in canonical JSON |
| Floating-point literals in authority path output | Must use fixed-point integer representation |

The `canonical_json()` function raises `ValueError` on any non-finite float via `allow_nan=False`.

---

## 5. JSON Number Representation in Canonical Objects

### 5.1 Integer Fields

Fields whose values are intrinsically integers (e.g., `frame_id`, fixed-point measurement values) MUST be represented as JSON integers (no decimal point, no scientific notation).

### 5.2 String-Encoded Hashes

Hash fields (`payload_hash`, `canon_hash`) are strings containing 64 lowercase hexadecimal characters. They are NOT numeric fields and are not subject to fixed-point encoding.

### 5.3 No Scientific Notation

Canonical JSON MUST NOT use scientific notation (e.g., `1e+4`). Use `10000`, not `1e4`.

---

## 6. Note on `ph6.canon.v1` Object Fields

The `ph6.canon.v1` object (see parent spec §4) contains:
- `frame_id` — integer (no fixed-point encoding needed; frame IDs are whole numbers)
- `payload_hash` — string (hexadecimal, not numeric)
- `hash_algorithm` — string (constant sentinel)
- `canon_hash` — string (hexadecimal, not numeric)

No floating-point or fixed-point encoded fields appear in the minimal `ph6.canon.v1` schema. This spec applies to any future `ph6.canon.v1` extensions that introduce measurement fields.

---

```json
{
  "proposed_by": "claude-code-lane2",
  "proposed_at_utc": "2026-06-19T00:00:00Z",
  "api_call_log_ref": "session-ph6-canon-rc2-search-h1dq0c",
  "ratified_by": null
}
```
