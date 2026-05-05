#!/usr/bin/env bash
set -u

PASS=0
WARN=0
FAIL=0

ok(){ echo "[PASS] $1"; PASS=$((PASS+1)); }
warn(){ echo "[WARN] $1"; WARN=$((WARN+1)); }
fail(){ echo "[FAIL] $1"; FAIL=$((FAIL+1)); }

echo "=================================================="
echo "SYSTEM INTEGRATION CHECK"
echo "Date: $(date)"
echo "Host: $(hostname)"
echo "Kernel: $(uname -a)"
echo "=================================================="
echo

echo "=== 1. POWER / THROTTLE CHECK ==="
if command -v vcgencmd >/dev/null 2>&1; then
    THROTTLE="$(vcgencmd get_throttled 2>/dev/null || true)"
    echo "$THROTTLE"
    if echo "$THROTTLE" | grep -q "0x0"; then
        ok "No undervoltage or throttling currently reported"
    else
        warn "Power/throttle flag detected: $THROTTLE"
    fi
else
    warn "vcgencmd not found"
fi
echo

echo "=== 2. DISK / STORAGE CHECK ==="
df -h /
ROOT_USE="$(df / | awk 'NR==2 {print $5}' | tr -d '%')"
if [ "$ROOT_USE" -lt 85 ]; then
    ok "Root disk usage acceptable: ${ROOT_USE}%"
else
    warn "Root disk usage high: ${ROOT_USE}%"
fi

echo
lsblk -o NAME,SIZE,TYPE,FSTYPE,MOUNTPOINT,MODEL 2>/dev/null || true

if lsblk | grep -qi "nvme"; then
    ok "NVMe detected"
else
    warn "No NVMe detected"
fi
echo

echo "=== 3. PCIe CHECK ==="
if command -v lspci >/dev/null 2>&1; then
    lspci
    if lspci | grep -Ei "Non-Volatile|NVMe|PCI bridge|Ethernet|USB" >/dev/null; then
        ok "PCIe bus responding"
    else
        warn "PCIe tool works, but no expected PCIe device found"
    fi
else
    warn "lspci not installed. Install with: sudo apt install pciutils"
fi
echo

echo "=== 4. USB CHECK ==="
if command -v lsusb >/dev/null 2>&1; then
    lsusb
    ok "USB bus responding"
else
    warn "lsusb not installed. Install with: sudo apt install usbutils"
fi
echo

echo "=== 5. NETWORK CHECK ==="
ip addr show | grep -E "^[0-9]+:|inet " || true

if ping -c 1 -W 2 8.8.8.8 >/dev/null 2>&1; then
    ok "Internet/IP connectivity works"
else
    warn "No external ping response"
fi

if ping -c 1 -W 2 google.com >/dev/null 2>&1; then
    ok "DNS works"
else
    warn "DNS may not be working"
fi
echo

echo "=== 6. CAMERA / VIDEO CHECK ==="
if ls /dev/video* >/dev/null 2>&1; then
    ls -l /dev/video*
    ok "Video device detected"
else
    warn "No /dev/video device detected"
fi
echo

echo "=== 7. PYTHON CHECK ==="
if command -v python3 >/dev/null 2>&1; then
    PY="$(python3 --version)"
    ok "Python available: $PY"
else
    fail "Python3 missing"
fi

python3 - <<'PY'
mods = ["json", "sqlite3", "hashlib", "pathlib"]
for m in mods:
    try:
        __import__(m)
        print(f"[PASS] Python module available: {m}")
    except Exception as e:
        print(f"[FAIL] Python module missing/broken: {m} -> {e}")

try:
    import cv2
    print(f"[PASS] OpenCV available: {cv2.__version__}")
except Exception as e:
    print(f"[WARN] OpenCV not available: {e}")

try:
    import numpy
    print(f"[PASS] NumPy available: {numpy.__version__}")
except Exception as e:
    print(f"[WARN] NumPy not available: {e}")
PY
echo

echo "=== 8. SYSTEM SERVICES CHECK ==="
systemctl --failed --no-pager || true
FAILED_SERVICES="$(systemctl --failed --no-legend 2>/dev/null | wc -l)"
if [ "$FAILED_SERVICES" -eq 0 ]; then
    ok "No failed systemd services"
else
    warn "$FAILED_SERVICES failed systemd service(s)"
fi
echo

echo "=== 9. KERNEL ERROR CHECK ==="
DMESG_ERRORS="$(dmesg -T 2>/dev/null | grep -Ei "undervoltage|voltage|i/o error|reset SuperSpeed|usb disconnect|nvme.*error|mmc.*error|Buffer I/O|EXT4-fs error" | tail -30 || true)"
if [ -z "$DMESG_ERRORS" ]; then
    ok "No recent major kernel hardware/storage errors found"
else
    warn "Recent kernel warnings/errors found:"
    echo "$DMESG_ERRORS"
fi
echo

echo "=== 10. BASIC WRITE TEST ==="
TESTFILE="$HOME/integration_write_test.tmp"
if dd if=/dev/zero of="$TESTFILE" bs=1M count=64 conv=fsync status=none 2>/tmp/write_test_err; then
    rm -f "$TESTFILE"
    ok "Basic disk write + fsync test passed"
else
    fail "Disk write/fsync test failed"
    cat /tmp/write_test_err
fi
echo

echo "=================================================="
echo "RESULT:"
echo "PASS: $PASS"
echo "WARN: $WARN"
echo "FAIL: $FAIL"

if [ "$FAIL" -gt 0 ]; then
    echo "STATUS: FAIL — something important is broken."
elif [ "$WARN" -gt 0 ]; then
    echo "STATUS: WARNING — system mostly works, but something needs attention."
else
    echo "STATUS: GOOD — system appears integrated and stable."
fi
echo "=================================================="
