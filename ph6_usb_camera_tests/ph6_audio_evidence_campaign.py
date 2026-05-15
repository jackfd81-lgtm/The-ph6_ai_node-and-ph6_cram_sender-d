"""
PH6 USB Audio Evidence Campaign — schema ph6.usb_audio_test.v1
3-minute (or configurable) run capturing per-second chunks with RMS/peak/hash.
Mirrors C01 camera test structure.
"""
import subprocess, time, wave, array, math, json, hashlib, os, sys, io
from datetime import datetime, timezone

DURATION_SEC = int(sys.argv[1]) if len(sys.argv) > 1 else 180
RATE         = 44100
CHANNELS     = 1
FORMAT       = "S16_LE"
ALSA_DEVICE  = "hw:2,0"
CHUNK_SEC    = 1          # one "frame" = 1 second of audio

run_id  = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
out_dir = f"audio_test_{run_id}"
os.makedirs(out_dir, exist_ok=True)

SAVE_AT = {0, DURATION_SEC//6, DURATION_SEC//3, DURATION_SEC//2,
           2*DURATION_SEC//3, 5*DURATION_SEC//6, DURATION_SEC-1}

print(f"--- PH6 AUDIO EVIDENCE CAMPAIGN: {DURATION_SEC}s @ {RATE}Hz mono ---")
print(f"run_id={run_id}  out_dir={out_dir}")

wav_path = os.path.join(out_dir, "raw_capture.wav")
t_start  = time.time()

proc = subprocess.Popen(
    ["arecord", "-D", ALSA_DEVICE,
     "--duration", str(DURATION_SEC),
     "-f", FORMAT, "-r", str(RATE), "-c", str(CHANNELS),
     "--buffer-size=65536", "--period-size=16384",
     wav_path],
    stderr=subprocess.PIPE
)
proc.wait()
t_end = time.time()

stderr_out = proc.stderr.read().decode(errors="replace")
overrun_count = stderr_out.count("overrun!!!")

print(f"arecord exited rc={proc.returncode}  overruns={overrun_count}")

# --- Analyse per-second chunks ---
with wave.open(wav_path, "r") as wf:
    total_frames = wf.getnframes()
    rate         = wf.getframerate()

chunk_samples = rate * CHUNK_SEC
chunk_records = []

with wave.open(wav_path, "r") as wf:
    for idx in range(DURATION_SEC):
        raw = wf.readframes(chunk_samples)
        if len(raw) < chunk_samples * 2:          # 2 bytes per S16 sample
            chunk_records.append({
                "chunk_index": idx,
                "status": "DROP",
                "reason": "short_read",
                "timestamp_utc": datetime.now(timezone.utc).isoformat()
            })
            continue

        samples = array.array("h", raw)
        rms  = math.sqrt(sum(s*s for s in samples) / len(samples))
        peak = max(abs(s) for s in samples)
        chunk_hash = hashlib.blake2b(raw, digest_size=32).hexdigest()

        if idx in SAVE_AT:
            clip_path = os.path.join(out_dir, f"chunk_{idx:04d}.wav")
            with wave.open(clip_path, "w") as cw:
                cw.setnchannels(CHANNELS)
                cw.setsampwidth(2)
                cw.setframerate(RATE)
                cw.writeframes(raw)

        chunk_records.append({
            "chunk_index": idx,
            "status":      "PASS",
            "rms":         round(rms, 2),
            "peak":        peak,
            "chunk_hash_blake2b_256": chunk_hash,
            "timestamp_utc": datetime.now(timezone.utc).isoformat()
        })

passed  = sum(1 for r in chunk_records if r["status"] == "PASS")
dropped = sum(1 for r in chunk_records if r["status"] == "DROP")
rms_vals = [r["rms"] for r in chunk_records if r["status"] == "PASS"]
avg_rms  = round(sum(rms_vals)/len(rms_vals), 2) if rms_vals else 0
peak_all = max((r["peak"] for r in chunk_records if r["status"] == "PASS"), default=0)
silent   = sum(1 for r in chunk_records if r["status"] == "PASS" and r["rms"] < 50)

result = {
    "schema":           "ph6.usb_audio_test.v1",
    "run_id":           run_id,
    "alsa_device":      ALSA_DEVICE,
    "rate_hz":          RATE,
    "channels":         CHANNELS,
    "format":           FORMAT,
    "duration_sec":     DURATION_SEC,
    "chunk_sec":        CHUNK_SEC,
    "target_chunks":    DURATION_SEC,
    "passed_chunks":    passed,
    "dropped_chunks":   dropped,
    "silent_chunks":    silent,
    "avg_rms":          avg_rms,
    "peak_all":         peak_all,
    "overrun_count":    overrun_count,
    "actual_duration":  round(t_end - t_start, 3),
    "arecord_rc":       proc.returncode,
    "valid_ph6_minimum": DURATION_SEC >= 180,
    "test_result":      "PASS" if passed == DURATION_SEC and dropped == 0 else "REVIEW",
    "records":          chunk_records
}

report_path = os.path.join(out_dir, "audio_test_report.json")
with open(report_path, "w") as f:
    json.dump(result, f, indent=2)

summary = {k: v for k, v in result.items() if k != "records"}
print(json.dumps(summary, indent=2))
