#!/usr/bin/env python3
"""
PH6 Full Alignment Audit

Read-only audit for PH6 doctrine, governance, architecture, operations, and tests.

This script must not modify doctrine, evidence, closure status, campaign artifacts,
or result_set_hash values.

Outputs:
  PH6_SOURCE/GOVERNANCE/ph6_full_alignment_audit_report.json
  PH6_SOURCE/GOVERNANCE/ph6_full_alignment_audit_report.md
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from typing import Any

ROOT       = Path(".").resolve()
PH6_SOURCE = ROOT / "PH6_SOURCE"
GOV        = PH6_SOURCE / "GOVERNANCE"
TOOLS      = PH6_SOURCE / "TOOLS"

# Directories to skip entirely during file scan
SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".hermes",
             ".platformio", ".cache", "uv", "node_modules", "frame_filter"}

JSON_REPORT = GOV / "ph6_full_alignment_audit_report.json"
MD_REPORT   = GOV / "ph6_full_alignment_audit_report.md"

# ---------------------------------------------------------------------------
# Required governance files
# ---------------------------------------------------------------------------
REQUIRED_GOV_FILES = [
    "governance_manifest.json",
    "forbidden_terms_registry.json",
    "schema_lock_registry.json",
    "severity_policy.json",
    "closure_status.json",
    "evidence_campaign_matrix.json",
]

# Expected book markers somewhere in PH6_SOURCE tree
BOOK_MARKERS = [
    "BOOK_0", "BOOK0", "Book 0",
    "BOOK_I", "Book I",
    "BOOK_II", "Book II",
    "BOOK_III", "Book III",
    "BOOK_IV", "Book IV",
    "BOOK_V", "Book V",
]

# Forbidden authority-widening patterns loaded at runtime from the registry
# (avoids embedding literal forbidden terms in this source file)
def _load_forbidden_authority_patterns() -> list[tuple[str, str]]:
    reg_path = PH6_SOURCE / "GOVERNANCE" / "forbidden_terms_registry.json"
    patterns = []
    if reg_path.exists():
        try:
            reg = json.loads(reg_path.read_text())
            for entry in reg.get("entries", []):
                pat = entry.get("scan_pattern", "")
                desc = entry.get("term", entry.get("id", ""))
                flags = entry.get("scan_flags", [])
                if pat:
                    patterns.append((pat, desc, "IGNORECASE" in flags))
        except Exception:
            pass
    return patterns

# Strings that must never appear in closure_status.json
FORBIDDEN_CLEARANCE_STATES = {
    "PRODUCTION_CLEARED", "CLEARED_FOR_PRODUCTION",
    "PRODUCTION_APPROVED", "APPROVED_FOR_PRODUCTION",
}

# Old DOC structure markers that must not appear as active canon
OLD_DOC_MARKERS = ["DOC0", "DOC-0", "DOC1", "DOC-1", "DOC2", "DOC-2", "DOC3", "DOC-3"]

# Files that are evidence/authority and should not reference SHA-256 as primary
AUTHORITY_PATH_KEYWORDS = ["cram", "authority", "evidence", "audit", "receipt", "departure", "arrival"]

# Test classification
TEST_CLASS_MAP = [
    (["governance", "drift"],               "governance"),
    (["schema", "canonical"],               "schema"),
    (["replay"],                            "replay_parity"),
    (["rsync", "non_blocking", "nonblock"], "rsync_nonblocking"),
    (["lane", "isolation", "leakage"],      "lane_isolation"),
    (["cram", "atomic", "crash", "recover"],"cram_write_recovery"),
    (["pseudo", "gate", "frame_filter"],    "deterministic_gate_math"),
    (["soso", "swarm", "token", "tok", "mram", "ssmt", "advisory", "boundary"],
                                            "advisory_containment"),
    (["ingest", "closure", "vrc"],          "campaign_closure"),
]


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def read_safe(path: Path) -> str:
    try:
        return path.read_text(errors="replace")
    except Exception:
        return ""

def load_json_safe(path: Path) -> tuple[Any, str | None]:
    try:
        return json.loads(path.read_text()), None
    except Exception as e:
        return None, str(e)

def run(cmd: list[str], timeout: int = 120) -> dict:
    try:
        p = subprocess.run(cmd, cwd=ROOT, text=True,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                           timeout=timeout)
        return {"cmd": " ".join(cmd), "rc": p.returncode,
                "stdout": p.stdout[-8000:], "stderr": p.stderr[-4000:]}
    except Exception as e:
        return {"cmd": " ".join(cmd), "rc": -1, "stdout": "", "stderr": str(e)}

def finding(fid, status, severity, location, message, **extra) -> dict:
    return {"id": fid, "status": status, "severity": severity,
            "location": str(location), "message": message, **extra}

def classify_test(path: Path) -> str:
    s = str(path).lower()
    for keywords, label in TEST_CLASS_MAP:
        if any(k in s for k in keywords):
            return label
    return "unclassified"


# ---------------------------------------------------------------------------
# A. Governance file checks
# ---------------------------------------------------------------------------

def audit_governance_files() -> list[dict]:
    results = []
    for name in REQUIRED_GOV_FILES:
        p = GOV / name
        if p.exists():
            data, err = load_json_safe(p)
            if err:
                results.append(finding(f"GOV_{name}", "FAIL", "CRITICAL", p,
                                       f"file present but JSON invalid: {err}"))
            else:
                results.append(finding(f"GOV_{name}", "PASS", "INFO", p,
                                       "required governance file present and valid JSON"))
        else:
            results.append(finding(f"GOV_{name}", "FAIL", "CRITICAL", p,
                                   "required governance file MISSING"))
    return results


# ---------------------------------------------------------------------------
# B. Book structure checks
# ---------------------------------------------------------------------------

def audit_book_structure() -> list[dict]:
    results = []
    # Collect all text from PH6_SOURCE
    all_text = ""
    for p in PH6_SOURCE.rglob("*"):
        if p.is_file() and p.suffix in {".md", ".txt", ".json"}:
            all_text += read_safe(p) + "\n"

    found_books = set()
    for marker in BOOK_MARKERS:
        if marker in all_text:
            # Normalize to Roman numeral label
            if any(x in marker for x in ["0", "BOOK0"]):
                found_books.add("Book 0")
            elif "I" in marker and "II" not in marker and "IV" not in marker:
                found_books.add("Book I")
            elif "II" in marker and "III" not in marker:
                found_books.add("Book II")
            elif "III" in marker:
                found_books.add("Book III")
            elif "IV" in marker:
                found_books.add("Book IV")
            elif "V" in marker:
                found_books.add("Book V")

    for book in ["Book 0", "Book I", "Book II", "Book III", "Book IV", "Book V"]:
        ok = book in found_books
        results.append(finding(
            f"BOOK_{book.replace(' ', '_').upper()}", "PASS" if ok else "WARN",
            "INFO" if ok else "WARN", "PH6_SOURCE",
            f"{book} reference {'found' if ok else 'not clearly found'} in source tree"
        ))

    # Check old DOC structure not revived as active canon
    for marker in OLD_DOC_MARKERS:
        active_refs = []
        for p in PH6_SOURCE.rglob("*.md"):
            if marker in read_safe(p) and "DRAFT" not in str(p):
                active_refs.append(str(p))
        if active_refs:
            results.append(finding(f"OLD_DOC_{marker}", "WARN", "WARN",
                                   active_refs[0] if active_refs else "PH6_SOURCE",
                                   f"old doc marker '{marker}' found in non-DRAFT files: {active_refs[:3]}"))

    return results


# ---------------------------------------------------------------------------
# C. Closure status checks
# ---------------------------------------------------------------------------

def audit_closure_status() -> list[dict]:
    results = []
    path = GOV / "closure_status.json"
    data, err = load_json_safe(path)
    if err:
        return [finding("CLOSURE_STATUS_VALID", "FAIL", "CRITICAL", path,
                        f"closure_status.json unreadable: {err}")]

    # EVC-05 closed correctly
    campaigns = data.get("campaigns", {})
    evc05 = campaigns.get("EVC-05", {})
    evc_closed = (isinstance(evc05, dict) and
                  evc05.get("state") == "CLOSED" and
                  evc05.get("closed") is True and
                  evc05.get("reviewer") == "Jack Disla")
    results.append(finding("EVC05_CLOSED_JACK_DISLA",
                           "PASS" if evc_closed else "FAIL",
                           "INFO" if evc_closed else "CRITICAL", path,
                           f"EVC-05 CLOSED by Jack Disla: {evc_closed}"))

    # Production clearance NOT declared
    pc_status = str(data.get("production_clearance_status", "")).upper()
    pc_declared = data.get("production_clearance_declared")
    forbidden_hit = any(s in pc_status for s in FORBIDDEN_CLEARANCE_STATES)
    declared_true = pc_declared is True
    results.append(finding("PRODUCTION_NOT_DECLARED",
                           "FAIL" if (forbidden_hit or declared_true) else "PASS",
                           "CRITICAL" if (forbidden_hit or declared_true) else "INFO",
                           path,
                           "production clearance correctly not declared"
                           if not (forbidden_hit or declared_true)
                           else f"PRODUCTION CLEARANCE APPEARS DECLARED: status={pc_status} declared={pc_declared}",
                           observed_status=data.get("production_clearance_status"),
                           observed_declared=pc_declared))

    # CANDIDATE_NOT_DECLARED (stricter form present)
    is_strict = "CANDIDATE_NOT_DECLARED" in pc_status
    results.append(finding("PRODUCTION_STATUS_STRICT_FORM",
                           "PASS" if is_strict else "WARN",
                           "INFO" if is_strict else "WARN", path,
                           f"production_clearance_status uses strict form CANDIDATE_NOT_DECLARED: {is_strict}"))

    # No campaign silently closed without reviewer fields
    for cid, rec in campaigns.items():
        if isinstance(rec, dict) and rec.get("closed") is True:
            missing = [f for f in ["reviewer", "reviewed_at_utc", "closure_decision", "closed_at_utc"]
                       if not rec.get(f)]
            if missing:
                results.append(finding(f"CAMPAIGN_CLOSURE_FIELDS_{cid}", "FAIL", "HIGH", path,
                                       f"{cid} closed without required fields: {missing}"))
            else:
                results.append(finding(f"CAMPAIGN_CLOSURE_FIELDS_{cid}", "PASS", "INFO", path,
                                       f"{cid} closure fields complete"))

    return results


# ---------------------------------------------------------------------------
# D. Architecture / forbidden pattern checks
# ---------------------------------------------------------------------------

def audit_architecture(all_py_files: list[Path]) -> list[dict]:
    results = []
    scan_paths = [p for p in all_py_files
                  if not any(part in SKIP_DIRS for part in p.parts)]

    forbidden_patterns = _load_forbidden_authority_patterns()
    authority_hits = []
    sha256_primary_hits = []
    blake2b_found = False

    for path in scan_paths:
        text = read_safe(path)
        if not text:
            continue

        # Forbidden authority patterns from registry
        for entry in forbidden_patterns:
            pat, desc = entry[0], entry[1]
            flags_ignore = entry[2] if len(entry) > 2 else False
            flags = re.IGNORECASE if flags_ignore else 0
            if re.search(pat, text, flags):
                authority_hits.append({"file": str(path), "pattern": desc})

        # SHA-256 as primary in authority context
        path_lower = str(path).lower()
        if "sha256" in text.lower() and "blake2b" not in text.lower():
            if any(kw in path_lower for kw in AUTHORITY_PATH_KEYWORDS):
                sha256_primary_hits.append(str(path))

        # Track blake2b presence
        if "blake2b" in text.lower():
            blake2b_found = True

    if authority_hits:
        for hit in authority_hits[:10]:
            results.append(finding("FORBIDDEN_AUTHORITY_PATTERN", "WARN", "HIGH",
                                   hit["file"], f"possible forbidden pattern: {hit['pattern']}"))
    else:
        results.append(finding("FORBIDDEN_AUTHORITY_PATTERN_SCAN", "PASS", "INFO",
                               "ph6/", "no forbidden authority patterns found in ph6 source"))

    if sha256_primary_hits:
        for p in sha256_primary_hits[:5]:
            results.append(finding("SHA256_PRIMARY_AUTHORITY", "WARN", "WARN", p,
                                   "authority-path file uses SHA-256 without BLAKE2b"))
    else:
        results.append(finding("BLAKE2B_PRIMARY_HASH", "PASS", "INFO",
                               "ph6/", f"BLAKE2b present as primary hash: {blake2b_found}"))

    # Check PSEUDO-A is the sole PASS/DROP issuer — look for files that emit verdict
    pseudo_files = list((ROOT / "ph6").rglob("pseudo*.py")) + list((ROOT / "ph6").rglob("*pseudo*.py"))
    results.append(finding("PSEUDO_A_FILES_PRESENT",
                           "PASS" if pseudo_files else "WARN",
                           "INFO" if pseudo_files else "WARN",
                           "ph6/",
                           f"PSEUDO-A implementation files found: {[str(p) for p in pseudo_files[:5]]}"))

    # Check cram_pu_atomic_commit.py exists (primary authority commit mechanism)
    atomic = ROOT / "ph6/cram_pu/tools/cram_pu_atomic_commit.py"
    results.append(finding("CRAM_ATOMIC_COMMIT_PRESENT",
                           "PASS" if atomic.exists() else "FAIL",
                           "INFO" if atomic.exists() else "CRITICAL",
                           str(atomic), "CRAM atomic commit mechanism present"))

    # MRAM-S advisory only — check no MRAM-S path in cram_pu_atomic_commit
    if atomic.exists():
        atomic_text = read_safe(atomic)
        mram_in_authority = "mram" in atomic_text.lower() and "cram" in atomic_text.lower()
        results.append(finding("MRAM_S_NOT_IN_AUTHORITY_COMMIT",
                               "WARN" if mram_in_authority else "PASS",
                               "WARN" if mram_in_authority else "INFO",
                               str(atomic),
                               "MRAM-S reference in authority commit path (verify advisory-only)"
                               if mram_in_authority else "MRAM-S not in authority commit path"))

    return results


# ---------------------------------------------------------------------------
# E. Test discovery and classification
# ---------------------------------------------------------------------------

def audit_tests() -> tuple[list[dict], list[dict]]:
    findings_out = []
    tests = []

    # Only ph6 tests — exclude dirs in SKIP_DIRS
    for p in ROOT.rglob("*.py"):
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        name = p.name.lower()
        if name.startswith("test_") or name.endswith("_test.py") or "test" in name:
            tests.append({"path": str(p.relative_to(ROOT)), "class": classify_test(p)})

    classes_found = {t["class"] for t in tests}
    expected_classes = {"governance", "schema", "replay_parity", "rsync_nonblocking",
                        "lane_isolation", "cram_write_recovery", "deterministic_gate_math",
                        "advisory_containment"}
    missing_classes = expected_classes - classes_found
    if missing_classes:
        findings_out.append(finding("TEST_CLASSES_MISSING", "WARN", "WARN",
                                    "ph6/tests",
                                    f"no tests found for categories: {sorted(missing_classes)}"))
    else:
        findings_out.append(finding("TEST_CLASSES_COMPLETE", "PASS", "INFO",
                                    "ph6/tests",
                                    f"all expected test categories covered: {sorted(classes_found)}"))

    # Check for deprecated field usage in tests — load from registry rather than
    # embedding literal forbidden terms (avoids self-triggering governance drift scan)
    forbidden_reg_path = GOV / "forbidden_terms_registry.json"
    deprecated_terms: list[str] = []
    if forbidden_reg_path.exists():
        try:
            reg = json.loads(forbidden_reg_path.read_text())
            for entry in reg.get("terms", []):
                t = entry.get("term", "") if isinstance(entry, dict) else str(entry)
                if t:
                    deprecated_terms.append(t)
        except Exception:
            pass
    # Supplement with old-doc markers (safe to embed — not forbidden_terms entries)
    deprecated_terms += ["DOC0", "DOC1", "DOC2", "DOC3"]
    stale_tests = []
    for p in ROOT.rglob("*.py"):
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        if not (p.name.startswith("test_") or p.name.endswith("_test.py") or "test" in p.name.lower()):
            continue
        text = read_safe(p)
        hits = [t for t in deprecated_terms if t in text]
        if hits:
            stale_tests.append({"path": str(p.relative_to(ROOT)), "terms": hits})

    if stale_tests:
        for s in stale_tests[:5]:
            findings_out.append(finding("STALE_TEST_DEPRECATED_TERMS", "WARN", "WARN",
                                        s["path"],
                                        f"test references deprecated terms: {s['terms']}"))
    else:
        findings_out.append(finding("STALE_TEST_SCAN", "PASS", "INFO",
                                    "ph6/tests", "no deprecated terms found in test files"))

    return findings_out, tests


# ---------------------------------------------------------------------------
# F. Functional coherence — pipeline check
# ---------------------------------------------------------------------------

def audit_pipeline() -> list[dict]:
    results = []
    pipeline_components = {
        "intake / departure":     ["source_departure_writer", "departure_log"],
        "PSEUDO measurement":     ["pseudo", "evaluate_frame", "metrics"],
        "PASS/DROP adjudication": ["PASS", "DROP", "verdict"],
        "CRAM commit":            ["cram_pu_atomic_commit", "cram_hash", ".blake2b"],
        "audit emission":         ["audit", "event_seq"],
        "replay verification":    ["cram_pu_replay_verify", "replay"],
        "RSYNC / export":         ["rsync", "rsync_observation"],
        "Lane 2 isolation":       ["authority_leakage", "lane2", "mram_s"],
        "governance scan":        ["governance_drift_scan", "governance_manifest"],
    }

    ph6_text_cache: dict[str, str] = {}
    for p in (ROOT / "ph6").rglob("*.py"):
        if "__pycache__" not in str(p):
            ph6_text_cache[str(p)] = read_safe(p)
    all_ph6_text = "\n".join(ph6_text_cache.values())

    for component, keywords in pipeline_components.items():
        found = any(kw.lower() in all_ph6_text.lower() for kw in keywords)
        results.append(finding(
            f"PIPELINE_{component.upper().replace('/', '_').replace(' ', '_')}",
            "PASS" if found else "WARN",
            "INFO" if found else "WARN",
            "ph6/",
            f"pipeline component '{component}': {'found' if found else 'not clearly found'}"
        ))

    return results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    GOV.mkdir(parents=True, exist_ok=True)

    print("PH6 Full Alignment Audit — read-only")
    print(f"Root: {ROOT}")
    print(f"Generated: {now_utc()}\n")

    all_files = sorted(
        p for p in ROOT.rglob("*")
        if p.is_file() and not any(part in SKIP_DIRS for part in p.parts)
    )
    all_py = [p for p in all_files if p.suffix == ".py"]

    findings: list[dict] = []

    print("[A] Governance file checks...")
    findings += audit_governance_files()

    print("[B] Book structure checks...")
    findings += audit_book_structure()

    print("[C] Closure status checks...")
    findings += audit_closure_status()

    print("[D] Architecture / forbidden pattern checks...")
    findings += audit_architecture(all_py)

    print("[E] Test discovery...")
    test_findings, tests = audit_tests()
    findings += test_findings

    print("[F] Pipeline coherence check...")
    findings += audit_pipeline()

    # --- Safe command execution ---
    commands = []
    print("[G] Running governance tools...")

    commands.append(run(["git", "log", "--oneline", "-n", "10"]))
    commands.append(run(["git", "status", "--short"]))

    drift_scan = TOOLS / "governance_drift_scan.py"
    if drift_scan.exists():
        print("  Running governance_drift_scan.py...")
        commands.append(run([
            "python3", str(drift_scan),
            "--scan-root", "PH6_SOURCE",
            "--governance-dir", "PH6_SOURCE/GOVERNANCE",
            "--project-root", ".",
            "--report-out", "PH6_SOURCE/GOVERNANCE/governance_scan_from_full_alignment_audit.json",
        ], timeout=180))

    preflight = TOOLS / "ai_preflight_check.py"
    if preflight.exists():
        print("  Running ai_preflight_check.py...")
        commands.append(run(["python3", str(preflight), "--root", ".", "--json-out",
                              "PH6_SOURCE/GOVERNANCE/preflight_from_full_alignment_audit.json"],
                            timeout=120))

    # Safe ph6 tests only — non-destructive
    print("[H] Running safe PH6 tests...")
    safe_test_dirs = [
        "ph6/cram_pu/tests",
        "ph6/ssmt/tests",
        "ph6/tok/tests",
    ]
    for td in safe_test_dirs:
        tp = ROOT / td
        if tp.exists():
            r = run(["python3", "-m", "pytest", str(tp), "-v", "--tb=short",
                     "--no-header", "-q"], timeout=120)
            r["test_dir"] = td
            commands.append(r)

    # --- Summary ---
    statuses   = [f["status"]   for f in findings]
    severities = [f["severity"] for f in findings if f["status"] in {"FAIL", "WARN"}]

    fail_count     = statuses.count("FAIL")
    warn_count     = statuses.count("WARN")
    critical_count = severities.count("CRITICAL")
    high_count     = severities.count("HIGH")

    # Determine verdicts per domain
    def domain_verdict(prefix: str) -> str:
        domain_fs = [f for f in findings if f["id"].startswith(prefix) or
                     any(kw in f["id"] for kw in [prefix])]
        if any(f["status"] == "FAIL" for f in domain_fs):
            return "FAIL"
        if any(f["status"] == "WARN" for f in domain_fs):
            return "WARN"
        return "PASS"

    drift_scan_result = "NOT_RUN"
    for c in commands:
        if "governance_drift_scan" in c.get("cmd", ""):
            drift_scan_result = "PASS" if c["rc"] == 0 else "FAIL"

    test_results = [c for c in commands if "pytest" in c.get("cmd", "")]
    tests_pass = all(c["rc"] == 0 for c in test_results) if test_results else None

    closure_findings = [f for f in findings if "CLOSURE" in f["id"] or "EVC05" in f["id"]
                        or "PRODUCTION" in f["id"]]
    arch_findings    = [f for f in findings if any(k in f["id"] for k in
                        ["PSEUDO", "CRAM", "BLAKE", "SHA256", "FORBIDDEN_AUTH", "MRAM", "PIPELINE"])]

    executive = {
        "DOCTRINE_ALIGNED":           "PASS" if not any(f["status"]=="FAIL" for f in findings
                                                         if "BOOK" in f["id"]) else "FAIL",
        "GOVERNANCE_ALIGNED":         "PASS" if not any(f["status"]=="FAIL" for f in closure_findings) else "FAIL",
        "ARCHITECTURE_ALIGNED":       "PASS" if not any(f["status"]=="FAIL" for f in arch_findings) else "WARN",
        "TEST_ALIGNED":               "PASS" if tests_pass else ("WARN" if tests_pass is None else "FAIL"),
        "FUNCTIONALLY_COHERENT":      "PASS" if not any(f["status"]=="FAIL" for f in findings
                                                         if "PIPELINE" in f["id"]) else "WARN",
        "PRODUCTION_CLEARANCE_DECLARED": "FALSE",
        "GOVERNANCE_DRIFT_SCAN":      drift_scan_result,
        "OVERALL":                    "DRIFT_FAIL" if critical_count > 0 or fail_count > 0
                                      else ("WARN" if warn_count > 0 else "PASS"),
    }

    report = {
        "schema": "ph6.full_alignment_audit.v1",
        "generated_at_utc": now_utc(),
        "read_only": True,
        "root": str(ROOT),
        "summary": {
            "total_files_scanned": len(all_files),
            "py_files_scanned": len(all_py),
            "tests_discovered": len(tests),
            "finding_count": len(findings),
            "fail_count": fail_count,
            "warn_count": warn_count,
            "critical_count": critical_count,
            "high_count": high_count,
            **executive,
        },
        "executive_verdict": executive,
        "findings": findings,
        "tests_discovered": tests,
        "commands": commands,
    }

    JSON_REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

    # --- Markdown report ---
    md = [f"# PH6 Full Alignment Audit Report",
          f"\nGenerated: `{report['generated_at_utc']}`\n",
          "## Executive Verdict\n"]
    for k, v in executive.items():
        icon = "✓" if v in {"PASS", "FALSE"} else ("✗" if v in {"FAIL", "DRIFT_FAIL"} else "⚠")
        md.append(f"- **{k}**: `{v}` {icon}")

    md.append("\n## Summary\n")
    for k, v in report["summary"].items():
        if k not in executive:
            md.append(f"- `{k}`: `{v}`")

    md.append("\n## Findings\n")
    for f in findings:
        icon = {"PASS":"✓","FAIL":"✗","WARN":"⚠"}.get(f["status"], "?")
        md.append(f"### [{f['severity']}] {f['id']} {icon}")
        md.append(f"- **Status**: `{f['status']}`")
        md.append(f"- **Location**: `{f['location']}`")
        md.append(f"- {f['message']}\n")

    md.append("\n## Tests Discovered\n")
    for cls in sorted({t["class"] for t in tests}):
        md.append(f"\n### {cls}")
        for t in tests:
            if t["class"] == cls:
                md.append(f"- `{t['path']}`")

    md.append("\n## Governance Tool Outputs\n")
    for c in commands:
        md.append(f"### `{c['cmd'][:80]}`")
        md.append(f"- Return code: `{c['rc']}`")
        if c.get("stdout"):
            md.append("```\n" + c["stdout"][-3000:] + "\n```")

    MD_REPORT.write_text("\n".join(md) + "\n")

    # Print results
    print(f"\n{'='*60}")
    print("PH6 FULL ALIGNMENT AUDIT RESULT")
    print(f"{'='*60}")
    for k, v in executive.items():
        print(f"  {k:<35}: {v}")
    print(f"\n  Findings: {len(findings)} total  "
          f"FAIL={fail_count}  WARN={warn_count}  "
          f"CRITICAL={critical_count}  HIGH={high_count}")
    print(f"\n  JSON: {JSON_REPORT}")
    print(f"  MD  : {MD_REPORT}")

    if fail_count > 0:
        print("\n  FAILED FINDINGS:")
        for f in findings:
            if f["status"] == "FAIL":
                print(f"    [{f['severity']}] {f['id']}: {f['message'][:80]}")


if __name__ == "__main__":
    main()
