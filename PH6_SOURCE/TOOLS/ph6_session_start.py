#!/usr/bin/env python3
"""
PH6 Session Start — Ingest Receipt Generator v1.0

Run this at the start of any AI session that involves PH6.
Generates an authoritative ingest receipt: build exists + build verified + build loaded.

The fourth state (build respected) cannot be machine-verified — it is Lane 2 advisory.

Usage:
  python3 ph6_session_start.py --profile minimal
  python3 ph6_session_start.py --profile engineering
  python3 ph6_session_start.py --profile governance
  python3 ph6_session_start.py --profile validation
  python3 ph6_session_start.py --profile forensic
  python3 ph6_session_start.py --profile full_canon

Output:
  - Prints SESSION ANCHOR block (paste as first message into AI session)
  - Writes receipt to builds/receipts/<timestamp>_<profile>.json
"""

import argparse
import hashlib
import json
import os
import platform
import secrets
import sys
from datetime import datetime, timezone
from pathlib import Path


_SOURCE_ROOT    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_BUILDS_DIR     = os.path.join(_SOURCE_ROOT, "builds")
_RECEIPTS_DIR   = os.path.join(_BUILDS_DIR, "receipts")
_MANIFEST_PATH  = os.path.join(_BUILDS_DIR, "build_manifest.json")
_CLF_PATH       = os.path.join(_SOURCE_ROOT, "GOVERNANCE", "ingest_classification.json")
_DIVIDER        = "=" * 80
_SEAL_MARKER    = f"\n{_DIVIDER}\nBUILD SEAL"
_GENESIS_HASH   = "0" * 64

PROFILES = ("minimal", "engineering", "governance", "validation", "forensic", "full_canon")


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _ts_slug() -> str:
    # Include microseconds to prevent same-second collisions in receipt filenames
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")


def _blake2b(data: bytes) -> str:
    return hashlib.blake2b(data, digest_size=32).hexdigest()


def _pre_seal_hash(path: str) -> str | None:
    try:
        content = Path(path).read_text(encoding="utf-8")
        idx = content.find(_SEAL_MARKER)
        payload = content[:idx] if idx != -1 else content
        return _blake2b(payload.encode("utf-8"))
    except FileNotFoundError:
        return None


def _canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(",", ":"))


def load_build_manifest() -> dict:
    if not os.path.isfile(_MANIFEST_PATH):
        sys.exit(
            f"FATAL: build manifest not found at {_MANIFEST_PATH}\n"
            "Run: python3 TOOLS/ph6_ingest_compiler.py"
        )
    with open(_MANIFEST_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def verify_profile(profile: str, build_manifest: dict) -> tuple[bool, str | None, dict | None]:
    """
    Returns (verified, actual_hash, build_record).
    Verified = build file exists AND hash matches manifest.
    """
    built = {b["target"]: b for b in build_manifest.get("builds", [])}
    if profile not in built:
        return False, None, None

    record    = built[profile]
    out_path  = os.path.join(_BUILDS_DIR, f"{profile}_ingest.txt")
    actual_h  = _pre_seal_hash(out_path)
    stored_h  = record.get("blake2b_256")
    verified  = (actual_h is not None) and (actual_h == stored_h)
    return verified, actual_h, record


_TYPE_ORDER = ("LAW", "SCHEMA", "RUNTIME", "STATE", "GAP", "TEST", "HISTORY")


def _load_order_string(clf_path: str, profile: str) -> str:
    """Return canonical load order string for this profile, e.g. LAW>SCHEMA>RUNTIME>STATE."""
    try:
        with open(clf_path, "r", encoding="utf-8") as f:
            clf = json.load(f)
        types = clf.get("build_targets", {}).get(profile, {}).get("types", [])
        return ">".join(t for t in _TYPE_ORDER if t in types)
    except Exception:
        return "UNKNOWN"


def _latest_receipt_hash() -> str:
    """Return BLAKE2b-256 of the most recent receipt file, or genesis hash."""
    try:
        receipts = sorted(Path(_RECEIPTS_DIR).glob("*.json"))
        if not receipts:
            return _GENESIS_HASH
        return _blake2b(receipts[-1].read_bytes())
    except (FileNotFoundError, OSError):
        return _GENESIS_HASH


def generate_receipt(
    profile: str,
    verified: bool,
    actual_hash: str | None,
    build_record: dict | None,
    now: str,
) -> dict:
    load_order = _load_order_string(_CLF_PATH, profile)
    session_id = f"ses-{secrets.token_hex(8)}"
    receipt = {
        "schema":               "ph6.ingest.receipt.v1",
        "receipt_version":      "1.1",
        "session_id":           session_id,
        "authority_level":      "SESSION-ANCHOR",
        "profile":              profile,
        "load_order":           load_order,
        "build_exists":         build_record is not None,
        "build_verified":       verified,
        "build_loaded":         True,
        "build_respected":      None,
        "build_respected_note": "Not machine-verifiable. Lane 2 advisory only.",
        "build_hash":           actual_hash,
        "manifest_hash":        build_record.get("blake2b_256") if build_record else None,
        "files_in_build":       build_record.get("file_count", 0) if build_record else 0,
        "files_loaded":         build_record.get("files_included", []) if build_record else [],
        "terminal_platform":    platform.system(),
        "python_version":       platform.python_version(),
        "timestamp_utc":        now,
    }
    return receipt


def _seal_receipt(receipt: dict) -> dict:
    """
    Add chain fields to receipt.
    prev_receipt_hash: BLAKE2b-256 of previous receipt file (or genesis).
    receipt_hash:      BLAKE2b-256 of canonical receipt body (excluding receipt_hash).
    Same pattern as CRAM atomic commit contract.
    """
    receipt["prev_receipt_hash"] = _latest_receipt_hash()
    body = {k: v for k, v in receipt.items() if k != "receipt_hash"}
    receipt["receipt_hash"] = _blake2b(_canonical(body).encode("utf-8"))
    return receipt


def write_receipt(receipt: dict, profile: str) -> str:
    os.makedirs(_RECEIPTS_DIR, exist_ok=True)
    receipt = _seal_receipt(receipt)
    slug     = _ts_slug()
    filename = f"{slug}_{profile}.json"
    out_path = os.path.join(_RECEIPTS_DIR, filename)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(_canonical(receipt))
    return out_path


def print_session_anchor(receipt: dict, profile: str, build_path: str) -> None:
    now       = receipt["timestamp_utc"]
    h         = receipt["build_hash"] or "UNVERIFIED"
    n_files   = receipt["files_in_build"]
    status    = "VERIFIED" if receipt["build_verified"] else "UNVERIFIED — run compiler first"

    print()
    print(_DIVIDER)
    print("PH6 SESSION ANCHOR")
    print(_DIVIDER)
    print(f"Profile:    {profile}")
    print(f"Build hash: {h}")
    print(f"Files:      {n_files}")
    print(f"Status:     {status}")
    print(f"Generated:  {now}")
    print(_DIVIDER)
    print()
    print("PASTE THIS BLOCK AS YOUR FIRST MESSAGE INTO THE AI SESSION:")
    print()
    print("```")
    print(f"PH6 SESSION ANCHOR")
    print(f"Build profile:  {profile}")
    print(f"Build hash:     {h}")
    print(f"File count:     {n_files}")
    print(f"Load status:    build_loaded=true, build_verified={str(receipt['build_verified']).lower()}")
    print(f"Timestamp:      {now}")
    print(f"")
    print(f"The following ingest build was loaded before this message.")
    print(f"LAW precedes SCHEMA precedes RUNTIME precedes STATE.")
    print(f"Runtime evidence outranks documentation.")
    print(f"Build respected: not machine-verifiable — Lane 2 advisory.")
    print("```")
    print()
    print(f"Build file: {build_path}")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description="PH6 Session Start — Ingest Receipt Generator v1.0")
    parser.add_argument(
        "--profile",
        choices=PROFILES,
        default="minimal",
        help="Ingest profile to load (default: minimal)",
    )
    parser.add_argument(
        "--no-write",
        action="store_true",
        help="Print anchor without writing receipt to disk",
    )
    args = parser.parse_args()

    now            = _utc_now()
    build_manifest = load_build_manifest()
    profile        = args.profile

    verified, actual_hash, build_record = verify_profile(profile, build_manifest)

    if not verified:
        print(f"WARNING: build '{profile}' is not verified or does not exist.", file=sys.stderr)
        print("Run: python3 TOOLS/ph6_ingest_compiler.py && python3 TOOLS/ph6_ingest_verify.py",
              file=sys.stderr)

    receipt    = generate_receipt(profile, verified, actual_hash, build_record, now)
    build_path = os.path.join(_BUILDS_DIR, f"{profile}_ingest.txt")

    if not args.no_write:
        out = write_receipt(receipt, profile)
        print(f"Receipt written: {out}")

    print_session_anchor(receipt, profile, build_path)


if __name__ == "__main__":
    main()
