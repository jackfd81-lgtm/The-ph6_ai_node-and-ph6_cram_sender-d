#!/usr/bin/env python3
"""PH6 Agent 2A -- neutral, non-authority test capture probe driver.

Structural isolation: this file imports nothing from the `ph6` package and
nothing that can reach CRAMWriter, Lane-1 committers, PASS/DROP evaluators,
CRAM-A/CRAM-R writers, or PSEUDO-A mutation paths. It depends only on the
Python standard library and two unmodified external system binaries
(v4l2-ctl, arecord), invoked as subprocesses. It writes only inside the
--out-dir given on the command line.

artifact_class: PH6_TEST_CAPTURE_REFERENCE
authority: NONE
lane: TEST
authoritative_evidence: false
ratification_status: NONE
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

AUTHORITY_BLOCK = {
    "artifact_class": "PH6_TEST_CAPTURE_REFERENCE",
    "authority": "NONE",
    "lane": "TEST",
    "authoritative_evidence": False,
    "ratification_status": "NONE",
}

FRAME_BYTES_YUYV_640x480 = 640 * 480 * 2  # 614400

# Reference acquisition envelope from the 2026-09-17 80-frame Agent 2A probe. This is a
# *startup sanity check default*, not a new PH6 camera specification -- it exists to catch a
# production run whose delivered cadence has drifted or broken, not to assert a device property.
# See fps_resolution_phase1.md for the full analysis. The ms-range below is a startup-tolerance
# envelope, not a machine-readable "fps" value, and is configurable via CLI. The exact reference
# probe fps figure is never hand-typed here -- see recover_reference_probe_effective_fps().
REFERENCE_INTERVAL_MS_RANGE = (80.0, 84.0)
DEFAULT_STARTUP_TOLERANCE_MS = 25.0
DEFAULT_STARTUP_CHECK_FRAMES = 20
DEFAULT_REFERENCE_PROBE_MANIFEST = (
    Path(__file__).resolve().parents[4]
    / "ph6/cram_pu/validation_runs/PH6_CAPTURE_3000_20260917T154028Z_probe_2A/probe_manifest.json"
)

SEQ_RE = re.compile(
    r"cap dqbuf:\s*\d+\s+seq:\s*(?P<seq>\d+)\s+bytesused:\s*(?P<bytesused>\d+)\s+"
    r"ts:\s*(?P<ts>[\d.]+)(?:\s+delta:\s*(?P<delta>[\d.]+)\s*ms)?"
    r"(?:\s+fps:\s*(?P<fps>[\d.]+))?\s+field:\s*(?P<field>\S+)"
    r"\s*\((?P<ts_flags>[^)]*)\)"
)


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def blake2b_hex(data: bytes) -> str:
    return hashlib.blake2b(data, digest_size=32).hexdigest()


def write_frame_atomic(final_path: Path, data: bytes) -> None:
    """temp-write -> flush -> fsync -> atomic rename. A frame must never be visible at
    final_path until it is complete; a crash/exception before os.replace() must leave no
    trace at final_path (only, at worst, an orphaned temp file under .tmp/)."""
    tmp_dir = final_path.parent / ".tmp"
    tmp_dir.mkdir(exist_ok=True)
    tmp_path = tmp_dir / f"{final_path.name}.{os.getpid()}.{time.monotonic_ns()}.tmp"
    with tmp_path.open("wb") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp_path, final_path)
    if not final_path.exists():
        raise RuntimeError(f"atomic replace did not produce final path: {final_path}")


def selftest_atomic_frame_persistence(scratch_dir: Path) -> tuple[str, str]:
    """Hardware-free filesystem self-test of write_frame_atomic(). Classifies:
    VERIFIED_IMPLEMENTED, NOT_IMPLEMENTED, or UNRESOLVED. No camera/audio device is touched."""
    scratch_dir.mkdir(parents=True, exist_ok=True)
    final_path = scratch_dir / "frame_000001.yuv"
    tmp_dir = scratch_dir / ".tmp"
    payload = os.urandom(1024)

    if final_path.exists():
        final_path.unlink()
    try:
        write_frame_atomic(final_path, payload)
    except Exception as e:
        return "NOT_IMPLEMENTED", f"write_frame_atomic raised on the normal success path: {e!r}"
    if not final_path.exists():
        return "NOT_IMPLEMENTED", "final path did not exist after write_frame_atomic"
    if final_path.read_bytes() != payload:
        return "NOT_IMPLEMENTED", "final path content did not match the written payload"
    leftover = list(tmp_dir.glob("*")) if tmp_dir.exists() else []
    if leftover:
        return "UNRESOLVED", f"temp file(s) left behind after a successful write: {leftover}"
    final_path.unlink()

    class _InjectedFailure(Exception):
        pass

    real_fsync = os.fsync

    def _boom_fsync(fd):
        raise _InjectedFailure("simulated failure after write(), before rename")

    os.fsync = _boom_fsync
    try:
        try:
            write_frame_atomic(final_path, payload)
        except _InjectedFailure:
            pass
        if final_path.exists():
            return "NOT_IMPLEMENTED", "final path was created despite a simulated mid-write failure"
    finally:
        os.fsync = real_fsync

    for p in (list(tmp_dir.glob("*")) if tmp_dir.exists() else []):
        p.unlink()
    if tmp_dir.exists():
        try:
            tmp_dir.rmdir()
        except OSError:
            pass

    return "VERIFIED_IMPLEMENTED", (
        "write_frame_atomic() confirmed: (1) a successful write produces exactly the final "
        "path with correct content and no leftover temp file; (2) a fault injected between "
        "write() and the atomic rename never produces a file at the final path."
    )


def recover_reference_probe_effective_fps(manifest_path: Path | None) -> tuple[float | None, str]:
    """Recover the exact previously-computed effective_fps from a preserved Agent 2A probe
    manifest rather than re-encoding a rounded figure from conversational recollection.
    Returns (value_or_None, status) where status is "RECOVERED" or
    "REFERENCE_PROBE_RATE_VALUE_UNRESOLVED"."""
    if manifest_path is None:
        return None, "REFERENCE_PROBE_RATE_VALUE_UNRESOLVED"
    try:
        data = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None, "REFERENCE_PROBE_RATE_VALUE_UNRESOLVED"
    value = data.get("effective_fps")
    if not isinstance(value, (int, float)):
        return None, "REFERENCE_PROBE_RATE_VALUE_UNRESOLVED"
    return float(value), "RECOVERED"


def compute_source_sequence_gaps(driver_frame_meta: list[dict]) -> int:
    seqs = [m["seq"] for m in driver_frame_meta if m.get("seq") is not None]
    gaps = 0
    for a, b in zip(seqs, seqs[1:]):
        if b > a:
            gaps += max(0, b - a - 1)
    return gaps


def verify_persisted_artifact_integrity(frames_dir: Path, frame_records: list[dict]) -> dict:
    """PERSISTED_FRAME_GAPS is a post-write integrity metric, not a camera-drop metric: it
    counts persisted_frame_number values that were recorded as successfully written but whose
    file is now missing, plus any content-hash mismatch. Under correct operation this is 0."""
    expected_numbers = {r["persisted_frame_number"] for r in frame_records}
    frame_re = re.compile(r"frame_(\d{6})\.yuv$")
    found_numbers = set()
    for p in frames_dir.glob("frame_*.yuv"):
        m = frame_re.match(p.name)
        if m:
            found_numbers.add(int(m.group(1)))
    missing = sorted(expected_numbers - found_numbers)
    hash_mismatches = []
    for rec in frame_records:
        fpath = frames_dir.parent / rec["filename"]
        if not fpath.exists():
            continue
        actual_hash = "blake2b256:" + blake2b_hex(fpath.read_bytes())
        if actual_hash != rec["content_hash"]:
            hash_mismatches.append(rec["persisted_frame_number"])
    persisted_frame_gaps = len(missing) + len(hash_mismatches)
    return {
        "persisted_frame_gaps": persisted_frame_gaps,
        "missing_frame_numbers": missing,
        "hash_mismatched_frame_numbers": hash_mismatches,
        "integrity_ok": persisted_frame_gaps == 0,
    }


def read_exact(stream, n: int) -> bytes:
    """Accumulate exactly n bytes from a pipe, or return short bytes at EOF."""
    chunks = []
    remaining = n
    while remaining > 0:
        chunk = stream.read(remaining)
        if not chunk:
            break
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


class EventLog:
    def __init__(self, path: Path):
        self.path = path
        self.records: list[dict] = []

    def emit(self, event_type: str, **fields) -> None:
        rec = {
            "utc": utc_now(),
            "monotonic_ns": time.monotonic_ns(),
            "event_type": event_type,
            **fields,
        }
        self.records.append(rec)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, sort_keys=True, default=str) + "\n")


def check_startup_timing(entries: list[dict], ref_range_ms: tuple[float, float],
                          tolerance_ms: float, skip_first_n_deltas: int = 1) -> tuple[str, str]:
    """Compare observed inter-frame source-timestamp deltas against a reference envelope.

    This never redefines the reference envelope -- it only classifies the current run's
    early behavior as CONSISTENT, DEVIATED, or UNRESOLVED against it.

    skip_first_n_deltas discards the leading frame-to-frame delta(s): the reference probe
    itself showed an anomalously long first delta (~168-268ms vs. a steady-state ~80-84ms),
    consistent with a UVC exposure/AGC settling transient right after STREAMON. Checking that
    transient against the steady-state envelope would produce a false DEVIATED on every run,
    including the reference run it was derived from -- so it is excluded by design, not hidden.
    """
    ts = [e["ts_seconds"] for e in entries if e.get("ts_seconds") is not None]
    if len(ts) < 3:
        return "UNRESOLVED", f"only {len(ts)} timestamped frames available for the startup check"
    deltas_ms = [(b - a) * 1000.0 for a, b in zip(ts, ts[1:])]
    checked = deltas_ms[skip_first_n_deltas:]
    if len(checked) < 2:
        return "UNRESOLVED", f"only {len(checked)} deltas remain after skipping the first {skip_first_n_deltas} (startup transient)"
    lo, hi = ref_range_ms[0] - tolerance_ms, ref_range_ms[1] + tolerance_ms
    bad = [d for d in checked if d < lo or d > hi]
    if bad:
        return "DEVIATED", (f"{len(bad)}/{len(checked)} startup inter-frame deltas (after "
                             f"skipping the first {skip_first_n_deltas} as a known settling "
                             f"transient) fell outside [{lo:.1f}, {hi:.1f}] ms (reference "
                             f"{ref_range_ms} +/-{tolerance_ms}ms); example deltas: {bad[:5]}")
    return "CONSISTENT", (f"all {len(checked)} checked inter-frame deltas (first "
                           f"{skip_first_n_deltas} skipped as a known settling transient) "
                           f"within [{lo:.1f}, {hi:.1f}] ms of the reference envelope")


def run_probe(
    device: str,
    out_dir: Path,
    frame_count: int,
    fps: int,
    audio_device: str,
    audio_rate: int,
    audio_channels: int,
    audio_format: str,
    preroll_s: float,
    postroll_s: float,
    max_duration_s: float,
    startup_check_frames: int = DEFAULT_STARTUP_CHECK_FRAMES,
    startup_tolerance_ms: float = DEFAULT_STARTUP_TOLERANCE_MS,
    reference_interval_ms_range: tuple[float, float] = REFERENCE_INTERVAL_MS_RANGE,
    startup_skip_first_deltas: int = 1,
) -> dict:
    frames_dir = out_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    ev = EventLog(out_dir / "probe_events.jsonl")

    probe_start_monotonic = time.monotonic()
    ev.emit("PROBE_START", device=device, frame_count_target=frame_count, fps=fps,
            max_duration_s=max_duration_s)

    nominal_video_s = frame_count / fps
    audio_duration_s = int(round(preroll_s + nominal_video_s + postroll_s + 3))
    audio_path = out_dir / "audio_probe.wav"
    audio_cmd = [
        "arecord", "-D", audio_device, "-f", audio_format, "-c", str(audio_channels),
        "-r", str(audio_rate), "-d", str(audio_duration_s), str(audio_path),
    ]
    ev.emit("AUDIO_START", cmd=audio_cmd)
    audio_proc = subprocess.Popen(audio_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(preroll_s)
    ev.emit("AUDIO_READY")

    video_cmd = [
        "v4l2-ctl", "-d", device,
        "--set-fmt-video=width=640,height=480,pixelformat=YUYV",
        f"--set-parm={fps}",
        "--stream-mmap=4",
        f"--stream-count={frame_count}",
        "--stream-to=-",
        "--verbose",
    ]
    ev.emit("VIDEO_START", cmd=video_cmd)
    video_proc = subprocess.Popen(video_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   bufsize=0)

    stderr_lines: list[str] = []
    driver_frame_meta_live: list[dict] = []
    meta_lock = threading.Lock()

    def read_stderr():
        for line in iter(video_proc.stderr.readline, b""):
            text = line.decode("utf-8", "replace").rstrip("\n")
            stderr_lines.append(text)
            m = SEQ_RE.search(text)
            if m:
                with meta_lock:
                    driver_frame_meta_live.append({
                        "seq": int(m.group("seq")),
                        "bytesused": int(m.group("bytesused")),
                        "ts_seconds": float(m.group("ts")),
                        "delta_ms": float(m.group("delta")) if m.group("delta") else None,
                        "field": m.group("field"),
                        "ts_flags": m.group("ts_flags"),
                    })

    stderr_thread = threading.Thread(target=read_stderr, daemon=True)
    stderr_thread.start()

    frame_records = []
    persisted = 0
    aborted_reason = None
    startup_check_result = None
    startup_check_reason = None
    startup_checked = False
    audio_health_status = "OK"
    while persisted < frame_count:
        if time.monotonic() - probe_start_monotonic > max_duration_s:
            aborted_reason = "PROBE_MAX_DURATION_EXCEEDED"
            ev.emit("PROBE_ABORT", reason=aborted_reason, persisted=persisted)
            break

        # Amendment 4: live audio health monitoring -- cheap non-blocking check every iteration.
        try:
            audio_rc = audio_proc.poll()
        except Exception as e:
            audio_health_status = "UNRESOLVED"
            aborted_reason = "AUDIO_HEALTH_UNRESOLVED"
            ev.emit("AUDIO_HEALTH_UNRESOLVED", error=str(e), persisted=persisted)
            break
        if audio_rc is not None:
            audio_health_status = "TERMINATED_EARLY"
            aborted_reason = "AUDIO_CAPTURE_FAILURE"
            ev.emit("AUDIO_CAPTURE_FAILURE", returncode=audio_rc, persisted=persisted)
            break

        chunk = read_exact(video_proc.stdout, FRAME_BYTES_YUYV_640x480)
        recv_utc = utc_now()
        recv_mono_ns = time.monotonic_ns()
        if len(chunk) != FRAME_BYTES_YUYV_640x480:
            ev.emit("FRAME_SHORT_READ_OR_EOF", expected=FRAME_BYTES_YUYV_640x480,
                    got=len(chunk), persisted=persisted)
            break

        # Amendment 5: atomic persistence -- persisted_frame_number/frame_records/persisted
        # counter are only touched after write_frame_atomic() succeeds.
        frame_index = persisted + 1
        fname = frames_dir / f"frame_{frame_index:06d}.yuv"
        try:
            write_frame_atomic(fname, chunk)
        except Exception as e:
            ev.emit("FRAME_WRITE_FAILURE", persisted_frame_number=frame_index, error=str(e))
            aborted_reason = "FRAME_PERSISTENCE_FAILURE"
            break
        digest = blake2b_hex(chunk)
        frame_records.append({
            "persisted_frame_number": frame_index,
            "filename": f"frames/{fname.name}",
            "local_recv_utc": recv_utc,
            "local_recv_monotonic_ns": recv_mono_ns,
            "content_hash": "blake2b256:" + digest,
            "file_size": len(chunk),
        })
        ev.emit("FRAME_PERSISTED", persisted_frame_number=frame_index,
                content_hash="blake2b256:" + digest)
        persisted += 1

        if not startup_checked and persisted >= startup_check_frames:
            startup_checked = True
            with meta_lock:
                snapshot = list(driver_frame_meta_live[:startup_check_frames])
            startup_check_result, startup_check_reason = check_startup_timing(
                snapshot, reference_interval_ms_range, startup_tolerance_ms,
                skip_first_n_deltas=startup_skip_first_deltas)
            ev.emit("STARTUP_TIMING_CHECK", result=startup_check_result,
                    reason=startup_check_reason, frames_checked=len(snapshot))
            # Amendment 1: fails closed on both DEVIATED and UNRESOLVED -- there is no
            # warn-and-continue path for an insufficiently characterized startup state.
            if startup_check_result in ("DEVIATED", "UNRESOLVED"):
                aborted_reason = ("STARTUP_TIMING_DEVIATION" if startup_check_result == "DEVIATED"
                                  else "STARTUP_TIMING_UNRESOLVED")
                ev.emit("PROBE_ABORT", reason=aborted_reason, persisted=persisted)
                break

    try:
        video_proc.stdout.close()
    except Exception:
        pass
    try:
        video_proc.wait(timeout=15)
    except subprocess.TimeoutExpired:
        video_proc.kill()
    stderr_thread.join(timeout=5)
    ev.emit("VIDEO_COMPLETE", persisted=persisted, aborted_reason=aborted_reason)

    time.sleep(postroll_s)
    try:
        audio_proc.wait(timeout=audio_duration_s + 15)
    except subprocess.TimeoutExpired:
        audio_proc.kill()
    audio_stderr = audio_proc.stderr.read().decode("utf-8", "replace") if audio_proc.stderr else ""
    ev.emit("AUDIO_STOP", returncode=audio_proc.returncode)

    with meta_lock:
        driver_frame_meta = list(driver_frame_meta_live)

    probe_end_monotonic = time.monotonic()
    ev.emit("PROBE_END", persisted=persisted,
            duration_s=probe_end_monotonic - probe_start_monotonic)

    return {
        "persisted": persisted,
        "target": frame_count,
        "aborted_reason": aborted_reason,
        "frame_records": frame_records,
        "driver_frame_meta": driver_frame_meta,
        "raw_video_stderr": stderr_lines,
        "audio_path": str(audio_path.name),
        "audio_stderr": audio_stderr,
        "audio_cmd": audio_cmd,
        "video_cmd": video_cmd,
        "probe_start_monotonic": probe_start_monotonic,
        "probe_end_monotonic": probe_end_monotonic,
        "actual_probe_duration_s": probe_end_monotonic - probe_start_monotonic,
        "startup_check_result": startup_check_result,
        "startup_check_reason": startup_check_reason,
        "startup_check_frames": startup_check_frames,
        "audio_health_status": audio_health_status,
    }


def classify_sequence_support(driver_frame_meta: list[dict], persisted: int) -> tuple[str, str]:
    if not driver_frame_meta:
        return "UNRESOLVED", "no driver diagnostic lines were parsed from v4l2-ctl stderr"
    seqs = [m["seq"] for m in driver_frame_meta]
    if len(seqs) < max(2, persisted // 2):
        return "UNRESOLVED", f"only {len(seqs)} of {persisted} frames had a parsed seq field"
    strictly_increasing = all(b > a for a, b in zip(seqs, seqs[1:]))
    if strictly_increasing:
        return "VERIFIED_AVAILABLE", "seq field present and strictly increasing across the probe stream"
    return "UNRESOLVED", "seq field present but not strictly increasing (unexpected ordering)"


def classify_timestamp_support(driver_frame_meta: list[dict], persisted: int) -> tuple[str, str, str]:
    if not driver_frame_meta:
        return "UNRESOLVED", "unknown", "no driver diagnostic lines were parsed from v4l2-ctl stderr"
    with_ts = [m for m in driver_frame_meta if m["ts_seconds"] is not None]
    if len(with_ts) < max(2, persisted // 2):
        return "UNRESOLVED", "unknown", f"only {len(with_ts)} of {persisted} frames had a parsed ts field"
    flags_join = " ".join(m["ts_flags"] for m in with_ts if m["ts_flags"])
    if "ts-monotonic" in flags_join:
        provenance = "monotonic (kernel/driver-supplied, ts-src per V4L2_BUF_FLAG_TSTAMP_SRC flags)"
    elif "ts-realtime" in flags_join:
        provenance = "realtime (kernel/driver-supplied)"
    else:
        provenance = "unknown"
    return "VERIFIED_AVAILABLE", provenance, "ts field present with parseable clock-source flags on the observed frames"


def compute_effective_fps(driver_frame_meta: list[dict]) -> tuple[float | None, float | None]:
    """Returns (effective_fps, actual_video_duration_s), both derived from source timestamps.

    actual_video_duration_s = last source timestamp - first source timestamp (NOT probe
    wall-clock duration, which also includes pre-roll/post-roll/process startup).
    """
    ts = [m["ts_seconds"] for m in driver_frame_meta if m.get("ts_seconds") is not None]
    if len(ts) < 2:
        return None, None
    duration = ts[-1] - ts[0]
    if duration <= 0:
        return None, duration
    effective_fps = (len(ts) - 1) / duration
    return effective_fps, duration


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--device", default="/dev/video0")
    ap.add_argument("--out-dir", required=True, type=Path)
    ap.add_argument("--frames", type=int, default=80)
    ap.add_argument("--fps", type=int, default=10, help="requested_fps passed to VIDIOC_S_PARM")
    ap.add_argument("--advertised-fps", type=float, default=10.0,
                    help="fps from VIDIOC_ENUM_FRAMEINTERVALS for the frozen mode (metadata, not measured)")
    ap.add_argument("--negotiated-fps", type=float, default=10.0,
                    help="fps from VIDIOC_G_PARM readback immediately after VIDIOC_S_PARM")
    ap.add_argument("--negotiated-fps-source", default="VIDIOC_G_PARM")
    ap.add_argument("--audio-device", default="hw:1,0")
    ap.add_argument("--audio-rate", type=int, default=48000)
    ap.add_argument("--audio-channels", type=int, default=1)
    ap.add_argument("--audio-format", default="S16_LE")
    ap.add_argument("--preroll-s", type=float, default=1.0)
    ap.add_argument("--postroll-s", type=float, default=1.0)
    ap.add_argument("--max-duration-s", type=float, default=76.0)
    ap.add_argument("--startup-check-frames", type=int, default=DEFAULT_STARTUP_CHECK_FRAMES)
    ap.add_argument("--startup-tolerance-ms", type=float, default=DEFAULT_STARTUP_TOLERANCE_MS)
    ap.add_argument("--startup-skip-first-deltas", type=int, default=1,
                    help="leading inter-frame deltas to exclude as a known settling transient")
    ap.add_argument("--ref-interval-min-ms", type=float, default=REFERENCE_INTERVAL_MS_RANGE[0])
    ap.add_argument("--ref-interval-max-ms", type=float, default=REFERENCE_INTERVAL_MS_RANGE[1])
    ap.add_argument("--reference-probe-manifest", type=Path,
                    default=DEFAULT_REFERENCE_PROBE_MANIFEST,
                    help="preserved Agent 2A probe_manifest.json to recover reference_probe_effective_fps from")
    ap.add_argument("--selftest-atomic-persistence", type=Path, default=None,
                    help="run a hardware-free filesystem self-test of atomic frame persistence and exit")
    args = ap.parse_args()

    if args.selftest_atomic_persistence is not None:
        status, detail = selftest_atomic_frame_persistence(args.selftest_atomic_persistence)
        print(f"ATOMIC_FRAME_PERSISTENCE: {status}")
        print(f"DETAIL: {detail}")
        return 0 if status == "VERIFIED_IMPLEMENTED" else 1

    out_dir: Path = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    result = run_probe(
        device=args.device, out_dir=out_dir, frame_count=args.frames, fps=args.fps,
        audio_device=args.audio_device, audio_rate=args.audio_rate,
        audio_channels=args.audio_channels, audio_format=args.audio_format,
        preroll_s=args.preroll_s, postroll_s=args.postroll_s,
        max_duration_s=args.max_duration_s,
        startup_check_frames=args.startup_check_frames,
        startup_tolerance_ms=args.startup_tolerance_ms,
        reference_interval_ms_range=(args.ref_interval_min_ms, args.ref_interval_max_ms),
        startup_skip_first_deltas=args.startup_skip_first_deltas,
    )

    seq_status, seq_reason = classify_sequence_support(result["driver_frame_meta"], result["persisted"])
    ts_status, ts_provenance, ts_reason = classify_timestamp_support(result["driver_frame_meta"], result["persisted"])
    effective_fps, actual_video_duration = compute_effective_fps(result["driver_frame_meta"])
    rate_enforcement_established = (
        effective_fps is not None
        and abs(effective_fps - args.negotiated_fps) <= 0.5  # within +/-0.5fps of what was negotiated
    )
    reference_probe_effective_fps, reference_probe_fps_status = recover_reference_probe_effective_fps(
        args.reference_probe_manifest)
    source_sequence_gaps = compute_source_sequence_gaps(result["driver_frame_meta"])
    integrity = verify_persisted_artifact_integrity(out_dir / "frames", result["frame_records"])
    audio_failed = result["aborted_reason"] in ("AUDIO_CAPTURE_FAILURE", "AUDIO_HEALTH_UNRESOLVED")
    session_status = "SESSION_INCOMPLETE" if (result["aborted_reason"] is not None) else "SESSION_COMPLETE_CANDIDATE"

    manifest = {
        **AUTHORITY_BLOCK,
        "probe_status": "PROBED",
        "device": args.device,
        "audio_device": args.audio_device,
        "frames_target": args.frames,
        "frames_persisted": result["persisted"],
        "aborted_reason": result["aborted_reason"],
        "probe_max_duration_s": args.max_duration_s,
        "actual_probe_duration_s": result["actual_probe_duration_s"],
        "time_bound_exceeded": result["aborted_reason"] == "PROBE_MAX_DURATION_EXCEEDED",
        "source_sequence_support": seq_status,
        "source_sequence_reason": seq_reason,
        "source_timestamp_support": ts_status,
        "source_timestamp_provenance": ts_provenance,
        "source_timestamp_reason": ts_reason,
        "requested_fps": args.fps,
        "advertised_fps": args.advertised_fps,
        "negotiated_fps": args.negotiated_fps,
        "negotiated_fps_source": args.negotiated_fps_source,
        "rate_enforcement_established": rate_enforcement_established,
        "source_timestamp_available": ts_status == "VERIFIED_AVAILABLE",
        "source_timestamp_type": "ts-src-soe (start-of-exposure)",
        "source_timestamp_clock": ts_provenance,
        "reference_probe_effective_fps": reference_probe_effective_fps,
        "reference_probe_effective_fps_basis": "source_timestamp_deltas",
        "reference_probe_effective_fps_role": "reference_observation_not_camera_specification",
        "reference_probe_effective_fps_status": reference_probe_fps_status,
        "effective_fps": effective_fps,
        "effective_fps_basis": "source_timestamp_deltas (this run)",
        "actual_video_duration": actual_video_duration,
        "actual_video_duration_basis": "first_to_last_source_timestamp (this run)",
        "control_plane_data_plane_rate_divergence": (
            effective_fps is not None and abs(effective_fps - args.negotiated_fps) > 0.5
        ),
        "root_cause": "UNRESOLVED",
        "startup_timing_check": {
            "result": result["startup_check_result"],
            "reason": result["startup_check_reason"],
            "frames_checked": result["startup_check_frames"],
            "reference_interval_ms_range": [args.ref_interval_min_ms, args.ref_interval_max_ms],
            "tolerance_ms": args.startup_tolerance_ms,
        },
        "startup_timing_unresolved_policy": "ABORT",
        "source_sequence_gaps": source_sequence_gaps,
        "persisted_frame_gaps": integrity["persisted_frame_gaps"],
        "persisted_frame_gap_semantics": "POST_WRITE_ARTIFACT_INTEGRITY_FAILURE",
        "persisted_artifact_integrity_ok": integrity["integrity_ok"],
        "persisted_artifact_integrity_detail": {
            "missing_frame_numbers": integrity["missing_frame_numbers"],
            "hash_mismatched_frame_numbers": integrity["hash_mismatched_frame_numbers"],
        },
        "audio_live_monitoring": True,
        "audio_failure_policy": "ABORT_VIDEO_AND_PRESERVE_PARTIAL_SESSION",
        "audio_unresolved_policy": "ABORT",
        "audio_health_status": result["audio_health_status"],
        "audio_failure_during_run": audio_failed,
        "atomic_frame_persistence": True,
        "atomic_frame_persistence_method": "tmp-write + flush + fsync + os.replace (atomic rename)",
        "session_status": session_status,
        "video_cmd": result["video_cmd"],
        "audio_cmd": result["audio_cmd"],
        "artifact_inventory": [
            {"path": "probe_events.jsonl", "kind": "event_log", **AUTHORITY_BLOCK},
            {"path": "video_stderr_raw.log", "kind": "diagnostic_output", **AUTHORITY_BLOCK},
            {"path": "audio_probe.wav", "kind": "pcm_audio_sample", **AUTHORITY_BLOCK},
            {"path": "driver_frame_meta.json", "kind": "v4l2_metadata_dump", **AUTHORITY_BLOCK},
            {"path": "probe_manifest.json", "kind": "manifest", **AUTHORITY_BLOCK},
        ] + [
            {"path": fr["filename"], "kind": "raw_frame_sample",
             "content_hash": fr["content_hash"], **AUTHORITY_BLOCK}
            for fr in result["frame_records"]
        ],
        "frame_records": result["frame_records"],
    }

    (out_dir / "driver_frame_meta.json").write_text(
        json.dumps(result["driver_frame_meta"], indent=2), encoding="utf-8")
    (out_dir / "video_stderr_raw.log").write_text(
        "\n".join(result["raw_video_stderr"]), encoding="utf-8")
    (out_dir / "probe_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True, default=str), encoding="utf-8")

    print(f"PROBE_STATUS: PROBED")
    print(f"FRAMES_PERSISTED: {result['persisted']} / {args.frames}")
    print(f"ABORTED_REASON: {result['aborted_reason']}")
    print(f"ACTUAL_PROBE_DURATION_S: {result['actual_probe_duration_s']:.2f}")
    print(f"TIME_BOUND_EXCEEDED: {manifest['time_bound_exceeded']}")
    print(f"STARTUP_TIMING_CHECK: {result['startup_check_result']} ({result['startup_check_reason']})")
    print(f"SOURCE_SEQUENCE_SUPPORT: {seq_status} ({seq_reason})")
    print(f"SOURCE_TIMESTAMP_SUPPORT: {ts_status} provenance={ts_provenance} ({ts_reason})")
    print(f"NEGOTIATED_FPS: {args.negotiated_fps} (source={args.negotiated_fps_source})")
    print(f"EFFECTIVE_FPS: {effective_fps} (basis=source_timestamp_deltas, this run)")
    print(f"REFERENCE_PROBE_EFFECTIVE_FPS: {reference_probe_effective_fps} ({reference_probe_fps_status})")
    print(f"ACTUAL_VIDEO_DURATION_S: {actual_video_duration}")
    print(f"CONTROL_PLANE_DATA_PLANE_RATE_DIVERGENCE: {manifest['control_plane_data_plane_rate_divergence']}")
    print(f"SOURCE_SEQUENCE_GAPS: {source_sequence_gaps}")
    print(f"PERSISTED_FRAME_GAPS: {integrity['persisted_frame_gaps']} (semantics=POST_WRITE_ARTIFACT_INTEGRITY_FAILURE)")
    print(f"AUDIO_HEALTH_STATUS: {result['audio_health_status']}")
    print(f"ATOMIC_FRAME_PERSISTENCE: true (tmp-write+fsync+os.replace)")
    print(f"SESSION_STATUS: {session_status}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
