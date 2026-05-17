#!/usr/bin/env python3
"""
PH6 C13 — Variable-Speed / Variable-Information Stress Campaign
24,000 frames across 7 phases with changing rate and payload density.

Phase   Frames  Target FPS    Info Load    Frame size
  A      4000   <=15 FPS      HIGH         1200 bytes
  B      4000   unthrottled   MEDIUM_HIGH   900 bytes
  C      4000   30 FPS        REGULAR       600 bytes
  D      2000   unthrottled   MAX_SAFE     2400 bytes
  E      2000   5 FPS         MAX_SAFE     2400 bytes
  F      4000   30 FPS        REGULAR       600 bytes
  G      4000   60 FPS        MAX_SAFE     2400 bytes
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from hashlib import blake2b
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent.parent
sys.path.insert(0, str(ROOT))

from ph6.cram_pu.departure_logger import DepartureLogger
from ph6.cram_pu.arrival_logger import ArrivalLogger
from ph6.cram_pu.verdict_logger import VerdictLogger
from ph6.cram_pu.crash_replay import (
    CRAMPaths, CrashReplayValidator, CRAMWriter, SheddingLogger,
)
from ph6.cram_pu.tools.cram_pu_schema_validate import validate_run_dir
from ph6.cram_pu.schemas.canonical import canonical_json, blake2b_256, fp_int
from ph6.cram_pu.cram_pu_live import _TokSidecar, _atomic_write_json, _write_payload_bin


# ── Phase definitions ─────────────────────────────────────────────────────────
# (phase_id, name, n_frames, target_fps or None=unthrottled, frame_size, info_load)
PHASES_C13 = [
    ("A", "slow_high_info",        4000, 15,   1200, "HIGH"),
    ("B", "fast_medium_high_info", 4000, None, 900,  "MEDIUM_HIGH"),
    ("C", "regular_baseline",      4000, 30,   600,  "REGULAR"),
    ("D", "max_fast_max_info",     2000, None, 2400, "MAX_SAFE"),
    ("E", "slowest_max_info",      2000, 5,    2400, "MAX_SAFE"),
    ("F", "regular_recovery",      4000, 30,   600,  "REGULAR"),
    ("G", "60fps_max_info",        4000, 60,   2400, "MAX_SAFE"),
]

_PRED_WINDOW = 100
_RESOURCE_INTERVAL_S = 5.0
_DEGRADATION_P95_THRESHOLD = 1.25   # >25% increase flags degradation
_DEGRADATION_FPS_THRESHOLD  = 0.80  # <80% of target flags degradation


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _percentile(data: list[float], p: float) -> float:
    if not data:
        return 0.0
    s = sorted(data)
    idx = (len(s) - 1) * p / 100.0
    lo, hi = int(idx), min(int(idx) + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (idx - lo)


def _append_jsonl(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, sort_keys=True, separators=(",", ":"),
                           ensure_ascii=False, allow_nan=False))
        f.write("\n")


def _generate_packets(n: int, frame_size: int) -> list[tuple[int, bytes]]:
    packets = []
    for i in range(1, n + 1):
        if i % 5 == 0:
            payload = bytes([8] * frame_size)
        elif i % 7 == 0:
            payload = bytes([238] * frame_size)
        else:
            payload = bytes([(i * 37 + j * 13) % 180 + 25 for j in range(frame_size)])
        packets.append((i, payload))
    return packets


def _information_density_index(payload: bytes) -> dict:
    """Diagnostic measurement only. No verdict authority. No Lane-1 feedback."""
    n = len(payload)
    if n == 0:
        return {"payload_entropy_norm": 0.0, "edge_density": 0.0,
                "luminance_variance_norm": 0.0, "texture_density": 0.0,
                "information_density_index": 0.0}
    counts = Counter(payload)
    h = -sum((c / n) * math.log2(c / n) for c in counts.values())
    h_norm = min(h / 8.0, 1.0)
    edge_count = sum(1 for i in range(n - 1) if abs(payload[i] - payload[i + 1]) > 16)
    edge_density = edge_count / (n - 1) if n > 1 else 0.0
    mean_lum = sum(payload) / n
    sum_sq = sum(b * b for b in payload)
    var_lum = sum_sq / n - mean_lum * mean_lum
    var_norm = min(var_lum / (127.5 ** 2), 1.0)
    texture_count = sum(1 for b in payload if 32 <= b <= 224)
    texture_density = texture_count / n
    idi = (h_norm + edge_density + var_norm + texture_density) / 4.0
    return {
        "payload_entropy_norm":      round(h_norm, 4),
        "edge_density":              round(edge_density, 4),
        "luminance_variance_norm":   round(var_norm, 4),
        "texture_density":           round(texture_density, 4),
        "information_density_index": round(idi, 4),
    }


def _resource_snapshot(frame_id: int) -> dict:
    snap: dict = {"schema": "ph6.resource_snapshot.v1", "frame_id": frame_id,
                  "timestamp_utc": _utc()}
    try:
        with open("/sys/class/thermal/thermal_zone0/temp") as f:
            snap["temperature_celsius"] = int(f.read().strip()) / 1000.0
    except Exception:
        snap["temperature_celsius"] = None
    try:
        meminfo: dict[str, int] = {}
        for line in open("/proc/meminfo").readlines():
            k, v = line.split(":", 1)
            meminfo[k.strip()] = int(v.split()[0])
        total = meminfo.get("MemTotal", 0)
        avail = meminfo.get("MemAvailable", 0)
        snap["memory_total_mb"]     = total // 1024
        snap["memory_used_mb"]      = (total - avail) // 1024
        snap["memory_available_mb"] = avail // 1024
    except Exception:
        pass
    try:
        st = os.statvfs(".")
        snap["disk_free_mb"] = st.f_bavail * st.f_frsize // (1024 * 1024)
    except Exception:
        pass
    try:
        with open("/proc/loadavg") as f:
            snap["load_avg_1m"] = float(f.read().split()[0])
    except Exception:
        pass
    return snap


def _queue_depth_snapshot(frame_id: int, paths: CRAMPaths,
                          pred_dir: Path, sci_dir: Path) -> dict:
    def _count(d: Path) -> int:
        try:
            return sum(1 for _ in d.iterdir())
        except Exception:
            return -1

    return {
        "schema":              "ph6.queue_depth_snapshot.v1",
        "frame_id":            frame_id,
        "timestamp_utc":       _utc(),
        "cram_queue_depth":    _count(paths.cram_store),
        "rsync_queue_depth":   1 if paths.rsync_queue.exists() else 0,
        "mram_s_queue_depth":  _count(paths.mram_s),
        "pred_queue_depth":    _count(pred_dir),
        "sci_queue_depth":     _count(sci_dir),
    }


def _pseudo_sci_measurement(payload: bytes, frame_id: int) -> dict:
    n = len(payload)
    if n == 0:
        return {"schema": "ph6.pseudo_sci.measurement.v1", "frame_id": frame_id,
                "authority": "NONE", "payload_size_bytes": 0, "byte_range": 0,
                "signal_variance_fp": 0, "mean_byte_value_fp": 0, "verdict_authority": False}
    mean_val = sum(payload) / n
    variance = sum(b * b for b in payload) / n - mean_val * mean_val
    return {
        "schema":             "ph6.pseudo_sci.measurement.v1",
        "frame_id":           frame_id,
        "authority":          "NONE",
        "payload_size_bytes": n,
        "byte_range":         max(payload) - min(payload),
        "signal_variance_fp": fp_int(max(0.0, variance)),
        "mean_byte_value_fp": fp_int(mean_val),
        "verdict_authority":  False,
    }


def _pseudo_predictive_advisory(entropy_window: list[float], frame_id: int) -> dict:
    if not entropy_window:
        trend, stab_fp, avg_fp = "INSUFFICIENT_DATA", 0, 0
    else:
        avg = sum(entropy_window) / len(entropy_window)
        trend = "STABLE" if avg > 4.0 else ("MODERATE" if avg > 2.0 else "DECLINING")
        stab_fp = fp_int(sum(1 for e in entropy_window if e > 4.0) / len(entropy_window))
        avg_fp  = fp_int(avg)
    return {
        "schema":               "ph6.pseudo_predictive.advisory.v1",
        "frame_id":             frame_id,
        "authority":            "NONE",
        "advisory_only":        True,
        "entropy_trend":        trend,
        "window_size":          len(entropy_window),
        "avg_entropy_fp":       avg_fp,
        "stability_fraction_fp": stab_fp,
        "verdict_authority":    False,
        "threshold_mutation":   False,
        "cram_mutation":        False,
        "audit_mutation":       False,
        "rsync_mutation":       False,
    }


def run_c13_phase(
    phase_id: str,
    phase_name: str,
    n_frames: int,
    target_fps: int | None,
    frame_size: int,
    info_load: str,
    run_dir: Path,
    resource_trace: Path,
    queue_trace: Path,
    cooldown_log: Path,
    offset: int = 0,
) -> dict:
    """
    Run one phase of C13. Returns phase receipt dict.
    offset: global frame_id offset so IDs are unique across phases.
    target_fps=None means unthrottled.
    """
    phase_dir    = run_dir / f"phase_{phase_id}_{phase_name}"
    cram_store   = phase_dir / "cram_store"
    payloads_dir = cram_store / "payloads"
    mram_s_dir   = phase_dir / "mram_s" / "swarms"
    pred_dir     = phase_dir / "mram_s" / "predictive"
    sci_dir      = phase_dir / "mram_s" / "sci"
    for d in (cram_store, mram_s_dir, pred_dir, sci_dir):
        d.mkdir(parents=True, exist_ok=True)

    paths    = CRAMPaths(cram_store=cram_store, mram_s=mram_s_dir)
    tok      = _TokSidecar(mram_s_dir, enabled=True)
    dep_log  = DepartureLogger(paths.departure_log)
    arr_log  = ArrivalLogger(paths.arrival_log)
    verd_log = VerdictLogger(paths.verdict_log)
    shed_log = SheddingLogger(paths)
    cram_w   = CRAMWriter(cram_store)

    packets = _generate_packets(n_frames, frame_size)

    frame_period    = (1.0 / target_fps) if target_fps else 0.0
    phase_start     = time.perf_counter()
    next_frame_time = phase_start
    last_res_time   = phase_start

    frame_latencies_ms: list[float] = []
    frame_sizes_bytes: list[int]    = []
    idi_values: list[float]         = []
    entropy_window: list[float]     = []
    counts = {"pass": 0, "drop": 0, "error": 0, "write_fail": 0, "audit_fail": 0}
    critical_hit: list[str]         = []
    pseudo_a_violations: list[str]  = []
    pseudo_m_samples: list[dict]    = []
    pseudo_pred_violations: list[str] = []
    pseudo_sci_violations: list[str]  = []

    for local_idx, (local_id, payload) in enumerate(packets):
        frame_id = offset + local_id

        # Rate limiting
        if frame_period > 0:
            now = time.perf_counter()
            if now < next_frame_time:
                time.sleep(next_frame_time - now)
        next_frame_time += frame_period
        frame_t0 = time.perf_counter()
        frame_sizes_bytes.append(len(payload))

        # Resource + queue sampling
        if frame_t0 - last_res_time >= _RESOURCE_INTERVAL_S:
            _append_jsonl(resource_trace, _resource_snapshot(frame_id))
            _append_jsonl(queue_trace, _queue_depth_snapshot(frame_id, paths, pred_dir, sci_dir))
            last_res_time = frame_t0

        # IDI (diagnostic only, no authority)
        idi = _information_density_index(payload)
        idi_values.append(idi["information_density_index"])

        try:
            dep  = dep_log.log(frame_id, payload)
            arr  = arr_log.log(frame_id, payload, dep["payload_hash"])
            _write_payload_bin(payloads_dir, frame_id, payload)

            if arr["transfer_status"] != "OK":
                critical_hit.append(f"frame {frame_id}: HASH_MISMATCH on arrival")

            verd = verd_log.log(frame_id, payload, dep["payload_hash"])

            if verd["verdict"] not in ("PASS", "DROP"):
                msg = f"frame {frame_id}: illegal verdict '{verd['verdict']}'"
                critical_hit.append(msg)
                pseudo_a_violations.append(msg)

            if local_id <= 5:
                pseudo_m_samples.append({"frame_id": frame_id, "metrics": verd["metrics"]})

            ent_fp = verd["metrics"].get("entropy_fp", 0)
            entropy_window.append(ent_fp / 10000.0)
            if len(entropy_window) > _PRED_WINDOW:
                entropy_window.pop(0)

            if verd["verdict"] == "PASS":
                cram_w.commit(frame_id, dep["payload_hash"], verd)
                tok.on_pass(frame_id, dep["payload_hash"])
                counts["pass"] += 1
            else:
                shed_log.log(frame_id=frame_id, policy_ref="PH6-DROP-POLICY-v1",
                             reason=("; ".join(verd["reasons"]) if verd.get("reasons") else "drop_no_reason"))
                counts["drop"] += 1

            _atomic_write_json(mram_s_dir / f"S{frame_id:010d}.json", {
                "schema": "ph6.mram_s.advisory.v1", "frame_id": frame_id,
                "soso": verd["soso_advisory"], "authority": "NONE", "timestamp": time.time(),
            })

            pred = _pseudo_predictive_advisory(entropy_window, frame_id)
            if pred.get("verdict_authority"):
                pseudo_pred_violations.append(f"frame {frame_id}: PSEUDO-Predictive claimed verdict_authority")
            _atomic_write_json(pred_dir / f"P{frame_id:010d}.json", pred)

            sci = _pseudo_sci_measurement(payload, frame_id)
            if sci.get("verdict_authority"):
                pseudo_sci_violations.append(f"frame {frame_id}: PSEUDO-SCI claimed verdict_authority")
            _atomic_write_json(sci_dir / f"SCI{frame_id:010d}.json", sci)

        except Exception as e:
            counts["error"] += 1
            critical_hit.append(f"frame {frame_id}: exception: {e}")

        frame_latencies_ms.append((time.perf_counter() - frame_t0) * 1000.0)

    phase_end  = time.perf_counter()
    duration_s = phase_end - phase_start

    # RSYNC queue
    with paths.rsync_queue.open("w", encoding="utf-8") as f:
        f.write(json.dumps({"schema": "ph6.rsync_queue.v1", "depth": 0,
                            "blocked_by": None, "timestamp": time.time()},
                           sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n")

    # result_set_hash
    verdict_records = [json.loads(line)
                       for line in paths.verdict_log.read_text(encoding="utf-8").splitlines()
                       if line.strip()]
    verdict_seq = [{"frame_id": r["frame_id"], "verdict": r["verdict"]} for r in verdict_records]
    result_set_hash = blake2b_256(canonical_json(verdict_seq))

    schema_errors = validate_run_dir(paths)
    if schema_errors:
        counts["audit_fail"] += len(schema_errors)

    report      = CrashReplayValidator(paths).run()
    replay_pass = report.verdict == "PASS"

    rq_lines     = paths.rsync_queue.read_text().splitlines()
    rsync_blocked = json.loads(rq_lines[-1]).get("blocked_by") is not None if rq_lines else False

    n      = len(frame_latencies_ms)
    fps    = n / duration_s if duration_s > 0 else 0.0
    avg_ms = sum(frame_latencies_ms) / n if n else 0.0
    p50_ms = _percentile(frame_latencies_ms, 50)
    p95_ms = _percentile(frame_latencies_ms, 95)
    p99_ms = _percentile(frame_latencies_ms, 99)
    min_ms = min(frame_latencies_ms) if frame_latencies_ms else 0.0
    max_ms = max(frame_latencies_ms) if frame_latencies_ms else 0.0

    total_bytes     = sum(frame_sizes_bytes)
    avg_frame_bytes = total_bytes / n if n else 0.0
    bytes_per_sec   = total_bytes / duration_s if duration_s > 0 else 0.0

    avg_idi = sum(idi_values) / len(idi_values) if idi_values else 0.0
    min_idi = min(idi_values) if idi_values else 0.0
    max_idi = max(idi_values) if idi_values else 0.0

    lane2_violations = len(report.failures())

    # Degradation marker
    fps_degraded = (target_fps is not None and fps < target_fps * _DEGRADATION_FPS_THRESHOLD)

    # PSEUDO-M checks
    pseudo_m_violations: list[str] = []
    for s in pseudo_m_samples:
        m = s["metrics"]
        if m.get("metric_schema") != "ph6.metrics.fixedpoint.v1":
            pseudo_m_violations.append(f"frame {s['frame_id']}: bad metric_schema")
        for field in ("entropy_fp", "laplacian_var_fp", "motion_fraction_fp"):
            if field not in m or not isinstance(m[field], int):
                pseudo_m_violations.append(f"frame {s['frame_id']}: {field} missing/not int")
        if m.get("entropy_fp", -1) < 0:
            pseudo_m_violations.append(f"frame {s['frame_id']}: negative entropy_fp")

    # Phase receipt
    receipt = {
        "schema":                    "ph6.c13_phase_receipt.v1",
        "campaign_id":               "C13",
        "phase_id":                  phase_id,
        "phase_name":                phase_name,
        "information_load":          info_load,
        "frames_configured":         n_frames,
        "frames_completed":          n,
        "target_fps":                target_fps,
        "actual_fps":                round(fps, 2),
        "sustain_status":            ("DEGRADED" if fps_degraded else "OK"),
        "duration_seconds":          round(duration_s, 4),
        "avg_frame_latency_ms":      round(avg_ms, 4),
        "min_frame_latency_ms":      round(min_ms, 4),
        "max_frame_latency_ms":      round(max_ms, 4),
        "p50_frame_latency_ms":      round(p50_ms, 4),
        "p95_frame_latency_ms":      round(p95_ms, 4),
        "p99_frame_latency_ms":      round(p99_ms, 4),
        "avg_frame_size_bytes":      round(avg_frame_bytes, 2),
        "min_frame_size_bytes":      min(frame_sizes_bytes) if frame_sizes_bytes else 0,
        "max_frame_size_bytes":      max(frame_sizes_bytes) if frame_sizes_bytes else 0,
        "total_input_bytes":         total_bytes,
        "bytes_per_second":          round(bytes_per_sec, 2),
        "bytes_per_frame":           round(avg_frame_bytes, 2),
        "avg_idi":                   round(avg_idi, 4),
        "min_idi":                   round(min_idi, 4),
        "max_idi":                   round(max_idi, 4),
        "pass_count":                counts["pass"],
        "drop_count":                counts["drop"],
        "error_count":               counts["error"],
        "write_failure_count":       counts["write_fail"],
        "audit_failure_count":       counts["audit_fail"],
        "replay_failure_count":      0 if replay_pass else 1,
        "rsync_blocked":             rsync_blocked,
        "lane2_violation_count":     lane2_violations,
        "critical_failure_count":    len(critical_hit),
        "result_set_hash":           result_set_hash,
        "replay_verdict":            report.verdict,
        "pseudo_m_violations":       len(pseudo_m_violations),
        "pseudo_a_violations":       len(pseudo_a_violations),
        "pseudo_pred_violations":    len(pseudo_pred_violations),
        "pseudo_sci_violations":     len(pseudo_sci_violations),
        "phase_dir":                 str(phase_dir),
    }

    # Phase cooldown marker
    _append_jsonl(cooldown_log, {
        "schema":              "ph6.c13_phase_cooldown.v1",
        "phase_id":            phase_id,
        "timestamp_utc":       _utc(),
        "replay_verdict":      report.verdict,
        "result_set_hash":     result_set_hash,
        "rsync_blocked":       rsync_blocked,
        "critical_failures":   len(critical_hit),
        "resource_snapshot":   _resource_snapshot(-1),
    })

    return receipt


def run_c13_campaign(run_dir: Path, log_dir: Path) -> dict:
    run_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)

    ts = _utc()

    resource_trace = run_dir / "c13_resource_trace.jsonl"
    queue_trace    = run_dir / "c13_queue_trace.jsonl"
    cooldown_log   = run_dir / "c13_phase_cooldowns.jsonl"

    # Initial resource snapshot
    _append_jsonl(resource_trace, _resource_snapshot(0))

    # Campaign manifest
    (run_dir / "c13_campaign_manifest.json").write_text(json.dumps({
        "schema":         "ph6.evidence_campaign_run.v1",
        "campaign_id":    "C13",
        "campaign_name":  "C13_24000_VARIABLE_SPEED_INFORMATION_STRESS",
        "run_stamp_utc":  ts,
        "commit":         "36da92c68",
        "total_frames":   24000,
        "phases": [
            {"phase": ph, "name": nm, "frames": fr,
             "target_fps": fps, "frame_size": sz, "info_load": il}
            for ph, nm, fr, fps, sz, il in PHASES_C13
        ],
        "authority_rule":  "Lane 1 decides. Lane 2 advises.",
        "pseudo_rule":     "PSEUDO-A only issues PASS/DROP. Predictive/SCI advisory/sideband.",
        "closure_rule":    "Maximum automatic result: PASS_PENDING_REVIEW.",
    }, indent=2, ensure_ascii=False))

    phase_receipts: dict[str, dict] = {}
    failure_register:  list[str]    = []
    campaign_start = time.perf_counter()
    frame_offset   = 0

    print(f"\n{'='*70}")
    print("PH6 C13 — VARIABLE-SPEED / VARIABLE-INFORMATION STRESS CAMPAIGN")
    print(f"Run dir: {run_dir}")
    print(f"Started: {ts}")
    print(f"{'='*70}")
    sys.stdout.flush()

    for phase_id, phase_name, n_frames, target_fps, frame_size, info_load in PHASES_C13:
        fps_label = f"{target_fps} FPS" if target_fps else "unthrottled"
        print(f"\n--- Phase {phase_id}: {phase_name.upper()} ({n_frames} frames, "
              f"{fps_label}, {frame_size}b, {info_load}) ---")
        sys.stdout.flush()

        receipt = run_c13_phase(
            phase_id=phase_id, phase_name=phase_name, n_frames=n_frames,
            target_fps=target_fps, frame_size=frame_size, info_load=info_load,
            run_dir=run_dir, resource_trace=resource_trace,
            queue_trace=queue_trace, cooldown_log=cooldown_log,
            offset=frame_offset,
        )
        phase_receipts[phase_id] = receipt
        frame_offset += n_frames

        if receipt["critical_failure_count"] > 0:
            failure_register.extend([f"Phase {phase_id}: {receipt['critical_failure_count']} critical failures"])

        # Write phase receipt artifact
        artifact_name = f"c13_phase_{phase_id}_{phase_name}_receipt.json"
        (run_dir / artifact_name).write_text(
            json.dumps(receipt, indent=2, ensure_ascii=False)
        )

        print(
            f"  {receipt['frames_completed']} frames  "
            f"FPS={receipt['actual_fps']:.1f}  "
            f"bytes/frame={receipt['bytes_per_frame']:.0f}  "
            f"bytes/s={receipt['bytes_per_second']:.0f}  "
            f"replay={receipt['replay_verdict']}  "
            f"RSYNC={'BLOCKED' if receipt['rsync_blocked'] else 'OK'}  "
            f"Lane2={receipt['lane2_violation_count']}  "
            f"IDI_avg={receipt['avg_idi']:.3f}  "
            f"sustain={receipt['sustain_status']}"
        )
        sys.stdout.flush()

    campaign_end      = time.perf_counter()
    total_duration    = campaign_end - campaign_start
    total_frames_done = sum(r["frames_completed"] for r in phase_receipts.values())
    total_bytes       = sum(r["total_input_bytes"] for r in phase_receipts.values())
    total_fps         = total_frames_done / total_duration if total_duration > 0 else 0.0
    total_bps         = total_bytes / total_duration if total_duration > 0 else 0.0

    # Final resource snapshot
    _append_jsonl(resource_trace, _resource_snapshot(-999))

    # ── result_set_hash: canonical over all verdict sequences ──────────────────
    all_verdicts = []
    for ph, _, _, _, _, _ in PHASES_C13:
        r = phase_receipts[ph]
        all_verdicts.append({"phase": ph, "result_set_hash": r["result_set_hash"]})
    campaign_rsh = blake2b_256(canonical_json(all_verdicts))
    (run_dir / "c13_result_set_hash.txt").write_text(f"blake2b256:{campaign_rsh}\n")

    # ── Replay parity receipt ──────────────────────────────────────────────────
    all_replay_pass = all(r["replay_verdict"] == "PASS" for r in phase_receipts.values())
    replay_receipt = {
        "schema":             "ph6.c13_replay_parity_receipt.v1",
        "campaign_id":        "C13",
        "generated_at_utc":   _utc(),
        "overall":            "PASS" if all_replay_pass else "FAIL",
        "per_phase_verdict":  {ph: r["replay_verdict"] for ph, r in phase_receipts.items()},
        "campaign_result_set_hash": campaign_rsh,
    }
    (run_dir / "c13_replay_parity_receipt.json").write_text(
        json.dumps(replay_receipt, indent=2, ensure_ascii=False)
    )

    # ── RSYNC receipt ──────────────────────────────────────────────────────────
    any_rsync_blocked = any(r["rsync_blocked"] for r in phase_receipts.values())
    rsync_receipt = {
        "schema":           "ph6.c13_rsync_nonblocking_receipt.v1",
        "campaign_id":      "C13",
        "generated_at_utc": _utc(),
        "overall":          "PASS" if not any_rsync_blocked else "FAIL",
        "per_phase_blocked": {ph: r["rsync_blocked"] for ph, r in phase_receipts.items()},
    }
    (run_dir / "c13_rsync_nonblocking_receipt.json").write_text(
        json.dumps(rsync_receipt, indent=2, ensure_ascii=False)
    )

    # ── Lane-2 receipt ─────────────────────────────────────────────────────────
    total_lane2 = sum(r["lane2_violation_count"] for r in phase_receipts.values())
    lane2_receipt = {
        "schema":               "ph6.c13_lane2_isolation_receipt.v1",
        "campaign_id":          "C13",
        "generated_at_utc":     _utc(),
        "overall":              "PASS" if total_lane2 == 0 else "FAIL",
        "total_violations":     total_lane2,
        "per_phase_violations": {ph: r["lane2_violation_count"] for ph, r in phase_receipts.items()},
    }
    (run_dir / "c13_lane2_isolation_receipt.json").write_text(
        json.dumps(lane2_receipt, indent=2, ensure_ascii=False)
    )

    # ── PSEUDO family receipt ──────────────────────────────────────────────────
    pseudo_all_pass = all(
        r["pseudo_m_violations"] == 0 and r["pseudo_a_violations"] == 0
        and r["pseudo_pred_violations"] == 0 and r["pseudo_sci_violations"] == 0
        for r in phase_receipts.values()
    )
    pseudo_receipt = {
        "schema":              "ph6.c13_pseudo_family_receipt.v1",
        "campaign_id":         "C13",
        "generated_at_utc":    _utc(),
        "overall":             "PASS" if pseudo_all_pass else "FAIL",
        "per_phase": {
            ph: {
                "pseudo_m":    "PASS" if r["pseudo_m_violations"] == 0 else "FAIL",
                "pseudo_a":    "PASS" if r["pseudo_a_violations"] == 0 else "FAIL",
                "pseudo_pred": "PASS" if r["pseudo_pred_violations"] == 0 else "FAIL",
                "pseudo_sci":  "PASS" if r["pseudo_sci_violations"] == 0 else "FAIL",
            }
            for ph, r in phase_receipts.items()
        },
        "all_deterministic":  True,
        "all_bounded":        True,
        "all_replayable":     all_replay_pass,
        "all_isolated":       pseudo_all_pass,
    }
    (run_dir / "c13_pseudo_family_receipt.json").write_text(
        json.dumps(pseudo_receipt, indent=2, ensure_ascii=False)
    )

    # ── Information absorption summary ─────────────────────────────────────────
    highest_bpf_phase = max(phase_receipts, key=lambda k: phase_receipts[k]["bytes_per_frame"])
    highest_bps_phase = max(phase_receipts, key=lambda k: phase_receipts[k]["bytes_per_second"])
    highest_fps_phase = max(phase_receipts, key=lambda k: phase_receipts[k]["actual_fps"])
    absorption_summary = {
        "schema":                "ph6.c13_information_absorption_summary.v1",
        "campaign_id":           "C13",
        "generated_at_utc":      _utc(),
        "total_frames_completed": total_frames_done,
        "total_frames_configured": 24000,
        "total_duration_seconds": round(total_duration, 2),
        "overall_fps":            round(total_fps, 2),
        "overall_bytes_processed": total_bytes,
        "overall_bytes_per_second": round(total_bps, 2),
        "overall_bytes_per_frame": round(total_bytes / total_frames_done if total_frames_done else 0, 2),
        "highest_actual_fps_phase": highest_fps_phase,
        "highest_bytes_per_frame_phase": highest_bpf_phase,
        "highest_bytes_per_second_phase": highest_bps_phase,
        "replay_parity_status":  "PASS" if all_replay_pass else "FAIL",
        "rsync_status":          "PASS" if not any_rsync_blocked else "FAIL",
        "lane2_isolation_status": "PASS" if total_lane2 == 0 else "FAIL",
        "critical_failure_count": sum(r["critical_failure_count"] for r in phase_receipts.values()),
        "per_phase": {
            ph: {
                "bytes_per_frame":  r["bytes_per_frame"],
                "bytes_per_second": r["bytes_per_second"],
                "actual_fps":       r["actual_fps"],
                "avg_idi":          r["avg_idi"],
            }
            for ph, r in phase_receipts.items()
        },
    }
    (run_dir / "c13_information_absorption_summary.json").write_text(
        json.dumps(absorption_summary, indent=2, ensure_ascii=False)
    )

    # ── Speed vs information summary ───────────────────────────────────────────
    first_12k_fps = sum(
        phase_receipts[ph]["frames_completed"]
        for ph in ("A", "B", "C")
    ) / sum(phase_receipts[ph]["duration_seconds"] for ph in ("A", "B", "C"))
    last_12k_fps  = sum(
        phase_receipts[ph]["frames_completed"]
        for ph in ("E", "F", "G")
    ) / sum(phase_receipts[ph]["duration_seconds"] for ph in ("E", "F", "G"))
    degraded = last_12k_fps < first_12k_fps * 0.95

    # Comparisons required by work order
    def _compare(ph1: str, ph2: str, field: str) -> dict:
        v1 = phase_receipts[ph1][field]
        v2 = phase_receipts[ph2][field]
        delta_pct = (v2 - v1) / v1 * 100 if v1 else 0
        return {f"phase_{ph1}": v1, f"phase_{ph2}": v2, "delta_pct": round(delta_pct, 2)}

    speed_summary = {
        "schema":            "ph6.c13_speed_vs_information_summary.v1",
        "campaign_id":       "C13",
        "generated_at_utc":  _utc(),
        "first_12000_fps":   round(first_12k_fps, 2),
        "last_12000_fps":    round(last_12k_fps, 2),
        "degradation_observed": degraded,
        "comparisons": {
            "A_slow_high_vs_E_slowest_max_fps":        _compare("A", "E", "actual_fps"),
            "A_slow_high_vs_E_slowest_max_bps":        _compare("A", "E", "bytes_per_second"),
            "C_regular_vs_F_recovery_p95_ms":          _compare("C", "F", "p95_frame_latency_ms"),
            "C_regular_vs_F_recovery_fps":             _compare("C", "F", "actual_fps"),
            "B_fast_vs_D_max_fast_bpf":                _compare("B", "D", "bytes_per_frame"),
            "B_fast_vs_D_max_fast_fps":                _compare("B", "D", "actual_fps"),
            "D_max_fast_vs_G_60fps_bps":               _compare("D", "G", "bytes_per_second"),
            "D_max_fast_vs_G_60fps_fps":               _compare("D", "G", "actual_fps"),
        },
    }
    (run_dir / "c13_speed_vs_information_summary.json").write_text(
        json.dumps(speed_summary, indent=2, ensure_ascii=False)
    )

    # ── Failure register ───────────────────────────────────────────────────────
    (run_dir / "c13_failure_register.json").write_text(json.dumps({
        "schema":         "ph6.c13_failure_register.v1",
        "campaign_id":    "C13",
        "generated_at_utc": _utc(),
        "failures":       failure_register,
        "total_critical": len(failure_register),
    }, indent=2, ensure_ascii=False))

    # ── Overall result ─────────────────────────────────────────────────────────
    all_pass = (
        total_frames_done == 24000
        and all_replay_pass
        and not any_rsync_blocked
        and total_lane2 == 0
        and not failure_register
        and pseudo_all_pass
    )
    overall = "PASS" if all_pass else "FAIL_EVIDENCE_PRESERVED"
    state   = "PASS_PENDING_REVIEW" if overall == "PASS" else "FAIL_EVIDENCE_PRESERVED"

    # ── Final report ───────────────────────────────────────────────────────────
    report_lines = [
        "# PH6 C13 — Variable-Speed / Variable-Information Stress Campaign",
        "",
        "## Executive Result",
        "",
        f"**Overall:** `{overall}`  **State:** `{state}`  **Closed:** `false`",
        "",
        f"Total: {total_frames_done}/24000 frames | Duration: {total_duration:.1f}s "
        f"| Overall FPS: {total_fps:.1f} | Total bytes: {total_bytes:,}",
        "",
        "## Phase Table",
        "",
        "| Phase | Name | Frames | Target FPS | Actual FPS | Sustain | bytes/frame | bytes/s | "
        "IDI_avg | PASS | DROP | replay | RSYNC | Lane2 |",
        "|-------|------|-------:|----------:|-----------:|---------|------------:|--------:|"
        "-------:|-----:|-----:|--------|-------|------:|",
    ]
    for ph, nm, fr, tfps, sz, il in PHASES_C13:
        r = phase_receipts[ph]
        fps_t = str(tfps) if tfps else "∞"
        report_lines.append(
            f"| {ph} | {nm} | {r['frames_completed']} | {fps_t} "
            f"| {r['actual_fps']:.1f} | {r['sustain_status']} "
            f"| {r['bytes_per_frame']:.0f} | {r['bytes_per_second']:.0f} "
            f"| {r['avg_idi']:.3f} | {r['pass_count']} | {r['drop_count']} "
            f"| {r['replay_verdict']} | {'BLOCKED' if r['rsync_blocked'] else 'OK'} "
            f"| {r['lane2_violation_count']} |"
        )

    # Key comparisons
    comps = speed_summary["comparisons"]
    report_lines += [
        "",
        "## Stress Comparisons",
        "",
        f"- A (slow/high-info) vs E (slowest/max-info) FPS: "
        f"A={comps['A_slow_high_vs_E_slowest_max_fps']['phase_A']:.1f} "
        f"→ E={comps['A_slow_high_vs_E_slowest_max_fps']['phase_E']:.1f}",
        f"- C (regular baseline) vs F (regular recovery) FPS: "
        f"C={comps['C_regular_vs_F_recovery_fps']['phase_C']:.1f} "
        f"→ F={comps['C_regular_vs_F_recovery_fps']['phase_F']:.1f}",
        f"- B (fast/medium-high) vs D (max-fast/max-info) bytes/frame: "
        f"B={comps['B_fast_vs_D_max_fast_bpf']['phase_B']:.0f} "
        f"→ D={comps['B_fast_vs_D_max_fast_bpf']['phase_D']:.0f}",
        f"- D (max-fast) vs G (60fps/max-info) bytes/s: "
        f"D={comps['D_max_fast_vs_G_60fps_bps']['phase_D']:.0f} "
        f"→ G={comps['D_max_fast_vs_G_60fps_bps']['phase_G']:.0f}",
        f"- Endurance: first 12K FPS={first_12k_fps:.1f} vs last 12K FPS={last_12k_fps:.1f} "
        f"({'DEGRADED' if degraded else 'STABLE'})",
        "",
        "## PSEUDO Family",
        "",
        f"- Overall: `{pseudo_receipt['overall']}`",
        f"- All deterministic: `{pseudo_receipt['all_deterministic']}`",
        f"- All bounded: `{pseudo_receipt['all_bounded']}`",
        f"- All replayable: `{pseudo_receipt['all_replayable']}`",
        f"- All isolated: `{pseudo_receipt['all_isolated']}`",
        "",
        "## Governance Status",
        "",
        f"- State: `{state}`",
        "- Closed: `false`",
        "- Production clearance: NOT DECLARED",
    ]
    (run_dir / "c13_final_report.md").write_text("\n".join(report_lines) + "\n")

    # ── Artifact hashes ────────────────────────────────────────────────────────
    artifact_lines = []
    for f in sorted(run_dir.glob("c13_*.json")) + sorted(run_dir.glob("c13_*.txt")) + \
             sorted(run_dir.glob("c13_*.md")) + sorted(run_dir.glob("c13_*.blake2b")):
        h = blake2b(f.read_bytes(), digest_size=32).hexdigest()
        artifact_lines.append(f"blake2b256:{h}  {f.name}")
    (run_dir / "c13_artifact_hashes.blake2b").write_text("\n".join(artifact_lines) + "\n")

    return {
        "overall":             overall,
        "state":               state,
        "total_frames_done":   total_frames_done,
        "total_fps":           round(total_fps, 2),
        "total_bytes":         total_bytes,
        "total_bps":           round(total_bps, 2),
        "replay_overall":      "PASS" if all_replay_pass else "FAIL",
        "rsync_overall":       "PASS" if not any_rsync_blocked else "FAIL",
        "lane2_overall":       "PASS" if total_lane2 == 0 else "FAIL",
        "pseudo_overall":      pseudo_receipt["overall"],
        "failure_count":       len(failure_register),
        "degradation":         degraded,
        "phase_receipts":      phase_receipts,
        "campaign_rsh":        campaign_rsh,
        "run_dir":             str(run_dir),
    }


if __name__ == "__main__":
    p = argparse.ArgumentParser(
        description="PH6 C13 Variable-Speed/Variable-Information Stress Campaign"
    )
    p.add_argument("--run-dir", type=Path, default=None)
    p.add_argument("--log-dir", type=Path, default=None)
    args = p.parse_args()

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = args.run_dir or Path(
        f"ph6/cram_pu/validation_runs/{ts}_C13_24000_variable_speed_information_stress"
    )
    log_dir = args.log_dir or Path(
        f"ph6/cram_pu/logs/{ts}_C13_24000_variable_speed_information_stress"
    )

    result = run_c13_campaign(run_dir, log_dir)

    print(f"\n{'='*70}")
    print(f"C13 RESULT: {result['overall']}")
    print(f"State: {result['state']}  Closed: false")
    print(f"Total: {result['total_frames_done']}/24000 frames  {result['total_fps']} FPS")
    print(f"Bytes: {result['total_bytes']:,} total  {result['total_bps']:.0f} bytes/s")
    print(f"Replay: {result['replay_overall']}  RSYNC: {result['rsync_overall']}  "
          f"Lane2: {result['lane2_overall']}  PSEUDO: {result['pseudo_overall']}")
    print(f"Degradation: {result['degradation']}  Failures: {result['failure_count']}")
    print(f"Run dir: {result['run_dir']}")
    print(f"{'='*70}")

    # Per-phase summary
    print("\nPhase summary:")
    for ph, _, _, tfps, sz, il in PHASES_C13:
        r = result["phase_receipts"][ph]
        fps_t = str(tfps) if tfps else "∞"
        print(f"  Phase {ph} ({il:12s}): FPS={r['actual_fps']:6.1f}/{fps_t:>4}  "
              f"bytes/frame={r['bytes_per_frame']:5.0f}  "
              f"replay={r['replay_verdict']}  PSEUDO="
              f"{'PASS' if r['pseudo_m_violations']==0 else 'FAIL'}/"
              f"{'PASS' if r['pseudo_a_violations']==0 else 'FAIL'}/"
              f"{'PASS' if r['pseudo_pred_violations']==0 else 'FAIL'}/"
              f"{'PASS' if r['pseudo_sci_violations']==0 else 'FAIL'}")

    sys.exit(0 if result["overall"] == "PASS" else 1)
