#!/usr/bin/env python3
"""
PH6 AI Preload Pack Generator v1.0

Assembles PH6_AI_PRELOAD_PACK_vX.txt — a deterministic, hash-sealed six-section
document that correctly primes an AI session before any content is loaded.

Sections (in mandatory load order):
  00 — AI Ingest Protocol     (static, human-curated)
  01 — Session Anchor         (generated from build manifest)
  02 — Current Master Canon   (selected build profile content)
  03 — Law Assertions         (generated from governance files)
  04 — Open Gaps Register     (from GAP_REGISTER)
  05 — Forbidden Terms & Drift Rules (from forbidden_terms_registry)
  06 — Task Instructions      (provided at generation time)

Output: PH6_SOURCE/AI_PRELOAD/PH6_AI_PRELOAD_PACK_v1.0.txt

Usage:
  python3 ph6_pack_generator.py --profile minimal --task "Review verdict_logger changes"
  python3 ph6_pack_generator.py --profile engineering --task-file /path/to/task.md
  python3 ph6_pack_generator.py --profile minimal  # no task — stub included
"""

import argparse
import hashlib
import json
import os
import secrets
import sys
from datetime import datetime, timezone
from pathlib import Path


_SOURCE_ROOT  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PRELOAD_DIR  = os.path.join(_SOURCE_ROOT, "AI_PRELOAD")
_BUILDS_DIR   = os.path.join(_SOURCE_ROOT, "builds")
_GOV_DIR      = os.path.join(_SOURCE_ROOT, "GOVERNANCE")
_CLF_PATH     = os.path.join(_GOV_DIR, "ingest_classification.json")
_SEAL_MARKER  = "\n" + "=" * 80 + "\nBUILD SEAL"

_PROTOCOL_FILE      = os.path.join(_PRELOAD_DIR, "00_READ_FIRST_AI_INGEST_PROTOCOL.md")
_MANIFEST_FILE      = os.path.join(_BUILDS_DIR, "build_manifest.json")
_GOV_MANIFEST       = os.path.join(_GOV_DIR, "governance_manifest.json")
_SCHEMA_LOCK        = os.path.join(_GOV_DIR, "schema_lock_registry.json")
_FORBIDDEN_TERMS    = os.path.join(_GOV_DIR, "forbidden_terms_registry.json")
_GAP_REGISTER       = os.path.join(_SOURCE_ROOT, "GAP_REGISTER_v3.0.md")
_GLOSSARY           = os.path.join(_SOURCE_ROOT, "GLOSSARY_LOCK.md")

_DIVIDER     = "=" * 80
_SECTION_DIV = "-" * 80
_TYPE_ORDER  = ("LAW", "SCHEMA", "RUNTIME", "STATE", "GAP", "TEST", "HISTORY")

PROFILES = ("minimal", "engineering", "governance", "validation", "forensic", "full_canon")


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _blake2b(data: bytes) -> str:
    return hashlib.blake2b(data, digest_size=32).hexdigest()


def _canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, allow_nan=False,
                      separators=(",", ":"))


def _read(path: str) -> str:
    try:
        return Path(path).read_text(encoding="utf-8")
    except FileNotFoundError:
        return f"[FILE NOT FOUND: {path}]"


def _load_json(path: str) -> dict | list | None:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def _load_order_string(profile: str) -> str:
    clf = _load_json(_CLF_PATH)
    if not clf:
        return "UNKNOWN"
    types = clf.get("build_targets", {}).get(profile, {}).get("types", [])
    return ">".join(t for t in _TYPE_ORDER if t in types)


def _pre_seal_hash(path: str) -> str | None:
    try:
        content = Path(path).read_text(encoding="utf-8")
        idx = content.find(_SEAL_MARKER)
        payload = content[:idx] if idx != -1 else content
        return _blake2b(payload.encode("utf-8"))
    except FileNotFoundError:
        return None


# ── Section builders ─────────────────────────────────────────────────────────

def section_header(num: int, title: str) -> str:
    return f"\n{_DIVIDER}\nSECTION {num:02d}: {title}\n{_DIVIDER}\n"


def build_section_00(now: str) -> str:
    """Static AI Ingest Protocol."""
    content = _read(_PROTOCOL_FILE)
    return section_header(0, "AI INGEST PROTOCOL") + content


def build_section_01(profile: str, now: str) -> str:
    """Session Anchor — generated from build manifest."""
    manifest = _load_json(_MANIFEST_FILE)
    session_id = f"ses-{secrets.token_hex(8)}"
    build_hash = None
    file_count = 0
    verified = False

    if manifest:
        built = {b["target"]: b for b in manifest.get("builds", [])}
        if profile in built:
            rec = built[profile]
            stored_hash = rec.get("blake2b_256")
            build_path = os.path.join(_BUILDS_DIR, f"{profile}_ingest.txt")
            actual_hash = _pre_seal_hash(build_path)
            verified = (actual_hash is not None) and (actual_hash == stored_hash)
            build_hash = actual_hash
            file_count = rec.get("file_count", 0)

    load_order = _load_order_string(profile)

    anchor = {
        "schema":           "ph6.ingest.receipt.v1",
        "receipt_version":  "1.0",
        "session_id":       session_id,
        "authority_level":  "SESSION-ANCHOR",
        "profile":          profile,
        "load_order":       load_order,
        "build_exists":     manifest is not None,
        "build_verified":   verified,
        "build_loaded":     True,
        "build_respected":  None,
        "build_respected_note": "Not machine-verifiable. Lane 2 advisory only.",
        "build_hash":       build_hash,
        "files_in_build":   file_count,
        "timestamp_utc":    now,
    }

    body = (
        f"Session ID:    {session_id}\n"
        f"Profile:       {profile}\n"
        f"Load order:    {load_order}\n"
        f"Build hash:    {build_hash or 'UNVERIFIED'}\n"
        f"Verified:      {verified}\n"
        f"Files:         {file_count}\n"
        f"Generated:     {now}\n"
        f"\n"
        f"LAW precedes SCHEMA precedes RUNTIME precedes STATE.\n"
        f"Runtime evidence outranks documentation.\n"
        f"build_respected = advisory only (not machine-verifiable).\n"
        f"\n"
        f"Machine-readable receipt:\n"
        f"{_canonical(anchor)}\n"
    )
    return section_header(1, "SESSION ANCHOR") + body


def build_section_02(profile: str) -> str:
    """
    Current Master Canon — the selected build profile content.
    For large profiles (engineering/forensic/full_canon) this section is a
    reference pointer rather than inline content to keep the pack usable.
    """
    build_path = os.path.join(_BUILDS_DIR, f"{profile}_ingest.txt")
    size = 0
    try:
        size = os.path.getsize(build_path)
    except FileNotFoundError:
        pass

    INLINE_THRESHOLD = 150 * 1024  # 150K — inline if small enough

    header = section_header(2, f"CURRENT MASTER CANON ({profile.upper()} PROFILE)")

    if not os.path.isfile(build_path):
        return header + f"[BUILD NOT FOUND: {build_path}]\nRun: python3 TOOLS/ph6_ingest_compiler.py\n"

    if size > INLINE_THRESHOLD:
        h = _pre_seal_hash(build_path) or "unknown"
        return (
            header
            + f"Profile '{profile}' build ({size // 1024}K) exceeds inline threshold.\n"
            f"Load separately: {build_path}\n"
            f"Build hash: {h}\n"
            f"\nFor pack usage, prefer 'minimal' or 'governance' profiles.\n"
        )

    return header + _read(build_path)


def build_section_03(now: str) -> str:
    """Law Assertions — machine-checkable invariants from governance files."""
    gm = _load_json(_GOV_MANIFEST) or {}
    sl = _load_json(_SCHEMA_LOCK) or {}

    assertions = []
    idx = 1

    def add(category: str, assertion: str, violation_class: str,
            forbidden_if: str, source: str):
        nonlocal idx
        assertions.append({
            "id":              f"LA-{idx:03d}",
            "category":        category,
            "assertion":       assertion,
            "violation_class": violation_class,
            "forbidden_if":    forbidden_if,
            "source":          source,
        })
        idx += 1

    # Authority assertions
    add("authority", "Lane 2 authority = ZERO",           "G5", "AI claims PASS/DROP authority", "governance_manifest.json")
    add("authority", "PASS/DROP authority = Lane 1 only", "G5", "non-Lane-1 component issues verdict", "governance_manifest.json")
    add("authority", "CVS-3 authority = VERIFY ONLY",     "G5", "validator alters PASS/DROP", "PH6-CVS3-VALIDATION-GOVERNOR-v6.9.md")
    add("authority", "RSYNC priority = ABSOLUTE",         "O1", "RSYNC is blocked or resource-starved", "governance_manifest.json")
    add("authority", "Advisory output replay_dependency = false", "G5", "Lane 2 output becomes replay dependency", "governance_manifest.json")

    # Field assertions
    forbidden_fields = gm.get("forbidden_fields", [])
    for ff in forbidden_fields:
        add("schema", f"Field '{ff}' is FORBIDDEN in all authoritative records", "S1",
            f"field '{ff}' appears in verdict or CRAM record", "governance_manifest.json")
    ff_str = " or ".join(forbidden_fields) if forbidden_fields else "forbidden metric fields"
    add("schema", "Canonical metric field = motion_fraction",       "S1", f"{ff_str} used", "governance_manifest.json")
    add("schema", "Canonical hash algorithm = BLAKE2b-256",         "S2", "SHA256 used as authoritative hash", "governance_manifest.json")
    add("schema", "Authoritative evidence marker = .blake2b",       "S2", ".sha256 used as authority marker", "governance_manifest.json")
    add("schema", "Metric encoding = fixedpoint integer scale=10000", "S4", "raw float used in authoritative metric field", "verdict_logger.py")
    add("schema", "metric_schema = ph6.metrics.fixedpoint.v1",      "S2", "metric_schema field missing from verdict records", "verdict_logger.py")

    # Write contract assertions
    add("cram",   "CRAM atomic write contract = write_tmp → fsync_file → rename → fsync_dir", "C1",
        "CRAM write uses non-atomic sequence", "governance_manifest.json")
    add("cram",   "CRAM-A records are immutable after commit",       "C2", "CRAM-A record mutated after write", "governance_manifest.json")
    add("cram",   "CRAM-R may not contain .blake2b markers",        "C3", ".blake2b marker appears in CRAM-R", "governance_manifest.json")

    # Stop-ship assertions
    stop_ship = gm.get("stop_ship_gates", [])
    for gate in stop_ship:
        if gate.get("status") == "OPEN":
            gid = gate["id"]
            desc = gate.get("description", "")
            add("stop_ship", f"{gid} is OPEN STOP-SHIP — hardware-gated",
                "G8", f"{gid} marked CLOSED without human-provided hardware evidence",
                "governance_manifest.json")

    add("stop_ship", "HRG9 is CLOSED at commit 2ef5fd6",            "G8",
        "HRG9 listed as open or regenerated", "governance_manifest.json")

    # Forbidden audit event types
    forbidden_events = gm.get("forbidden_audit_event_types", [])
    if forbidden_events:
        add("audit", f"Forbidden audit event types: {', '.join(forbidden_events)}", "A2",
            "any of these event types appears in an audit record", "governance_manifest.json")

    # Schema lock assertions
    locked_schemas = sl.get("locked_schemas", [])
    for s in locked_schemas:
        sid = s.get("schema_id", "")
        if s.get("locked"):
            ff = s.get("forbidden_fields", [])
            if ff:
                add("schema", f"Schema '{sid}' forbids fields: {', '.join(ff)}", "S1",
                    f"forbidden field appears in {sid} record", "schema_lock_registry.json")

    doc = {
        "schema":            "ph6.law_assertions.v1",
        "generated_at_utc":  now,
        "assertion_count":   len(assertions),
        "authority":         "GENERATED — derived deterministically from governance files. "
                             "Do not edit directly. Regenerate via ph6_pack_generator.py.",
        "assertions":        assertions,
    }

    body = (
        "Machine-checkable law assertions derived from governance_manifest.json,\n"
        "schema_lock_registry.json, and runtime contracts.\n\n"
        "IF you are about to produce output that violates an assertion below:\n"
        "STOP. State the violation. Do not proceed.\n\n"
        f"{json.dumps(doc, indent=2, ensure_ascii=False, sort_keys=True)}\n"
    )
    return section_header(3, "LAW ASSERTIONS (MACHINE-CHECKABLE)") + body


def build_section_04() -> str:
    """Open Gaps Register."""
    return section_header(4, "OPEN GAPS REGISTER") + _read(_GAP_REGISTER)


def build_section_05() -> str:
    """Forbidden Terms and Drift Rules."""
    ft = _load_json(_FORBIDDEN_TERMS) or {}
    terms = ft.get("forbidden_terms", ft.get("terms", []))

    lines = [
        "Forbidden terms are scanned on every governance commit.\n",
        "Using a forbidden term in an authority path is a G3 (Governance) failure.\n\n",
    ]

    if isinstance(terms, list) and terms:
        lines.append("FORBIDDEN TERMS:\n")
        for t in terms:
            if isinstance(t, dict):
                lines.append(f"  - {t.get('term', t)}: {t.get('reason', '')}\n")
            else:
                lines.append(f"  - {t}\n")
    else:
        lines.append(f"[Source: {_FORBIDDEN_TERMS}]\n")
        lines.append(_read(_FORBIDDEN_TERMS))

    # Load forbidden fields from governance manifest to avoid hardcoding them here
    gm_data = _load_json(_GOV_MANIFEST) or {}
    ffd = gm_data.get("forbidden_fields", [])
    forbidden_field_line = (
        f"  DRIFT: using forbidden metric fields ({', '.join(ffd)})\n"
        if ffd else
        "  DRIFT: using forbidden metric fields (see governance_manifest.json)\n"
    )

    lines += [
        "\nDRIFT DETECTION RULES:\n",
        "Stop and report (do not proceed) if you produce:\n",
        "  DRIFT: claiming Lane 2 may decide\n",
        "  DRIFT: claiming tokens are authoritative\n",
        "  DRIFT: claiming RSYNC may be blocked\n",
        "  DRIFT: claiming floats are canonical\n",
        "  DRIFT: claiming replay is optional\n",
        "  DRIFT: claiming a STOP-SHIP gate is closed without evidence\n",
        forbidden_field_line,
        "  DRIFT: treating commentary as authority\n",
        "  DRIFT: blending contradictory doctrine\n",
        "  DRIFT: calling advisory output a 'verdict'\n",
    ]
    return section_header(5, "FORBIDDEN TERMS AND DRIFT RULES") + "".join(lines)


def build_section_06(task: str) -> str:
    """Task Instructions — session-specific."""
    if not task:
        task = (
            "[NO TASK PROVIDED]\n\n"
            "This pack was generated without a specific task.\n"
            "Add task instructions with: --task 'your task' or --task-file path\n"
        )
    return section_header(6, "TASK INSTRUCTIONS") + task + "\n"


# ── Pack assembly ─────────────────────────────────────────────────────────────

def assemble_pack(profile: str, task: str, now: str) -> str:
    header_lines = [
        _DIVIDER,
        "PH6 AI PRELOAD PACK v1.0",
        f"Generated:  {now}",
        f"Profile:    {profile}",
        f"Load order: {_load_order_string(profile)}",
        _DIVIDER,
        "",
        "READ SECTION 00 FIRST. DO NOT SKIP. DO NOT REORDER.",
        "Protocol first. Canon second. Assertions third. Gaps fourth. Task last.",
        "",
    ]
    header = "\n".join(header_lines)

    sections = [
        build_section_00(now),
        build_section_01(profile, now),
        build_section_02(profile),
        build_section_03(now),
        build_section_04(),
        build_section_05(),
        build_section_06(task),
    ]

    body = header + "".join(sections)
    pack_hash = _blake2b(body.encode("utf-8"))

    seal = (
        f"\n{_DIVIDER}\nPACK SEAL\n"
        f"Profile:    {profile}\n"
        f"Generated:  {now}\n"
        f"BLAKE2b-256: {pack_hash}\n"
        f"{_DIVIDER}\n"
    )
    return body + seal


def main() -> None:
    parser = argparse.ArgumentParser(description="PH6 AI Preload Pack Generator v1.0")
    parser.add_argument("--profile", choices=PROFILES, default="minimal",
                        help="Ingest profile (default: minimal)")
    parser.add_argument("--task", default="", help="Task instructions (inline text)")
    parser.add_argument("--task-file", default="", help="Task instructions from file")
    parser.add_argument("--output", default="",
                        help="Output path (default: AI_PRELOAD/PH6_AI_PRELOAD_PACK_v1.0.txt)")
    args = parser.parse_args()

    task = args.task
    if args.task_file:
        task = _read(args.task_file)

    now = _utc_now()
    pack = assemble_pack(args.profile, task, now)

    out_path = args.output or os.path.join(_PRELOAD_DIR, "PH6_AI_PRELOAD_PACK_v1.0.txt")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(pack)

    # Extract hash from seal line for reporting
    for line in pack.splitlines():
        if line.startswith("BLAKE2b-256:"):
            print(f"Pack generated: {out_path}")
            print(f"Hash:           {line.split(':', 1)[1].strip()}")
            break
    print(f"Profile:        {args.profile}")
    print(f"Sections:       00-06")


if __name__ == "__main__":
    main()
