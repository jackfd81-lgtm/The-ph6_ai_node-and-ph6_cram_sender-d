#!/usr/bin/env bash
set +e

REPORT="$HOME/pi5_unfinished_work_report_$(date +%Y%m%d_%H%M%S).txt"

{
echo "=================================================="
echo "PI 5 UNFINISHED WORK REPORT"
echo "=================================================="
date
hostname
uname -a
echo

echo "=================================================="
echo "APT / PACKAGE CHECK"
echo "=================================================="
sudo dpkg --audit
sudo apt --fix-broken install --dry-run
apt list --upgradable 2>/dev/null
apt-mark showhold
grep -iE "error|fail|half|unpack|configure" /var/log/dpkg.log 2>/dev/null | tail -80

echo
echo "=================================================="
echo "REBOOT / SERVICES"
echo "=================================================="
if [ -f /var/run/reboot-required ]; then
  echo "REBOOT REQUIRED"
  cat /var/run/reboot-required.pkgs 2>/dev/null
else
  echo "No reboot-required flag found."
fi
systemctl --failed
journalctl -p 3 -xb --no-pager | tail -100

echo
echo "=================================================="
echo "DISK / MEMORY / TEMP"
echo "=================================================="
df -h
free -h
vcgencmd measure_temp 2>/dev/null
vcgencmd get_throttled 2>/dev/null

echo
echo "=================================================="
echo "NETWORK"
echo "=================================================="
hostname -I
ip addr show
nmcli connection show --active 2>/dev/null
ping -c 3 8.8.8.8
ping -c 3 google.com

echo
echo "=================================================="
echo "CAMERA"
echo "=================================================="
ls -lah /dev/video* 2>/dev/null
lsusb
v4l2-ctl --list-devices 2>/dev/null

python3 - <<'PYEOF'
import cv2, time
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("FAIL — camera 0 did not open")
    raise SystemExit(0)
good = bad = 0
start = time.time()
for i in range(100):
    ok, frame = cap.read()
    if ok and frame is not None:
        good += 1
    else:
        bad += 1
cap.release()
elapsed = time.time() - start
fps = good / elapsed if elapsed else 0
print(f"frames_good={good}")
print(f"frames_bad={bad}")
print(f"fps={fps:.2f}")
PYEOF

echo
echo "=================================================="
echo "FRAME_FILTER / PH6 PROJECT"
echo "=================================================="
if [ -d "$HOME/frame_filter" ]; then
  cd "$HOME/frame_filter"
  pwd
  ls -lah
  git status 2>/dev/null
  python3 --version
  python3 -m pip --version 2>/dev/null

  python3 - <<'PYEOF'
mods = ["cv2", "numpy", "json", "time", "os", "argparse"]
for m in mods:
    try:
        mod = __import__(m)
        ver = getattr(mod, "__version__", "stdlib/no-version")
        print(f"PASS {m}: {ver}")
    except Exception as e:
        print(f"FAIL {m}: {e}")
PYEOF

  for f in frame_filter.py cram_writer.py virtual_tokens.py scenario_engine_v1.py; do
    if [ -f "$f" ]; then
      echo "FOUND: $f"
    else
      echo "MISSING: $f"
    fi
  done

  ls -lah logs 2>/dev/null
else
  echo "MISSING: $HOME/frame_filter"
fi

} 2>&1 | tee "$REPORT"

echo
echo "Report saved to:"
echo "$REPORT"
