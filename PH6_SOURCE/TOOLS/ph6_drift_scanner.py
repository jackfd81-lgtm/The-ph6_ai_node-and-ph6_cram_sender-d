#!/usr/bin/env python3
"""
PH6 Session Drift Scanner v1.0

Detects deterministic contradictions between ingest state and session content.
Steps 1-4 produce authoritative findings. Step 5 is advisory only.

This scanner NEVER:
  - infers hidden cognition
  - claims semantic certainty
  - asserts internal attention state
  - claims "AI understood correctly"
  - issues PASS/DROP

Usage:
  python3 ph6_drift_scanner.py --session-text transcript.txt
  python3 ph6_drift_scanner.py --receipt builds/receipts/<id>.json --session-text file.txt
  python3 ph6_drift_scanner.py --stdin < transcript.txt
  python3 ph6_drift_scanner.py --session-text code.py --json

Output model (canonical):
  {
    "session_id": "...",
    "build_hash": "...",
    "build_verified": true,
    "law_assertions_checked": N,
    "deterministic_contradictions": 0,
    "advisory_semantic_warnings": 0,
    "drift_status": "PASS|WARN|FAIL",
    "authority_level": "DETERMINISTIC"
  }
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


_SOURCE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_BUILDS_DIR  = os.path.join(_SOURCE_ROOT, "builds")
_GOV_DIR     = os.path.join(_SOURCE_ROOT, "GOVERNANCE")
_GOV_MANIFEST    = os.path.join(_GOV_DIR, "governance_manifest.json")
_SCHEMA_LOCK     = os.path.join(_GOV_DIR, "schema_lock_registry.json")
_FORBIDDEN_TERMS = os.path.join(_GOV_DIR, "forbidden_terms_registry.json")
_RECEIPTS_DIR    = os.path.join(_BUILDS_DIR, "receipts")
_SEAL_MARKER     = "\n" + "=" * 80 + "\nBUILD SEAL"


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _blake2b(data: bytes) -> str:
    return hashlib.blake2b(data, digest_size=32).hexdigest()


def _load_json(path: str) -> Any:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def _canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False,
                      allow_nan=False, separators=(",", ":"))


def _pre_seal_hash(path: str) -> str | None:
    try:
        content = Path(path).read_text(encoding="utf-8")
        idx = content.find(_SEAL_MARKER)
        payload = content[:idx] if idx != -1 else content
        return _blake2b(payload.encode("utf-8"))
    except FileNotFoundError:
        return None


# ── Step 1: Read session anchor ───────────────────────────────────────────────

def step1_read_anchor(receipt_path: str | None) -> dict:
    """
    Read session anchor receipt.
    Returns anchor dict. If no receipt provided, returns minimal stub.
    """
    if receipt_path:
        data = _load_json(receipt_path)
        if data and data.get("schema") == "ph6.ingest.receipt.v1":
            return {
                "session_id":   data.get("session_id", "unknown"),
                "profile":      data.get("profile", "unknown"),
                "build_hash":   data.get("build_hash"),
                "build_verified": data.get("build_verified", False),
                "load_order":   data.get("load_order", "UNKNOWN"),
                "receipt_path": receipt_path,
                "anchor_found": True,
            }
        return {
            "session_id":   "unknown",
            "profile":      "unknown",
            "build_hash":   None,
            "build_verified": False,
            "load_order":   "UNKNOWN",
            "receipt_path": receipt_path,
            "anchor_found": False,
            "anchor_error": f"Invalid or missing receipt at {receipt_path}",
        }

    # No receipt — use latest if available
    latest = _find_latest_receipt()
    if latest:
        return step1_read_anchor(latest)

    return {
        "session_id":   "none",
        "profile":      "none",
        "build_hash":   None,
        "build_verified": False,
        "load_order":   "UNKNOWN",
        "receipt_path": None,
        "anchor_found": False,
        "anchor_note":  "No receipt provided. Drift scan proceeds without session anchor.",
    }


def _find_latest_receipt() -> str | None:
    try:
        receipts = sorted(Path(_RECEIPTS_DIR).glob("*.json"))
        return str(receipts[-1]) if receipts else None
    except FileNotFoundError:
        return None


# ── Step 2: Reverify build ────────────────────────────────────────────────────

def step2_reverify_build(anchor: dict) -> dict:
    """
    Reverify the build referenced in the session anchor.
    Returns verification result dict.
    """
    profile = anchor.get("profile", "none")
    stored_hash = anchor.get("build_hash")

    if profile == "none" or not stored_hash:
        return {
            "verified":      False,
            "profile":       profile,
            "stored_hash":   stored_hash,
            "actual_hash":   None,
            "skipped":       True,
            "skip_reason":   "No build profile or hash in anchor",
        }

    build_path = os.path.join(_BUILDS_DIR, f"{profile}_ingest.txt")
    actual_hash = _pre_seal_hash(build_path)

    return {
        "verified":      actual_hash is not None and actual_hash == stored_hash,
        "profile":       profile,
        "stored_hash":   stored_hash,
        "actual_hash":   actual_hash,
        "build_path":    build_path,
        "skipped":       False,
    }


# ── Step 3: Extract law assertions ───────────────────────────────────────────

def step3_extract_assertions() -> list[dict]:
    """
    Extract machine-checkable law assertions from governance files.
    Returns list of assertion dicts with associated contradiction patterns.
    """
    gm = _load_json(_GOV_MANIFEST) or {}
    sl = _load_json(_SCHEMA_LOCK) or {}
    assertions = []

    forbidden_fields = gm.get("forbidden_fields", [])
    stop_ship = gm.get("stop_ship_gates", [])
    forbidden_events = gm.get("forbidden_audit_event_types", [])

    def add(assertion_id: str, statement: str, violation_class: str,
            patterns: list[str], severity: str = "HIGH") -> None:
        assertions.append({
            "assertion_id":        assertion_id,
            "statement":           statement,
            "violation_class":     violation_class,
            "severity":            severity,
            "contradiction_patterns": patterns,
        })

    # Authority assertions
    add("LA-001", "Lane 2 authority = ZERO", "G5",
        [r"(?:AI|Lane\s*2|advisory|SoSo|swarm|token)\s+(?:issued?|approved?|decided?)\s+(?:PASS|DROP)",
         r"Lane\s*2\s+authority\s*[=:]\s*(?!ZERO|NONE|zero|none)"],
        "CRITICAL")

    add("LA-002", "Only PSEUDO-A may issue PASS/DROP", "G5",
        [r"(?:SoSo|swarm|AI|Claude|Gemini|GPT|token)\s+(?:issued?|emits?|produces?|generates?)\s+(?:PASS|DROP)",
         r"(?:advisory|Lane\s*2)\s+verdict"],
        "CRITICAL")

    add("LA-003", "RSYNC priority = ABSOLUTE and must never be blocked", "O1",
        [r"(?:block|pause|stop|halt|delay|starve)\s+RSYNC",
         r"RSYNC\s+(?:is|was|will\s+be)\s+(?:blocked|paused|stopped|halted)"],
        "CRITICAL")

    add("LA-004", "Lane 2 outputs may not enter CRAM-A or CRAM-0", "G5",
        [r"(?:AI|SoSo|swarm|advisory)\s+(?:writes?|wrote|committed?)\s+(?:to\s+)?CRAM[-\s]?[A0]",
         r"(?:MRAM-S|advisory)\s+output\s+(?:into|to)\s+CRAM[-\s]?A"],
        "CRITICAL")

    add("LA-005", "CRAM-A records are immutable after commit", "C2",
        [r"mutat(?:e|ed|ing)\s+CRAM[-\s]?A",
         r"modif(?:y|ied|ying)\s+CRAM[-\s]?A"],
        "HIGH")

    add("LA-006", "CRAM atomic write contract must be preserved", "C1",
        [r"direct\s+write\s+to\s+CRAM",
         r"write\s+(?:directly|without\s+tmp)\s+to\s+CRAM"],
        "HIGH")

    # Field assertions — patterns loaded from governance manifest
    for ff in forbidden_fields:
        add(f"LA-FF-{ff}", f"Field '{ff}' is forbidden in all authoritative records", "S1",
            [rf'["\']?{re.escape(ff)}["\']?\s*[:=]',
             rf'\.get\(["\'{re.escape(ff)}"\']',
             rf'record\[.{re.escape(ff)}.\]'],
            "HIGH")

    add("LA-007", "Canonical metric field = motion_fraction (not deprecated aliases)", "S1",
        [],  # Covered by forbidden_fields above
        "HIGH")

    add("LA-008", "Canonical hash algorithm = BLAKE2b-256", "S2",
        [r"(?:sha256|sha-256|SHA256)\s+(?:is|as)\s+(?:the\s+)?(?:canonical|authoritative|primary)\s+hash"],
        "MEDIUM")

    add("LA-009", "Authoritative evidence marker = .blake2b (not .sha256)", "S2",
        [r"\.sha256\s+(?:is|as)\s+(?:the\s+)?(?:canonical|authoritative|primary)"],
        "MEDIUM")

    add("LA-010", "Metric encoding = fixedpoint integer; raw floats forbidden in authority", "S4",
        [r"float\s+(?:metric|value|field)\s+in\s+(?:verdict|CRAM|authority)",
         r"raw\s+float\s+in\s+(?:CRAM|verdict|authority|canonical)"],
        "HIGH")

    # Stop-ship assertions
    for gate in stop_ship:
        if gate.get("status") == "OPEN":
            gid = gate["id"]
            desc = gate.get("description", "")
            add(f"LA-STOP-{gid}", f"{gid} is OPEN STOP-SHIP — not closeable by software", "G8",
                [rf"{re.escape(gid)}\s+(?:is\s+)?(?:CLOSED|closed|complete|done|finished)",
                 rf"{re.escape(gid)}\s+(?:marked|=|:)\s+(?:CLOSED|closed)"],
                "CRITICAL")

    add("LA-HRG9", "HRG9 is CLOSED at commit 2ef5fd6", "G8",
        [r"HRG9\s+(?:is\s+)?(?:OPEN|open)",
         r"HRG9.*(?:STOP-SHIP|stop.ship|still\s+open)"],
        "HIGH")

    # Forbidden audit event types
    if forbidden_events:
        for evt in forbidden_events:
            add(f"LA-EVT-{evt}", f"Audit event type '{evt}' is forbidden", "A2",
                [rf'["\']?{re.escape(evt)}["\']?\s*[:=]',
                 rf'event_type["\']?\s*[=:]\s*["\']?{re.escape(evt)}'],
                "HIGH")

    # Schema lock assertions
    locked = sl.get("locked_schemas", [])
    for s in locked:
        sid = s.get("schema_id", "")
        for ff in s.get("forbidden_fields", []):
            add(f"LA-SL-{sid}-{ff}", f"Schema '{sid}' forbids field '{ff}'", "S1",
                [rf'["\']?{re.escape(ff)}["\']?\s*[:=]'],
                "HIGH")

    return assertions


# ── Step 4: Detect deterministic contradictions ───────────────────────────────

def step4_detect_contradictions(
    assertions: list[dict],
    text: str,
) -> list[dict]:
    """
    Scan text for explicit contradictions of law assertions.
    Returns list of contradiction findings. These are AUTHORITATIVE.
    """
    findings = []
    lines = text.splitlines()

    for assertion in assertions:
        for pattern_str in assertion.get("contradiction_patterns", []):
            try:
                pattern = re.compile(pattern_str, re.IGNORECASE)
            except re.error:
                continue

            for lineno, line in enumerate(lines, 1):
                if pattern.search(line):
                    findings.append({
                        "type":            "deterministic_contradiction",
                        "assertion_id":    assertion["assertion_id"],
                        "violation_class": assertion["violation_class"],
                        "severity":        assertion["severity"],
                        "statement":       assertion["statement"],
                        "line_number":     lineno,
                        "matched_line":    line.strip()[:200],
                        "pattern":         pattern_str,
                        "authoritative":   True,
                    })
                    break  # one finding per assertion per pattern per line is enough

    return findings


# ── Step 5: Advisory semantic warnings (NOT authoritative) ───────────────────

# Advisory patterns: softer signals that MAY indicate drift.
# These are NOT violations — they are hints for human review.
_ADVISORY_PATTERNS: list[tuple[str, str, str]] = [
    (r"(?:probably|likely|should\s+be)\s+(?:PASS|DROP)",
     "Probabilistic verdict language near PASS/DROP",
     "AW-001"),
    (r"AI\s+(?:can|could|may|will)\s+determine\s+(?:whether|if)",
     "AI claiming determination authority",
     "AW-002"),
    (r"(?:assume|assuming)\s+(?:the\s+)?(?:gap|OI-\d+|gate)\s+(?:is\s+)?(?:closed|done|resolved)",
     "Gap assumed closed without evidence",
     "AW-003"),
    (r"(?:advisory|Lane\s*2)\s+output\s+(?:is|becomes?)\s+(?:canonical|authoritative|evidence)",
     "Advisory output treated as authoritative",
     "AW-004"),
    (r"(?:soft|weak|partial|approximate)\s+authority",
     "Non-binary authority language",
     "AW-005"),
    (r"AI\s+understood\s+(?:correctly|the\s+context|this)",
     "AI self-certifying comprehension",
     "AW-006"),
    (r"(?:blend|merge|combine|average)\s+(?:the\s+)?(?:contradictory|conflicting|different)\s+(?:doctrine|versions?|sources?)",
     "Doctrine blending suggested",
     "AW-007"),
]


def step5_advisory_warnings(text: str) -> list[dict]:
    """
    Scan for soft patterns that may indicate drift. ADVISORY ONLY.
    Never authoritative. Never blocks commits. Never issues verdicts.
    """
    warnings = []
    lines = text.splitlines()

    for pattern_str, description, warning_id in _ADVISORY_PATTERNS:
        try:
            pattern = re.compile(pattern_str, re.IGNORECASE)
        except re.error:
            continue

        for lineno, line in enumerate(lines, 1):
            if pattern.search(line):
                warnings.append({
                    "type":          "advisory_semantic_warning",
                    "warning_id":    warning_id,
                    "description":   description,
                    "line_number":   lineno,
                    "matched_line":  line.strip()[:200],
                    "authoritative": False,
                    "note":          "Advisory only. Does not block. Human review required.",
                })
                break

    return warnings


# ── Report assembly ───────────────────────────────────────────────────────────

def build_report(
    anchor: dict,
    reverify: dict,
    assertions: list[dict],
    contradictions: list[dict],
    warnings: list[dict],
    now: str,
    source_label: str,
) -> dict:
    n_contra = len(contradictions)
    n_warn   = len(warnings)
    verified = reverify.get("verified", False)

    if n_contra > 0:
        drift_status = "FAIL"
    elif not verified and not reverify.get("skipped"):
        drift_status = "WARN"
    elif n_warn > 0:
        drift_status = "WARN"
    else:
        drift_status = "PASS"

    return {
        "schema":                      "ph6.drift_scan.v1",
        "session_id":                  anchor.get("session_id", "none"),
        "profile":                     anchor.get("profile", "none"),
        "build_hash":                  anchor.get("build_hash"),
        "build_verified":              verified,
        "load_order":                  anchor.get("load_order", "UNKNOWN"),
        "law_assertions_checked":      len(assertions),
        "deterministic_contradictions": n_contra,
        "advisory_semantic_warnings":  n_warn,
        "drift_status":                drift_status,
        "authority_level":             "DETERMINISTIC",
        "step5_authority_note":        "Advisory warnings are not authoritative. Step 5 may warn. Step 5 may not decide.",
        "source_scanned":              source_label,
        "generated_at_utc":            now,
        "findings": {
            "contradictions": contradictions,
            "warnings":       warnings,
        },
    }


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="PH6 Session Drift Scanner v1.0")
    parser.add_argument("--receipt",      default="", help="Path to ingest receipt JSON")
    parser.add_argument("--session-text", default="", help="Path to text file to scan")
    parser.add_argument("--stdin",        action="store_true", help="Read text from stdin")
    parser.add_argument("--json",         action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args()

    # Read session text
    if args.stdin:
        text = sys.stdin.read()
        source_label = "stdin"
    elif args.session_text:
        try:
            text = Path(args.session_text).read_text(encoding="utf-8", errors="replace")
            source_label = args.session_text
        except FileNotFoundError:
            sys.exit(f"FATAL: session text file not found: {args.session_text}")
    else:
        sys.exit("FATAL: provide --session-text <file> or --stdin")

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Steps 1–5
    anchor        = step1_read_anchor(args.receipt or None)
    reverify      = step2_reverify_build(anchor)
    assertions    = step3_extract_assertions()
    contradictions = step4_detect_contradictions(assertions, text)
    warnings      = step5_advisory_warnings(text)

    report = build_report(anchor, reverify, assertions, contradictions, warnings,
                          now, source_label)

    if args.json:
        print(_canonical(report))
        sys.exit(0 if report["drift_status"] == "PASS" else 1)

    # Human-readable summary
    status = report["drift_status"]
    print(f"PH6 DRIFT SCAN: {status}")
    print(f"  Source:         {source_label}")
    print(f"  Session:        {report['session_id']}")
    print(f"  Profile:        {report['profile']}")
    print(f"  Build verified: {report['build_verified']}")
    print(f"  Assertions:     {report['law_assertions_checked']}")
    print(f"  Contradictions: {report['deterministic_contradictions']} (authoritative)")
    print(f"  Warnings:       {report['advisory_semantic_warnings']} (advisory only)")

    if contradictions:
        print("\n  DETERMINISTIC CONTRADICTIONS (authoritative):")
        for c in contradictions:
            print(f"    [{c['violation_class']}] {c['severity']} — {c['statement']}")
            print(f"      Line {c['line_number']}: {c['matched_line'][:100]}")

    if warnings:
        print("\n  ADVISORY WARNINGS (not authoritative — human review):")
        for w in warnings:
            print(f"    [{w['warning_id']}] {w['description']}")
            print(f"      Line {w['line_number']}: {w['matched_line'][:100]}")

    sys.exit(0 if status in ("PASS", "WARN") else 1)


if __name__ == "__main__":
    main()
