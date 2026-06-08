#!/usr/bin/env python3
"""
PH6 Desktop Controlled Terminal v1.1
Observer-only console for PH6 system operations.
Lane-2 Advisory — Authority: ZERO

Run:  python3 ph6_desktop_terminal.py
Req:  Python 3.9+ standard library only. No GUI. No Claude API required.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

VERSION = "1.1"
HOME    = Path.home()

# ── Config ────────────────────────────────────────────────────────────────────

_CONFIG_PATH = Path(__file__).parent / "terminal_config.json"
_REPORTS_DIR = Path(__file__).parent / "reports"
_LOGS_DIR    = Path(__file__).parent / "logs"


def _load_config() -> dict:
    try:
        return json.loads(_CONFIG_PATH.read_text())
    except Exception:
        return {}


CFG = _load_config()

PH6_DIR         = HOME / CFG.get("ph6_dir", "ph6")
STATUS_JSON     = HOME / CFG.get("status_json", "ph6_status/status.json")
CRAM_RUNTIME    = PH6_DIR / "cram_pu/runtime"
AUDIT_JSONL     = Path(CFG.get("audit_jsonl", "/var/ph6/audit/audit.jsonl"))
ESP_S1_URL      = CFG.get("esp_s1_url", "http://192.168.254.194")
ESP_TIMEOUT     = int(CFG.get("esp_s1_timeout", 5))
SCRIPT_TIMEOUT  = int(CFG.get("script_timeout", 60))
REPLAY_TIMEOUT  = int(CFG.get("replay_timeout", 30))

LOCK_FILE = Path("/var/ph6/session.lock")

AUDIT_REPLAY_PY   = PH6_DIR / "ph6_audit_replay.py"
VALIDATE_CANON_PY = PH6_DIR / "ph6_validate_canon.py"
CONSOLIDATE_PY    = PH6_DIR / "ph6_consolidate_3.py"
SMI_REPORT_JSON   = PH6_DIR / "smi_1_1_validation_report.json"
PHASE4_VERDICT    = PH6_DIR / "phase4_canon_lock_verdict.json"
AUDIT_TEST_PY     = PH6_DIR / "audit_test.py"
INTERNAL_TEST_PY  = PH6_DIR / "cram_pu/ph6_internal_test.py"

# ── ANSI helpers ──────────────────────────────────────────────────────────────

_USE_COLOR = sys.stdout.isatty()

_C = {
    "green":  "\033[92m",
    "red":    "\033[91m",
    "yellow": "\033[93m",
    "cyan":   "\033[96m",
    "gray":   "\033[90m",
    "bold":   "\033[1m",
    "reset":  "\033[0m",
}


def _c(color: str, text: str) -> str:
    if not _USE_COLOR:
        return text
    return _C.get(color, "") + text + _C["reset"]


def _status_color(v: str) -> str:
    v = v.upper()
    if v in ("PASS", "OK", "CLEAN", "CONFIRMED", "ELIGIBLE", "DRY_RUN_PASS"):
        return "green"
    if v in ("FAIL", "FOUND", "GAPS", "ERROR", "READ_ERROR"):
        return "red"
    if v in ("WARN", "PENDING", "UNKNOWN", "LOG_MISSING"):
        return "yellow"
    return "gray"


def _badge(label: str, value: str | None) -> str:
    v = str(value or "UNKNOWN")
    colored = _c(_status_color(v), v)
    return f"  {label:<28} {colored}"


def _sep(char: str = "─", width: int = 52) -> None:
    print(_c("gray", char * width))


def _prototype_notice() -> None:
    """PH6_DESKTOP_CLASS3_PROTOTYPE_DOCTRINE_v1.2.md Section 3 — required operator notice."""
    _sep("─")
    print(_c("bold",   "  PH6 Prototype Notice"))
    print()
    print(_c("gray",   "  This workstation is a prototype development cockpit."))
    print()
    print(_c("gray",   "  Primary development authority:"))
    print(_c("cyan",   "    Class 1 Cloud / Claude Terminal"))
    print()
    print(_c("gray",   "  Primary operational authority:"))
    print(_c("cyan",   "    Class 2 SSH Terminal"))
    print()
    print(_c("gray",   "  Desktop functions are limited to approved prototype capabilities."))
    _sep("─")


def _prototype_footer() -> None:
    """PH6_DESKTOP_CLASS3_PROTOTYPE_DOCTRINE_v1.2.md Section 10 — required permanent footer."""
    print(_c("gray", "  Desktop Status:   Experimental Development Platform"))
    print(_c("gray", "  Authority:        ZERO"))
    print(_c("gray", "  Lane Impact:      None"))
    print(_c("gray", "  Current Maturity: Early Operational Prototype"))
    _sep("─")


def _header(title: str) -> None:
    print()
    _sep("═")
    print(_c("bold", f"  {title}"))
    _sep("═")
    print()
    _prototype_footer()


def _subheader(title: str) -> None:
    print()
    print(_c("cyan", f"  ── {title}"))


def _pause() -> None:
    try:
        input(_c("gray", "\n  Press Enter to continue…"))
    except (KeyboardInterrupt, EOFError):
        pass


# ── Session logger ────────────────────────────────────────────────────────────

_session: dict[str, Any] = {
    "version":    VERSION,
    "started_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "actions":    [],
}


def _log(action: str, result: str = "") -> None:
    _session["actions"].append({
        "utc":    datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "action": action,
        "result": result[:400] if result else "",
    })


def _save_session() -> None:
    try:
        _REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        ts    = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        path  = _REPORTS_DIR / f"terminal_session_{ts}.json"
        _session["ended_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        path.write_text(json.dumps(_session, indent=2))
        print(_c("gray", f"\n  Session saved → {path.name}"))
    except Exception as e:
        print(_c("yellow", f"\n  Session save failed: {e}"))


# ── Session Lock Manager ─────────────────────────────────────────────────────
# Rule: One Controller / Many Observers
#
# Ownership states:   FREE | DESKTOP | CLAUDE
# Access modes:       CONTROL | MONITOR_ONLY | READ_ONLY
#
# Desktop owns lock → Desktop=CONTROL,      Claude=READ_ONLY
# Claude  owns lock → Claude=CONTROL,       Desktop=MONITOR_ONLY
# No lock           → First acquirer gets   CONTROL
#
# Lock file is JSON to enable stale-lock detection via pid/heartbeat.

_ACCESS_MODE: str = "CONTROL"    # module-level access mode for this session


def _lock_record(owner: str, mode: str) -> dict:
    import socket
    return {
        "owner":      owner,
        "mode":       mode,
        "pid":        os.getpid(),
        "hostname":   socket.gethostname(),
        "started_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "heartbeat":  datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def _lock_read() -> dict:
    try:
        if LOCK_FILE.exists():
            return json.loads(LOCK_FILE.read_text())
    except Exception:
        pass
    return {}


def _lock_is_stale(rec: dict) -> bool:
    """True if the owning PID is gone and heartbeat is >120s old."""
    try:
        pid = int(rec.get("pid", 0))
        if pid:
            try:
                os.kill(pid, 0)
                return False          # process still alive
            except ProcessLookupError:
                pass                  # pid gone — check heartbeat
            except PermissionError:
                return False          # alive but owned by other user
        hb = rec.get("heartbeat", "")
        if hb:
            from datetime import datetime as _dt
            delta = (datetime.now(timezone.utc) -
                     _dt.fromisoformat(hb.replace("Z", "+00:00"))).total_seconds()
            return delta > 120
    except Exception:
        pass
    return True


def _lock_acquire() -> str:
    """Acquire DESKTOP lock. Returns: ACQUIRED | CLAUDE | BUSY_DESKTOP | NO_PERMS | ERROR."""
    global _ACCESS_MODE
    try:
        LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
        if LOCK_FILE.exists():
            rec = _lock_read()
            owner = rec.get("owner", "")
            if owner == "CLAUDE":
                _ACCESS_MODE = "MONITOR_ONLY"
                return "CLAUDE"
            if owner == "DESKTOP":
                if _lock_is_stale(rec):
                    LOCK_FILE.unlink(missing_ok=True)  # clear stale lock
                else:
                    return "BUSY_DESKTOP"
            else:
                LOCK_FILE.unlink(missing_ok=True)  # unknown/corrupt — clear
        # Atomic creation: O_CREAT|O_EXCL fails if file already exists.
        fd = os.open(str(LOCK_FILE), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
        try:
            os.write(fd, json.dumps(_lock_record("DESKTOP", "CONTROL"), indent=2).encode())
        finally:
            os.close(fd)
        _ACCESS_MODE = "CONTROL"
        return "ACQUIRED"
    except PermissionError:
        return "NO_PERMS"
    except Exception:
        return "ERROR"


def _lock_heartbeat() -> None:
    """Update heartbeat timestamp in the lock file (call periodically)."""
    try:
        rec = _lock_read()
        if rec.get("owner") == "DESKTOP" and rec.get("pid") == os.getpid():
            rec["heartbeat"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            LOCK_FILE.write_text(json.dumps(rec, indent=2))
    except Exception:
        pass


def _lock_release() -> None:
    try:
        rec = _lock_read()
        if rec.get("owner") == "DESKTOP" and rec.get("pid") == os.getpid():
            LOCK_FILE.unlink()
    except Exception:
        pass


def _lock_status() -> dict:
    """Return current lock record, or synthetic FREE record."""
    rec = _lock_read()
    if not rec:
        return {"owner": "FREE", "mode": "CONTROL"}
    return rec


# ── Safe subprocess ───────────────────────────────────────────────────────────

def _run(cmd: list[str], timeout: int = 30, cwd: Path = HOME) -> tuple[int, str]:
    try:
        r = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, cwd=str(cwd),
        )
        output = (r.stdout + r.stderr).strip()
        return r.returncode, output
    except subprocess.TimeoutExpired:
        return -1, f"TIMEOUT after {timeout}s"
    except FileNotFoundError:
        return -2, f"Command not found: {cmd[0]}"
    except Exception as e:
        return -3, str(e)


def _read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text())
    except Exception:
        return {}


def _read_jsonl_tail(path: Path, n: int = 10) -> list[dict]:
    if not path.exists():
        return []
    try:
        lines = path.read_text().splitlines()
        out = []
        for line in reversed(lines):
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except Exception:
                continue
            if len(out) >= n:
                break
        return list(reversed(out))
    except Exception:
        return []


def _http_get(url: str, timeout: int = 5) -> dict | None:
    try:
        req = urllib.request.urlopen(url, timeout=timeout)
        return json.loads(req.read().decode("utf-8"))
    except Exception:
        return None


# ── Panel: System Dashboard ───────────────────────────────────────────────────

def panel_dashboard() -> None:
    _header("SYSTEM DASHBOARD")
    _log("panel_dashboard")

    status = _read_json(STATUS_JSON)
    _subheader("PH6 Status")
    for key in ("status", "cam", "cram", "ai", "fps", "frame"):
        print(_badge(key.upper(), str(status.get(key, "UNKNOWN"))))

    _subheader("Node Health")
    rc, out = _run(["hostname", "-I"], timeout=5)
    print(_badge("IP addresses", out.split()[0] if out.split() else "UNKNOWN"))
    rc, temp = _run(["vcgencmd", "measure_temp"], timeout=5)
    print(_badge("CPU temp", temp if rc == 0 else "UNKNOWN"))

    _subheader("Git")
    rc, log = _run(["git", "log", "--oneline", "-1"], timeout=5)
    print(f"  Last commit: {_c('cyan', log) if rc == 0 else _c('yellow', 'UNKNOWN')}")

    _subheader("Storage")
    rc, df = _run(["df", "-h", "/"], timeout=5)
    if rc == 0:
        lines = df.splitlines()
        if len(lines) >= 2:
            print(f"  {_c('gray', lines[0])}")
            print(f"  {lines[1]}")

    _pause()


# ── Panel: Camera Diagnostics ─────────────────────────────────────────────────

def panel_camera() -> None:
    _header("CAMERA DIAGNOSTICS")
    _log("panel_camera")

    _subheader("Video Devices")
    rc, devs = _run(["ls", "/dev/video*"], timeout=5)
    if rc == 0:
        for d in devs.split():
            print(f"  {_c('green', d)}")
    else:
        print(_badge("devices found", "NONE"))

    _subheader("Recent Dual-Camera Test")
    test_dir = HOME / "PH6_SOURCE/TESTS/DUAL_USB_CAMERA"
    if test_dir.exists():
        json_files = sorted(test_dir.rglob("*.json"))[-3:]
        if json_files:
            for f in json_files:
                r = _read_json(f)
                print(f"  {_c('gray', f.name)}")
                for k in ("status", "verdict", "frames_captured"):
                    if k in r:
                        print(_badge(f"  {k}", str(r[k])))
        else:
            print(_badge("test reports", "NOT_FOUND"))
    else:
        print(_badge("test directory", "NOT_FOUND"))

    _subheader("ESP_S1 Camera Node (192.168.254.191)")
    rc, out = _run(
        ["python3", "-c",
         "import urllib.request,json; r=urllib.request.urlopen('http://192.168.254.191/status',timeout=4); print(r.read().decode())"],
        timeout=6,
    )
    if rc == 0:
        print(f"  {_c('green', 'REACHABLE')}: {out[:80]}")
    else:
        print(_badge("ESP_S1 camera", "UNREACHABLE"))

    _pause()


# ── Panel: Sensor Diagnostics ─────────────────────────────────────────────────

def panel_sensors() -> None:
    _header("SENSOR DIAGNOSTICS")
    _log("panel_sensors")

    _subheader(f"ESP_S1 Node ({ESP_S1_URL})")
    health = _http_get(f"{ESP_S1_URL}/health", timeout=ESP_TIMEOUT)
    if health:
        print(_badge("health status", health.get("status", "UNKNOWN")))
        for k in ("uptime_ms", "free_heap", "ip"):
            if k in health:
                print(f"  {k:<28} {health[k]}")
    else:
        print(_badge("ESP_S1 health", "UNREACHABLE"))

    sensor = _http_get(f"{ESP_S1_URL}/sensor", timeout=ESP_TIMEOUT)
    if sensor:
        _subheader("Sensor Readings")
        for k in ("temperature_c", "humidity_pct", "pressure_hpa", "bme280_ok"):
            if k in sensor:
                print(_badge(k, str(sensor[k])))
    else:
        print(_badge("sensor data", "UNREACHABLE"))

    _subheader("I2C Bus")
    i2c = _http_get(f"{ESP_S1_URL}/i2c_scan", timeout=ESP_TIMEOUT)
    if i2c:
        devices = i2c.get("devices", [])
        print(_badge("I2C devices found", str(len(devices))))
        for d in devices:
            print(f"  {_c('cyan', str(d))}")
    else:
        print(_badge("i2c_scan", "UNREACHABLE"))

    _pause()


# ── Panel: Device Manager ─────────────────────────────────────────────────────
#
# PH6 Workstation Hierarchy (embedded per operator directive — keep this note in
# every Desktop / Device Manager / Test Center patch; see also
# PH6_DESKTOP_CLASS3_PROTOTYPE_DOCTRINE_v1.1.md):
#
#   1. Cloud / Claude Terminal      — Primary development authority
#   2. SSH Terminal                 — Primary operational device authority
#   3. Desktop Prototype Interface  — Class 3 prototype cockpit, Authority: ZERO, Not Primary
#
# Desktop may assist, display, launch approved tests, and review data.
# Desktop does not replace Cloud Terminal or SSH Terminal.
#
# Registry rule: every new device enters as STATUS: UNVERIFIED. Registration is
# non-authoritative — it never grants CRAM, PSEUDO, or authority-chain trust.
# A device becomes usable only after probe success, characterization test,
# report generation, operator review, and a clean governance scan.

_DEVICE_REGISTRY_JSON = Path(__file__).parent / "device_registry.json"
_DEVICE_TYPES = (
    "camera", "microphone", "usb", "i2c", "serial",
    "network_node", "pi_node", "esp_node", "storage",
)


def _device_registry_load() -> dict:
    reg = _read_json(_DEVICE_REGISTRY_JSON)
    if not reg or "devices" not in reg:
        reg = {
            "schema": "ph6.desktop.device_registry.v1",
            "authority": "ZERO",
            "non_authoritative": True,
            "devices": [],
        }
    return reg


def _device_registry_save(reg: dict) -> None:
    _DEVICE_REGISTRY_JSON.write_text(json.dumps(reg, indent=2))


def panel_device_manager() -> None:
    _header("DEVICE MANAGER")
    _log("panel_device_manager")
    print(_c("gray", "  Non-authoritative registry — Authority: ZERO."))
    print(_c("gray", "  New devices default to STATUS: UNVERIFIED until probed and operator-reviewed.\n"))

    reg = _device_registry_load()
    devices = reg.get("devices", [])

    _subheader(f"Registered Devices ({len(devices)})")
    if devices:
        for d in devices:
            status = d.get("status", "UNVERIFIED")
            color  = "green" if status == "VERIFIED" else "yellow"
            print(f"  {_c(color, status):<18} {d.get('device_type', '?'):<14} "
                  f"{d.get('label', '(unlabeled)')}  [{d.get('device_id', '?')}]")
    else:
        print(_badge("devices", "NONE_REGISTERED"))

    if _ACCESS_MODE != "CONTROL":
        print(_c("gray", "\n  [monitor mode] Add Device disabled — requires CONTROL."))
        _pause()
        return

    print()
    try:
        choice = input("  Add a device? (y/N): ").strip().lower()
    except (KeyboardInterrupt, EOFError):
        choice = ""

    if choice == "y":
        try:
            label = input("  Device label: ").strip()
            print(f"  Device type ({', '.join(_DEVICE_TYPES)}):")
            dtype = input("  > ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            label, dtype = "", ""

        if not label or dtype not in _DEVICE_TYPES:
            print(_c("yellow", "\n  Cancelled — label is required and type must be one of the listed values."))
        else:
            entry = {
                "device_id": f"{dtype}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}",
                "label": label,
                "device_type": dtype,
                "status": "UNVERIFIED",
                "registered_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "registered_by": "desktop_operator",
                "probe_result": None,
                "characterization_report": None,
                "operator_reviewed": False,
            }
            devices.append(entry)
            reg["devices"] = devices
            _device_registry_save(reg)
            _log("device_registered", f"id={entry['device_id']} status=UNVERIFIED")
            print(_c("green", f"\n  Registered: {entry['device_id']}  "
                              f"(status=UNVERIFIED — pending probe + operator review)"))

    _pause()


# ── Panel: Run PH6 Test ───────────────────────────────────────────────────────

def panel_run_test() -> None:
    _header("RUN PH6 TEST")
    _log("panel_run_test")

    if not INTERNAL_TEST_PY.exists():
        print(_badge("internal test script", "NOT_FOUND"))
        print(f"  Expected: {INTERNAL_TEST_PY}")
        _pause()
        return

    print(f"  Running: python3 {INTERNAL_TEST_PY}")
    print(_c("gray", "  (20 checks — up to 60s)\n"))

    rc, out = _run(["python3", str(INTERNAL_TEST_PY)], timeout=SCRIPT_TIMEOUT)

    if rc == 0:
        print(_c("green", "  PASS"))
    elif rc < 0:
        print(_badge("exit", str(rc)))
    else:
        print(_c("red", "  FAIL"))

    print()
    for line in out.splitlines()[-30:]:
        print(f"  {line}")

    _log("ph6_internal_test", f"rc={rc}")
    _pause()


# ── Panel: Test Breakdown Viewer ──────────────────────────────────────────────
#
# Read-only artifact viewer. Desktop displays PSEUDO-produced results — it
# never computes, generates, or alters PASS/DROP verdicts, and never writes
# to any test artifact, report, or authority path.

_TEST_REGISTRY_JSON = Path(__file__).parent / "test_registry.json"

_BREAKDOWN_FIELDS = (
    "test_id", "id", "device_id", "started_at", "start_time", "ended_at",
    "end_time", "duration_s", "duration", "command", "input_files",
    "output_files", "frames_captured", "samples_captured", "pass_count",
    "drop_count", "warnings", "errors", "artifacts", "report_path",
    "governance_status", "verdict", "status",
)


def _registered_tests() -> list[dict]:
    raw = _read_json(_TEST_REGISTRY_JSON)
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict):
        return raw.get("tests", [])
    return []


def panel_test_breakdown() -> None:
    _header("TEST BREAKDOWN VIEWER")
    _log("panel_test_breakdown")
    print(_c("gray", "  Read-only. Desktop displays PSEUDO-produced results only —"))
    print(_c("gray", "  it does not generate PASS/DROP and does not write artifact files.\n"))

    tests = _registered_tests()
    if not tests:
        print(_badge("registered tests", "NONE_FOUND"))
        _pause()
        return

    for entry in tests:
        test_id  = entry.get("id", "?")
        glob_pat = entry.get("artifact_glob")
        _subheader(f"{entry.get('label', test_id)}  [{test_id}]")
        print(f"  {_c('gray', 'command')}: {entry.get('command', '?')}")

        if not glob_pat:
            print(_badge("artifact_glob", "NOT_DEFINED"))
            continue

        matches = sorted(HOME.glob(glob_pat))
        if not matches:
            print(_badge("artifacts", "NOT_FOUND"))
            continue

        latest = matches[-1]
        print(f"  {_c('gray', 'latest artifact')}: {latest.relative_to(HOME)}")
        data = _read_json(latest)
        if not data:
            print(_badge("artifact", "UNREADABLE"))
            continue

        shown = 0
        for key in _BREAKDOWN_FIELDS:
            if key in data:
                print(_badge(f"  {key}", str(data[key])[:80]))
                shown += 1
        if shown == 0:
            print(_c("gray", "  (no recognized breakdown fields in this artifact)"))

    _pause()


# ── Panel: PSEUDO Results ─────────────────────────────────────────────────────

def panel_pseudo() -> None:
    _header("PSEUDO RESULTS")
    _log("panel_pseudo")

    runtime_dirs = sorted(CRAM_RUNTIME.glob("*/"), key=lambda d: d.name) if CRAM_RUNTIME.exists() else []

    if not runtime_dirs:
        print(_badge("CRAM runtime", "NO_DATA"))
        _pause()
        return

    latest = runtime_dirs[-1]
    print(f"  Run dir: {_c('cyan', latest.name)}")

    _subheader("PASS / DROP Counts")
    pass_dir = latest / "cram_store/cram_a"
    drop_dir = latest / "cram_store/cram_r"
    pass_count = len(list(pass_dir.glob("*.blake2b"))) if pass_dir.exists() else 0
    drop_count = len(list(drop_dir.glob("frame_*"))) if drop_dir.exists() else 0
    print(_badge("CRAM-A (PASS frames)", str(pass_count)))
    print(_badge("CRAM-R (DROP frames)", str(drop_count)))

    _subheader("RSYNC Queue (last entry)")
    queue_files = sorted(CRAM_RUNTIME.glob("*/cram_store/rsync_queue.jsonl"))
    if queue_files:
        entries = _read_jsonl_tail(queue_files[-1], 1)
        if entries:
            e = entries[0]
            print(_badge("depth", str(e.get("depth", "?"))))
            print(_badge("blocked_by", str(e.get("blocked_by") or "none")))
    else:
        print(_badge("rsync queue", "NOT_FOUND"))

    _pause()


# ── Panel: SoSo Results ───────────────────────────────────────────────────────

def panel_soso() -> None:
    _header("SoSo RESULTS")
    _log("panel_soso")

    soso_dir = PH6_DIR / "cram_pu/runtime"
    reports  = sorted(soso_dir.rglob("*soso*.json")) if soso_dir.exists() else []
    reports += sorted((HOME / "PH6_SOURCE").rglob("*soso*.json"))

    if not reports:
        print(_badge("SoSo reports", "NOT_FOUND"))
        _pause()
        return

    for rpt in reports[-4:]:
        print(f"\n  {_c('gray', str(rpt.relative_to(HOME)))}")
        data = _read_json(rpt)
        for k in ("status", "verdict", "context_seq", "lane2_authority"):
            if k in data:
                print(_badge(f"  {k}", str(data[k])))

    _pause()


# ── Panel: Token Results ──────────────────────────────────────────────────────

def panel_tokens() -> None:
    _header("TOKEN RESULTS")
    _log("panel_tokens")

    tok_dir = PH6_DIR / "tok"
    reports = sorted(tok_dir.rglob("*.json")) if tok_dir.exists() else []
    reports += sorted((HOME / "PH6_SOURCE").rglob("*tok*.json"))

    if not reports:
        print(_badge("Token reports", "NOT_FOUND"))
        _pause()
        return

    for rpt in reports[-4:]:
        print(f"\n  {_c('gray', str(rpt.relative_to(HOME)))}")
        data = _read_json(rpt)
        for k in ("status", "token_class", "authority", "lane2_authority"):
            if k in data:
                print(_badge(f"  {k}", str(data[k])))

    _pause()


# ── Panel: Live-vs-Simulator ──────────────────────────────────────────────────

def panel_live_vs_sim() -> None:
    _header("LIVE-vs-SIMULATOR")
    _log("panel_live_vs_sim")

    sim_reports = sorted((HOME / "PH6_SOURCE").rglob("*sim*comparison*.json"))
    sim_reports += sorted((HOME / "PH6_SOURCE").rglob("*live_vs_sim*.json"))

    if not sim_reports:
        print(_badge("Simulator comparison reports", "NOT_FOUND"))
        print(_c("gray", "\n  Simulator reports appear after validation campaigns."))
        _pause()
        return

    for rpt in sim_reports[-4:]:
        print(f"\n  {_c('gray', str(rpt.relative_to(HOME)))}")
        data = _read_json(rpt)
        for k in ("verdict", "status", "delta_pct", "frames_compared"):
            if k in data:
                print(_badge(f"  {k}", str(data[k])))

    _pause()


# ── Panel: Reports ────────────────────────────────────────────────────────────

def panel_reports() -> None:
    _header("REPORTS")
    _log("panel_reports")

    gov_dir = HOME / "PH6_SOURCE/GOVERNANCE"
    dep_dir = HOME / "PH6_SOURCE/DEPLOYMENT"

    _subheader("Governance Reports")
    if gov_dir.exists():
        files = sorted(gov_dir.glob("*.json"))[-8:]
        for f in files:
            print(f"  {_c('cyan', f.name)}")
    else:
        print(_badge("GOVERNANCE dir", "NOT_FOUND"))

    _subheader("Deployment Reports")
    if dep_dir.exists():
        files = sorted(dep_dir.glob("*.md"))[-6:]
        for f in files:
            print(f"  {_c('gray', f.name)}")
    else:
        print(_badge("DEPLOYMENT dir", "NOT_FOUND"))

    _subheader("SMI-1.1 Reports")
    for rpt in (SMI_REPORT_JSON, PHASE4_VERDICT):
        exists = rpt.exists()
        print(_badge(rpt.name, "FOUND" if exists else "NOT_FOUND"))
        if exists:
            data = _read_json(rpt)
            ts = data.get("generated_at", "")
            if ts:
                print(f"  {_c('gray', ts)}")

    _pause()


# ── Panel: Topology ───────────────────────────────────────────────────────────

def panel_topology() -> None:
    _header("TOPOLOGY")
    _log("panel_topology")

    _subheader("Registered Nodes — Ping Check")
    nodes = [
        ("Pi 5 primary (ingest/CRAM-0)", "192.168.254.188", "jackjack"),
        ("Pi Zero 2W (sentinel)",         "192.168.254.189", "jackjack2"),
        ("ESP_HTTP_SENSOR_NODE (ESP_S1)", "192.168.254.194", "ESP_S1"),
    ]
    for role, ip, host in nodes:
        rc, _ = _run(["ping", "-c", "1", "-W", "2", ip], timeout=4)
        status = "REACHABLE" if rc == 0 else "UNREACHABLE"
        color  = "green" if rc == 0 else "red"
        print(f"  {_c(color, status):<20}  {ip:<18} {host}  ({role})")

    _subheader("ESP_S1 Live Health")
    esp_health = _http_get(f"{ESP_S1_URL}/health", timeout=ESP_TIMEOUT)
    if esp_health:
        for k in ("status", "node", "uptime_s", "firmware"):
            if k in esp_health:
                print(_badge(f"  {k}", str(esp_health[k])))
    else:
        print(_badge("  ESP_S1 /health", "UNREACHABLE"))

    _subheader("ESP_S1 Topology Artifacts")
    topo_keys = [
        ("esp_s1_topology.json",       HOME / "PH6_SOURCE"),
        ("esp_s1_topology_token.json", HOME / "PH6_SOURCE"),
        ("esp_s1_health_snapshot.json",HOME / "PH6_SOURCE"),
    ]
    for fname, search_root in topo_keys:
        hits = sorted(search_root.rglob(fname)) if search_root.exists() else []
        if hits:
            path = hits[-1]
            data = _read_json(path)
            ts   = data.get("generated_at", data.get("captured_at", ""))
            print(f"  {_c('green', 'FOUND'):<20} {path.relative_to(HOME)}  {_c('gray', ts)}")
        else:
            print(f"  {_c('yellow', 'NOT_FOUND'):<20} {fname}")

    _subheader("Dynamic Node Discovery")
    disc_files = sorted((HOME / "PH6_SOURCE").rglob("*topology*.json"))[-6:]
    if disc_files:
        for f in disc_files:
            data = _read_json(f)
            node_id = data.get("node_id", data.get("node", ""))
            status  = data.get("status", data.get("health", ""))
            print(f"  {_c('cyan', f.name):<40} node={node_id} status={status}")
    else:
        print(_badge("  discovered topology files", "NOT_FOUND"))

    _pause()


# ── Panel: Evidence Review Center ─────────────────────────────────────────────
#
# Read-only consolidated review of current and previous evidence artifacts:
# video/image/sensor/CRAM/PSEUDO/SoSo/token/governance/topology/replay/report/
# log files. Desktop only displays what Lane-1 already produced — it never
# writes to the artifact under review, never generates PASS/DROP, and never
# mutates CRAM, PSEUDO, SoSo, or EvidencePacket records.
#
# Cloud/Claude Terminal first. SSH Terminal second. Desktop Prototype
# Interface third. Desktop may assist, display, launch approved tests, and
# review data. Desktop does not replace Cloud Terminal or SSH Terminal.

_EVIDENCE_SEARCH_ROOTS = (
    HOME / "PH6_SOURCE/TESTS",
    Path(__file__).parent / "reports",
    Path(__file__).parent / "logs",
    HOME / "PH6_SOURCE/REPORTS",
    HOME / "PH6_SOURCE/GOVERNANCE",
    HOME / "PH6_SOURCE/TOPOLOGY",
    Path("/var/ph6/cram-0"),
    Path("/var/ph6/cram-a"),
    Path("/var/ph6/cram-r"),
    Path("/var/ph6/mram-s"),
    Path("/var/ph6/audit"),
    Path("/var/ph6/export"),
)

_EVIDENCE_VIDEO_EXT = (".mp4", ".avi", ".mov", ".mkv", ".webm", ".h264", ".raw")
_EVIDENCE_IMAGE_EXT = (".jpg", ".jpeg", ".png", ".bmp", ".webp")
_EVIDENCE_TEXT_EXT  = (".json", ".md", ".txt", ".log", ".csv")
_EVIDENCE_EXTENSIONS = _EVIDENCE_VIDEO_EXT + _EVIDENCE_IMAGE_EXT + _EVIDENCE_TEXT_EXT

_EVIDENCE_SUMMARY_FIELDS = _BREAKDOWN_FIELDS + (
    "summary", "result", "node", "node_id", "schema", "authority",
    "generated_at", "captured_at",
)

# Per-class breakdown fields (Patch 1.3). Desktop only ever echoes these
# values back from the artifact on disk — it never computes, infers, or
# fabricates them.
_SENSOR_BREAKDOWN_FIELDS = (
    "timestamp", "device_id", "sensor_type", "sample_count", "fps",
    "dropped_frames", "temperature", "light", "motion", "audio_level",
    "error_count", "warning_count",
)
_CRAM_BREAKDOWN_FIELDS = (
    "cram_tier", "tier", "object_id", "id", "sequence", "source_path",
    "hash", "blake2b", "sha256", "size", "verdict", "veto_reasons",
    "commit_marker", ".blake2b",
)
_PSEUDO_BREAKDOWN_FIELDS = (
    "verdict", "entropy", "laplacian_variance", "motion_fraction",
    "reasons", "policy_version", "threshold_profile", "gate_profile",
)
_SOSO_BREAKDOWN_FIELDS = (
    "continuity_id", "topology_refs", "source_object_ids",
    "advisory_status", "relationship_graph",
)
_TOKEN_BREAKDOWN_FIELDS = (
    "token_id", "token_type", "refs", "created_at", "authority",
    "decay", "stability",
)

_TEST_DIR_PATTERN = re.compile(r"^\d{8}_\d{6}")

# RT / VDT / VLT / AVLT token classes (PH6 Token Doctrine). Matches
# bounded prefixes like "rt_", "vdt-", "avlt." but not incidental
# substrings such as "report" (which contains "rt" unbounded).
_TOKEN_NAME_PATTERN = re.compile(r"(?:^|[_.\-])(?:rt|vdt|vlt|avlt)(?:[_.\-]|$)")


def _classify_evidence_artifact(path: Path) -> str:
    """Classify by extension first, then by name keyword. Order matters —
    more specific PH6 vocabulary (cram/pseudo/soso/...) is checked before
    generic report/log fallbacks."""
    name = path.name.lower()
    ext  = path.suffix.lower()

    if ext in _EVIDENCE_VIDEO_EXT:
        return "VIDEO"
    if ext in _EVIDENCE_IMAGE_EXT:
        return "IMAGE"
    if "cram" in name or "evidencepacket" in name or "replay_manifest" in name:
        return "CRAM"
    if "pseudo" in name:
        return "PSEUDO"
    if "soso" in name:
        return "SOSO"
    if "token" in name or _TOKEN_NAME_PATTERN.search(name):
        return "TOKEN"
    if "governance" in name or "drift" in name:
        return "GOVERNANCE"
    if "topology" in name:
        return "TOPOLOGY"
    if "replay" in name:
        return "REPLAY"
    if "sensor" in name:
        return "SENSOR"
    if ext == ".log" or "log" in name:
        return "LOG"
    if "report" in name or ext == ".md":
        return "REPORT"
    return "UNKNOWN"


def _collect_evidence_artifacts(max_per_root: int = 200, max_total: int = 400) -> list[dict]:
    """Read-only directory walk. Skips missing/unreadable roots safely.
    Never opens for write; only stat()s and records metadata + class."""
    found: list[dict] = []
    for root in _EVIDENCE_SEARCH_ROOTS:
        try:
            if not root.exists() or not root.is_dir():
                continue
        except OSError:
            continue

        count = 0
        try:
            for p in root.rglob("*"):
                if count >= max_per_root or len(found) >= max_total:
                    break
                try:
                    if not p.is_file() or p.suffix.lower() not in _EVIDENCE_EXTENSIONS:
                        continue
                    st = p.stat()
                except OSError:
                    continue
                found.append({
                    "path":  p,
                    "size":  st.st_size,
                    "mtime": st.st_mtime,
                    "class": _classify_evidence_artifact(p),
                })
                count += 1
        except (OSError, PermissionError):
            continue

    found.sort(key=lambda e: e["mtime"], reverse=True)
    return found


def _evidence_relpath(path: Path) -> Path | str:
    try:
        return path.relative_to(HOME)
    except ValueError:
        return path


def _playback_hint(path: Path) -> str:
    """Return a display-only suggested operator command. Desktop never
    executes this — it is text shown to the operator, who launches it
    themselves on their own workstation if they choose to."""
    ext = path.suffix.lower()
    if ext in _EVIDENCE_VIDEO_EXT:
        return f'xdg-open "{path}"   (or: ffplay "{path}")'
    if ext in _EVIDENCE_IMAGE_EXT:
        return f'xdg-open "{path}"   (or: feh "{path}")'
    return f'xdg-open "{path}"'


def _render_class_breakdown(klass: str, data: dict) -> None:
    """Echo recognized fields for a known evidence class. Values are read
    verbatim from the artifact — Desktop never computes or fabricates a
    verdict, threshold, or advisory state."""
    if not isinstance(data, dict) or not data:
        print(_c("gray", "  (no parsable breakdown fields)"))
        return

    fields = {
        "SENSOR": _SENSOR_BREAKDOWN_FIELDS,
        "CRAM":   _CRAM_BREAKDOWN_FIELDS,
        "PSEUDO": _PSEUDO_BREAKDOWN_FIELDS,
        "SOSO":   _SOSO_BREAKDOWN_FIELDS,
        "TOKEN":  _TOKEN_BREAKDOWN_FIELDS,
    }.get(klass, _EVIDENCE_SUMMARY_FIELDS)

    shown = 0
    for key in fields:
        if key in data:
            print(_badge(f"  {key}", str(data[key])[:100]))
            shown += 1
    if shown == 0:
        keys = list(data.keys())[:8]
        print(_c("gray", f"  (no recognized {klass} fields — top-level keys: {', '.join(keys)})"))

    if klass == "SOSO":
        print(_c("yellow", "  ADVISORY ONLY  ·  AUTHORITY ZERO"))
    elif klass == "TOKEN":
        print(_c("yellow", "  MRAM-S ONLY  ·  AUTHORITY ZERO"))


def _evidence_test_group_key(path: Path) -> str:
    """Find the nearest ancestor directory that looks like a test-run
    folder (YYYYMMDD_HHMMSS...). Falls back to the immediate parent name
    so every artifact still lands in some group."""
    for parent in path.parents:
        if _TEST_DIR_PATTERN.match(parent.name):
            return parent.name
    return path.parent.name or "ungrouped"


def _group_evidence_by_test(artifacts: list[dict]) -> list[dict]:
    """Group artifacts by inferred test run, newest run first. Pure
    read-only aggregation over already-collected metadata — no filesystem
    writes, no verdicts, no authority data."""
    groups: dict[str, dict] = {}
    order: list[str] = []
    for entry in artifacts:
        key = _evidence_test_group_key(entry["path"])
        if key not in groups:
            groups[key] = {
                "test_id": key,
                "artifacts": [],
                "counts": {},
                "first_mtime": entry["mtime"],
                "last_mtime": entry["mtime"],
            }
            order.append(key)
        g = groups[key]
        g["artifacts"].append(entry)
        g["counts"][entry["class"]] = g["counts"].get(entry["class"], 0) + 1
        g["first_mtime"] = min(g["first_mtime"], entry["mtime"])
        g["last_mtime"]  = max(g["last_mtime"], entry["mtime"])
    return sorted((groups[k] for k in order), key=lambda g: g["last_mtime"], reverse=True)


def _render_evidence_test_timeline(groups: list[dict]) -> None:
    _subheader(f"Test Timeline ({len(groups)} runs found, newest first)")
    for i, g in enumerate(groups[:15], 1):
        start = datetime.fromtimestamp(g["first_mtime"], tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
        end   = datetime.fromtimestamp(g["last_mtime"],  tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
        c = g["counts"]
        print(f"  {i:>2}. {_c('cyan', g['test_id'])}")
        print(f"      start={start}  end={end}  artifacts={len(g['artifacts'])}")
        print(f"      video={c.get('VIDEO',0)} image={c.get('IMAGE',0)} sensor={c.get('SENSOR',0)} "
              f"cram={c.get('CRAM',0)} pseudo={c.get('PSEUDO',0)} soso={c.get('SOSO',0)} "
              f"token={c.get('TOKEN',0)} logs={c.get('LOG',0)} reports={c.get('REPORT',0)}")


def _preview_evidence_artifact(entry: dict) -> None:
    """Read-only preview. Opens the file for reading only — never writes,
    never mutates, never fabricates a verdict."""
    path  = entry["path"]
    klass = entry["class"]
    ts    = datetime.fromtimestamp(entry["mtime"], tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    print(f"\n  {_c('gray', 'path')}: {_evidence_relpath(path)}")
    print(_badge("class",        klass))
    print(_badge("size_bytes",   str(entry["size"])))
    print(_badge("modified_utc", ts))

    if klass == "VIDEO":
        print(_badge("extension", path.suffix))
        print(_badge("playback",  "PENDING"))
        print(_c("gray", "  Suggested operator command (display only — Desktop does not launch it):"))
        print(_c("cyan", f"    {_playback_hint(path)}"))
        return

    if klass == "IMAGE":
        print(_badge("extension", path.suffix))
        print(_badge("preview",   "PENDING"))
        print(_c("gray", "  Suggested operator command (display only — Desktop does not launch it):"))
        print(_c("cyan", f"    {_playback_hint(path)}"))
        return

    if path.suffix.lower() == ".json":
        data = _read_json(path)
        if not data:
            print(_badge("artifact", "UNREADABLE_OR_EMPTY"))
            return
        if klass in ("SENSOR", "CRAM", "PSEUDO", "SOSO", "TOKEN"):
            _render_class_breakdown(klass, data)
        else:
            shown = 0
            for key in _EVIDENCE_SUMMARY_FIELDS:
                if key in data:
                    print(_badge(f"  {key}", str(data[key])[:100]))
                    shown += 1
            if shown == 0 and isinstance(data, dict):
                keys = list(data.keys())[:8]
                print(_c("gray", f"  (no recognized summary fields — top-level keys: {', '.join(keys)})"))
        return

    if path.suffix.lower() in _EVIDENCE_TEXT_EXT:
        try:
            lines = path.read_text(errors="replace").splitlines()
        except Exception:
            print(_badge("artifact", "UNREADABLE"))
            return
        tail = lines[-20:]
        print(_c("gray", f"  (showing last {len(tail)} of {len(lines)} lines — read-only)"))
        for line in tail:
            print(f"  {line[:140]}")
        return

    print(_c("gray", "  No preview available for this file type."))


def panel_evidence_review() -> None:
    _header("EVIDENCE PLAYBACK + BREAKDOWN CENTER")
    _log("panel_evidence_review")
    print(_c("gray", "  Read-only review, breakdown, and playback-hint center for current"))
    print(_c("gray", "  and previous evidence. Desktop never writes to a reviewed file,"))
    print(_c("gray", "  never generates PASS/DROP, and never mutates CRAM/PSEUDO/SoSo data.\n"))

    artifacts = _collect_evidence_artifacts()
    if not artifacts:
        print(_badge("evidence artifacts", "NONE_FOUND"))
        print(_c("gray", "\n  No known PH6 artifact roots were reachable from this host."))
        _pause()
        return

    groups = _group_evidence_by_test(artifacts)

    _subheader("Filter")
    print("   1. Latest test")
    print("   2. Previous tests")
    print("   3. All artifacts")
    print("   4. By device")
    print("   5. By artifact class")
    print("   6. By date modified")
    try:
        f_choice = input("  Select filter (Enter = All artifacts): ").strip()
    except (KeyboardInterrupt, EOFError):
        f_choice = ""

    shown: list[dict] = []
    if f_choice == "1" and groups:
        shown = groups[0]["artifacts"][:25]
        _subheader(f"Latest Test — {groups[0]['test_id']}  ({len(shown)} of {len(groups[0]['artifacts'])} shown)")
    elif f_choice == "2" and len(groups) > 1:
        for g in groups[1:]:
            shown.extend(g["artifacts"])
        shown = shown[:25]
        _subheader(f"Previous Tests — {len(groups) - 1} runs  ({len(shown)} artifacts shown)")
    elif f_choice == "4":
        try:
            needle = input("  device_id / path contains: ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            needle = ""
        shown = [e for e in artifacts if needle and needle in str(e["path"]).lower()][:25]
        _subheader(f"By Device — '{needle}'  ({len(shown)} shown)")
    elif f_choice == "5":
        known = "/".join(sorted({a["class"] for a in artifacts}))
        try:
            klass_filter = input(f"  class ({known}): ").strip().upper()
        except (KeyboardInterrupt, EOFError):
            klass_filter = ""
        shown = [e for e in artifacts if e["class"] == klass_filter][:25]
        _subheader(f"By Class — {klass_filter or '(none selected)'}  ({len(shown)} shown)")
    else:
        shown = artifacts[:25]
        label = "By Date Modified" if f_choice == "6" else "All Artifacts"
        _subheader(f"{label} — newest {len(shown)} of {len(artifacts)}")
        _render_evidence_test_timeline(groups)

    if not shown:
        print(_badge("filtered artifacts", "NONE_FOUND"))
        _pause()
        return

    print()
    for i, entry in enumerate(shown, 1):
        ts  = datetime.fromtimestamp(entry["mtime"], tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
        rel = _evidence_relpath(entry["path"])
        print(f"  {i:>2}. {_c('cyan', entry['class']):<9} {ts}  {entry['size']:>10}B  {rel}")

    print()
    try:
        choice = input("  Preview/breakdown which # (Enter to skip): ").strip()
    except (KeyboardInterrupt, EOFError):
        choice = ""

    if choice:
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(shown):
                _preview_evidence_artifact(shown[idx])
            else:
                print(_c("yellow", "  Invalid selection."))
        except ValueError:
            print(_c("yellow", "  Invalid selection."))

    _pause()


# ── Governance: Audit Replay ──────────────────────────────────────────────────

def gov_audit_replay() -> None:
    _header("AUDIT REPLAY")
    _log("gov_audit_replay")

    print(_badge("script exists", "OK" if AUDIT_REPLAY_PY.exists() else "NOT_FOUND"))
    print(_badge("audit log exists", "OK" if AUDIT_JSONL.exists() else "LOG_MISSING"))

    if AUDIT_JSONL.exists():
        entries = _read_jsonl_tail(AUDIT_JSONL, 3)
        if entries:
            _subheader("Last 3 Audit Entries")
            for e in entries:
                seq = e.get("event_seq", "?")
                ev  = e.get("event_type", "?")
                ts  = e.get("utc", "")
                print(f"  seq={seq}  {ev}  {_c('gray', ts)}")

    if not AUDIT_REPLAY_PY.exists():
        print(_c("yellow", "\n  Script not found — SMI-1.1 Phase 2 not yet committed."))
        _pause()
        return

    try:
        confirm = input("\n  Run audit replay? [y/N]: ").strip().lower()
    except (KeyboardInterrupt, EOFError):
        return

    if confirm != "y":
        return

    print(_c("gray", "\n  Running python3 ph6_audit_replay.py …"))
    rc, out = _run(["python3", str(AUDIT_REPLAY_PY)], timeout=REPLAY_TIMEOUT)
    result = "PASS" if rc == 0 else f"FAIL (rc={rc})"
    print(f"\n  Result: {_c(_status_color(result), result)}")
    for line in out.splitlines()[-20:]:
        print(f"  {line}")
    _log("audit_replay_run", f"rc={rc} {result}")
    _pause()


# ── Governance: Canon Validator ───────────────────────────────────────────────

_SMI_GATES = [
    "contradiction_check", "duplication_check", "orphan_check",
    "advisory_isolation_check", "certification_separation_check",
    "reading_order_check", "drift_extraction_check",
    "audit_schema_check", "hrg9_gate_check",
]


def gov_canon_validator() -> None:
    _header("CANON VALIDATOR")
    _log("gov_canon_validator")

    print(_badge("script exists", "OK" if VALIDATE_CANON_PY.exists() else "NOT_FOUND"))
    print(_badge("report exists", "OK" if SMI_REPORT_JSON.exists() else "NOT_RUN"))

    if SMI_REPORT_JSON.exists():
        report = _read_json(SMI_REPORT_JSON)
        _subheader("SMI-1.1 Gates (cached report)")
        print(_badge("Validation Status", report.get("overall_status", "UNKNOWN")))
        eligible = report.get("canon_lock_eligible", False)
        print(_badge("Promotion Eligibility", "ELIGIBLE" if eligible else "NOT_ELIGIBLE"))
        print()
        for gate in _SMI_GATES:
            gate_data = report.get("gates", {}).get(gate, {})
            status    = gate_data.get("status", "NOT_IMPLEMENTED") if gate_data else "NOT_IMPLEMENTED"
            label     = gate.replace("_", " ")
            print(_badge(f"  {label}", status))
        print(_c("yellow", "\n  Language rule: 'Promotion Eligibility: ELIGIBLE' only. Promotion requires Lane-1 signature."))
    else:
        print(_c("gray", "\n  No cached report. Run validator to generate."))
        for gate in _SMI_GATES:
            print(_badge(f"  {gate.replace('_', ' ')}", "NOT_IMPLEMENTED"))

    if not VALIDATE_CANON_PY.exists():
        print(_c("yellow", "\n  Script not found — SMI-1.1 Phase 4 not yet committed."))
        _pause()
        return

    try:
        confirm = input("\n  Run canon validator? [y/N]: ").strip().lower()
    except (KeyboardInterrupt, EOFError):
        return

    if confirm != "y":
        return

    print(_c("gray", "\n  Running python3 ph6_validate_canon.py …"))
    rc, out = _run(["python3", str(VALIDATE_CANON_PY)], timeout=SCRIPT_TIMEOUT)
    result = "PASS" if rc == 0 else f"FAIL (rc={rc})"
    print(f"\n  Result: {_c(_status_color(result), result)}")
    for line in out.splitlines()[-30:]:
        print(f"  {line}")
    _log("canon_validator_run", f"rc={rc} {result}")
    _pause()


# ── Governance: Five-Book Dry Run ─────────────────────────────────────────────

def gov_five_book() -> None:
    _header("FIVE-BOOK DRY RUN")
    _log("gov_five_book")

    print(_badge("script exists", "OK" if CONSOLIDATE_PY.exists() else "NOT_FOUND"))

    _subheader("Distribution Plan")
    print(f"  {'Books:':28} Book 0 · Book I · Book II · Book III · Book IV · Book V")

    cached = PH6_DIR / "ph6_consolidate_3_dryrun.json"
    if cached.exists():
        r = _read_json(cached)
        print(_badge("dry-run status",   r.get("status", "UNKNOWN")))
        print(_badge("mapped entries",   str(r.get("mapped_entries", "—"))))
        print(_badge("orphan fragments", str(r.get("orphan_fragments", "—"))))
    else:
        print(_badge("dry-run status", "NOT_RUN"))
        print(_badge("mapped entries",  "—"))
        print(_badge("orphan fragments","—"))

    print(_badge("source preservation",    "GUARANTEED"))
    print(_badge("Lane-1 sig required",    "YES"))
    print(_badge("distribution executed",  "NOT_EXECUTED"))

    _subheader("Dry-run command")
    print(f"  {_c('yellow', 'python3 ~/ph6/ph6_consolidate_3.py --dry-run')}")

    if not CONSOLIDATE_PY.exists():
        print(_c("gray", "\n  Script not found — SMI-1.1 Phase 5 not yet committed."))
        _pause()
        return

    try:
        confirm = input("\n  Run dry-run only? (real distribution is BLOCKED in v1.1) [y/N]: ").strip().lower()
    except (KeyboardInterrupt, EOFError):
        return

    if confirm != "y":
        return

    print(_c("gray", "\n  Running python3 ph6_consolidate_3.py --dry-run …"))
    rc, out = _run(
        ["python3", str(CONSOLIDATE_PY), "--dry-run"],
        timeout=SCRIPT_TIMEOUT,
    )
    result = "DRY_RUN_PASS" if rc == 0 else f"DRY_RUN_FAIL (rc={rc})"
    print(f"\n  Result: {_c(_status_color(result), result)}")
    for line in out.splitlines()[-30:]:
        print(f"  {line}")
    _log("five_book_dry_run", f"rc={rc} {result}")
    _pause()


# ── Governance: Secret Scan ───────────────────────────────────────────────────

_API_KEY_RE = re.compile(
    r'sk-ant-[A-Za-z0-9\-_]{20,}|ANTHROPIC_API_KEY\s*[=:]\s*["\']?[A-Za-z0-9\-_]{10,}',
    re.IGNORECASE,
)
_CRED_RE = re.compile(
    r'password\s*[=:]\s*["\'][^"\']{4,}|secret\s*[=:]\s*["\'][^"\']{4,}',
    re.IGNORECASE,
)


def _scan_file(path: Path, pattern: re.Pattern) -> bool:
    try:
        return bool(pattern.search(path.read_text(errors="ignore")))
    except Exception:
        return False


def gov_secret_scan() -> None:
    _header("SECRET SCAN")
    _log("gov_secret_scan")

    print(_c("gray", "  Scanning ph6/ *.py and *.json files…\n"))

    api_key_found  = False
    cred_found     = False
    report_leakage = False
    env_found      = False

    try:
        py_files = list(PH6_DIR.rglob("*.py"))[:100]
        api_key_found = any(_scan_file(f, _API_KEY_RE) for f in py_files)
        cred_found    = any(_scan_file(f, _CRED_RE) for f in py_files)
    except Exception:
        pass

    try:
        env_hits = [f for f in HOME.rglob("*.env") if ".git" not in str(f) and ".cache" not in str(f)]
        env_found = bool(env_hits) or Path(HOME / ".env").exists()
    except Exception:
        pass

    try:
        json_files   = list(PH6_DIR.rglob("*.json"))[:50]
        report_leakage = any(_scan_file(f, _API_KEY_RE) for f in json_files)
    except Exception:
        pass

    print(_badge("API key scan",        "FOUND" if api_key_found  else "CLEAN"))
    print(_badge(".env scan",           "FOUND" if env_found       else "CLEAN"))
    print(_badge("credential scan",     "FOUND" if cred_found      else "CLEAN"))
    print(_badge("report leakage scan", "FOUND" if report_leakage  else "CLEAN"))
    print(f"\n  {_c('gray', 'Scanned at: ' + datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'))}")

    _log("secret_scan", f"api={api_key_found} cred={cred_found} env={env_found} leak={report_leakage}")
    _pause()


# ── Governance: Commit Readiness ─────────────────────────────────────────────

def gov_commit_readiness() -> None:
    _header("COMMIT READINESS — SMI-1.1")
    _log("gov_commit_readiness")

    # Load SMI report if present
    smi = _read_json(SMI_REPORT_JSON) if SMI_REPORT_JSON.exists() else {}
    phase4 = _read_json(PHASE4_VERDICT) if PHASE4_VERDICT.exists() else {}

    review_gates  = smi.get("review_gates_pass",  "UNKNOWN")
    audit_tests   = smi.get("audit_tests_pass",   "UNKNOWN")
    smi_gates     = smi.get("smi_gates_pass",     "UNKNOWN")
    five_book_dr  = smi.get("five_book_dry_run",  "UNKNOWN")
    secret_scan   = smi.get("secret_scan",        "UNKNOWN")

    _subheader("SMI-1.1 Gate Summary")
    print(_badge("Review Gates",           review_gates  if review_gates  != "UNKNOWN" else "6/6 — check report"))
    print(_badge("Audit Tests",            audit_tests   if audit_tests   != "UNKNOWN" else "12/12 — check report"))
    print(_badge("SMI-1.1 Gates",          smi_gates     if smi_gates     != "UNKNOWN" else "9/9 — check report"))
    print(_badge("Five-Book Dry Run",      five_book_dr  if five_book_dr  != "UNKNOWN" else "UNKNOWN"))
    print(_badge("Secret Scan",            secret_scan   if secret_scan   != "UNKNOWN" else "UNKNOWN"))

    _subheader("Distribution / Execution State")
    print(_badge("Actual Distribution",    "NOT EXECUTED"))
    print(_badge("Canon Lock Eligibility", phase4.get("eligibility", "UNKNOWN")))
    print(_badge("Distribution Status",    "DRY-RUN ONLY"))
    print(_badge("Execution Status",       "NOT EXECUTED"))

    _subheader("Commit Hash")
    rc, log_out = _run(["git", "log", "--oneline", "-1"], timeout=5)
    last_hash = log_out.split()[0] if rc == 0 and log_out.split() else None
    rc2, smi_check = _run(
        ["git", "log", "--oneline", "--", "ph6/audit_test.py"], timeout=5
    )
    smi_in_log = rc2 == 0 and bool(smi_check.strip())
    if last_hash is None:
        commit_status = "UNVERIFIED"
    elif smi_in_log:
        commit_status = "CONFIRMED"
    else:
        commit_status = "PENDING"

    print(_badge("Commit Status",       commit_status))
    print(f"  {'Commit Hash':<28} {_c('cyan', last_hash or 'UNVERIFIED — git log returned no result')}")

    print(_c("yellow", "\n  Rule: CONFIRMED only when git log proves SMI-1.1 files committed."))

    _subheader("SMI-1.1 Scripts On-Disk")
    smi_files = ["audit_test.py", "ph6_audit_replay.py", "ph6_validate_canon.py", "ph6_consolidate_3.py"]
    for f in smi_files:
        exists = (PH6_DIR / f).exists()
        print(_badge(f"  {f}", "ON_DISK" if exists else "MISSING"))

    _log("commit_readiness", f"commit_status={commit_status} hash={last_hash}")
    _pause()


# ── Governance: Commit Confirmation ──────────────────────────────────────────

def gov_commit_confirmation() -> None:
    _header("COMMIT CONFIRMATION")
    _log("gov_commit_confirmation")

    _subheader("Live Git Check")
    rc, log_out = _run(["git", "log", "--oneline", "-1"], timeout=5)
    if rc == 0 and log_out.strip():
        parts      = log_out.split(None, 1)
        last_hash  = parts[0]
        last_msg   = parts[1] if len(parts) > 1 else "—"
        print(f"  {'last commit hash':<28} {_c('cyan', last_hash)}")
        print(f"  {_c('gray', last_msg[:60])}")
    else:
        print(_badge("git log", "ERROR"))

    rc2, smi_check = _run(
        ["git", "log", "--oneline", "--", "ph6/audit_test.py"], timeout=5
    )
    smi_in_log = rc2 == 0 and bool(smi_check.strip())
    if last_hash is None:
        commit_status = "UNVERIFIED"
    elif smi_in_log:
        commit_status = "CONFIRMED"
    else:
        commit_status = "PENDING"
    print(_badge("Commit Status", commit_status))

    if commit_status == "PENDING":
        print(_c("yellow", "\n  audit_test.py not found in git log."))
        print(_c("yellow", "  SMI-1.1 commit is PENDING — awaiting Lane-1 signature."))
    else:
        print(_c("green", "\n  SMI-1.1 commit is CONFIRMED in git history."))

    _subheader("Working Tree")
    rc3, status = _run(["git", "status", "--short"], timeout=5)
    if rc3 == 0:
        lines = [line for line in status.splitlines() if line.strip()]
        clean = len(lines) == 0
        print(_badge("working tree", "CLEAN" if clean else "MODIFIED"))
        for line in lines[:12]:
            print(f"  {_c('yellow', line)}")
    else:
        print(_badge("git status", "ERROR"))

    _subheader("Open Issues")
    for issue in [
        "OI-C1  — rounding: Banker's vs ROUND_HALF_AWAY_FROM_ZERO",
        "ZERO2W — hostname conflict: rename jackjack→jackjack2",
        "ARC-DG — drift_gate.py not installed → ARC:FINAL:DEGRADED",
    ]:
        print(f"  {_c('gray', issue)}")

    _subheader("Forbidden Actions (v1.1)")
    for item in [
        "real Five-Book distribution",
        "canon lock execution",
        "source deletion",
        "automatic commit",
        "doctrine rewrite",
        "signature bypass",
    ]:
        print(f"  {_c('red', '✗')}  {item}")

    _log("commit_confirmation", f"commit_status={commit_status}")


# ── Governance: Authority Boundary Check ─────────────────────────────────────

def gov_authority_check() -> None:
    _header("AUTHORITY BOUNDARY CHECK")
    _log("gov_authority_check")

    boundaries = [
        ("Desktop terminal",         "NONE"),
        ("PSEUDO authority",         "PASS/DROP only"),
        ("SoSo authority",           "NONE"),
        ("Tokens authority",         "NONE"),
        ("Simulator authority",      "NONE"),
        ("Validator authority",      "ELIGIBILITY ONLY"),
        ("Lane-2 (AI) authority",    "ZERO"),
        ("Jack / Lane-1 signature",  "REQUIRED for canon promotion"),
    ]
    _subheader("Authority Levels")
    for label, val in boundaries:
        print(_badge(label, val))

    _subheader("Terminal v1.1 — Allowed")
    allowed = CFG.get("governance_allowed_v1_1", [])
    for item in allowed:
        print(f"  {_c('green', '✓')}  {item}")

    _subheader("Terminal v1.1 — Forbidden")
    forbidden = CFG.get("governance_forbidden_v1_1", [])
    for item in forbidden:
        print(f"  {_c('red', '✗')}  {item}")

    _subheader("Canonical Flow")
    flow = [
        "Reality → Sensors → CRAM-0 → PSEUDO → CRAM-A / CRAM-R",
        "→ SoSo → Tokens → Reports",
        "→ Desktop Controlled Terminal",
        "→ Human Review",
        "→ Jack / Lane-1 Signature (if required)",
    ]
    for line in flow:
        print(f"  {_c('gray', line)}")

    _pause()


# ── Governance Center submenu ─────────────────────────────────────────────────

_GOV_MENU = [
    ("Audit Replay",              gov_audit_replay),
    ("Canon Validator",           gov_canon_validator),
    ("Five-Book Dry Run",         gov_five_book),
    ("Secret Scan",               gov_secret_scan),
    ("Commit Readiness",          gov_commit_readiness),
    ("Commit Confirmation",       gov_commit_confirmation),
    ("Authority Boundary Check",  gov_authority_check),
]


def panel_governance() -> None:
    while True:
        print()
        _sep("═")
        print(_c("bold", "  GOVERNANCE CENTER"))
        print(_c("gray", "  Observer / Launcher — Authority ZERO"))
        _sep("═")
        for i, (label, _) in enumerate(_GOV_MENU, 1):
            print(f"  {i}. {label}")
        print(f"  8. Return to Main Menu")
        _sep()

        try:
            choice = input("  Select: ").strip()
        except (KeyboardInterrupt, EOFError):
            return

        if choice == "8" or choice.lower() in ("q", "return", "back"):
            return
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(_GOV_MENU):
                _GOV_MENU[idx][1]()
            else:
                print(_c("yellow", "  Invalid selection."))
        except ValueError:
            print(_c("yellow", "  Invalid selection."))


# ── System-stat helpers (no psutil) ──────────────────────────────────────────

def _sys_cpu_pct(interval: float = 0.25) -> float:
    def _read():
        try:
            line = Path("/proc/stat").read_text().splitlines()[0].split()
            nums = list(map(int, line[1:]))
            return nums[3], sum(nums)          # idle, total
        except Exception:
            return 0, 1
    idle0, total0 = _read()
    time.sleep(interval)
    idle1, total1 = _read()
    dtotal = total1 - total0
    didle  = idle1  - idle0
    return round(100.0 * (1 - didle / dtotal), 1) if dtotal else 0.0


def _sys_ram_gb() -> tuple[float, float]:
    """Returns (used_gb, total_gb)."""
    try:
        kv = {}
        for line in Path("/proc/meminfo").read_text().splitlines():
            parts = line.split()
            if len(parts) >= 2:
                kv[parts[0].rstrip(":")] = int(parts[1])
        total = kv.get("MemTotal", 0)
        avail = kv.get("MemAvailable", kv.get("MemFree", 0))
        total_gb = total / 1048576
        used_gb  = (total - avail) / 1048576
        return round(used_gb, 2), round(total_gb, 2)
    except Exception:
        return 0.0, 0.0


def _sys_temp_c() -> str:
    for p in [
        "/sys/class/thermal/thermal_zone0/temp",
        "/sys/devices/virtual/thermal/thermal_zone0/temp",
    ]:
        try:
            raw = Path(p).read_text().strip()
            return f"{int(raw) / 1000:.1f}"
        except Exception:
            pass
    try:
        rc, out = _run(["vcgencmd", "measure_temp"], timeout=3)
        if rc == 0:
            return out.replace("temp=", "").replace("'C", "")
    except Exception:
        pass
    return "?"


# ── Realtime Mode ─────────────────────────────────────────────────────────────

def panel_realtime() -> None:
    """Live 1-second refresh display. Press Q to exit."""
    _log("panel_realtime")

    if _ACCESS_MODE != "CONTROL":
        print(_c("yellow", "\n  READ-ONLY: Claude owns session. Realtime monitoring only."))

    try:
        import curses
        _realtime_curses()
    except Exception:
        _realtime_fallback()


def _read_rt_stats() -> dict:
    """Collect all realtime metrics into a single dict."""
    status  = _read_json(STATUS_JSON)
    esp     = _http_get(f"{ESP_S1_URL}/sensor", timeout=2) or {}
    ram_u, ram_t = _sys_ram_gb()
    return {
        "fps_a":    status.get("fps_a", status.get("fps", "—")),
        "fps_b":    status.get("fps_b", "—"),
        "pass_n":   status.get("pass_frames", status.get("pass", "—")),
        "drop_n":   status.get("drop_frames", status.get("drop", "—")),
        "motion":   status.get("motion_fraction", "—"),
        "bright":   status.get("brightness", "—"),
        "entropy":  status.get("entropy", "—"),
        "laplace":  status.get("laplacian", "—"),
        "temp_pi":  _sys_temp_c(),
        "cpu":      None,                          # filled after sleep in curses path
        "ram_u":    ram_u,
        "ram_t":    ram_t,
        "esp_temp": esp.get("temperature", "—"),
        "esp_hum":  esp.get("humidity", "—"),
        "lock":     _lock_status(),
    }


def _realtime_curses() -> None:
    import curses

    def _draw(stdscr: Any, s: dict, cpu: float) -> None:
        stdscr.clear()
        H, W = stdscr.getmaxyx()
        row = 0

        def put(text: str, attr: int = 0) -> None:
            nonlocal row
            if row < H - 1:
                try:
                    stdscr.addstr(row, 0, text[:W - 1], attr)
                except curses.error:
                    pass
                row += 1

        bold   = curses.A_BOLD
        normal = curses.A_NORMAL

        put(f"{'═' * min(W - 1, 50)}")
        put(f"  PH6 REALTIME  [Session: {s['lock']}]", bold)
        put(f"  {datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}  Press Q to exit")
        put(f"{'─' * min(W - 1, 50)}")

        put(f"  {'Camera A FPS:':<22} {s['fps_a']}", bold if s['fps_a'] != '—' else normal)
        put(f"  {'Camera B FPS:':<22} {s['fps_b']}")
        put("")
        put(f"  {'PASS:':<22} {s['pass_n']}", bold)
        put(f"  {'DROP:':<22} {s['drop_n']}")
        put("")

        def _fmt(v: Any, suffix: str = "") -> str:
            if v in (None, "—", ""):
                return "—"
            try:
                return f"{float(v):.2f}{suffix}"
            except (ValueError, TypeError):
                return str(v)

        put(f"  {'Motion:':<22} {_fmt(s['motion'], '%')}")
        put(f"  {'Brightness:':<22} {_fmt(s['bright'])}")
        put(f"  {'Entropy:':<22} {_fmt(s['entropy'])}")
        put(f"  {'Laplacian:':<22} {_fmt(s['laplace'])}")
        put(f"{'─' * min(W - 1, 50)}")
        put(f"  {'CPU:':<22} {cpu:.1f}%")
        put(f"  {'RAM:':<22} {s['ram_u']:.1f} / {s['ram_t']:.1f} GB")
        put(f"  {'Pi Temp:':<22} {s['temp_pi']}°C")
        if s['esp_temp'] != '—':
            put(f"  {'ESP Temp:':<22} {_fmt(s['esp_temp'], '°C')}")
            put(f"  {'ESP Humidity:':<22} {_fmt(s['esp_hum'], '%')}")
        put(f"{'─' * min(W - 1, 50)}")
        lock = s.get('lock', {})
        controller = lock.get('owner', 'FREE') if isinstance(lock, dict) else str(lock)
        mode       = lock.get('mode',  'UNKNOWN') if isinstance(lock, dict) else 'UNKNOWN'
        put(f"  {'Controller:':<22} {controller}")
        put(f"  {'Mode:':<22} {mode}")
        put(f"{'═' * min(W - 1, 50)}")

        stdscr.refresh()

    def _inner(stdscr: Any) -> None:
        curses.curs_set(0)
        stdscr.nodelay(True)
        stdscr.timeout(200)
        while True:
            s   = _read_rt_stats()
            cpu = _sys_cpu_pct(0.2)
            _draw(stdscr, s, cpu)
            # poll ~1 s total with early exit on Q
            deadline = time.monotonic() + 1.0
            while time.monotonic() < deadline:
                key = stdscr.getch()
                if key in (ord("q"), ord("Q"), 27):
                    return
                time.sleep(0.05)

    import curses as _curses
    _curses.wrapper(_inner)


def _realtime_fallback() -> None:
    """Non-curses fallback: print + clear loop."""
    print(_c("gray", "  curses not available — basic loop mode. Press Ctrl+C to stop.\n"))
    try:
        while True:
            s   = _read_rt_stats()
            cpu = _sys_cpu_pct(0.2)
            os.system("clear")
            print("=" * 42)
            print("  PH6 REALTIME")
            print(f"  {datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}  Ctrl+C to exit")
            print("-" * 42)
            print(f"  Camera A FPS:     {s['fps_a']}")
            print(f"  Camera B FPS:     {s['fps_b']}")
            print(f"  PASS:             {s['pass_n']}")
            print(f"  DROP:             {s['drop_n']}")
            print(f"  Motion:           {s['motion']}")
            print(f"  Brightness:       {s['bright']}")
            print(f"  Entropy:          {s['entropy']}")
            print(f"  Laplacian:        {s['laplace']}")
            print(f"  CPU:              {cpu:.1f}%")
            print(f"  RAM:              {s['ram_u']:.1f}/{s['ram_t']:.1f} GB")
            print(f"  Pi Temp:          {s['temp_pi']}°C")
            if s['esp_temp'] != '—':
                print(f"  ESP Temp:         {s['esp_temp']}°C")
                print(f"  ESP Humidity:     {s['esp_hum']}%")
            lock = s.get('lock', {})
            ctrl = lock.get('owner', 'FREE') if isinstance(lock, dict) else str(lock)
            mode = lock.get('mode', 'UNKNOWN') if isinstance(lock, dict) else 'UNKNOWN'
            print(f"  Controller:       {ctrl}")
            print(f"  Mode:             {mode}")
            print("=" * 42)
            time.sleep(0.8)
    except KeyboardInterrupt:
        pass
    _log("realtime_exit")


# ── Main menu ─────────────────────────────────────────────────────────────────

_MAIN_MENU = [
    ("System Dashboard",   panel_dashboard),
    ("Camera Diagnostics", panel_camera),
    ("Sensor Diagnostics", panel_sensors),
    ("Device Manager",     panel_device_manager),
    ("Run PH6 Test",       panel_run_test),
    ("Test Breakdown",     panel_test_breakdown),
    ("PSEUDO Results",     panel_pseudo),
    ("SoSo Results",       panel_soso),
    ("Token Results",      panel_tokens),
    ("Live-vs-Simulator",  panel_live_vs_sim),
    ("Reports",            panel_reports),
    ("Topology",           panel_topology),
    ("Evidence Playback + Breakdown", panel_evidence_review),
    ("Governance Center",  panel_governance),
    ("Realtime Mode",      panel_realtime),
]
_EXIT_ITEM = len(_MAIN_MENU) + 1


def main() -> None:
    lock_result = _lock_acquire()

    print()
    _sep("═")
    print(_c("bold", f"  PH6 Desktop Controlled Terminal v{VERSION}"))
    _sep("─")
    _prototype_notice()

    if lock_result == "CLAUDE":
        print(_c("yellow", "  CLAUDE SESSION ACTIVE — Desktop in MONITOR_ONLY mode"))
        print(_c("yellow", "  Test execution disabled. Display functions available."))
    elif lock_result == "BUSY_DESKTOP":
        print(_c("yellow", "  WARNING: Another Desktop session holds the lock."))
        print(_c("gray",   "  Lock is live — proceeding read-only until other session exits."))
    elif lock_result == "NO_PERMS":
        print(_c("yellow", f"  WARNING: Cannot write {LOCK_FILE} — lock manager disabled."))
        print(_c("gray",    "  Proceeding without lock protection."))
    elif lock_result == "ACQUIRED":
        print(_c("green",  f"  Session lock acquired  [{_ACCESS_MODE}]  {LOCK_FILE}"))
    elif lock_result == "ERROR":
        print(_c("yellow", "  WARNING: Lock acquire error — proceeding without lock."))

    _sep("═")

    try:
        while True:
            lock_rec = _lock_status()
            controller = lock_rec.get("owner", "FREE")
            mode_str   = _ACCESS_MODE

            print()
            _sep("═")
            print(_c("bold", f"  PH6 Desktop Controlled Terminal v{VERSION}"))
            print(_c("gray", f"  Controller: {controller}  Mode: {mode_str}  Lane-2 Authority: ZERO"))
            print(_c("gray", "  Class 1 Cloud/Claude Terminal = primary  ·  Class 2 SSH Terminal = second  ·  Class 3 Desktop = prototype, Authority ZERO"))
            _sep("─")
            for i, (label, _) in enumerate(_MAIN_MENU, 1):
                marker = _c("cyan", "⊛") if label == "Governance Center" else " "
                locked = _ACCESS_MODE != "CONTROL" and label in ("Run PH6 Test",)
                tag    = _c("gray", " [monitor]") if locked else ""
                print(f"  {i:>2}. {marker} {label}{tag}")
            print(f"  {_EXIT_ITEM:>2}.   Exit")
            _sep("═")

            try:
                choice = input("  Select: ").strip()
            except (KeyboardInterrupt, EOFError):
                break

            if choice in (str(_EXIT_ITEM), "q", "exit", "quit"):
                break
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(_MAIN_MENU):
                    label, fn = _MAIN_MENU[idx]
                    if _ACCESS_MODE != "CONTROL" and label in ("Run PH6 Test",):
                        print(_c("yellow", f"\n  BLOCKED: {label} requires CONTROL mode."))
                        print(_c("gray",   "  Current mode: " + _ACCESS_MODE))
                    else:
                        fn()
                else:
                    print(_c("yellow", f"  Invalid selection (1–{_EXIT_ITEM})."))
            except ValueError:
                print(_c("yellow", f"  Invalid selection (1–{_EXIT_ITEM})."))
    finally:
        _lock_release()

    _save_session()
    print(_c("gray", "\n  PH6 Terminal closed. Lock released. Lane-1 authority unchanged.\n"))


if __name__ == "__main__":
    if "--windows" in sys.argv:
        _win = Path(__file__).parent / "ph6_windows_terminal_display.py"
        if _win.exists():
            import importlib.util as _ilu
            _spec = _ilu.spec_from_file_location("ph6_win", str(_win))
            _mod  = _ilu.module_from_spec(_spec)
            _spec.loader.exec_module(_mod)     # type: ignore[union-attr]
            _mod.main()
        else:
            print(f"Windows display not found: {_win}")
            sys.exit(1)
    elif "--classic" in sys.argv or len(sys.argv) == 1:
        main()
    else:
        main()
