"""
PH6 Audio+Video Simultaneous Contention Test — schema ph6.usb_av_contention_test.v1
Runs arecord + OpenCV camera capture in parallel threads for GAP-16 characterisation.
"""
import subprocess, threading, time, wave, array, math, json, hashlib, os, sys, cv2
from datetime import datetime, timezone

DURATION_SEC = int(sys.argv[1]) if len(sys.argv) > 1 else 60
RATE         = 44100
ALSA_DEVICE  = "hw:2,0"
CAM_INDEX    = 1
WIDTH, HEIGHT = 640, 480

run_id  = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
out_dir = f"av_contention_{run_id}"
os.makedirs(out_dir, exist_ok=True)

print(f"--- PH6 AV CONTENTION TEST: {DURATION_SEC}s audio+video simultaneous ---")
print(f"run_id={run_id}")

audio_path = os.path.join(out_dir, "audio_capture.wav")
audio_result = {}
video_records = []
audio_overruns = [0]

def run_audio():
    proc = subprocess.Popen(
        ["arecord", "-D", ALSA_DEVICE,
         "--duration", str(DURATION_SEC),
         "-f", "S16_LE", "-r", str(RATE), "-c", "1",
         "--buffer-size=65536", "--period-size=16384",
         audio_path],
        stderr=subprocess.PIPE
    )
    proc.wait()
    stderr = proc.stderr.read().decode(errors="replace")
    audio_overruns[0] = stderr.count("overrun!!!")
    audio_result["rc"] = proc.returncode
    audio_result["overruns"] = audio_overruns[0]

audio_thread = threading.Thread(target=run_audio, daemon=True)

cap = cv2.VideoCapture(CAM_INDEX)
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)
cap.set(cv2.CAP_PROP_FPS, 30)

if not cap.isOpened():
    print("FAIL: camera not opened")
    sys.exit(1)

for _ in range(5):
    cap.read()

# start both simultaneously
t_start = time.time()
audio_thread.start()

consecutive_failures = 0
DISCONNECT_THRESHOLD = 30
camera_disconnect_at = None

while (time.time() - t_start) < DURATION_SEC:
    t0 = time.time()
    ok, frame = cap.read()
    t1 = time.time()
    idx = len(video_records)

    if not ok or frame is None:
        consecutive_failures += 1
        video_records.append({
            "frame_index": idx,
            "status": "DROP",
            "elapsed_sec": round(t1 - t_start, 3),
            "timestamp_utc": datetime.now(timezone.utc).isoformat()
        })
        if consecutive_failures >= DISCONNECT_THRESHOLD:
            camera_disconnect_at = round(t1 - t_start, 3)
            print(f"CAMERA_DISCONNECT detected at {camera_disconnect_at}s — stopping video loop")
            break
        time.sleep(0.01)
        continue

    consecutive_failures = 0
    frame_hash = hashlib.blake2b(frame.tobytes(), digest_size=32).hexdigest()
    video_records.append({
        "frame_index": idx,
        "status": "PASS",
        "capture_ms": round((t1 - t0) * 1000, 3),
        "elapsed_sec": round(t1 - t_start, 3),
        "frame_hash_blake2b_256": frame_hash,
        "timestamp_utc": datetime.now(timezone.utc).isoformat()
    })

t_end = time.time()
cap.release()
audio_thread.join(timeout=DURATION_SEC + 10)

# analyse audio
audio_stats = {}
if os.path.exists(audio_path):
    try:
        with wave.open(audio_path, "r") as wf:
            raw = wf.readframes(wf.getnframes())
        s = array.array("h", raw)
        rms  = math.sqrt(sum(x*x for x in s)/len(s))
        peak = max(abs(x) for x in s)
        audio_stats = {"rms": round(rms,2), "peak": peak, "captured": True}
    except Exception as e:
        audio_stats = {"captured": False, "error": str(e)}
else:
    audio_stats = {"captured": False, "error": "file_missing"}

v_pass   = sum(1 for r in video_records if r["status"] == "PASS")
v_drop   = sum(1 for r in video_records if r["status"] == "DROP")
duration = t_end - t_start
fps_act  = v_pass / duration if duration > 0 else 0

result = {
    "schema":            "ph6.usb_av_contention_test.v1",
    "run_id":            run_id,
    "gap_reference":     "GAP-16",
    "duration_sec":      DURATION_SEC,
    "actual_duration":   round(duration, 3),
    "video": {
        "camera_index":   CAM_INDEX,
        "resolution":     f"{WIDTH}x{HEIGHT}",
        "passed_frames":  v_pass,
        "dropped_frames": v_drop,
        "actual_fps":     round(fps_act, 3),
        "drop_rate_pct":  round(100 * v_drop / max(v_pass + v_drop, 1), 2)
    },
    "audio": {
        "alsa_device":   ALSA_DEVICE,
        "rate_hz":       RATE,
        "overrun_count": audio_result.get("overruns", -1),
        "arecord_rc":    audio_result.get("rc", -1),
        **audio_stats
    },
    "camera_disconnect_at_sec": camera_disconnect_at,
    "contention_verdict": None,   # filled below
    "video_records": video_records
}

# verdict heuristic
v_drops_ok  = v_drop == 0
a_overruns  = audio_result.get("overruns", 999)
a_ok        = audio_stats.get("captured", False) and audio_stats.get("rms", 0) > 50
fps_ok      = fps_act > 25

if v_drops_ok and a_overruns == 0 and a_ok and fps_ok:
    verdict = "PASS — no contention detected"
elif not a_ok and not v_drops_ok:
    verdict = "FAIL — both streams degraded"
elif not a_ok or a_overruns > 10:
    verdict = "AUDIO_DEGRADED — audio affected, video OK"
elif not v_drops_ok or not fps_ok:
    verdict = "VIDEO_DEGRADED — video affected, audio OK"
else:
    verdict = "MARGINAL — minor artefacts on one or both streams"

result["contention_verdict"] = verdict

report_path = os.path.join(out_dir, "av_contention_report.json")
with open(report_path, "w") as f:
    json.dump(result, f, indent=2)

summary = {k: v for k, v in result.items() if k != "video_records"}
print(json.dumps(summary, indent=2))
