#!/usr/bin/env python3
"""
verify_manifest.py — updated 2026-09-03 for the unified scaffold layout.

CHANGE LOG (disclosed, not silent):
  - Original paths were relative to the old flat repo layout
    (spec/, docs/, tests/golden_vectors/, cert/). That layout no longer
    exists after the 01_DOCTRINE_AND_SPEC / 02_CONTROL_PLANE /
    03_VERIFICATION_AND_TESTS reorg. PATH_MAP below is the ONLY change:
    it re-points each logical name at its new physical location.
    File CONTENT is untouched, so every hash in sha256_manifest_v1.0.json
    still matches — this was verified by running the script (see chat).
  - This reorg is PROPOSED, not Lane-1-ratified. Treat this script's
    passing status as "content unchanged after move," not as canon
    acceptance of the new layout.
  - Still SHA-256, not BLAKE2b-256. If BLAKE2b-256 is locked canon,
    that is a separate, not-yet-made fix — see verify_manifest_blake2b.py.
"""
import json, hashlib, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "03_VERIFICATION_AND_TESTS" / "sha256_manifest_v1.0.json"

PATH_MAP = {
    "docs/GOVERNANCE.md": "02_CONTROL_PLANE/GOVERNANCE.md",
    "spec/ph6_master_v1.0.md": "01_DOCTRINE_AND_SPEC/ph6_master_v1.0.md",
    "spec/ph6_system_operation_reconstruction_v1.0.md":
        "01_DOCTRINE_AND_SPEC/ph6_system_operation_reconstruction_v1.0.md",
    "spec/constants_v1.0.json": "03_VERIFICATION_AND_TESTS/constants_v1.0.json",
    "spec/constants_v1.0.bin": "03_VERIFICATION_AND_TESTS/constants_v1.0.bin",
    "tests/golden_vectors/golden_vectors_v1.0.json":
        "03_VERIFICATION_AND_TESTS/golden_vectors/golden_vectors_v1.0.json",
}

def resolve(logical_path: str) -> Path:
    return ROOT / PATH_MAP.get(logical_path, logical_path)

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    governance_hash = sha256_file(resolve("docs/GOVERNANCE.md"))
    if manifest["GOVERNANCE_HASH"] != governance_hash:
        print("GOVERNANCE_HASH_MISMATCH")
        return 1
    for entry in manifest["files"]:
        actual = sha256_file(resolve(entry["path"]))
        if actual != entry["sha256"]:
            print(f"HASH_MISMATCH {entry['path']} expected={entry['sha256']} actual={actual}")
            return 1
    # binding presence checks
    const_obj = json.loads(resolve("spec/constants_v1.0.json").read_text(encoding="utf-8"))
    vec_obj = json.loads(resolve("tests/golden_vectors/golden_vectors_v1.0.json").read_text(encoding="utf-8"))
    if const_obj.get("GOVERNANCE_HASH") != governance_hash:
        print("CONSTANTS_GOVERNANCE_HASH_MISMATCH")
        return 1
    if vec_obj.get("GOVERNANCE_HASH") != governance_hash:
        print("VECTORS_GOVERNANCE_HASH_MISMATCH")
        return 1
    if vec_obj.get("CONST_SET_HASH") != sha256_file(resolve("spec/constants_v1.0.json")):
        print("VECTOR_CONST_HASH_MISMATCH")
        return 1
    print("MANIFEST_VALID (SHA-256, paths remapped for unified layout)")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
