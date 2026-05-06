#!/usr/bin/env bash
set -u

PASS=0
WARN=0
FAIL=0

ok(){ echo "[PASS] $1"; PASS=$((PASS+1)); }
warn(){ echo "[WARN] $1"; WARN=$((WARN+1)); }
fail(){ echo "[FAIL] $1"; FAIL=$((FAIL+1)); }

echo "=================================================="
echo "WHOLE SYSTEM INTEGRATION CHECK"
echo "Date: $(date)"
echo "Host: $(hostname)"
echo "=================================================="
echo

echo "=== 1. BASIC HARDWARE / OS HEALTH ==="

if command -v vcgencmd >/dev/null 2>&1; then
    T="$(vcgencmd get_throttled 2>/dev/null || true)"
    echo "$T"
    if echo "$T" | grep -q "0x0"; then
        ok "Power/throttle clean"
    else
        warn "Power/throttle flag present: $T"
    fi
else
    warn "vcgencmd missing"
fi

if lsblk | grep -qi nvme; then
    ok "NVMe detected"
else
    warn "No NVMe detected"
fi

if ls /dev/video* >/dev/null 2>&1; then
    ok "Camera/video devices detected"
    ls /dev/video* | head
else
    warn "No /dev/video devices detected"
fi

if systemctl --failed --no-legend | grep -q .; then
    warn "Failed services exist"
    systemctl --failed --no-pager
else
    ok "No failed systemd services"
fi

DMESG_BAD="$(dmesg -T 2>/dev/null | grep -Ei 'undervoltage|i/o error|nvme.*error|pcie.*error|usb disconnect|reset SuperSpeed|Buffer I/O|EXT4-fs error' | tail -20 || true)"
if [ -z "$DMESG_BAD" ]; then
    ok "No major recent kernel hardware/storage errors"
else
    warn "Kernel warnings/errors found:"
    echo "$DMESG_BAD"
fi

echo
echo "=== 2. PYTHON / PACKAGE HEALTH ==="

if command -v python3 >/dev/null 2>&1; then
    ok "python3 available: $(python3 --version)"
else
    fail "python3 missing"
fi

python3 - <<'PY'
import importlib

mods = [
    "json",
    "hashlib",
    "pathlib",
    "sqlite3",
]

optional = [
    "cv2",
    "numpy",
    "pytest",
]

for m in mods:
    try:
        importlib.import_module(m)
        print(f"[PASS_PY] required module available: {m}")
    except Exception as e:
        print(f"[FAIL_PY] required module broken/missing: {m}: {e}")

for m in optional:
    try:
        mod = importlib.import_module(m)
        v = getattr(mod, "__version__", "version_unknown")
        print(f"[PASS_PY] optional module available: {m} {v}")
    except Exception as e:
        print(f"[WARN_PY] optional module missing: {m}: {e}")
PY

echo
echo "=== 3. PH6 / SSMT SOURCE CHECK ==="

if [ -d "$HOME/ph6" ]; then
    ok "~/ph6 directory exists"
elif [ -d "./ph6" ]; then
    ok "./ph6 directory exists"
else
    warn "ph6 directory not found in current directory or home"
fi

if python3 - <<'PY' >/tmp/ph6_import_check.out 2>&1
try:
    from ph6.ssmt.live_sidecar import SSMTLiveSidecar
    from ph6.ssmt.scheduler import SwarmScheduler
    from ph6.ssmt.audit_writer import AdvisoryAuditWriter
    print("IMPORT_OK")
except Exception as e:
    print("IMPORT_FAIL", repr(e))
    raise
PY
then
    ok "PH6/SSMT imports clean"
else
    fail "PH6/SSMT import failed"
    cat /tmp/ph6_import_check.out
fi

echo
echo "=== 4. SSMT LIVE SIDECAR CLOSURE TEST ==="

python3 - <<'PY' >/tmp/ssmt_live_check.out 2>&1
from ph6.ssmt.live_sidecar import SSMTLiveSidecar

REF = "cram://frame/0001#c0c08c7db0fdab02499da88eecfb3884b7f29bbe4bf4699da043bb2eb2e12b31"

sidecar = SSMTLiveSidecar()
result = sidecar.process_cram_ref(REF)

print("CRAM_REF", result.get("cram_ref"))
print("CRAM_HASHES", result.get("cram_packet_hashes"))
print("TOK_REFS", result.get("tok_refs"))
print("PACKETS", result.get("packet_count"))
print("AUDIT_EVENTS", result.get("audit_event_count"))
print("RECEIPT", result.get("receipt", {}).get("receipt_hash"))
print("CLOSURE", result.get("closure"))

packet_count = result.get("packet_count")
audit_count = result.get("audit_event_count")
closure = result.get("closure", {})

assert packet_count == 9, f"expected 9 packets, got {packet_count}"
assert audit_count == 9, f"expected 9 audit events, got {audit_count}"
assert closure.get("passed") is True, f"closure did not pass: {closure}"

print("SSMT_WHOLE_SYSTEM_PASS")
PY

if grep -q "SSMT_WHOLE_SYSTEM_PASS" /tmp/ssmt_live_check.out; then
    ok "SSMT live sidecar closure passed"
    cat /tmp/ssmt_live_check.out
else
    fail "SSMT live sidecar closure failed"
    cat /tmp/ssmt_live_check.out
fi

echo
echo "=== 5. FULL SSMT TEST SUITE ==="

if [ -d "ph6/ssmt/tests" ] || [ -d "$HOME/ph6/ssmt/tests" ]; then
    if [ -d "ph6/ssmt/tests" ]; then
        TEST_PATH="ph6/ssmt/tests/"
    else
        TEST_PATH="$HOME/ph6/ssmt/tests/"
    fi

    if python3 -m pytest "$TEST_PATH" -q >/tmp/ssmt_pytest.out 2>&1; then
        ok "SSMT pytest suite passed"
        tail -20 /tmp/ssmt_pytest.out
    else
        fail "SSMT pytest suite failed"
        cat /tmp/ssmt_pytest.out
    fi
else
    warn "SSMT test directory not found"
fi

echo
echo "=== 6. MRAM-S / ADVISORY WRITE BOUNDARY CHECK ==="

if [ -d "/var/ph6/mram-s" ]; then
    ok "/var/ph6/mram-s exists"
else
    warn "/var/ph6/mram-s does not exist"
fi

if [ -d "/var/ph6/mram-s/swarms" ]; then
    ok "/var/ph6/mram-s/swarms exists"
else
    warn "/var/ph6/mram-s/swarms does not exist"
fi

if [ -w "/var/ph6/mram-s" ]; then
    ok "MRAM-S is writable by current user"
else
    warn "MRAM-S not writable by current user"
fi

echo
echo "=== 7. AUTHORITY LEAKAGE STRING SCAN ==="

if [ -d "ph6/ssmt" ]; then
    SCAN_PATH="ph6/ssmt"
elif [ -d "$HOME/ph6/ssmt" ]; then
    SCAN_PATH="$HOME/ph6/ssmt"
else
    SCAN_PATH=""
fi

if [ -n "$SCAN_PATH" ]; then
    BAD="$(grep -RInE 'PASS|DROP|write_cram|PSEUDO|authority.*true|Authority.*TRUE' "$SCAN_PATH" 2>/dev/null || true)"
    if [ -z "$BAD" ]; then
        ok "No obvious SSMT authority-leakage strings found"
    else
        warn "Review possible authority-boundary strings:"
        echo "$BAD" | head -40
    fi
else
    warn "Cannot scan SSMT path because it was not found"
fi

echo
echo "=================================================="
echo "WHOLE SYSTEM RESULT"
echo "PASS: $PASS"
echo "WARN: $WARN"
echo "FAIL: $FAIL"

if [ "$FAIL" -gt 0 ]; then
    echo "STATUS: FAIL — whole system is not fully integrated."
elif [ "$WARN" -gt 0 ]; then
    echo "STATUS: WARNING — core may work, but review warnings."
else
    echo "STATUS: GOOD — hardware, OS, storage, PH6/SSMT, audit, and closure are integrated."
fi
echo "=================================================="
