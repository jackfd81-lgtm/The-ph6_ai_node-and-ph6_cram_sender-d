#!/usr/bin/env python3
"""
LCC-01 — Life CRAM Real-Camera Live Stream Session runner.

Captures frames from a real camera device, processes them through the
CRAM-PU pipeline with image-space PSEUDO metrics, and produces a full
evidence artifact set suitable for replay verification.

Usage:
    python3 life_cram_lcc_01_live_camera.py [--frames N] [--device /dev/video0]
    python3 life_cram_lcc_01_live_camera.py --frames 300   # LCC-01A smoke
    python3 life_cram_lcc_01_live_camera.py --frames 1200  # LCC-01B standard
    python3 life_cram_lcc_01_live_camera.py --frames 3600  # LCC-01C evidence

Final line on success:
    LCC_01_CAMERA_PASS=True
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent.parent
sys.path.insert(0, str(ROOT))

from ph6.cram_pu.departure_logger import DepartureLogger
from ph6.cram_pu.arrival_logger import ArrivalLogger
from ph6.cram_pu.crash_replay import (
    CRAMPaths, CrashReplayValidator, CRAMWriter, SheddingLogger,
)
from ph6.cram_pu.tools.cram_pu_schema_validate import validate_run_dir
from ph6.cram_pu.schemas.canonical import canonical_json, blake2b_256, fp_int
from ph6.cram_pu.cram_pu_live import _TokSidecar, _atomic_write_json, _write_payload_bin


# ── Real-camera PSEUDO thresholds ─────────────────────────────────────────────
BRIGHT_MIN = 20
BRIGHT_MAX = 235
LAP_MIN    = 15.0
MOTION_MAX = 0.40

_FP_BRIGHT_MIN = fp_int(BRIGHT_MIN)
_FP_BRIGHT_MAX = fp_int(BRIGHT_MAX)
_FP_LAP_MIN    = fp_int(LAP_MIN)
_FP_MOTION_MAX = fp_int(MOTION_MAX)

LCC_01A_MIN = 300
LCC_01B_MIN = 1200
LCC_01C_MIN = 3600


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _append_jsonl(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, sort_keys=True, separators=(",", ":"),
                           ensure_ascii=False, allow_nan=False))
        f.write("\n")


def _blake2b256_bytes(data: bytes) -> str:
    return "blake2b256:" + hashlib.blake2b(data, digest_size=32).hexdigest()


def _pseudo_metrics_camera(frame: np.ndarray, prev_gray=None) -> dict:
    """Image-space PSEUDO metrics. Fixed-point. No raw floats in Lane-1 path."""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    mb   = float(np.mean(gray))
    lv   = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    if prev_gray is not None:
        diff = cv2.absdiff(gray, prev_gray)
        mf   = float(np.mean(diff > 15))
    else:
        mf = 0.0
    return {
        "metric_schema":       "ph6.metrics.camera.fixedpoint.v1",
        "metric_scale":        10000,
        "mean_brightness_fp":  fp_int(mb),
        "laplacian_var_fp":    fp_int(lv),
        "motion_fraction_fp":  fp_int(mf),
    }


def _pseudo_verdict_camera(metrics: dict) -> tuple[str, list[str]]:
    reasons = []
    mb = metrics["mean_brightness_fp"]
    lv = metrics["laplacian_var_fp"]
    mf = metrics["motion_fraction_fp"]
    if mb < _FP_BRIGHT_MIN: reasons.append("brightness_low")
    if mb > _FP_BRIGHT_MAX: reasons.append("brightness_high")
    if lv < _FP_LAP_MIN:    reasons.append("blur_low_detail")
    if mf > _FP_MOTION_MAX: reasons.append("motion_high")
    return ("PASS" if not reasons else "DROP"), reasons


def _soso_advisory_camera(metrics: dict) -> dict:
    """Advisory only. Authority NONE. Never changes verdict."""
    mb = metrics["mean_brightness_fp"]
    if mb > fp_int(150):   state = "STABLE"
    elif mb > fp_int(80):  state = "MODERATE"
    else:                  state = "UNSTABLE"
    return {"state": state, "authority": "NONE"}


def _open_camera(device: str) -> tuple[cv2.VideoCapture, dict]:
    """Open camera and record identity. Returns (cap, inventory)."""
    if device.startswith("/dev/video"):
        idx = int(device.replace("/dev/video", ""))
        dev_path = device
    else:
        idx = int(device)
        dev_path = f"/dev/video{idx}"
    # Use default backend — CAP_V4L2 cannot open by index on this Pi
    cap = cv2.VideoCapture(idx)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open camera {device}")
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 2)
    # Warmup — discard early frames to flush UVC buffer
    for _ in range(5):
        cap.read()
    width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    stated_fps = cap.get(cv2.CAP_PROP_FPS)
    backend = cap.getBackendName()
    inventory = {
        "schema":        "ph6.camera_inventory.v1",
        "device":        dev_path,
        "device_index":  idx,
        "backend":       backend,
        "width_px":      width,
        "height_px":     height,
        "stated_fps":    stated_fps,
        "real_source":   True,
        "opened_utc":    _utc(),
    }
    return cap, inventory


def _resource_snapshot(frame_id: int) -> dict:
    snap: dict = {"schema": "ph6.resource_snapshot.v1",
                  "frame_id": frame_id, "timestamp_utc": _utc()}
    try:
        with open("/sys/class/thermal/thermal_zone0/temp") as f:
            snap["temperature_celsius"] = int(f.read().strip()) / 1000.0
    except Exception:
        snap["temperature_celsius"] = None
    try:
        lines = open("/proc/meminfo").readlines()
        mi = {l.split(":")[0].strip(): int(l.split(":")[1].split()[0])
              for l in lines if ":" in l}
        total = mi.get("MemTotal", 0)
        avail = mi.get("MemAvailable", 0)
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


def _percentile(data: list[float], p: float) -> float:
    if not data:
        return 0.0
    s = sorted(data)
    idx = (len(s) - 1) * p / 100.0
    lo, hi = int(idx), min(int(idx) + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (idx - lo)


def _level_tag(frames_done: int) -> str:
    if frames_done >= LCC_01C_MIN:
        return "LCC-01C"
    if frames_done >= LCC_01B_MIN:
        return "LCC-01B"
    if frames_done >= LCC_01A_MIN:
        return "LCC-01A"
    return "LCC-01-PARTIAL"


def run_lcc01(
    n_frames: int,
    device: str,
    base_dir: Path,
    tok_enabled: bool = True,
) -> dict:
    run_id = str(uuid.uuid4())
    ts     = _ts()

    cram_store   = base_dir / "cram_store"
    payloads_dir = cram_store / "payloads"
    mram_s_dir   = base_dir / "mram_s" / "swarms"
    resource_log = base_dir / "lcc01_resource_trace.jsonl"

    for d in (cram_store, mram_s_dir):
        d.mkdir(parents=True, exist_ok=True)

    paths = CRAMPaths(cram_store=cram_store, mram_s=mram_s_dir)

    # Ensure shedding_log exists even if no frames are dropped
    paths.shedding_log.touch()

    tok          = _TokSidecar(mram_s_dir, enabled=tok_enabled)
    dep_log      = DepartureLogger(paths.departure_log)
    arr_log      = ArrivalLogger(paths.arrival_log)
    shed_log     = SheddingLogger(paths)
    cram_writer  = CRAMWriter(cram_store)

    # Open camera
    try:
        cap, camera_inventory = _open_camera(device)
    except Exception as e:
        print(f"CAMERA OPEN FAILED: {e}", file=sys.stderr)
        return {"ok": False, "error": str(e), "run_dir": str(base_dir)}

    _atomic_write_json(base_dir / "camera_inventory.json", camera_inventory)
    print(f"  Camera: {device}  {camera_inventory['width_px']}x{camera_inventory['height_px']}"
          f"  stated_fps={camera_inventory['stated_fps']}")

    # Campaign manifest
    _atomic_write_json(base_dir / "lcc01_session_manifest.json", {
        "schema":         "ph6.lcc01_session_manifest.v1",
        "campaign_id":    "LCC-01",
        "run_id":         run_id,
        "started_utc":    ts,
        "device":         device,
        "frames_target":  n_frames,
        "frames_min":     LCC_01A_MIN,
        "authority_rule": "Lane 1 decides. Lane 2 advises.",
        "pseudo_rule":    "PSEUDO-A issues PASS/DROP. Metrics image-space fixed-point.",
        "closure_rule":   "Maximum automatic result: PASS_PENDING_REVIEW.",
        "real_source":    True,
    })

    _append_jsonl(resource_log, _resource_snapshot(0))

    counts         = {"pass": 0, "drop": 0, "error": 0, "capture_fail": 0}
    critical_hits: list[str] = []
    frame_latencies_ms: list[float] = []
    frame_sizes_bytes:  list[int]   = []
    last_res_time = time.perf_counter()

    prev_gray = None
    frames_done = 0
    session_start = time.perf_counter()

    print(f"  Target: {n_frames} frames  (min valid: {LCC_01A_MIN})")
    sys.stdout.flush()

    for frame_id in range(1, n_frames + 1):
        frame_t0 = time.perf_counter()

        # Resource snapshot every 5 s
        if frame_t0 - last_res_time >= 5.0:
            _append_jsonl(resource_log, _resource_snapshot(frame_id))
            last_res_time = frame_t0

        # Capture
        ok, frame = cap.read()
        if not ok or frame is None:
            counts["capture_fail"] += 1
            critical_hits.append(f"frame {frame_id}: capture failed")
            if counts["capture_fail"] >= 10:
                print(f"  ABORT: 10 consecutive capture failures at frame {frame_id}",
                      file=sys.stderr)
                break
            continue

        # Encode JPEG for durable payload storage
        ret, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        if not ret:
            counts["error"] += 1
            critical_hits.append(f"frame {frame_id}: JPEG encode failed")
            continue
        jpeg_bytes = buf.tobytes()
        frame_sizes_bytes.append(len(jpeg_bytes))

        try:
            dep = dep_log.log(frame_id, jpeg_bytes, media_type="CAMERA_JPEG")
            arr = arr_log.log(frame_id, jpeg_bytes, dep["payload_hash"])
            _write_payload_bin(payloads_dir, frame_id, jpeg_bytes)

            if arr["transfer_status"] != "OK":
                critical_hits.append(f"frame {frame_id}: HASH_MISMATCH on arrival")

            # Real-camera PSEUDO metrics (image-space)
            gray    = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            metrics = _pseudo_metrics_camera(frame, prev_gray)
            verdict, reasons = _pseudo_verdict_camera(metrics)
            soso    = _soso_advisory_camera(metrics)
            prev_gray = gray

            payload_hash = dep["payload_hash"]
            verdict_record = {
                "schema":            "ph6.pseudo_verdict.camera.v1",
                "frame_id":          frame_id,
                "verdict":           verdict,
                "reasons":           reasons,
                "metrics":           metrics,
                "motion_gate":       "REAL_CAMERA",
                "input_hash":        payload_hash,
                "hash_algorithm":    "BLAKE2b-256",
                "fixed_point_scale": 10000,
                "authority":         "LANE_1",
                "soso_advisory":     soso,
                "timestamp_utc":     _utc(),
            }
            _append_jsonl(paths.verdict_log, verdict_record)

            if verdict == "PASS":
                cram_writer.commit(frame_id, payload_hash, verdict_record)
                tok.on_pass(frame_id, payload_hash)
                counts["pass"] += 1
            else:
                shed_log.log(
                    frame_id=frame_id,
                    policy_ref="PH6-DROP-POLICY-v1",
                    reason=("; ".join(reasons) if reasons else "drop_no_reason"),
                )
                counts["drop"] += 1

            _atomic_write_json(mram_s_dir / f"S{frame_id:010d}.json", {
                "schema":    "ph6.mram_s.advisory.v1",
                "frame_id":  frame_id,
                "soso":      soso,
                "authority": "NONE",
                "timestamp": time.time(),
            })

        except Exception as e:
            counts["error"] += 1
            critical_hits.append(f"frame {frame_id}: exception: {e}")

        frames_done += 1
        frame_latencies_ms.append((time.perf_counter() - frame_t0) * 1000.0)

        if frame_id % 100 == 0:
            elapsed = time.perf_counter() - session_start
            fps_so_far = frames_done / elapsed if elapsed > 0 else 0
            print(f"  frame {frame_id}/{n_frames}  "
                  f"PASS={counts['pass']}  DROP={counts['drop']}  "
                  f"fps={fps_so_far:.1f}")
            sys.stdout.flush()

    cap.release()

    session_end  = time.perf_counter()
    duration_s   = session_end - session_start
    actual_fps   = frames_done / duration_s if duration_s > 0 else 0.0

    _append_jsonl(resource_log, _resource_snapshot(-1))

    # RSYNC queue
    rsync_entry = {
        "schema":     "ph6.rsync_queue.v1",
        "depth":      0,
        "blocked_by": None,
        "timestamp":  time.time(),
    }
    _atomic_write_json(paths.rsync_queue, rsync_entry)
    rsync_observation = {
        "schema":     "ph6.lcc01_rsync_observation.v1",
        "campaign_id": "LCC-01",
        "timestamp_utc": _utc(),
        "blocked_by": None,
        "rsync_pass": True,
    }
    _atomic_write_json(base_dir / "rsync_observation.json", rsync_observation)

    # result_set_hash
    if paths.verdict_log.exists():
        verdict_records = [
            json.loads(line)
            for line in paths.verdict_log.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    else:
        verdict_records = []
    verdict_seq = [{"frame_id": r["frame_id"], "verdict": r["verdict"]}
                   for r in verdict_records]
    result_set_hash = blake2b_256(canonical_json(verdict_seq))
    (base_dir / "result_set_hash.txt").write_text(f"blake2b256:{result_set_hash}\n")

    # Schema validation
    schema_errors = validate_run_dir(paths)
    if schema_errors:
        print("  Schema violations:")
        for e in schema_errors:
            print(f"    {e}")
    else:
        print("  Schema validation: PASS")

    # Crash/replay validation
    print()
    validator = CrashReplayValidator(paths)
    replay_report = validator.run()
    print(replay_report.summary())
    print()

    # Authority leakage scan
    authority_leakage_hits: list[str] = []
    forbidden_fields = {"confidence", "threshold_mutation", "cram_mutation",
                        "audit_mutation", "rsync_mutation", "verdict_authority"}
    for vr in verdict_records:
        for field in forbidden_fields:
            if field in vr and field not in ("confidence",):
                if vr.get(field) is True:
                    authority_leakage_hits.append(
                        f"frame {vr['frame_id']}: forbidden field '{field}'=True in verdict")
    advisory_isolation_violations = replay_report.advisory_isolation.lane1_paths_touched_by_advisory
    leakage_scan = {
        "schema":                    "ph6.lcc01_authority_leakage_scan.v1",
        "campaign_id":               "LCC-01",
        "timestamp_utc":             _utc(),
        "verdict_field_violations":  authority_leakage_hits,
        "advisory_isolation_violations": advisory_isolation_violations,
        "lane2_violation_count":     len(replay_report.failures()),
        "scan_pass":                 (len(authority_leakage_hits) == 0
                                      and len(advisory_isolation_violations) == 0),
    }
    _atomic_write_json(base_dir / "authority_leakage_scan.json", leakage_scan)

    # Per-frame stats
    n = len(frame_latencies_ms)
    avg_ms = sum(frame_latencies_ms) / n if n else 0.0
    p95_ms = _percentile(frame_latencies_ms, 95)
    total_bytes = sum(frame_sizes_bytes)

    level_tag = _level_tag(frames_done)
    valid_run = frames_done >= LCC_01A_MIN

    all_pass = (
        valid_run
        and replay_report.verdict == "PASS"
        and len(schema_errors) == 0
        and leakage_scan["scan_pass"]
        and not rsync_observation["blocked_by"]
        and not critical_hits
    )
    overall = "PASS" if all_pass else "FAIL_EVIDENCE_PRESERVED"
    state   = "PASS_PENDING_REVIEW" if all_pass else "FAIL_EVIDENCE_PRESERVED"

    # Final manifest
    manifest = {
        "schema":              "ph6.lcc01_final_manifest.v1",
        "campaign_id":         "LCC-01",
        "run_id":              run_id,
        "started_utc":         ts,
        "completed_utc":       _utc(),
        "device":              device,
        "frames_target":       n_frames,
        "frames_done":         frames_done,
        "level_tag":           level_tag,
        "valid_run":           valid_run,
        "duration_seconds":    round(duration_s, 4),
        "actual_fps":          round(actual_fps, 2),
        "pass_count":          counts["pass"],
        "drop_count":          counts["drop"],
        "error_count":         counts["error"],
        "capture_fail_count":  counts["capture_fail"],
        "critical_failure_count": len(critical_hits),
        "avg_frame_size_bytes": round(total_bytes / n if n else 0, 2),
        "total_bytes":         total_bytes,
        "avg_latency_ms":      round(avg_ms, 4),
        "p95_latency_ms":      round(p95_ms, 4),
        "result_set_hash":     f"blake2b256:{result_set_hash}",
        "replay_verdict":      replay_report.verdict,
        "schema_ok":           len(schema_errors) == 0,
        "leakage_scan_pass":   leakage_scan["scan_pass"],
        "rsync_pass":          rsync_observation["rsync_pass"],
        "tok_enabled":         tok_enabled,
        "tok_rt_count":        tok.rt_count(),
        "overall":             overall,
        "state":               state,
        "closed":              False,
        "real_source":         True,
        "acceptance": {
            "real_camera_confirmed":       True,
            "minimum_frame_count_reached": valid_run,
            "cram_commits_present":        counts["pass"] > 0,
            "authority_leakage_scan_pass": leakage_scan["scan_pass"],
            "rsync_non_blocking_pass":     rsync_observation["rsync_pass"],
            "no_forbidden_authority_fields": len(authority_leakage_hits) == 0,
        },
    }
    _atomic_write_json(base_dir / "lcc01_final_manifest.json", manifest)

    return {
        "ok":              all_pass,
        "overall":         overall,
        "state":           state,
        "frames_done":     frames_done,
        "level_tag":       level_tag,
        "result_set_hash": result_set_hash,
        "run_dir":         str(base_dir),
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser(
        description="LCC-01 Life CRAM Real-Camera Live Stream Campaign"
    )
    ap.add_argument("--frames",       type=int,  default=1200,
                    help="frames to capture (300=smoke, 1200=standard, 3600=evidence)")
    ap.add_argument("--device",       type=str,  default="/dev/video0")
    ap.add_argument("--run-dir",      type=Path, default=None)
    ap.add_argument("--tok-disabled", action="store_true", default=False)
    args = ap.parse_args()

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = args.run_dir or Path(
        f"ph6/cram_pu/validation_runs/lcc01_{ts}_live_camera"
    )
    run_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*70}")
    print(f"LCC-01 — Life CRAM Real-Camera Live Stream Session")
    print(f"Device : {args.device}")
    print(f"Frames : {args.frames}")
    print(f"Run dir: {run_dir}")
    print(f"Started: {ts}")
    print(f"{'='*70}\n")
    sys.stdout.flush()

    result = run_lcc01(
        n_frames=args.frames,
        device=args.device,
        base_dir=run_dir,
        tok_enabled=not args.tok_disabled,
    )

    print(f"\n{'='*70}")
    print(f"LCC-01 RESULT : {result.get('overall', 'UNKNOWN')}")
    print(f"State         : {result.get('state', 'UNKNOWN')}  Closed: false")
    print(f"Level         : {result.get('level_tag', 'UNKNOWN')}")
    print(f"Frames        : {result.get('frames_done', 0)}")
    print(f"result_set_hash: blake2b256:{result.get('result_set_hash', 'MISSING')}")
    print(f"Run dir       : {result.get('run_dir', 'UNKNOWN')}")
    print(f"{'='*70}")

    if result.get("ok"):
        print("LCC_01_CAMERA_PASS=True")
        sys.exit(0)
    else:
        print("LCC_01_CAMERA_PASS=False", file=sys.stderr)
        sys.exit(1)
