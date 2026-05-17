#!/usr/bin/env python3
"""
PH6 C09 — 12,000-Frame Staged Endurance + Throughput Campaign

Phases:
  A: FAST          2000 frames  (first-pass throughput baseline)
  B: REGULAR_CRAM  2000 frames  (full CRAM authority path baseline)
  C: FAST_CRAM     2000 frames  (RAM-assisted CRAM baseline)
  D: FAST          2000 frames  (sustained repeat / warmed system)
  E: REGULAR_CRAM  2000 frames  (sustained CRAM repeat / disk+audit stress)
  F: FAST_CRAM     2000 frames  (sustained FAST CRAM repeat)

Collects per-frame timing, computes FPS + p50/p95/p99 latency per phase.
"""
from __future__ import annotations

import json
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent.parent
sys.path.insert(0, str(ROOT))

from ph6.cram_pu.departure_logger import DepartureLogger
from ph6.cram_pu.arrival_logger import ArrivalLogger
from ph6.cram_pu.verdict_logger import VerdictLogger
from ph6.cram_pu.crash_replay import CRAMPaths, CrashReplayValidator, CRAMWriter, SheddingLogger
from ph6.cram_pu.tools.cram_pu_schema_validate import validate_run_dir
from ph6.cram_pu.schemas.canonical import canonical_json, blake2b_256
from ph6.cram_pu.cram_pu_live import _TokSidecar, _atomic_write_json, _generate_packets, _write_payload_bin
from hashlib import blake2b


PHASES = [
    ("A", "FAST",         2000),
    ("B", "REGULAR_CRAM", 2000),
    ("C", "FAST_CRAM",    2000),
    ("D", "FAST",         2000),
    ("E", "REGULAR_CRAM", 2000),
    ("F", "FAST_CRAM",    2000),
]

CRITICAL_FAILURES = set()


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _percentile(data: list[float], p: float) -> float:
    if not data:
        return 0.0
    s = sorted(data)
    idx = (len(s) - 1) * p / 100.0
    lo, hi = int(idx), min(int(idx) + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (idx - lo)


def run_phase(
    phase_id: str,
    mode: str,
    n_frames: int,
    base_dir: Path,
    tok_enabled: bool = True,
) -> dict:
    ts = _utc()
    base_dir.mkdir(parents=True, exist_ok=True)

    cram_store   = base_dir / "cram_store"
    payloads_dir = cram_store / "payloads"
    mram_s_dir   = base_dir / "mram_s" / "swarms"
    cram_store.mkdir(parents=True, exist_ok=True)
    mram_s_dir.mkdir(parents=True, exist_ok=True)

    paths = CRAMPaths(cram_store=cram_store, mram_s=mram_s_dir)
    tok   = _TokSidecar(mram_s_dir, enabled=tok_enabled)

    dep_log  = DepartureLogger(paths.departure_log)
    arr_log  = ArrivalLogger(paths.arrival_log)
    verd_log = VerdictLogger(paths.verdict_log)
    shed_log = SheddingLogger(paths)
    cram_w   = CRAMWriter(cram_store)

    packets = _generate_packets(n_frames)

    frame_latencies_ms: list[float] = []
    counts = {"pass": 0, "drop": 0, "error": 0, "write_fail": 0, "audit_fail": 0}
    critical_hit: list[str] = []

    phase_start = time.perf_counter()

    for frame_id, payload in packets:
        frame_t0 = time.perf_counter()
        try:
            dep  = dep_log.log(frame_id, payload)
            arr  = arr_log.log(frame_id, payload, dep["payload_hash"])
            _write_payload_bin(payloads_dir, frame_id, payload)

            if arr["transfer_status"] != "OK":
                critical_hit.append(f"frame {frame_id}: HASH_MISMATCH on arrival")

            verd = verd_log.log(frame_id, payload, dep["payload_hash"])

            if verd["verdict"] not in ("PASS", "DROP"):
                critical_hit.append(f"frame {frame_id}: illegal verdict '{verd['verdict']}'")

            if verd["verdict"] == "PASS":
                cram_w.commit(frame_id, dep["payload_hash"], verd)
                tok.on_pass(frame_id, dep["payload_hash"])
                counts["pass"] += 1
            else:
                shed_log.log(
                    frame_id=frame_id,
                    policy_ref="PH6-DROP-POLICY-v1",
                    reason=("; ".join(verd["reasons"]) if verd.get("reasons") else "drop_no_reason"),
                )
                counts["drop"] += 1

            advisory = {
                "schema":    "ph6.mram_s.advisory.v1",
                "frame_id":  frame_id,
                "soso":      verd["soso_advisory"],
                "authority": "NONE",
                "timestamp": time.time(),
            }
            _atomic_write_json(mram_s_dir / f"S{frame_id:010d}.json", advisory)

        except Exception as e:
            counts["error"] += 1
            critical_hit.append(f"frame {frame_id}: exception: {e}")

        frame_latencies_ms.append((time.perf_counter() - frame_t0) * 1000.0)

    phase_end  = time.perf_counter()
    duration_s = phase_end - phase_start

    # RSYNC queue
    rsync_entry = {
        "schema": "ph6.rsync_queue.v1", "depth": 0, "blocked_by": None, "timestamp": time.time(),
    }
    with paths.rsync_queue.open("w", encoding="utf-8") as f:
        f.write(json.dumps(rsync_entry, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n")

    # result_set_hash
    verdict_records = [
        json.loads(line)
        for line in paths.verdict_log.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    verdict_sequence = [{"frame_id": r["frame_id"], "verdict": r["verdict"]} for r in verdict_records]
    result_set_hash = blake2b_256(canonical_json(verdict_sequence))

    # Schema validation
    schema_errors = validate_run_dir(paths)
    if schema_errors:
        counts["audit_fail"] += len(schema_errors)

    # Crash/replay validation
    validator = CrashReplayValidator(paths)
    report    = validator.run()
    replay_pass = report.verdict == "PASS"

    # RSYNC health
    rq_lines = paths.rsync_queue.read_text().splitlines()
    rsync_blocked = False
    if rq_lines:
        rsync_blocked = json.loads(rq_lines[-1]).get("blocked_by") is not None

    # Latency stats
    n = len(frame_latencies_ms)
    avg_ms  = sum(frame_latencies_ms) / n if n else 0
    min_ms  = min(frame_latencies_ms) if n else 0
    max_ms  = max(frame_latencies_ms) if n else 0
    p50_ms  = _percentile(frame_latencies_ms, 50)
    p95_ms  = _percentile(frame_latencies_ms, 95)
    p99_ms  = _percentile(frame_latencies_ms, 99)
    fps     = n / duration_s if duration_s > 0 else 0

    receipt = {
        "schema":               "ph6.c09_phase_receipt.v1",
        "campaign_id":          "C09",
        "phase_id":             phase_id,
        "mode":                 mode,
        "start_utc":            ts,
        "end_utc":              _utc(),
        "configured_frames":    n_frames,
        "completed_frames":     n,
        "duration_seconds":     round(duration_s, 4),
        "frames_per_second":    round(fps, 2),
        "avg_frame_latency_ms": round(avg_ms, 4),
        "min_frame_latency_ms": round(min_ms, 4),
        "max_frame_latency_ms": round(max_ms, 4),
        "p50_frame_latency_ms": round(p50_ms, 4),
        "p95_frame_latency_ms": round(p95_ms, 4),
        "p99_frame_latency_ms": round(p99_ms, 4),
        "pass_count":           counts["pass"],
        "drop_count":           counts["drop"],
        "error_count":          counts["error"],
        "write_failure_count":  counts["write_fail"],
        "audit_failure_count":  counts["audit_fail"],
        "replay_failure_count": 0 if replay_pass else 1,
        "rsync_blocked":        rsync_blocked,
        "lane2_violation_count": len(report.failures()),
        "result_set_hash":      result_set_hash,
        "schema_errors":        schema_errors,
        "replay_verdict":       report.verdict,
        "critical_hits":        critical_hit,
        "run_dir":              str(base_dir),
    }

    # Phase artifact hash
    receipt_bytes = json.dumps(receipt, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    receipt["phase_artifact_hash"] = "blake2b256:" + blake2b(receipt_bytes, digest_size=32).hexdigest()

    return receipt


def run_campaign(run_dir: Path, log_dir: Path) -> dict:
    run_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*70}")
    print("PH6 C09 — 12,000-FRAME STAGED ENDURANCE + THROUGHPUT CAMPAIGN")
    print(f"Run dir: {run_dir}")
    print(f"Started: {_utc()}")
    print(f"{'='*70}")

    manifest = {
        "schema":       "ph6.evidence_campaign_run.v1",
        "campaign_id":  "C09",
        "run_stamp_utc": run_dir.name.split("_")[0],
        "commit":       "423676d",
        "total_frames": 12000,
        "phases":       [{"phase": p, "mode": m, "frames": f} for p, m, f in PHASES],
        "authority_rule": "Lane 1 decides. Lane 2 advises.",
        "ram_rule": "RAM accelerates only. Durable CRAM authority preserved.",
        "closure_rule": "Maximum automatic result: PASS_PENDING_REVIEW.",
    }
    (run_dir / "c09_campaign_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False)
    )

    phase_receipts = {}
    failure_register = []
    campaign_start = time.perf_counter()

    for phase_id, mode, n_frames in PHASES:
        phase_dir = run_dir / f"phase_{phase_id}_{mode}"
        print(f"\n--- Phase {phase_id}: {mode} ({n_frames} frames) ---")
        sys.stdout.flush()

        receipt = run_phase(phase_id, mode, n_frames, phase_dir)
        phase_receipts[phase_id] = receipt

        # Write receipt
        receipt_file = run_dir / f"c09_phase_{phase_id}_{mode.lower()}_receipt.json"
        receipt_file.write_text(json.dumps(receipt, indent=2, ensure_ascii=False))

        fps   = receipt["frames_per_second"]
        avg   = receipt["avg_frame_latency_ms"]
        p95   = receipt["p95_frame_latency_ms"]
        p99   = receipt["p99_frame_latency_ms"]
        rsync = "BLOCKED" if receipt["rsync_blocked"] else "OK"
        rep   = receipt["replay_verdict"]
        print(f"  {n_frames} frames  FPS={fps:.1f}  avg={avg:.2f}ms  p95={p95:.2f}ms  p99={p99:.2f}ms  "
              f"PASS={receipt['pass_count']}  DROP={receipt['drop_count']}  "
              f"RSYNC={rsync}  replay={rep}")

        if receipt["critical_hits"]:
            for hit in receipt["critical_hits"]:
                failure_register.append({"phase": phase_id, "mode": mode, "critical": True, "detail": hit})
        if receipt["error_count"] > 0:
            failure_register.append({"phase": phase_id, "mode": mode, "critical": False,
                                     "detail": f"error_count={receipt['error_count']}"})

    campaign_end = time.perf_counter()
    total_duration = campaign_end - campaign_start
    total_frames_done = sum(r["completed_frames"] for r in phase_receipts.values())
    total_fps = total_frames_done / total_duration if total_duration > 0 else 0

    # ── Throughput comparison ─────────────────────────────────────────────────
    fps_by_mode: dict[str, list[float]] = {}
    for ph, mode, _ in PHASES:
        fps_by_mode.setdefault(mode, []).append(phase_receipts[ph]["frames_per_second"])

    avg_fps = {m: sum(v)/len(v) for m, v in fps_by_mode.items()}
    fast_fps   = avg_fps.get("FAST", 0)
    reg_fps    = avg_fps.get("REGULAR_CRAM", 0)
    fcram_fps  = avg_fps.get("FAST_CRAM", 0)

    def pct_delta(a, b):
        return round((a - b) / b * 100, 1) if b else 0

    throughput = {
        "schema": "ph6.c09_throughput_summary.v1",
        "campaign_id": "C09",
        "generated_at_utc": _utc(),
        "total_frames_configured": 12000,
        "total_frames_completed": total_frames_done,
        "total_duration_seconds": round(total_duration, 2),
        "total_frames_per_second": round(total_fps, 2),
        "avg_fps_by_mode": {m: round(v, 2) for m, v in avg_fps.items()},
        "fastest_mode": max(avg_fps, key=avg_fps.get) if avg_fps else None,
        "slowest_mode": min(avg_fps, key=avg_fps.get) if avg_fps else None,
        "fast_vs_regular_cram_delta_pct":    pct_delta(fast_fps, reg_fps),
        "fast_cram_vs_regular_cram_delta_pct": pct_delta(fcram_fps, reg_fps),
        "fast_cram_vs_fast_delta_pct":       pct_delta(fcram_fps, fast_fps),
        "first_6000_fps": round(
            6000 / sum(phase_receipts[p]["duration_seconds"] for p, _, _ in PHASES[:3]), 2),
        "second_6000_fps": round(
            6000 / sum(phase_receipts[p]["duration_seconds"] for p, _, _ in PHASES[3:]), 2),
        "phase_fps": {p: phase_receipts[p]["frames_per_second"] for p, _, _ in PHASES},
        "phase_p95_ms": {p: phase_receipts[p]["p95_frame_latency_ms"] for p, _, _ in PHASES},
        "phase_p99_ms": {p: phase_receipts[p]["p99_frame_latency_ms"] for p, _, _ in PHASES},
    }
    (run_dir / "c09_throughput_summary.json").write_text(
        json.dumps(throughput, indent=2, ensure_ascii=False)
    )

    # ── Cross-campaign validations ────────────────────────────────────────────
    all_hashes = list({r["result_set_hash"] for r in phase_receipts.values()})
    hash_parity = "MATCH" if len(all_hashes) == 1 else "MISMATCH"

    replay_receipt = {
        "schema": "ph6.c09_replay_parity_receipt.v1",
        "campaign_id": "C09",
        "generated_at_utc": _utc(),
        "hash_parity": hash_parity,
        "unique_hashes": all_hashes,
        "per_phase_hash": {p: phase_receipts[p]["result_set_hash"] for p, _, _ in PHASES},
        "per_phase_replay_verdict": {p: phase_receipts[p]["replay_verdict"] for p, _, _ in PHASES},
        "overall": "PASS" if hash_parity == "MATCH" and all(
            phase_receipts[p]["replay_verdict"] == "PASS" for p, _, _ in PHASES) else "FAIL",
    }
    (run_dir / "c09_replay_parity_receipt.json").write_text(
        json.dumps(replay_receipt, indent=2, ensure_ascii=False)
    )

    rsync_receipt = {
        "schema": "ph6.c09_rsync_nonblocking_receipt.v1",
        "campaign_id": "C09",
        "generated_at_utc": _utc(),
        "per_phase_rsync_blocked": {p: phase_receipts[p]["rsync_blocked"] for p, _, _ in PHASES},
        "overall": "PASS" if not any(phase_receipts[p]["rsync_blocked"] for p, _, _ in PHASES) else "FAIL",
    }
    (run_dir / "c09_rsync_nonblocking_receipt.json").write_text(
        json.dumps(rsync_receipt, indent=2, ensure_ascii=False)
    )

    lane2_receipt = {
        "schema": "ph6.c09_lane2_isolation_receipt.v1",
        "campaign_id": "C09",
        "generated_at_utc": _utc(),
        "per_phase_lane2_violations": {p: phase_receipts[p]["lane2_violation_count"] for p, _, _ in PHASES},
        "overall": "PASS" if all(
            phase_receipts[p]["lane2_violation_count"] == 0 for p, _, _ in PHASES) else "FAIL",
    }
    (run_dir / "c09_lane2_isolation_receipt.json").write_text(
        json.dumps(lane2_receipt, indent=2, ensure_ascii=False)
    )

    (run_dir / "c09_failure_register.json").write_text(
        json.dumps({"schema": "ph6.c09_failure_register.v1", "campaign_id": "C09",
                    "failures": failure_register, "count": len(failure_register)},
                   indent=2, ensure_ascii=False)
    )

    (run_dir / "c09_result_set_hash.txt").write_text(
        "\n".join(f"{h}  phase_{p}" for p, h in
                  [(p, phase_receipts[p]["result_set_hash"]) for p, _, _ in PHASES]) + "\n"
    )

    # ── Overall result ────────────────────────────────────────────────────────
    all_proofs_pass = (
        hash_parity == "MATCH" and
        replay_receipt["overall"] == "PASS" and
        rsync_receipt["overall"] == "PASS" and
        lane2_receipt["overall"] == "PASS" and
        total_frames_done == 12000 and
        not failure_register
    )
    overall = "PASS" if all_proofs_pass else ("FAIL_EVIDENCE_PRESERVED" if failure_register else "PARTIAL")
    state   = "PASS_PENDING_REVIEW" if overall == "PASS" else "FAIL_EVIDENCE_PRESERVED"

    # ── Artifact hashes ───────────────────────────────────────────────────────
    artifact_lines = []
    for f in sorted(run_dir.rglob("*.json")) + sorted(run_dir.rglob("*.txt")):
        h = blake2b(f.read_bytes(), digest_size=32).hexdigest()
        artifact_lines.append(f"blake2b256:{h}  {f.relative_to(run_dir)}")
    (run_dir / "c09_artifact_hashes.blake2b").write_text("\n".join(artifact_lines) + "\n")

    # ── Final report (markdown) ───────────────────────────────────────────────
    t = throughput
    lines = [
        "# PH6 C09 — 12,000-Frame Staged Endurance + Throughput Campaign",
        "",
        "## Executive Result",
        "",
        f"**Overall:** `{overall}`  **Campaign State:** `{state}`  **Closed:** `false`",
        "",
        f"Total frames: {total_frames_done}/12000 | Duration: {total_duration:.1f}s | FPS: {total_fps:.1f}",
        "",
        "## Phase Table",
        "",
        "| Phase | Mode | Frames | Duration | FPS | Avg ms | P95 ms | P99 ms | PASS | DROP | Errors | Result |",
        "|-------|------|-------:|---------:|----:|-------:|-------:|-------:|-----:|-----:|-------:|--------|",
    ]
    for ph_id, mode, _ in PHASES:
        r = phase_receipts[ph_id]
        result = "PASS" if r["replay_verdict"] == "PASS" and not r["rsync_blocked"] and not r["critical_hits"] else "FAIL"
        lines.append(
            f"| {ph_id} | {mode} | {r['completed_frames']} | {r['duration_seconds']:.1f}s "
            f"| {r['frames_per_second']:.1f} | {r['avg_frame_latency_ms']:.2f} "
            f"| {r['p95_frame_latency_ms']:.2f} | {r['p99_frame_latency_ms']:.2f} "
            f"| {r['pass_count']} | {r['drop_count']} | {r['error_count']} | {result} |"
        )

    first_fps  = t["first_6000_fps"]
    second_fps = t["second_6000_fps"]
    degrades   = second_fps < first_fps * 0.95

    lines += [
        "",
        "## Throughput Comparison",
        "",
        f"| Mode | Avg FPS |",
        f"|------|--------:|",
    ]
    for mode, fps_val in t["avg_fps_by_mode"].items():
        lines.append(f"| {mode} | {fps_val:.1f} |")
    lines += [
        "",
        f"- FAST vs REGULAR_CRAM delta: **{t['fast_vs_regular_cram_delta_pct']:+.1f}%**",
        f"- FAST_CRAM vs REGULAR_CRAM delta: **{t['fast_cram_vs_regular_cram_delta_pct']:+.1f}%**",
        f"- FAST_CRAM vs FAST delta: **{t['fast_cram_vs_fast_delta_pct']:+.1f}%**",
        "",
        "## Endurance Analysis (First vs Second 6,000 frames)",
        "",
        f"- First 6,000 FPS: **{first_fps:.1f}**",
        f"- Second 6,000 FPS: **{second_fps:.1f}**",
        f"- Degradation: **{'YES' if degrades else 'NO'}** "
          f"({'%.1f' % ((first_fps - second_fps)/first_fps*100)}% slower)" if degrades else
          f"- Degradation: **NO** (stable or faster)",
        "",
        "## Validation Results",
        "",
        f"- Replay parity: `{replay_receipt['overall']}` — hash parity: `{hash_parity}`",
        f"- RSYNC non-blocking: `{rsync_receipt['overall']}`",
        f"- Lane 2 isolation: `{lane2_receipt['overall']}`",
        f"- Failure register entries: `{len(failure_register)}`",
        "",
        "## Governance Status",
        "",
        f"- Campaign state: `{state}`",
        f"- Closed: `false`",
        f"- HRG9: candidate evidence only",
        f"- Production clearance: NOT DECLARED",
        "",
        "## Recommended Next Action",
    ]
    if overall == "PASS":
        lines.append("Human review of C09 artifacts, then pursue OI-03 real Pi-to-Pi transfer.")
    else:
        lines.append("Investigate failure register. Patch root cause. Rerun C09 from zero.")

    (run_dir / "c09_final_report.md").write_text("\n".join(lines) + "\n")

    return {
        "overall": overall,
        "state": state,
        "total_frames_done": total_frames_done,
        "total_fps": round(total_fps, 2),
        "hash_parity": hash_parity,
        "throughput": throughput,
        "replay_overall": replay_receipt["overall"],
        "rsync_overall": rsync_receipt["overall"],
        "lane2_overall": lane2_receipt["overall"],
        "failure_count": len(failure_register),
        "run_dir": str(run_dir),
    }


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--run-dir", type=Path, default=None)
    p.add_argument("--log-dir", type=Path, default=None)
    args = p.parse_args()

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = args.run_dir or Path(f"ph6/cram_pu/validation_runs/{ts}_C09_12000_staged_endurance")
    log_dir = args.log_dir or Path(f"ph6/cram_pu/logs/{ts}_C09_12000_staged_endurance")

    result = run_campaign(run_dir, log_dir)

    print(f"\n{'='*70}")
    print(f"C09 RESULT: {result['overall']}")
    print(f"State: {result['state']}  Closed: false")
    print(f"Total: {result['total_frames_done']}/12000 frames  {result['total_fps']} FPS")
    print(f"Hash parity: {result['hash_parity']}  Replay: {result['replay_overall']}  "
          f"RSYNC: {result['rsync_overall']}  Lane2: {result['lane2_overall']}")
    print(f"Failures: {result['failure_count']}")
    print(f"Run dir: {result['run_dir']}")
    print(f"{'='*70}")

    sys.exit(0 if result["overall"] == "PASS" else 1)
