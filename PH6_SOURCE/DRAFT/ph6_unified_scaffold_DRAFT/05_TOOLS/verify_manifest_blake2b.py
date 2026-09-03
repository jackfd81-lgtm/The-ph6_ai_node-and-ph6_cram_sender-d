#!/usr/bin/env python3
"""
verify_manifest_blake2b.py — NEW, 2026-09-03.

WHY THIS EXISTS:
  Prior session record states BLAKE2b-256 is the locked canonical hash
  for PH6 (not SHA-256). verify_manifest.py in this scaffold has always
  used hashlib.sha256 — that is a real canon-vocabulary violation, but
  I have not seen a source document THIS SESSION that defines the
  BLAKE2b-256 rule (only a memory note from a prior conversation).
  Per the terminology-verification rule, that makes it [TERMINOLOGY:
  UNVERIFIED] against material actually in front of me right now.

WHAT THIS SCRIPT DOES:
  Generates a SEPARATE, additive BLAKE2b-256 manifest
  (blake2b256_manifest_v1.0.json) alongside the existing
  sha256_manifest_v1.0.json — it does NOT delete, rename, or overwrite
  the SHA-256 one. BLAKE2b-256 = BLAKE2b with a 32-byte (256-bit)
  digest, which is the standard, unambiguous meaning of that name;
  no additional spec is needed to implement the hash itself.

WHAT THIS SCRIPT DOES NOT DO:
  Decide which hash is canonical. That's a Lane 1 call. Until you say
  which one governs, both manifests exist side by side and
  verify_manifest.py (SHA-256) remains the one wired into CI.

Usage:
    python3 verify_manifest_blake2b.py            # generate + print
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "03_VERIFICATION_AND_TESTS" / "blake2b256_manifest_v1.0.json"

# Same file set as sha256_manifest_v1.0.json, new physical paths.
FILES = [
    "02_CONTROL_PLANE/GOVERNANCE.md",
    "01_DOCTRINE_AND_SPEC/ph6_master_v1.0.md",
    "01_DOCTRINE_AND_SPEC/ph6_system_operation_reconstruction_v1.0.md",
    "03_VERIFICATION_AND_TESTS/constants_v1.0.json",
    "03_VERIFICATION_AND_TESTS/constants_v1.0.bin",
    "03_VERIFICATION_AND_TESTS/golden_vectors/golden_vectors_v1.0.json",
]


def blake2b_256_file(path: Path) -> str:
    h = hashlib.blake2b(digest_size=32)
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    entries = []
    for rel in FILES:
        digest = blake2b_256_file(ROOT / rel)
        entries.append({"path": rel, "blake2b256": digest})
        print(f"{rel}: {digest}")

    manifest = {
        "PH6_VERSION": "v1.0",
        "RATIFICATION_STATE": "PROPOSED",
        "HASH_ALGORITHM": "BLAKE2b-256 (blake2b, digest_size=32)",
        "NOTE": "Additive. Does not supersede sha256_manifest_v1.0.json "
                "without explicit Lane 1 decision.",
        "files": entries,
    }
    OUT.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"\nWritten: {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
