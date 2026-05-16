#!/usr/bin/env python3
"""
PH6 Ingest Compiler v1.0

Input:  PH6_SOURCE/GOVERNANCE/ingest_classification.json
Output: PH6_SOURCE/builds/{target}_ingest.txt  (one per build target)
        PH6_SOURCE/builds/build_manifest.json

Each build is:
  - ordered by (type_priority, file_priority)
  - deduplicated (each file appears once)
  - type-tagged with section headers
  - BLAKE2b-256 hash-sealed

Usage:
  python3 ph6_ingest_compiler.py [--target minimal|engineering|governance|validation|forensic|full_canon]
  python3 ph6_ingest_compiler.py  # builds all targets
"""

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone


CLASSIFICATION_REL = "GOVERNANCE/ingest_classification.json"
BUILDS_DIR_NAME    = "builds"
DIVIDER            = "=" * 80
SECTION_DIV        = "-" * 80


def blake2b_256(data: bytes) -> str:
    return hashlib.blake2b(data, digest_size=32).hexdigest()


def load_classification(source_root: str) -> dict:
    path = os.path.join(source_root, CLASSIFICATION_REL)
    if not os.path.exists(path):
        sys.exit(f"FATAL: classification manifest not found at {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def read_file_safe(path: str) -> tuple[bool, str]:
    """Returns (found, content). Never raises."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return True, f.read()
    except FileNotFoundError:
        return False, ""
    except Exception as e:
        return False, f"[READ ERROR: {e}]"


def build_target(
    source_root: str,
    classification: dict,
    target_name: str,
    target_cfg: dict,
    now_utc: str,
) -> tuple[str, dict]:
    """
    Build a single ingest target. Returns (output_text, build_record).
    build_record has: target, types, files_included, files_missing, hash
    """
    type_priority   = classification["type_priority"]
    allowed_types   = set(target_cfg["types"])
    files_all       = classification["files"]

    # Filter to allowed types, sort by (type_priority, file_priority)
    candidates = [
        f for f in files_all if f["type"] in allowed_types
    ]
    candidates.sort(key=lambda f: (type_priority[f["type"]], f["priority"]))

    # Deduplicate by path (preserve first occurrence after sort)
    seen_paths: set[str] = set()
    ordered: list[dict] = []
    for f in candidates:
        if f["path"] not in seen_paths:
            seen_paths.add(f["path"])
            ordered.append(f)

    # Build header
    header_lines = [
        DIVIDER,
        f"PH6 INGEST BUILD: {target_name.upper()}",
        f"Generated:        {now_utc}",
        f"Description:      {target_cfg['description']}",
        f"Types included:   {', '.join(target_cfg['types'])}",
        f"Files scheduled:  {len(ordered)}",
        DIVIDER,
        "",
    ]

    body_lines: list[str] = []
    files_included: list[str] = []
    files_missing:  list[str] = []
    current_type    = None

    for entry in ordered:
        file_type = entry["type"]
        file_path = entry["path"]
        file_desc = entry.get("description", "")
        abs_path  = os.path.join(source_root, file_path)

        # Type section header
        if file_type != current_type:
            if body_lines:
                body_lines.append("")
            body_lines.extend([
                DIVIDER,
                f"TYPE: {file_type}  |  Priority tier: {type_priority[file_type]}",
                DIVIDER,
                "",
            ])
            current_type = file_type

        found, content = read_file_safe(abs_path)

        if not found:
            files_missing.append(file_path)
            body_lines.extend([
                f"[MISSING | {file_type} | {file_path}]",
                f"# {file_desc}",
                "# File not found on disk — registered but not yet present.",
                "",
            ])
            continue

        files_included.append(file_path)
        body_lines.extend([
            SECTION_DIV,
            f"[{file_type} | priority {entry['priority']} | {file_path}]",
            f"# {file_desc}",
            SECTION_DIV,
            content.rstrip(),
            "",
        ])

    # Compute hash over everything before the seal footer
    pre_seal = "\n".join(header_lines) + "\n" + "\n".join(body_lines)
    build_hash = blake2b_256(pre_seal.encode("utf-8"))

    seal_lines = [
        "",
        DIVIDER,
        "BUILD SEAL",
        f"Target:          {target_name}",
        f"Files included:  {len(files_included)}",
        f"Files missing:   {len(files_missing)}",
        f"Generated:       {now_utc}",
        f"BLAKE2b-256:     {build_hash}",
        DIVIDER,
    ]

    if files_missing:
        seal_lines.append("")
        seal_lines.append("MISSING FILES (registered but not on disk):")
        for m in files_missing:
            seal_lines.append(f"  - {m}")

    output = pre_seal + "\n".join(seal_lines) + "\n"

    build_record = {
        "target":          target_name,
        "description":     target_cfg["description"],
        "types_included":  target_cfg["types"],
        "files_included":  files_included,
        "files_missing":   files_missing,
        "file_count":      len(files_included),
        "missing_count":   len(files_missing),
        "blake2b_256":     build_hash,
        "generated_at":    now_utc,
    }

    return output, build_record


def main() -> None:
    parser = argparse.ArgumentParser(description="PH6 Ingest Compiler v1.0")
    parser.add_argument(
        "--target",
        choices=["minimal", "engineering", "governance", "validation", "forensic", "full_canon"],
        help="Build a single target (default: all)",
    )
    parser.add_argument(
        "--source-root",
        default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        help="Path to PH6_SOURCE root (default: parent of TOOLS/)",
    )
    args = parser.parse_args()

    source_root = args.source_root
    if not os.path.isdir(source_root):
        sys.exit(f"FATAL: source root not found: {source_root}")

    classification = load_classification(source_root)
    all_targets    = classification["build_targets"]
    now_utc        = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    targets_to_build = (
        {args.target: all_targets[args.target]}
        if args.target
        else all_targets
    )

    builds_dir = os.path.join(source_root, BUILDS_DIR_NAME)
    os.makedirs(builds_dir, exist_ok=True)

    build_records: list[dict] = []

    for target_name, target_cfg in targets_to_build.items():
        print(f"Building: {target_name} ...", end=" ", flush=True)
        output, record = build_target(
            source_root, classification, target_name, target_cfg, now_utc
        )

        out_path = os.path.join(builds_dir, f"{target_name}_ingest.txt")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(output)

        build_records.append(record)
        status = "PASS" if record["missing_count"] == 0 else f"WARN ({record['missing_count']} missing)"
        print(f"{status}  |  {record['file_count']} files  |  {record['blake2b_256'][:16]}...")

    # Write build manifest
    manifest = {
        "schema":             "ph6.ingest.build_manifest.v1",
        "generated_at_utc":  now_utc,
        "source_root":        source_root,
        "classification":     CLASSIFICATION_REL,
        "builds":             build_records,
        "compiler_version":   "1.0",
    }
    manifest_path = os.path.join(builds_dir, "build_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"\nBuild manifest: {manifest_path}")

    missing_total = sum(r["missing_count"] for r in build_records)
    if missing_total > 0:
        print(f"\nWARNING: {missing_total} registered files missing from disk across all builds.")
        print("Run with --target <name> to see details in the output file.")
        sys.exit(1)
    else:
        print(f"\nAll builds PASS. No missing files.")


if __name__ == "__main__":
    main()
