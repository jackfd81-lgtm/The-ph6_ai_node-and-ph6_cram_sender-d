"""
ph6.cvs3_preflight — Validator Self-Verification (VAH-1.0)

Must run before any CVS-3 validation session.
If any check fails, the validation run is INVALID.

Verifies:
  1. governance manifest presence and hash
  2. schema lock registry presence and hash
  3. forbidden terms registry presence and hash
  4. severity policy presence and hash
  5. caller validator file hash (if provided)

Emits a structured preflight receipt using CFC-1.0.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from typing import Any

from ph6.cfc import make_failure, SEVERITIES


# ── Paths (relative to repo root /home/jack) ────────────────────────────────

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PH6_SOURCE = os.path.join(_REPO_ROOT, "PH6_SOURCE")

GOVERNANCE_FILES: dict[str, str] = {
    "governance_manifest":       os.path.join(_PH6_SOURCE, "GOVERNANCE", "governance_manifest.json"),
    "schema_lock_registry":      os.path.join(_PH6_SOURCE, "GOVERNANCE", "schema_lock_registry.json"),
    "forbidden_terms_registry":  os.path.join(_PH6_SOURCE, "GOVERNANCE", "forbidden_terms_registry.json"),
    "severity_policy":           os.path.join(_PH6_SOURCE, "GOVERNANCE", "severity_policy.json"),
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _blake2b(path: str) -> str | None:
    try:
        with open(path, "rb") as f:
            return hashlib.blake2b(f.read(), digest_size=32).hexdigest()
    except FileNotFoundError:
        return None


def _canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(",", ":"))


def run_preflight(
    validator_id: str,
    validator_version: str,
    validator_file: str | None = None,
    *,
    strict: bool = True,
) -> dict:
    """
    Run self-verification preflight for a CVS-3 validator.

    Args:
        validator_id:      Identifier string, e.g. "ph6-cvs-normal"
        validator_version: Version string, e.g. "1.0"
        validator_file:    Absolute path to the validator .py file (optional).
        strict:            If True, sys.exit(1) on any failure (default).

    Returns preflight receipt dict. On failure in strict mode: exits.
    """
    now = _utc_now()
    failures: list[dict] = []
    gov_hashes: dict[str, str | None] = {}

    # 1. Check governance files
    for name, path in GOVERNANCE_FILES.items():
        h = _blake2b(path)
        gov_hashes[name] = h
        if h is None:
            failures.append(make_failure(
                "O3", "CRITICAL",
                f"governance file missing: {name}",
                file=path,
                timestamp_utc=now,
            ))

    # 2. Check validator file if provided
    validator_hash: str | None = None
    if validator_file is not None:
        validator_hash = _blake2b(validator_file)
        if validator_hash is None:
            failures.append(make_failure(
                "O3", "CRITICAL",
                "validator file not found",
                file=validator_file,
                timestamp_utc=now,
            ))

    # 3. Build receipt
    passed = len(failures) == 0
    receipt: dict[str, Any] = {
        "schema":                    "ph6.cvs3.preflight.v1",
        "validator_id":              validator_id,
        "validator_version":         validator_version,
        "validator_hash":            validator_hash,
        "governance_manifest_hash":  gov_hashes.get("governance_manifest"),
        "schema_registry_hash":      gov_hashes.get("schema_lock_registry"),
        "forbidden_terms_hash":      gov_hashes.get("forbidden_terms_registry"),
        "severity_policy_hash":      gov_hashes.get("severity_policy"),
        "passed":                    passed,
        "failure_count":             len(failures),
        "failures":                  failures,
        "timestamp_utc":             now,
    }

    if not passed:
        msg = f"CVS-3 preflight FAILED for {validator_id}: {len(failures)} failure(s)"
        if strict:
            print(f"PREFLIGHT FAIL: {msg}", file=sys.stderr)
            for f in failures:
                print(f"  [{f['failure_class']}] {f['reason']}", file=sys.stderr)
            sys.exit(1)

    return receipt


def print_receipt(receipt: dict) -> None:
    status = "PASS" if receipt["passed"] else "FAIL"
    print(f"CVS-3 PREFLIGHT {status}: {receipt['validator_id']} v{receipt['validator_version']}")
    print(f"  governance_manifest: {receipt['governance_manifest_hash'] or 'MISSING'}")
    print(f"  schema_registry:     {receipt['schema_registry_hash'] or 'MISSING'}")
    print(f"  forbidden_terms:     {receipt['forbidden_terms_hash'] or 'MISSING'}")
    print(f"  severity_policy:     {receipt['severity_policy_hash'] or 'MISSING'}")
    if receipt["validator_hash"]:
        print(f"  validator_hash:      {receipt['validator_hash']}")
    if receipt["failures"]:
        print(f"  FAILURES ({receipt['failure_count']}):")
        for f in receipt["failures"]:
            print(f"    [{f['failure_class']}] {f['severity']}: {f['reason']}")


if __name__ == "__main__":
    receipt = run_preflight(
        validator_id="ph6-cvs-preflight-selftest",
        validator_version="1.0",
        validator_file=os.path.abspath(__file__),
        strict=False,
    )
    print_receipt(receipt)
