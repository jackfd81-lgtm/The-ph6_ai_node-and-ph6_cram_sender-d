#!/usr/bin/env python3
"""
ph6_arc_update_check.py — PH6 ARC Update Lookup Test
=====================================================
Verifies that PH6 session updates are correctly distributed across:
  A — Architecture documentation  (PH6_SOURCE/DEPLOYMENT/)
  R — Runtime / Operations        (CLAUDE.md, hooks, boot script)
  C — Canon / Governance          (03_SCIENTIFIC_INSTRUMENT doctrine)

Location: ph6/cram_pu/ph6_arc_update_check.py
Do NOT move to PH6_SOURCE/TOOLS/ — authoritative scan territory.

Usage:
    python3 ph6/cram_pu/ph6_arc_update_check.py [--node-id ID] [--report-dir DIR]
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

# ---------------------------------------------------------------------------
# Paths — resolved relative to this file so the script runs from any cwd
# ---------------------------------------------------------------------------
REPO_ROOT  = Path(__file__).resolve().parents[2]
PH6_SRC    = REPO_ROOT / "ph6"
CANON_SRC  = REPO_ROOT / "PH6_SOURCE"
DEPLOYMENT = CANON_SRC / "DEPLOYMENT"

Status = Literal["PASS", "FAIL", "DEGRADED", "MISSING"]


# ---------------------------------------------------------------------------
# Result tracking
# ---------------------------------------------------------------------------

@dataclass
class LayerResult:
    layer: str
    status: Status
    findings: list[str] = field(default_factory=list)

    def add(self, msg: str) -> None:
        self.findings.append(msg)


@dataclass
class ARCResult:
    system:       LayerResult = field(default_factory=lambda: LayerResult("SYSTEM",       "FAIL"))
    operations:   LayerResult = field(default_factory=lambda: LayerResult("OPERATIONS",   "FAIL"))
    architecture: LayerResult = field(default_factory=lambda: LayerResult("ARCHITECTURE", "FAIL"))
    governance:   LayerResult = field(default_factory=lambda: LayerResult("GOVERNANCE",   "FAIL"))
    drift_gate:   LayerResult = field(default_factory=lambda: LayerResult("DRIFT_GATE",   "MISSING"))

    @property
    def final(self) -> Status:
        core = [self.system, self.architecture, self.governance]
        if any(r.status == "FAIL" for r in core):
            return "FAIL"
        if (self.operations.status == "DEGRADED"
                or self.drift_gate.status == "MISSING"
                or self.drift_gate.status == "FAIL"):
            return "DEGRADED"
        return "PASS"


# ---------------------------------------------------------------------------
# Atomic write — 4-step contract
# ---------------------------------------------------------------------------

def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_str = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp",
                                   dir=str(path.parent))
    tmp = Path(tmp_str)
    replaced = False
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
        replaced = True
        dfd = os.open(str(path.parent), os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(dfd)
        finally:
            os.close(dfd)
    finally:
        if not replaced and tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass


# ---------------------------------------------------------------------------
# Layer checks
# ---------------------------------------------------------------------------

def check_system(r: ARCResult) -> None:
    required = [
        PH6_SRC / "cram_pu" / "ph6_cram_sim.py",
        PH6_SRC / "cram_pu" / "ph6_internal_test.py",
    ]
    missing = [str(p.relative_to(REPO_ROOT)) for p in required if not p.exists()]
    if missing:
        r.system.status = "FAIL"
        for m in missing:
            r.system.add(f"MISSING: {m}")
    else:
        r.system.status = "PASS"
        for p in required:
            r.system.add(f"present: {p.relative_to(REPO_ROOT)}")


def check_operations(r: ARCResult) -> None:
    required = {
        "CLAUDE.md":          REPO_ROOT / "CLAUDE.md",
        "ph6_commit_gate.sh": REPO_ROOT / ".claude" / "hooks" / "ph6_commit_gate.sh",
        "ph6_write_audit.sh": REPO_ROOT / ".claude" / "hooks" / "ph6_write_audit.sh",
        "ph6_session_boot.sh": REPO_ROOT / "ph6_session_boot.sh",  # note: actual name varies
    }
    # Also accept ph6_claude_boot.sh as the boot script
    if not (REPO_ROOT / "ph6_session_boot.sh").exists():
        required["ph6_session_boot.sh"] = REPO_ROOT / "ph6_claude_boot.sh"

    missing = []
    for label, path in required.items():
        if path.exists():
            r.operations.add(f"present: {label}")
        else:
            missing.append(label)
            r.operations.add(f"MISSING: {label}")

    if not missing:
        r.operations.status = "PASS"
    elif len(missing) < len(required):
        r.operations.status = "DEGRADED"
    else:
        r.operations.status = "FAIL"


def _search_dir(directory: Path, terms: list[str]) -> dict[str, bool]:
    """Return {term: found} for each term across all files under directory."""
    found = {t: False for t in terms}
    if not directory.is_dir():
        return found
    for fpath in directory.rglob("*"):
        if not fpath.is_file():
            continue
        try:
            text = fpath.read_text(errors="ignore")
        except OSError:
            continue
        for t in terms:
            if not found[t] and t in text:
                found[t] = True
        if all(found.values()):
            break
    return found


def check_architecture(r: ARCResult) -> None:
    # Commit hashes from the modular harness transition (82f658f20d, f904544411).
    # File names searched without .py — deployment reports reference them as module
    # names in commit descriptions; AI_HANDOFF and GOVERNANCE docs have full paths.
    # Search the whole PH6_SOURCE/ canon tree (not just DEPLOYMENT/) since the
    # transition record lives in GOVERNANCE/ and handoff docs in AI_HANDOFF/.
    terms = [
        "82f658f20d",
        "f904544411",
        "ph6_cram_sim",
        "ph6_internal_test",
    ]
    found = _search_dir(CANON_SRC, terms)
    missing_terms = [t for t, ok in found.items() if not ok]

    if not missing_terms:
        r.architecture.status = "PASS"
        for t in terms:
            r.architecture.add(f"found: {t!r} in PH6_SOURCE/")
    else:
        r.architecture.status = "FAIL"
        for t in terms:
            if found[t]:
                r.architecture.add(f"found: {t!r}")
            else:
                r.architecture.add(f"MISSING: {t!r} not found in PH6_SOURCE/")


def check_governance(r: ARCResult) -> None:
    doctrine = (CANON_SRC / "03_SCIENTIFIC_INSTRUMENT"
                / "PH6-SCIENTIFIC-INTEGRITY-EXPANSION-v2.1.md")

    if not doctrine.exists():
        r.governance.status = "FAIL"
        r.governance.add(f"MISSING: {doctrine.relative_to(REPO_ROOT)}")
        return

    r.governance.add(f"present: {doctrine.relative_to(REPO_ROOT)}")

    required_sections = [
        "Epistemic Hierarchy",
        "Observer Contamination Doctrine",
        "Environmental Boundedness Law",
        "Replay-Reproducible Measurement",
        "Replay-Stable Interpretation",
    ]
    try:
        text = doctrine.read_text()
    except OSError as e:
        r.governance.status = "FAIL"
        r.governance.add(f"ERROR reading doctrine: {e}")
        return

    missing_sections = [s for s in required_sections if s not in text]
    if not missing_sections:
        r.governance.status = "PASS"
        for s in required_sections:
            r.governance.add(f"found: {s!r}")
    else:
        r.governance.status = "FAIL"
        for s in required_sections:
            if s in text:
                r.governance.add(f"found: {s!r}")
            else:
                r.governance.add(f"MISSING section: {s!r}")


def check_drift_gate(r: ARCResult) -> None:
    gate = PH6_SRC / "governance" / "drift_gate.py"

    if not gate.exists():
        r.drift_gate.status = "MISSING"
        r.drift_gate.add(f"MISSING: {gate.relative_to(REPO_ROOT)}")
        r.drift_gate.add("Install drift_gate.py to enable real governance enforcement.")
        return

    r.drift_gate.add(f"present: {gate.relative_to(REPO_ROOT)}")

    try:
        result = subprocess.run(
            [sys.executable, str(gate), "--path", str(CANON_SRC) + "/"],
            capture_output=True, text=True, timeout=60
        )
        output = result.stdout + result.stderr
    except (subprocess.TimeoutExpired, OSError) as e:
        r.drift_gate.status = "FAIL"
        r.drift_gate.add(f"ERROR running drift_gate.py: {e}")
        return

    if not output.strip():
        # Empty output is not a PASS — cannot confirm gate ran successfully
        r.drift_gate.status = "FAIL"
        r.drift_gate.add("ERROR: drift_gate.py produced no output — cannot confirm PASS")
        return

    critical = output.count("CRITICAL")
    high     = output.count("HIGH")

    if critical > 0 or high > 0:
        r.drift_gate.status = "FAIL"
        r.drift_gate.add(f"FAIL: {critical}C {high}H found in PH6_SOURCE/")
    else:
        r.drift_gate.status = "PASS"
        r.drift_gate.add(f"PASS: 0C 0H in PH6_SOURCE/")


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def format_report(arc: ARCResult, node_id: str, stamp: str) -> str:
    lines = [
        f"# PH6 ARC Update Check — {stamp}",
        "",
        f"**Node:** {node_id}",
        f"**Repo:** {REPO_ROOT}",
        "",
        "---",
        "",
        "## Results",
        "",
        "| Layer | Status |",
        "|-------|--------|",
        f"| SYSTEM | {arc.system.status} |",
        f"| OPERATIONS | {arc.operations.status} |",
        f"| ARCHITECTURE | {arc.architecture.status} |",
        f"| GOVERNANCE | {arc.governance.status} |",
        f"| DRIFT_GATE | {arc.drift_gate.status} |",
        f"| **FINAL** | **{arc.final}** |",
        "",
        "---",
        "",
    ]

    for layer in [arc.system, arc.operations, arc.architecture,
                  arc.governance, arc.drift_gate]:
        lines.append(f"## {layer.layer}")
        lines.append("")
        for f in layer.findings:
            lines.append(f"- {f}")
        lines.append("")

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="PH6 ARC Update Check")
    parser.add_argument("--node-id",    default="unknown")
    parser.add_argument("--report-dir", type=Path, default=None)
    args = parser.parse_args()

    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    arc   = ARCResult()

    print("PH6 ARC UPDATE CHECK")
    print("====================")
    print()

    check_system(arc)
    check_operations(arc)
    check_architecture(arc)
    check_governance(arc)
    check_drift_gate(arc)

    print(f"SYSTEM:       {arc.system.status}")
    print(f"OPERATIONS:   {arc.operations.status}")
    print(f"ARCHITECTURE: {arc.architecture.status}")
    print(f"GOVERNANCE:   {arc.governance.status}")
    print(f"DRIFT_GATE:   {arc.drift_gate.status}")
    print()
    print(f"FINAL: {arc.final}")

    if args.report_dir is not None:
        report_path = args.report_dir / f"PH6_ARC_UPDATE_CHECK_{stamp}.md"
        content = format_report(arc, args.node_id, stamp)
        atomic_write(report_path, content.encode())
        print()
        print(f"Report: {report_path}")

    return 0 if arc.final in ("PASS", "DEGRADED") else 1


if __name__ == "__main__":
    sys.exit(main())
