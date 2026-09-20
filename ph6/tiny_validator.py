#!/usr/bin/env python3
"""
ph6.canon.v1 Tiny Validator — TEST_HARNESS_ONLY

Scope:      ph6.canon.v1 canonical serialization and hash construction only.
Authority:  ZERO (Lane 2 — TEST_HARNESS_ONLY)
Production: STOP_SHIP

Spec:    PH6_SOURCE/CANON/PH6-CANON-V1-SPEC-0.3-RC2.md
Req doc: PH6_SOURCE/CANON/PH6_CANON_V1_TINY_VALIDATOR_REQUIREMENTS.md

Usage:
    python3 ph6/tiny_validator.py
    python3 ph6/tiny_validator.py PH6_SOURCE/CANON/ph6_canon_v1_vectors

Exit 0 if all vectors match expected_outcome. Exit 1 otherwise.

{"proposed_by":"claude-code-lane2","proposed_at_utc":"2026-06-19T00:00:00Z",
 "api_call_log_ref":"session-ph6-canon-rc2-search-h1dq0c","ratified_by":null}
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Implementation A — stdlib json.dumps (mirrors ph6/cram_pu/schemas/canonical.py)
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Implementation B — independent (no calls to A; hand-rolled dict sort + encode)
# ---------------------------------------------------------------------------

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


def _b2_B(data: bytes) -> str:
    h = hashlib.blake2b(digest_size=32)
    h.update(data)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# Validation logic (REQ-01 through REQ-08)
# ---------------------------------------------------------------------------

_REQUIRED = frozenset({"schema", "frame_id", "payload_hash", "hash_algorithm", "canon_hash"})
_HEX64 = re.compile(r"^[0-9a-f]{64}$")


def _validate(obj: Any) -> dict:
    if not isinstance(obj, dict):
        return {"outcome": "REJECT", "errors": ["top-level object must be a JSON object"]}

    missing = _REQUIRED - obj.keys()
    if missing:
        return {"outcome": "REJECT", "errors": [f"missing_required_fields: {sorted(missing)}"]}

    # REQ-02: schema version check
    if obj["schema"] != "ph6.canon.v1":
        return {
            "outcome": "QUARANTINE",
            "errors": [f"UNKNOWN_SCHEMA_VERSION: {obj['schema']!r} not within ph6.canon.v1 scope"],
            "impl_match": None,
        }

    errors: list[str] = []

    # REQ-03: hash_algorithm
    if obj["hash_algorithm"] != "BLAKE2b-256":
        errors.append(f"WRONG_HASH_ALGORITHM: {obj['hash_algorithm']!r} — must be BLAKE2b-256")

    # REQ-04: frame_id
    fid = obj["frame_id"]
    if not isinstance(fid, int) or isinstance(fid, bool) or fid < 1:
        errors.append(f"INVALID_FRAME_ID: {fid!r} — must be integer >= 1")

    # REQ-05: payload_hash format
    ph = obj["payload_hash"]
    if not isinstance(ph, str) or not _HEX64.match(ph):
        errors.append("INVALID_PAYLOAD_HASH_FORMAT: must be 64-char lowercase hex")

    # REQ-06: canon_hash format
    ch = obj["canon_hash"]
    if not isinstance(ch, str) or not _HEX64.match(ch):
        errors.append("INVALID_CANON_HASH_FORMAT: must be 64-char lowercase hex")

    if errors:
        return {"outcome": "REJECT", "errors": errors, "impl_match": None}

    # REQ-07 + REQ-08: recompute canon_hash with both implementations
    body = {
        "frame_id": obj["frame_id"],
        "hash_algorithm": obj["hash_algorithm"],
        "payload_hash": obj["payload_hash"],
        "schema": obj["schema"],
    }
    computed_A = _b2_A(_cj_A(body))
    computed_B = _b2_B(_cj_B(body))
    impl_match = computed_A == computed_B

    if computed_A != obj["canon_hash"]:
        return {
            "outcome": "REJECT",
            "errors": [
                f"CANON_HASH_MISMATCH: provided={obj['canon_hash']} computed={computed_A}"
            ],
            "impl_a": computed_A,
            "impl_b": computed_B,
            "impl_match": impl_match,
        }

    return {
        "outcome": "ACCEPT",
        "errors": [],
        "computed_canon_hash": computed_A,
        "impl_a": computed_A,
        "impl_b": computed_B,
        "impl_match": impl_match,
    }


# ---------------------------------------------------------------------------
# Vector runner
# ---------------------------------------------------------------------------

def _run_vectors(vectors_dir: Path) -> list[dict]:
    results: list[dict] = []
    for subdir in ("accept", "reject", "quarantine"):
        d = vectors_dir / subdir
        if not d.exists():
            continue
        for vec_file in sorted(d.glob("*.json")):
            try:
                obj = json.loads(vec_file.read_text(encoding="utf-8"))
                result = _validate(obj)
                expected = obj.get("expected_outcome", "UNKNOWN")
                actual = result["outcome"]
                results.append({
                    "vector_file": str(vec_file.relative_to(vectors_dir.parent)),
                    "expected_outcome": expected,
                    "actual_outcome": actual,
                    "match": actual == expected,
                    "errors": result.get("errors", []),
                    "impl_match": result.get("impl_match"),
                })
            except Exception as exc:
                results.append({
                    "vector_file": str(vec_file),
                    "expected_outcome": "UNKNOWN",
                    "actual_outcome": "REJECT",
                    "match": False,
                    "errors": [f"PARSE_ERROR: {exc}"],
                    "impl_match": None,
                })
    return results


def main() -> int:
    vectors_dir = (
        Path(sys.argv[1])
        if len(sys.argv) > 1
        else Path("PH6_SOURCE/CANON/ph6_canon_v1_vectors")
    )
    if not vectors_dir.exists():
        print(json.dumps({"error": f"vectors_dir not found: {vectors_dir}"}))
        return 1

    results = _run_vectors(vectors_dir)
    total = len(results)
    matched = sum(1 for r in results if r["match"])
    all_impl_match = all(
        r["impl_match"] is True for r in results if r["impl_match"] is not None
    )

    report = {
        "schema": "ph6.canon.v1.validator_run",
        "validator_version": "0.3-RC2",
        "authority": "ZERO",
        "production_status": "TEST_HARNESS_ONLY",
        "total_vectors": total,
        "vectors_matched": matched,
        "vectors_mismatched": total - matched,
        "all_match": matched == total,
        "all_impl_match": all_impl_match,
        "results": results,
    }
    print(json.dumps(report, indent=2))
    return 0 if report["all_match"] else 1


if __name__ == "__main__":
    sys.exit(main())
