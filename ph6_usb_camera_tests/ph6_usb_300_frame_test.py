import cv2
import time
import json
import hashlib
import os
import sys
from datetime import datetime, timezone

CAM_INDEX = int(sys.argv[1]) if len(sys.argv) > 1 else 0
WIDTH = int(sys.argv[2]) if len(sys.argv) > 2 else 640
HEIGHT = int(sys.argv[3]) if len(sys.argv) > 3 else 480
TARGET_FRAMES = int(sys.argv[4]) if len(sys.argv) > 4 else 300

run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
out_dir = f"usb_test_{run_id}"
os.makedirs(out_dir, exist_ok=True)

cap = cv2.VideoCapture(CAM_INDEX)
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)
cap.set(cv2.CAP_PROP_FPS, 30)

if not cap.isOpened():
    print("FAIL: camera_not_opened")
    sys.exit(1)

# warmup — discard first few frames before evidence capture
for _ in range(5):
    cap.read()

frame_records = []
start = time.time()
failures = 0

for idx in range(TARGET_FRAMES):
    t0 = time.time()
    ok, frame = cap.read()
    t1 = time.time()

    if not ok or frame is None:
        failures += 1
        frame_records.append({
            "frame_index": idx,
            "status": "DROP",
            "reason": "capture_failed",
            "timestamp_utc": datetime.now(timezone.utc).isoformat()
        })
        continue

    frame_bytes = frame.tobytes()
    frame_hash = hashlib.blake2b(frame_bytes, digest_size=32).hexdigest()

    if idx in [0, 1, 2, 50, 100, 150, 200, 250, 299]:
        cv2.imwrite(os.path.join(out_dir, f"frame_{idx:04d}.jpg"), frame)

    frame_records.append({
        "frame_index": idx,
        "status": "PASS",
        "shape": list(frame.shape),
        "capture_ms": round((t1 - t0) * 1000, 3),
        "frame_hash_blake2b_256": frame_hash,
        "timestamp_utc": datetime.now(timezone.utc).isoformat()
    })

end = time.time()
cap.release()

passed = sum(1 for r in frame_records if r["status"] == "PASS")
dropped = sum(1 for r in frame_records if r["status"] == "DROP")
duration = end - start
fps_actual = passed / duration if duration > 0 else 0

result = {
    "schema": "ph6.usb_camera_test.v1",
    "run_id": run_id,
    "camera_index": CAM_INDEX,
    "requested_width": WIDTH,
    "requested_height": HEIGHT,
    "target_frames": TARGET_FRAMES,
    "passed_frames": passed,
    "dropped_frames": dropped,
    "duration_sec": round(duration, 3),
    "actual_fps": round(fps_actual, 3),
    "valid_ph6_minimum": TARGET_FRAMES >= 300,
    "test_result": "PASS" if passed >= 300 and dropped == 0 else "REVIEW",
    "records": frame_records
}

with open(os.path.join(out_dir, "usb_camera_test_report.json"), "w") as f:
    json.dump(result, f, indent=2)

print(json.dumps({
    "run_id": run_id,
    "camera_index": CAM_INDEX,
    "passed_frames": passed,
    "dropped_frames": dropped,
    "duration_sec": round(duration, 3),
    "actual_fps": round(fps_actual, 3),
    "test_result": result["test_result"],
    "output_dir": out_dir
}, indent=2))
