#!/usr/bin/env python3
"""
PH6 Canon Compiler — scans GOVERNANCE/ and SCHEMAS/, produces manifests in CANON/.
PROPOSED artifact. Ratified_by: null.
"""

import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
GOVERNANCE_ROOT = REPO_ROOT / "GOVERNANCE"
SCHEMAS_ROOT = REPO_ROOT / "SCHEMAS"
CANON_ROOT = REPO_ROOT / "CANON"

PROPOSED_BY = "claude-code-lane2"


def blake2b_file(path: Path) -> str:
    h = hashlib.blake2b(digest_size=32)
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def scan_governance() -> list:
    results = []
    if not GOVERNANCE_ROOT.exists():
        return results
    for p in sorted(GOVERNANCE_ROOT.rglob("*.md")):
        rel = str(p.relative_to(REPO_ROOT))
        results.append({
            "path": rel,
            "hash": blake2b_file(p),
            "size_bytes": p.stat().st_size,
        })
    return results


def scan_schemas() -> list:
    results = []
    if not SCHEMAS_ROOT.exists():
        return results
    for p in sorted(SCHEMAS_ROOT.rglob("*.json")):
        rel = str(p.relative_to(REPO_ROOT))
        try:
            with open(p) as f:
                data = json.load(f)
            schema_id = data.get("$id", "UNKNOWN")
            title = data.get("title", "UNKNOWN")
        except Exception as e:
            schema_id = f"PARSE_ERROR: {e}"
            title = "UNKNOWN"
        results.append({
            "path": rel,
            "schema_id": schema_id,
            "title": title,
            "hash": blake2b_file(p),
            "size_bytes": p.stat().st_size,
        })
    return results


def write_manifest(name: str, content: dict) -> Path:
    CANON_ROOT.mkdir(parents=True, exist_ok=True)
    out = CANON_ROOT / name
    tmp = out.with_suffix(".tmp")
    with open(tmp, "w") as fd:
        json.dump(content, fd, indent=2)
        fd.flush()
        os.fsync(fd.fileno())
    os.replace(tmp, out)
    dir_fd = os.open(str(CANON_ROOT), os.O_RDONLY)
    try:
        os.fsync(dir_fd)
    finally:
        os.close(dir_fd)
    return out


def main():
    ts = datetime.now(timezone.utc).isoformat()

    gov_entries = scan_governance()
    schema_entries = scan_schemas()

    gov_manifest = {
        "manifest_type": "governance_doc_manifest",
        "generated_at_utc": ts,
        "proposed_by": PROPOSED_BY,
        "ratified_by": None,
        "doc_count": len(gov_entries),
        "docs": gov_entries,
    }

    schema_manifest = {
        "manifest_type": "schema_manifest",
        "generated_at_utc": ts,
        "proposed_by": PROPOSED_BY,
        "ratified_by": None,
        "schema_count": len(schema_entries),
        "schemas": schema_entries,
    }

    combined = {
        "manifest_type": "canon_combined_manifest",
        "generated_at_utc": ts,
        "proposed_by": PROPOSED_BY,
        "ratified_by": None,
        "governance_doc_count": len(gov_entries),
        "schema_count": len(schema_entries),
        "governance_docs": gov_entries,
        "schemas": schema_entries,
    }

    p1 = write_manifest("governance_manifest.json", gov_manifest)
    p2 = write_manifest("schema_manifest.json", schema_manifest)
    p3 = write_manifest("canon_combined_manifest.json", combined)

    print(f"CANON COMPILER: PASS")
    print(f"  governance docs : {len(gov_entries)}")
    print(f"  schemas         : {len(schema_entries)}")
    print(f"  output dir      : {CANON_ROOT}")
    print(f"  manifests       : {p1.name}, {p2.name}, {p3.name}")
    print(f"  generated_at    : {ts}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
