#!/usr/bin/env bash
set +e

STAMP="$(date +%Y%m%d_%H%M%S)"
REPORT="$HOME/ph6_total_systems_test_$STAMP.txt"

{
echo "=================================================="
echo "PH6 TOTAL SYSTEMS TEST"
echo "=================================================="
echo "Time: $(date -Is)"
echo "Host: $(hostname)"
echo "User: $(whoami)"
echo "Kernel: $(uname -a)"
echo

echo "=================================================="
echo "0) BASIC SYSTEM HEALTH"
echo "=================================================="
echo "--- Python ---"
python3 --version

echo
echo "--- Disk ---"
df -h

echo
echo "--- Memory ---"
free -h

echo
echo "--- Temperature / Throttle ---"
vcgencmd measure_temp 2>/dev/null || echo "vcgencmd unavailable"
vcgencmd get_throttled 2>/dev/null || echo "vcgencmd unavailable"

echo
echo "--- Reboot Required ---"
if [ -f /var/run/reboot-required ]; then
  echo "REBOOT REQUIRED"
  cat /var/run/reboot-required.pkgs 2>/dev/null
else
  echo "No reboot-required flag found."
fi

echo
echo "=================================================="
echo "1) PACKAGE / INSTALL HEALTH"
echo "=================================================="
echo "--- dpkg audit ---"
sudo dpkg --audit

echo
echo "--- apt broken dependency dry run ---"
sudo apt --fix-broken install --dry-run

echo
echo "--- held packages ---"
apt-mark showhold

echo
echo "--- upgradable packages tail ---"
apt list --upgradable 2>/dev/null | tail -80

echo
echo "=================================================="
echo "2) SERVICES / BOOT ERRORS"
echo "=================================================="
echo "--- failed services ---"
systemctl --failed

echo
echo "--- serious journal errors tail ---"
journalctl -p 3 -xb --no-pager | tail -120

echo
echo "=================================================="
echo "3) NETWORK / SSH"
echo "=================================================="
echo "--- IP addresses ---"
hostname -I

echo
echo "--- active connections ---"
nmcli connection show --active 2>/dev/null || echo "nmcli unavailable"

echo
echo "--- ping gateway/internet ---"
ping -c 3 8.8.8.8

echo
echo "--- DNS test ---"
ping -c 3 google.com

echo
echo "--- SSH service ---"
systemctl status ssh --no-pager 2>/dev/null || echo "ssh service unavailable"

echo
echo "=================================================="
echo "4) CAMERA DEVICE DISCOVERY"
echo "=================================================="
echo "--- video devices ---"
ls -lah /dev/video* 2>/dev/null || echo "No /dev/video devices found"

echo
echo "--- USB devices ---"
lsusb

echo
echo "--- v4l2 list devices ---"
v4l2-ctl --list-devices 2>/dev/null || echo "v4l2-ctl unavailable; install with: sudo apt install -y v4l-utils"

echo
echo "--- v4l2 camera 0 formats ---"
v4l2-ctl -d /dev/video0 --list-formats-ext 2>/dev/null | head -120 || echo "Could not read /dev/video0 formats"

echo
echo "=================================================="
echo "5) CAMERA OPENCV STABILITY TEST"
echo "=================================================="
python3 - <<'PY'
import cv2
import time
import statistics

source = 0
width = 640
height = 480
target_fps = 18
frames = 300

cap = cv2.VideoCapture(source)

if not cap.isOpened():
    print("BLOCK: camera did not open")
    raise SystemExit(0)

cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
cap.set(cv2.CAP_PROP_FPS, target_fps)

try:
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
except Exception:
    pass

good = 0
bad = 0
times = []

start = time.time()

for i in range(frames):
    t0 = time.time()
    ok, frame = cap.read()
    t1 = time.time()

    if ok and frame is not None:
        good += 1
        times.append((t1 - t0) * 1000.0)
    else:
        bad += 1

cap.release()

elapsed = time.time() - start
fps = good / elapsed if elapsed > 0 else 0

print(f"camera_source={source}")
print(f"requested_width={width}")
print(f"requested_height={height}")
print(f"requested_fps={target_fps}")
print(f"frames_requested={frames}")
print(f"frames_good={good}")
print(f"frames_bad={bad}")
print(f"measured_fps={fps:.2f}")

if times:
    print(f"capture_ms_min={min(times):.2f}")
    print(f"capture_ms_avg={statistics.mean(times):.2f}")
    print(f"capture_ms_max={max(times):.2f}")

if bad == 0:
    print("PASS: camera stable")
elif bad < frames * 0.05:
    print("HOLD: camera mostly stable but has read failures")
else:
    print("BLOCK: camera unstable")
PY

echo
echo "=================================================="
echo "6) FRAME_FILTER REPO STATUS"
echo "=================================================="
if [ -d "$HOME/frame_filter" ]; then
  cd "$HOME/frame_filter"
  echo "--- path ---"
  pwd

  echo
  echo "--- git status ---"
  git status --short

  echo
  echo "--- recent commits ---"
  git log --oneline -5

  echo
  echo "--- key files ---"
  for f in frame_filter.py cram_writer.py test_segment_cram_writer.py ph6lite_coherence_check.py run_ph6lite_check.sh test_ph6lite_phase2.py; do
    if [ -f "$f" ]; then
      echo "FOUND: $f"
    else
      echo "MISSING: $f"
    fi
  done

  echo
  echo "--- SegmentCRAMWriter test ---"
  if [ -f test_segment_cram_writer.py ]; then
    python3 test_segment_cram_writer.py
  else
    echo "MISSING test_segment_cram_writer.py"
  fi

  echo
  echo "--- PH6-Lite coherence direct check ---"
  if [ -f ph6lite_coherence_check.py ]; then
    python3 ph6lite_coherence_check.py
  else
    echo "MISSING ph6lite_coherence_check.py"
  fi

  echo
  echo "--- Phase 2 test / known log-path mismatch check ---"
  if [ -f test_ph6lite_phase2.py ]; then
    timeout 60 python3 test_ph6lite_phase2.py
  else
    echo "MISSING test_ph6lite_phase2.py"
  fi

  echo
  echo "--- log path grep ---"
  grep -nE "run_log|spike_events|jsonl|hot/" test_ph6lite_phase2.py frame_filter.py ph6lite_coherence_check.py run_ph6lite_check.sh 2>/dev/null | head -120

else
  echo "BLOCK: ~/frame_filter missing"
fi

echo
echo "=================================================="
echo "7) LIVE FRAME_FILTER CAMERA RUN"
echo "=================================================="
if [ -d "$HOME/frame_filter" ]; then
  cd "$HOME/frame_filter"

  if [ -f frame_filter.py ]; then
    echo "Running short live CRAM/camera smoke test..."
    timeout 90 python3 frame_filter.py \
      --source 0 \
      --width 640 \
      --height 480 \
      --fps 18 \
      --max_frames 300 \
      --save_mode all \
      --postrun
  else
    echo "MISSING frame_filter.py"
  fi

  echo
  echo "--- latest logs ---"
  latest="$(ls -td logs/run_* 2>/dev/null | head -1)"
  echo "latest=$latest"
  if [ -n "$latest" ]; then
    find "$latest" -maxdepth 3 -type f -print | sort
    echo
    echo "--- latest hot files ---"
    find "$latest/hot" -maxdepth 2 -type f -print 2>/dev/null | sort
    echo
    echo "--- spike events head ---"
    head -5 "$latest/hot/spike_events.jsonl" 2>/dev/null || echo "No hot/spike_events.jsonl found"
  fi
else
  echo "SKIP: no ~/frame_filter"
fi

echo
echo "=================================================="
echo "8) PH6 STORAGE MONITOR"
echo "=================================================="
if [ -d "$HOME/ph6_storage_monitor" ]; then
  cd "$HOME/ph6_storage_monitor"
  echo "--- path ---"
  pwd

  echo
  echo "--- git status ---"
  git status --short

  echo
  echo "--- recent commits ---"
  git log --oneline -5

  echo
  echo "--- key files ---"
  for f in ph6_storage_score_history.py test_storage_monitor.py; do
    if [ -f "$f" ]; then
      echo "FOUND: $f"
    else
      echo "MISSING: $f"
    fi
  done

  echo
  echo "--- storage monitor tests ---"
  if [ -f test_storage_monitor.py ]; then
    python3 test_storage_monitor.py
  else
    echo "MISSING test_storage_monitor.py"
  fi
else
  echo "HOLD: ~/ph6_storage_monitor missing"
fi

echo
echo "=================================================="
echo "9) PSEUDO + SOSO AGENT"
echo "=================================================="
if command -v run-pseudo-soso >/dev/null 2>&1; then
  run-pseudo-soso
elif [ -x "$HOME/bin/run-pseudo-soso" ]; then
  "$HOME/bin/run-pseudo-soso"
elif [ -f "$HOME/ph6_pseudo_soso/pseudo_soso_agent.py" ]; then
  cd "$HOME/ph6_pseudo_soso"
  source "$HOME/ph6_pseudo_soso/.venv/bin/activate" 2>/dev/null
  python3 pseudo_soso_agent.py
else
  echo "HOLD: PSEUDO + SoSo agent not installed"
fi

echo
echo "=================================================="
echo "10) CLEAN GENERATED ARTIFACT SCAN"
echo "=================================================="
echo "--- frame_filter generated leftovers ---"
find "$HOME/frame_filter" -maxdepth 3 \
  \( -name "__pycache__" -o -name "*.pyc" -o -name "*.bak.*" -o -name "*report*.json" -o -name "*report*.txt" \) \
  -print 2>/dev/null

echo
echo "--- storage monitor generated leftovers ---"
find "$HOME/ph6_storage_monitor" -maxdepth 3 \
  \( -name "__pycache__" -o -name "*.pyc" -o -name "*.bak.*" -o -name "*report*.json" -o -name "*report*.txt" \) \
  -print 2>/dev/null

echo
echo "=================================================="
echo "11) FINAL GIT STATUS"
echo "=================================================="
echo "--- frame_filter ---"
cd "$HOME/frame_filter" 2>/dev/null && git status --short || echo "missing frame_filter"

echo
echo "--- ph6_storage_monitor ---"
cd "$HOME/ph6_storage_monitor" 2>/dev/null && git status --short || echo "missing ph6_storage_monitor"

echo
echo "=================================================="
echo "TOTAL SYSTEMS TEST COMPLETE"
echo "=================================================="
echo "Report: $REPORT"

} 2>&1 | tee "$REPORT"

echo
echo "Saved report:"
echo "$REPORT"
