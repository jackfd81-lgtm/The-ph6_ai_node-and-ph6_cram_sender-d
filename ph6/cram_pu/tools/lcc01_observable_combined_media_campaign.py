#!/usr/bin/env python3
"""Observable 3,000-frame video + synchronized audio campaign.

Pure orchestration/reporting wrapper around the EXISTING, UNMODIFIED
ph6/cram_pu/tools/lcc01_live_multimodal.py (itself a thin wrapper around the
existing run_lcc01 video capture and arecord audio capture). This script
adds no new CRAM/MRAM-S write path of its own: it launches the existing
tool as a subprocess and only *reads back* the run directory it produces
(verdict_log.jsonl, cram_store/, mram_s/) to render live progress and a
final evidence report. No Lane-1 or Lane-2 code is modified.

Live progress is rendered by polling the real verdict_log.jsonl as it grows
during capture -- the same permanent, machine-readable per-frame record the
final report is built from, not a separate/parallel bookkeeping mechanism.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent.parent
sys.path.insert(0, str(ROOT))

_PRINT_LOCK = threading.Lock()


def _tail_progress(run_dir: Path, target: int, stop_event: threading.Event) -> None:
    verdict_log = run_dir / "cram_store" / "verdict_log.jsonl"
    last_count = -1
    t0 = time.time()
    while not stop_event.is_set():
        time.sleep(0.5)
        if not verdict_log.exists():
            continue
        try:
            lines = [l for l in verdict_log.read_text().splitlines() if l.strip()]
        except Exception:
            continue
        count = len(lines)
        if count == last_count:
            continue
        last_count = count
        passes = 0
        for l in lines:
            try:
                if json.loads(l).get("verdict") == "PASS":
                    passes += 1
            except Exception:
                pass
        drops = count - passes
        elapsed = time.time() - t0
        fps = count / elapsed if elapsed > 0 else 0.0
        eta = (target - count) / fps if fps > 0 else float("inf")
        with _PRINT_LOCK:
            sys.stdout.write(
                f"\rFRAME {count:5d} / {target}   PASS={passes:5d}  DROP={drops:5d}  "
                f"fps={fps:5.1f}  elapsed={elapsed:6.1f}s  eta={eta:6.1f}s   "
            )
            sys.stdout.flush()
        if count >= target:
            break
    with _PRINT_LOCK:
        sys.stdout.write("\n")
        sys.stdout.flush()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--frames", type=int, default=3000)
    ap.add_argument("--device", default="/dev/video0")
    ap.add_argument("--alsa-device", default="plughw:CARD=Device,DEV=0")
    ap.add_argument("--audio-seconds", type=int, default=None)
    ap.add_argument("--run-dir", type=Path, default=None)
    args = ap.parse_args()

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = args.run_dir or (
        ROOT / "ph6/cram_pu/validation_runs" / f"lcc01_{ts}_observable_3000frame_multimodal"
    )
    run_dir.parent.mkdir(parents=True, exist_ok=True)

    est_fps = 12.3  # observed this session; used only to size the audio recording window
    audio_seconds = args.audio_seconds or (int(args.frames / est_fps) + 20)

    print("=" * 70)
    print("PH6 COMBINED MEDIA TEST")
    print("=" * 70)
    print(f"Video device: {args.device}")
    print(f"Audio device: {args.alsa_device}")
    print(f"Target frames: {args.frames}")
    print(f"Audio recording window: {audio_seconds}s")
    print(f"Run dir: {run_dir}")
    print("=" * 70)
    print(f"FRAME     0 / {args.frames}   [START]")
    sys.stdout.flush()

    tool = HERE / "lcc01_live_multimodal.py"
    cmd = [
        sys.executable, str(tool),
        "--device", args.device,
        "--alsa-device", args.alsa_device,
        "--frames", str(args.frames),
        "--audio-seconds", str(audio_seconds),
        "--run-dir", str(run_dir),
    ]

    stop_event = threading.Event()
    poller = threading.Thread(target=_tail_progress, args=(run_dir, args.frames, stop_event), daemon=True)
    poller.start()

    t_start = time.time()
    proc = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
    t_end = time.time()
    stop_event.set()
    poller.join(timeout=2.0)

    if proc.returncode != 0:
        print("\nCOMBINED CAPTURE FAILED")
        print("stdout (tail):", proc.stdout[-4000:])
        print("stderr (tail):", proc.stderr[-4000:])
        return 1

    tool_result = json.loads(proc.stdout.strip().splitlines()[-1])

    from ph6.cram_pu.crash_replay import CRAMPaths, CrashReplayValidator

    verdict_log = run_dir / "cram_store" / "verdict_log.jsonl"
    records = [json.loads(l) for l in verdict_log.read_text().splitlines() if l.strip()]
    pass_count = sum(1 for r in records if r["verdict"] == "PASS")
    drop_count = len(records) - pass_count

    cram_paths = CRAMPaths(cram_store=run_dir / "cram_store", mram_s=run_dir / "mram_s" / "swarms")
    replay = CrashReplayValidator(cram_paths).run()

    audio_wav = run_dir / "audio_capture.wav"
    audio_size = audio_wav.stat().st_size if audio_wav.exists() else 0
    audio_hash = (
        hashlib.blake2b(audio_wav.read_bytes(), digest_size=32).hexdigest()
        if audio_wav.exists() else None
    )

    correlations_dir = run_dir / "mram_s" / "swarms" / "correlations"
    correlation_count = len(list(correlations_dir.glob("*.json"))) if correlations_dir.exists() else 0

    print("\n" + "=" * 70)
    print("PH6 COMBINED MEDIA TEST COMPLETE")
    print("=" * 70)

    print("\nVIDEO\n-----")
    print(f"attempted: {args.frames}")
    print(f"captured:  {len(records)}")
    print(f"PASS:      {pass_count}")
    print(f"DROP:      {drop_count}")

    print("\nAUDIO\n-----")
    print(f"file: {audio_wav.name if audio_wav.exists() else 'MISSING'}")
    print(f"bytes captured: {audio_size}")
    print(f"audio hash (blake2b-256): {audio_hash}")
    print(f"audio verdict/status: {tool_result.get('audio_verdict')}")
    print("audio CRAM-A status: NOT_PROMOTED_TO_CRAM_A -- no ratified audio verdict policy (documented, not a defect)")

    print("\nCRAM\n----")
    print(f"CRAM-A/CRAM-R records: {len(records)}")
    print(f"chain continuity: {'PASS' if replay.continuity.ok else 'FAIL'}")
    print(f"hash verification: {'PASS' if replay.cram_integrity.ok else 'FAIL'}")
    print(f"replay verdict: {replay.verdict}")

    print("\nLANE 2\n------")
    print(f"camera-audio correlations written: {correlation_count}")
    print(f"SoSo status: {tool_result.get('soso')}")
    print(f"audio RT status: {tool_result.get('audio_rt')}")

    video_errors = args.frames - len(records)
    audio_errors = 0 if audio_wav.exists() else 1
    overall_ok = replay.verdict == "PASS" and len(records) == args.frames and audio_wav.exists()

    print("\nFINAL\n-----")
    print(f"{len(records)}/{args.frames} frames")
    print(f"video errors: {video_errors}")
    print(f"audio errors: {audio_errors}")
    print(f"CRAM integrity: {'PASS' if replay.verdict == 'PASS' else 'FAIL'}")
    print("Lane-1 authority: unchanged (no Lane-1 code modified by this campaign)")
    print("Lane-2 authority: ZERO (advisory-only correlation records; no PASS/DROP capability exercised or added)")
    print(f"\nRun dir: {run_dir.relative_to(ROOT)}")
    print(f"Total wall time: {t_end - t_start:.1f}s")

    report = {
        "schema": "ph6.observable_combined_media_report.v1",
        "run_dir": str(run_dir.relative_to(ROOT)),
        "video": {"attempted": args.frames, "captured": len(records), "pass": pass_count, "drop": drop_count},
        "audio": {
            "bytes": audio_size,
            "hash_blake2b256": audio_hash,
            "status": tool_result.get("audio_verdict"),
            "cram_a_status": "NOT_PROMOTED_TO_CRAM_A -- no ratified audio verdict policy",
        },
        "cram": {
            "continuity_ok": replay.continuity.ok,
            "cram_integrity_ok": replay.cram_integrity.ok,
            "replay_verdict": replay.verdict,
        },
        "lane2": {
            "correlations": correlation_count,
            "soso": tool_result.get("soso"),
            "audio_rt": tool_result.get("audio_rt"),
        },
        "wall_time_seconds": round(t_end - t_start, 2),
        "overall_ok": overall_ok,
    }
    (run_dir / "observable_combined_media_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n"
    )

    return 0 if overall_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
