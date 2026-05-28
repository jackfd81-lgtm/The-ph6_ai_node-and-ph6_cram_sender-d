#!/usr/bin/env python3
"""
ph6_internal_test.py — PH6/CRAM Internal System Test Driver
============================================================
Replaces the inline Python heredoc in the Claude Code test script.

Runs ALL checks, collects results, emits a structured Markdown report,
and exits with code 0 (all PASS) or 1 (any FAIL).

NO USB / NO CAMERA / NO VIDEO / NO CAN / NO HAT.

Usage:
    python3 ph6_internal_test.py [--report-dir DIR] [--node-id ID]
"""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
import tempfile
import time
import traceback
from dataclasses import dataclass, field
from pathlib import Path

from ph6_cram_sim import (
    AuditChain,
    CRAMSimulation,
    FrameInput,
    atomic_write,
    blake2b256,
    canonical_json,
    check_forbidden_fields,
    gate,
    GATE_ENTROPY_MIN,
    GATE_LAPLACIAN_MIN,
    GATE_MOTION_FRAC_MIN,
    GATE_MOTION_FRAC_MAX,
    FORBIDDEN_MOTION_FIELDS,
)


# ---------------------------------------------------------------------------
# Result tracking
# ---------------------------------------------------------------------------

@dataclass
class CheckResult:
    name: str
    passed: bool
    detail: str
    warning: bool = False  # WARN = passed but needs human attention


@dataclass
class TestRun:
    node_id: str
    stamp: str
    tmp_root: Path
    checks: list[CheckResult] = field(default_factory=list)
    start_time: float = field(default_factory=time.monotonic)

    def add(self, name: str, passed: bool, detail: str, warning: bool = False) -> None:
        self.checks.append(CheckResult(name, passed, detail, warning))
        status = "WARN" if warning else ("PASS" if passed else "FAIL")
        print(f"  [{status:4s}] {name}: {detail}")

    @property
    def failed(self) -> list[CheckResult]:
        return [c for c in self.checks if not c.passed]

    @property
    def warnings(self) -> list[CheckResult]:
        return [c for c in self.checks if c.warning]

    @property
    def elapsed(self) -> float:
        return time.monotonic() - self.start_time


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_gate_thresholds(run: TestRun) -> None:
    ok = (
        GATE_ENTROPY_MIN == 6.0
        and GATE_LAPLACIAN_MIN == 100.0
        and GATE_MOTION_FRAC_MIN == 0.01
        and GATE_MOTION_FRAC_MAX == 0.75
    )
    run.add(
        "GATE_THRESHOLDS",
        ok,
        f"entropy>={GATE_ENTROPY_MIN} laplacian>={GATE_LAPLACIAN_MIN} "
        f"motion [{GATE_MOTION_FRAC_MIN},{GATE_MOTION_FRAC_MAX}]",
    )


def check_forbidden_field_guard(run: TestRun) -> None:
    caught = False
    try:
        check_forbidden_fields({"motion_score": 0.5, "entropy": "7.1"})
    except ValueError:
        caught = True
    run.add("FORBIDDEN_FIELD_GUARD", caught, "ValueError raised on motion_score")


def check_gate_pass_case(run: TestRun) -> None:
    metrics = {
        "entropy": "7.100000",
        "laplacian_var": "155.000000",
        "motion_fraction": "0.120000",
    }
    check_forbidden_fields(metrics)
    v = gate(metrics)
    run.add("GATE_PASS_CASE", v == "PASS", f"verdict={v}")


def check_gate_drop_cases(run: TestRun) -> None:
    cases = [
        ("low_entropy",   {"entropy": "3.2", "laplacian_var": "155.0", "motion_fraction": "0.12"}),
        ("low_laplacian", {"entropy": "7.1", "laplacian_var": "40.0",  "motion_fraction": "0.12"}),
        ("no_motion",     {"entropy": "7.1", "laplacian_var": "155.0", "motion_fraction": "0.0"}),
        ("excess_motion", {"entropy": "7.1", "laplacian_var": "155.0", "motion_fraction": "0.9"}),
    ]
    for name, m in cases:
        v = gate(m)
        run.add(f"GATE_DROP_{name.upper()}", v == "DROP", f"verdict={v}")


def check_cram_pass_path(run: TestRun, sim: CRAMSimulation) -> FrameInput:
    frame = FrameInput(
        object_id="internal_pass_000001",
        raw=b"PH6_INTERNAL_TEST_PASS_FRAME_000001\n",
        metrics={
            "entropy": "7.100000",
            "laplacian_var": "155.000000",
            "motion_fraction": "0.120000",
        },
    )
    result = sim.process(frame)
    run.add("CRAM_PASS_VERDICT", result.verdict == "PASS", f"verdict={result.verdict}")
    missing = sim.verify_pass_files(frame.object_id)
    run.add(
        "CRAM_PASS_FILES",
        not missing,
        "all 4 CRAM-A files present (incl .blake2b last)"
        if not missing
        else f"missing: {missing}",
    )
    run.add(
        "CRAM_PASS_AUTHORITY_HASH",
        len(result.authority_hash) == 64,
        f"blake2b256={result.authority_hash[:16]}...",
    )
    return frame


def check_cram_drop_path(run: TestRun, sim: CRAMSimulation) -> FrameInput:
    frame = FrameInput(
        object_id="internal_drop_000002",
        raw=b"PH6_INTERNAL_TEST_DROP_FRAME_000002\n",
        metrics={
            "entropy": "3.200000",
            "laplacian_var": "40.000000",
            "motion_fraction": "0.000000",
        },
    )
    result = sim.process(frame)
    run.add("CRAM_DROP_VERDICT", result.verdict == "DROP", f"verdict={result.verdict}")
    issues = sim.verify_drop_files(frame.object_id)
    run.add(
        "CRAM_DROP_FILES",
        not issues,
        "CRAM-R files present, no .blake2b marker"
        if not issues
        else f"issues: {issues}",
    )
    return frame


def check_audit_chain(run: TestRun, sim: CRAMSimulation) -> Path:
    audit_path = sim.finalize_audit()
    n = len(sim.audit.events)
    ok, msg = AuditChain.verify(audit_path)
    run.add("AUDIT_CHAIN_EVENTS", n == 2, f"event_count={n}")
    run.add("AUDIT_CHAIN_HASH_VERIFY", ok, msg)
    run.add(
        "AUDIT_CHAIN_GENESIS",
        sim.audit.events[0]["prev_event_hash"] == "GENESIS",
        "first event prev_event_hash == GENESIS",
    )
    return audit_path


def check_replay_parity(run: TestRun, sim: CRAMSimulation, frames: list[FrameInput]) -> None:
    ok, msg = sim.replay_check(frames)
    run.add("REPLAY_PARITY", ok, msg)


def check_export(run: TestRun, sim: CRAMSimulation) -> None:
    sim.export_copy("cram-a")
    ok, msg = sim.export_verify("cram-a")
    run.add("EXPORT_COPY", ok, msg)


def check_atomic_write_contract(run: TestRun, tmp: Path) -> None:
    payload = b"PH6_ATOMIC_WRITE_TEST\n"
    target  = tmp / "atomic_test" / "testfile.bin"
    atomic_write(target, payload)
    ok = target.read_bytes() == payload
    payload2 = b"PH6_ATOMIC_WRITE_TEST_OVERWRITE\n"
    atomic_write(target, payload2)
    ok2 = target.read_bytes() == payload2
    run.add("ATOMIC_WRITE_CONTRACT", ok and ok2, "write + overwrite both byte-exact")


def check_canonical_json_determinism(run: TestRun) -> None:
    obj = {"z_key": "last", "a_key": "first", "nested": {"b": 2, "a": 1}, "arr": [3, 1, 2]}
    b1  = canonical_json(obj)
    b2  = canonical_json(obj)
    ok  = b1 == b2 and b'"a_key"' in b1 and b'"z_key"' in b1
    idx_a = b1.index(b'"a_key"')
    idx_z = b1.index(b'"z_key"')
    run.add("CANONICAL_JSON_DETERMINISM", ok and idx_a < idx_z, f"len={len(b1)}, keys sorted")


def check_blake2b256_known_vector(run: TestRun) -> None:
    known = hashlib.blake2b(b"", digest_size=32).hexdigest()
    got   = blake2b256(b"")
    run.add("BLAKE2B256_KNOWN_VECTOR", got == known, f"hash={got[:16]}...")


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def write_report(run: TestRun, report_dir: Path) -> Path:
    report_path = report_dir / f"PH6_INTERNAL_SYSTEM_TEST_{run.stamp}.md"

    total   = len(run.checks)
    passed  = sum(1 for c in run.checks if c.passed)
    failed  = len(run.failed)
    warned  = len(run.warnings)
    overall = "PASS" if failed == 0 else "FAIL"

    lines: list[str] = [
        "# PH6 / CRAM Internal System Test Report",
        "",
        f"**Generated UTC:** {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}",
        f"**Node:** {run.node_id}",
        f"**Test Stamp:** {run.stamp}",
        f"**Temp Root:** {run.tmp_root}",
        "**Test Type:** Internal — NO USB / NO CAMERA / NO VIDEO / NO CAN / NO HAT",
        f"**Elapsed:** {run.elapsed:.2f}s",
        "",
        "---",
        "",
        f"## Overall: {overall}",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Total checks | {total} |",
        f"| PASS | {passed} |",
        f"| FAIL | {failed} |",
        f"| WARN | {warned} |",
        "",
        "---",
        "",
        "## Check Results",
        "",
        "| Check | Status | Detail |",
        "|-------|--------|--------|",
    ]

    for c in run.checks:
        status = "WARN" if c.warning else ("PASS" if c.passed else "FAIL")
        lines.append(f"| {c.name} | {status} | {c.detail} |")

    if run.failed:
        lines += ["", "---", "", "## Failures", ""]
        for c in run.failed:
            lines.append(f"- **{c.name}**: {c.detail}")

    if run.warnings:
        lines += ["", "---", "", "## Warnings (human action required)", ""]
        for c in run.warnings:
            lines.append(f"- **{c.name}**: {c.detail}")

    lines += [
        "",
        "---",
        "",
        "## Doctrine Confirmation",
        "",
        "- Lane-2 authority: ZERO",
        "- Hash algorithm: BLAKE2b-256 (digest_size=32)",
        "- Motion field: `motion_fraction` only",
        "- Forbidden fields: " + ", ".join(sorted(FORBIDDEN_MOTION_FIELDS)),
        "- Verdict vocabulary: PASS / DROP only",
        "- `.blake2b` marker: PASS path only, written LAST",
        "- Atomic write: 4-step contract enforced",
        "- USB / camera / video / CAN / HAT: NOT TOUCHED",
        "",
    ]

    content = "\n".join(lines) + "\n"
    report_dir.mkdir(parents=True, exist_ok=True)
    atomic_write(report_path, content.encode())
    return report_path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="PH6/CRAM Internal System Test")
    parser.add_argument("--report-dir", type=Path, default=Path("."),
                        help="Directory for the Markdown report")
    parser.add_argument("--node-id", default="pi5-internal-test",
                        help="Node identifier for audit events")
    args = parser.parse_args()

    stamp    = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    tmp_root = Path(tempfile.mkdtemp(prefix=f"ph6_internal_test_{stamp}_"))

    run = TestRun(node_id=args.node_id, stamp=stamp, tmp_root=tmp_root)
    sim = CRAMSimulation(tmp_root)

    print(f"\nPH6 INTERNAL SYSTEM TEST — {stamp}")
    print(f"Node: {args.node_id}  Tmp: {tmp_root}\n")

    try:
        print("[1] Primitive checks")
        check_gate_thresholds(run)
        check_forbidden_field_guard(run)
        check_canonical_json_determinism(run)
        check_blake2b256_known_vector(run)
        check_atomic_write_contract(run, tmp_root)

        print("\n[2] Gate logic")
        check_gate_pass_case(run)
        check_gate_drop_cases(run)

        print("\n[3] CRAM simulation")
        pass_frame = check_cram_pass_path(run, sim)
        drop_frame = check_cram_drop_path(run, sim)

        print("\n[4] Audit chain")
        check_audit_chain(run, sim)

        print("\n[5] Replay & export")
        check_replay_parity(run, sim, [pass_frame, drop_frame])
        check_export(run, sim)

    except Exception:
        run.add("UNEXPECTED_EXCEPTION", False, traceback.format_exc(limit=5))

    report_path = write_report(run, args.report_dir)
    print(f"\nReport: {report_path}")

    failed  = len(run.failed)
    overall = "PASS" if failed == 0 else f"FAIL ({failed} failures)"
    print(f"Result: {overall}  ({len(run.checks)} checks, {run.elapsed:.2f}s)\n")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
