#!/usr/bin/env python3
"""
C01-GAP16-R2: 600-frame simultaneous AV confirmation run.
GAP-16 stability classification: STABLE-CONFIRMED vs split GAP-16A/16B.
"""
import subprocess, threading, time, wave, array, math, json, hashlib, os, sys, cv2
from datetime import datetime, timezone

TARGET_FRAMES = int(sys.argv[1]) if len(sys.argv) > 1 else 600
RATE          = 44100
ALSA_DEVICE   = "hw:2,0"
CAM_INDEX     = 1
WIDTH, HEIGHT = 640, 480

run_id  = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
out_dir = f"gap16_r2_{run_id}"
os.makedirs(out_dir, exist_ok=True)

def read_temp_c():
    try:
        raw = open("/sys/class/thermal/thermal_zone0/temp").read().strip()
        return round(int(raw) / 1000.0, 1)
    except Exception:
        return None

def usb_path(vid_pid="0c45:636b"):
    try:
        out = subprocess.check_output(["lsusb"], text=True)
        for line in out.splitlines():
            if vid_pid in line:
                return line.strip()
        return "not_found"
    except Exception:
        return "error"

print(f"--- C01-GAP16-R2: {TARGET_FRAMES} frames, simultaneous AV ---")
print(f"run_id={run_id}  out={out_dir}")

audio_path   = os.path.join(out_dir, "audio_capture.wav")
audio_result = {}

def run_audio(duration_sec):
    proc = subprocess.Popen(
        ["arecord", "-D", ALSA_DEVICE,
         "--duration", str(int(duration_sec) + 5),
         "-f", "S16_LE", "-r", str(RATE), "-c", "1",
         "--buffer-size=65536", "--period-size=16384",
         audio_path],
        stderr=subprocess.PIPE
    )
    proc.wait()
    stderr = proc.stderr.read().decode(errors="replace")
    audio_result["rc"]       = proc.returncode
    audio_result["overruns"] = stderr.count("overrun!!!")

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

temp_start    = read_temp_c()
usb_dev_path  = usb_path()
t_start       = time.time()

# start audio thread with generous cap; will be killed after video finishes
audio_thread = threading.Thread(target=run_audio, args=(TARGET_FRAMES / 20 + 30,), daemon=True)
audio_thread.start()

video_records    = []
consecutive_fail = 0
DISCONNECT_THRESH = 30
disconnect_at    = None
temp_mid         = None

for idx in range(TARGET_FRAMES):
    t0    = time.time()
    ok, f = cap.read()
    t1    = time.time()

    if not ok or f is None:
        consecutive_fail += 1
        video_records.append({
            "frame_index": idx,
            "status":      "DROP",
            "elapsed_sec": round(t1 - t_start, 3),
        })
        if consecutive_fail >= DISCONNECT_THRESH:
            disconnect_at = round(t1 - t_start, 3)
            print(f"CAMERA_DISCONNECT at {disconnect_at}s — stopping")
            break
        time.sleep(0.01)
        continue

    consecutive_fail = 0
    fh = hashlib.blake2b(f.tobytes(), digest_size=32).hexdigest()
    video_records.append({
        "frame_index": idx,
        "status":      "PASS",
        "capture_ms":  round((t1 - t0) * 1000, 3),
        "elapsed_sec": round(t1 - t_start, 3),
        "frame_hash_blake2b_256": fh,
    })

    if idx == TARGET_FRAMES // 2:
        temp_mid = read_temp_c()

    if idx % 100 == 0:
        print(f"  frame {idx:04d}  elapsed={t1-t_start:.1f}s  temp={read_temp_c()}°C")

t_end = time.time()
cap.release()

# kill arecord after video done
subprocess.run(["pkill", "-f", f"arecord.*{audio_path}"], stderr=subprocess.DEVNULL)
audio_thread.join(timeout=15)

temp_end = read_temp_c()

# analyse audio
audio_stats = {}
if os.path.exists(audio_path):
    try:
        with wave.open(audio_path, "r") as wf:
            raw = wf.readframes(wf.getnframes())
        s    = array.array("h", raw)
        rms  = math.sqrt(sum(x*x for x in s) / len(s))
        peak = max(abs(x) for x in s)
        audio_stats = {
            "captured":      True,
            "rms":           round(rms, 2),
            "peak":          peak,
            "clipping":      peak >= 32767,
        }
    except Exception as e:
        audio_stats = {"captured": False, "error": str(e)}
else:
    audio_stats = {"captured": False, "error": "file_missing"}

v_pass   = sum(1 for r in video_records if r["status"] == "PASS")
v_drop   = sum(1 for r in video_records if r["status"] == "DROP")
duration = t_end - t_start
fps_act  = v_pass / duration if duration > 0 else 0

result = {
    "schema":           "ph6.gap16_r2.v1",
    "run_id":           run_id,
    "gap_reference":    "GAP-16",
    "run_label":        "C01-GAP16-R2",
    "target_frames":    TARGET_FRAMES,
    "actual_duration":  round(duration, 3),
    "video": {
        "camera_index":    CAM_INDEX,
        "usb_device":      usb_dev_path,
        "resolution":      f"{WIDTH}x{HEIGHT}",
        "passed_frames":   v_pass,
        "dropped_frames":  v_drop,
        "actual_fps":      round(fps_act, 3),
        "drop_rate_pct":   round(100 * v_drop / max(v_pass + v_drop, 1), 2),
        "disconnect_at_sec": disconnect_at,
    },
    "audio": {
        "alsa_device":   ALSA_DEVICE,
        "rate_hz":       RATE,
        "overrun_count": audio_result.get("overruns", -1),
        "arecord_rc":    audio_result.get("rc", -1),
        **audio_stats,
    },
    "thermal": {
        "temp_start_c": temp_start,
        "temp_mid_c":   temp_mid,
        "temp_end_c":   temp_end,
    },
    "gap16_verdict": None,
    "video_records": video_records,
}

# classification
no_disconnect = disconnect_at is None
no_drops      = v_drop == 0
fps_degraded  = fps_act < 25
audio_ok      = audio_stats.get("captured", False) and audio_result.get("overruns", 999) == 0

if no_disconnect and no_drops and fps_degraded and audio_ok:
    verdict = "STABLE-CONFIRMED: GAP-16 = AV contention degradation, no disconnect"
elif not no_disconnect:
    verdict = "SPLIT-REQUIRED: disconnect observed — classify GAP-16A + GAP-16B"
elif not no_drops:
    verdict = "DEGRADED: video frame drops present"
else:
    verdict = "REVIEW"

result["gap16_verdict"] = verdict

report = os.path.join(out_dir, "gap16_r2_report.json")
with open(report, "w") as f:
    json.dump(result, f, indent=2)

summary = {k: v for k, v in result.items() if k != "video_records"}
print(json.dumps(summary, indent=2))
print(f"\ngap16_verdict: {verdict}")
