#!/usr/bin/env python3
"""Bounded real camera + audio observation using the existing LCC-01 runner.

Audio is CRAM-0 MEASURED evidence only.  A ratified audio verdict policy is
required before it can reach CRAM-A/CRAM-R or mint an RT.
"""
from __future__ import annotations
import argparse, json, subprocess, sys, time, uuid
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent.parent
sys.path.insert(0, str(ROOT))
from ph6.cram_pu.multimodal import normalize_wav, write_audio_intake, correlate, soso_input, write_correlation
from ph6.cram_pu.tools.life_cram_lcc_01_live_camera import run_lcc01

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument('--device', default='/dev/video0'); p.add_argument('--alsa-device', required=True)
    p.add_argument('--frames', type=int, default=60); p.add_argument('--audio-seconds', type=int, default=5)
    p.add_argument('--run-dir', type=Path, required=True); args = p.parse_args()
    run, wav = args.run_dir, args.run_dir / 'audio_capture.wav'; run.mkdir(parents=True, exist_ok=True)
    start = time.time_ns()
    proc = subprocess.Popen(['arecord', '-D', args.alsa_device, '-f', 'S16_LE', '-r', '44100', '-c', '1', '--duration', str(args.audio_seconds), str(wav)], stderr=subprocess.PIPE)
    camera = run_lcc01(args.frames, args.device, run)
    _, stderr = proc.communicate(); end = time.time_ns()
    if proc.returncode != 0 or not wav.exists():
        print('AUDIO CAPTURE FAILED:', stderr.decode(errors='replace'), file=sys.stderr); return 1
    audio = write_audio_intake(run / 'cram_store', wav, normalize_wav(wav, audio_event_id='audio_' + uuid.uuid4().hex[:16], sensor_id=args.alsa_device, capture_start_ns=start, capture_end_ns=end, alsa_overrun_count=stderr.count(b'overrun!!!')))
    records = [json.loads(x) for x in (run/'cram_store/verdict_log.jsonl').read_text().splitlines() if x]
    linked = 0
    for v in records:
        commit = run/'cram_store'/f"cram_{v['frame_id']:010d}.json"
        if not commit.exists() or 'capture_timestamp_ns' not in v: continue
        c = json.loads(commit.read_text())
        link = correlate(session_id=run.name, camera_event_id=f"frame_{v['frame_id']:010d}", camera_evidence_hash=c['cram_hash'], camera_capture_ns=v['capture_timestamp_ns'], audio_record=audio)
        write_correlation(run/'mram_s'/'swarms', link, soso_input(link, v['metrics'], audio)); linked += 1
    print(json.dumps({'camera_result': camera, 'audio_evidence_id': audio['evidence_id'], 'audio_verdict': audio['verdict_status'], 'correlations': linked, 'soso': 'INPUT_WRITTEN_NOT_CONNECTED_TO_EXECUTABLE_SOSO', 'audio_rt': 'NOT_CREATED_NO_AUDIO_PASS_POLICY'}, sort_keys=True))
    return 0
if __name__ == '__main__': raise SystemExit(main())
