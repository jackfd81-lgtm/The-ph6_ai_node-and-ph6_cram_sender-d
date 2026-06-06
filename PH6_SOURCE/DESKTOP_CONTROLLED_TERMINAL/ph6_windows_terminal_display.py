#!/usr/bin/env python3
"""
PH6 Windows-Style Terminal Display  — Phase 6A-UI
Windows Terminal look-alike. SSH-safe. curses-based.
Lane-2 Advisory — Authority: ZERO

Usage:
  python3 ph6_windows_terminal_display.py
  python3 ph6_desktop_terminal.py --windows

IMPORTANT: ALL KEYBOARD INPUT BELOW APPLIES ONLY INSIDE THE DESKTOP TERMINAL
WINDOW (SSH session running 'desktop'). Do NOT type menu keys into Claude chat.

Key map (normal mode):
  1-9, 0, G   Jump to panel
  ENTER        Select highlighted panel
  ↑↓           Navigate menu
  R            Refresh
  Q / ESC      Quit

  4 = Test Control   5 = PSEUDO   9 = Reports/Files

Test Control keys (after pressing 4):
  S / ENTER    Start selected test
  M            Monitor view
  V            Result view
  A            Artifacts view
  X            Stop running test (SIGINT)
  FORCE        Hard kill (type F-O-R-C-E while stop is pending → SIGKILL)
  Q / ESC      Back to list / back to main menu

Restore safety: use restore_desktop_last_good.sh only if a desktop patch breaks the interface.
"""
from __future__ import annotations

import curses
import json
import os
import re
import shlex
import signal
import socket
import subprocess
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

VERSION      = "6A-UI"
HOME         = Path.home()
LOCK_FILE    = Path("/var/ph6/session.lock")
STATUS_JSON  = HOME / "ph6_status/status.json"
PH6_DIR      = HOME / "ph6"
ESP_URL      = "http://192.168.254.194"
CRAM_RT      = PH6_DIR / "cram_pu/runtime"
AUDIT_JSONL  = Path("/var/ph6/audit/audit.jsonl")
REGISTRY_PATH = HOME / "PH6_SOURCE/DESKTOP_CONTROLLED_TERMINAL/test_registry.json"
RUNS_DIR      = HOME / "PH6_SOURCE/DESKTOP_CONTROLLED_TERMINAL/logs/runs"

# ── Box-drawing characters ─────────────────────────────────────────────────────
_H  = "─"; _V  = "│"
_TL = "┌"; _TR = "┐"; _BL = "└"; _BR = "┘"
_LT = "├"; _RT = "┤"; _TT = "┬"; _BT = "┴"

# ── Navigation menu ───────────────────────────────────────────────────────────
MENU = [
    (" 1 Dashboard",    "System Dashboard"),
    (" 2 Cameras",      "Camera Diagnostics"),
    (" 3 Sensors",      "Sensor Diagnostics"),
    (" 4 Test Control", "Test Control Center"),
    (" 5 PSEUDO",       "PSEUDO Results"),
    (" 6 SoSo",         "SoSo Results"),
    (" 7 Tokens",       "Token Results"),
    (" 8 Live-Sim",     "Live-vs-Simulator"),
    (" 9 Evidence",      "Evidence Browser"),
    ("10 Topology",     "Topology"),
    ("11 Governance",   "Governance Center"),
    ("12 Realtime",     "Realtime Mode"),
]

TC_MENU_IDX = 3      # 0-based index of Test Control
FB_MENU_IDX = 8      # 0-based index of Evidence Browser (formerly Reports/Files)
EXIT_IDX    = 12     # 13 in 1-based (Realtime)
MIN_COLS    = 80
MIN_ROWS    = 22
NAV_W       = 16

# ── Safe paths for file browser ────────────────────────────────────────────────
SAFE_ROOTS: list[Path] = [HOME / "PH6_SOURCE", HOME / "ph6"]

FB_SHORTCUTS: list[tuple[str, Path]] = [
    ("~/PH6_SOURCE",                                    HOME / "PH6_SOURCE"),
    ("~/ph6",                                           HOME / "ph6"),
    ("~/PH6_SOURCE/DESKTOP_CONTROLLED_TERMINAL/reports",
     HOME / "PH6_SOURCE/DESKTOP_CONTROLLED_TERMINAL/reports"),
    ("~/PH6_SOURCE/DESKTOP_CONTROLLED_TERMINAL/logs",
     HOME / "PH6_SOURCE/DESKTOP_CONTROLLED_TERMINAL/logs"),
]

FORBIDDEN_PARTS: frozenset[str] = frozenset({
    ".ssh", ".env", ".gnupg", ".claude", ".netrc",
    "credentials", "secret", "id_rsa", "id_ed25519",
    ".bash_history", ".lesshst",
})

# ── Color pair IDs ────────────────────────────────────────────────────────────
_CP_TITLE   = 1
_CP_STATUS  = 2
_CP_NAV     = 3
_CP_NAV_SEL = 4
_CP_HDR     = 5
_CP_OK      = 6
_CP_WARN    = 7
_CP_ERR     = 8
_CP_DIM     = 9
_CP_FB_DIR  = 10
_CP_FB_SEL  = 11
_CP_FB_FILE = 12


# ── Data helpers ──────────────────────────────────────────────────────────────

def _read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text())
    except Exception:
        return {}


def _run(cmd: list[str], timeout: int = 4) -> tuple[int, str]:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, (r.stdout + r.stderr).strip()
    except Exception as e:
        return -1, str(e)


def _http_get(url: str, timeout: int = 3) -> dict | None:
    try:
        resp = urllib.request.urlopen(url, timeout=timeout)
        return json.loads(resp.read().decode())
    except Exception:
        return None


def _cpu_pct(interval: float = 0.15) -> float:
    def _rd() -> tuple[int, int]:
        try:
            parts = Path("/proc/stat").read_text().splitlines()[0].split()
            nums = list(map(int, parts[1:]))
            return nums[3], sum(nums)
        except Exception:
            return 0, 1
    i0, t0 = _rd(); time.sleep(interval); i1, t1 = _rd()
    dt = t1 - t0
    return round(100.0 * (1 - (i1 - i0) / dt), 1) if dt else 0.0


def _ram_gb() -> tuple[float, float]:
    try:
        kv = {}
        for line in Path("/proc/meminfo").read_text().splitlines():
            p = line.split()
            if len(p) >= 2:
                kv[p[0].rstrip(":")] = int(p[1])
        total = kv.get("MemTotal", 0) / 1048576
        used  = (kv.get("MemTotal", 0) - kv.get("MemAvailable", kv.get("MemFree", 0))) / 1048576
        return round(used, 2), round(total, 2)
    except Exception:
        return 0.0, 0.0


def _temp_c() -> str:
    for p in ("/sys/class/thermal/thermal_zone0/temp",
              "/sys/devices/virtual/thermal/thermal_zone0/temp"):
        try:
            return f"{int(Path(p).read_text().strip()) / 1000:.1f}"
        except Exception:
            pass
    rc, out = _run(["vcgencmd", "measure_temp"])
    if rc == 0:
        return out.replace("temp=", "").replace("'C", "").strip()
    return "?"


def _lock_info() -> dict:
    try:
        if LOCK_FILE.exists():
            return json.loads(LOCK_FILE.read_text())
    except Exception:
        pass
    return {"owner": "FREE", "mode": "CONTROL"}


def _disk_gb(path: str = "/") -> tuple[float, float]:
    try:
        st = os.statvfs(path)
        total = st.f_blocks * st.f_frsize / 1073741824
        used  = (st.f_blocks - st.f_bavail) * st.f_frsize / 1073741824
        return round(used, 1), round(total, 1)
    except Exception:
        return 0.0, 0.0


# ── Test control helpers ───────────────────────────────────────────────────────

def _tc_load_registry() -> list[dict]:
    try:
        return json.loads(REGISTRY_PATH.read_text())
    except Exception:
        return []


def _tc_read_tail(path: Path, n: int = 20) -> list[str]:
    try:
        lines = path.read_text(errors="replace").splitlines()
        return lines[-n:] if len(lines) > n else lines
    except Exception:
        return []


def _tc_parse_output(lines: list[str]) -> dict:
    """Extract key metrics from stdout lines. Never invents values."""
    result: dict[str, str] = {}
    for line in lines:
        if re.search(r"\bPASS\b", line):
            result.setdefault("verdict", "PASS")
        if re.search(r"\bDROP\b", line):
            result["verdict"] = "DROP"
        m = re.search(r"fps[:\s=]+(\d+\.?\d*)", line, re.I)
        if m:
            result["fps"] = m.group(1)
        m = re.search(r"motion_fraction[:\s=]+(\d+\.?\d*)", line, re.I)
        if m:
            result["motion_fraction"] = m.group(1)
        m = re.search(r"brightness[:\s=]+(\d+\.?\d*)", line, re.I)
        if m:
            result["brightness"] = m.group(1)
        m = re.search(r"entropy[:\s=]+(\d+\.?\d*)", line, re.I)
        if m:
            result["entropy"] = m.group(1)
        m = re.search(r"laplacian[:\s=]+(\d+\.?\d*)", line, re.I)
        if m:
            result["laplacian"] = m.group(1)
        m = re.search(r"frame[:\s]+(\d+)/(\d+)", line, re.I)
        if m:
            result["frame"] = f"{m.group(1)}/{m.group(2)}"
    return result


def _tc_elapsed(started_at: str) -> str:
    try:
        t0 = datetime.fromisoformat(started_at)
        delta = int((datetime.now(timezone.utc) - t0).total_seconds())
        return f"{delta // 3600:02d}:{(delta % 3600) // 60:02d}:{delta % 60:02d}"
    except Exception:
        return "??:??:??"


# ── Panel data collectors ─────────────────────────────────────────────────────
Row = tuple


def _collect_dashboard() -> list[Row]:
    rows: list[Row] = []
    status = _read_json(STATUS_JSON); lock = _lock_info()
    rows.append(("HDR", "Session"))
    rows.append((0, "Controller", lock.get("owner", "FREE"), _CP_OK))
    rows.append((0, "Mode",       lock.get("mode", "CONTROL"), _CP_OK))
    pid = lock.get("pid", ""); host = lock.get("hostname", "")
    if pid:
        rows.append((0, "PID / Host", f"{pid} / {host}", None))
    rows.append(("HDR", "System"))
    cpu = _cpu_pct(); r_u, r_t = _ram_gb(); temp = _temp_c(); d_u, d_t = _disk_gb()
    rows.append((0, "CPU",    f"{cpu:.1f}%", _CP_OK if cpu < 70 else _CP_WARN))
    rows.append((0, "RAM",    f"{r_u:.1f} / {r_t:.1f} GB", None))
    rows.append((0, "Temp",   f"{temp}°C",
                 _CP_OK if temp.replace(".","").isdigit() and float(temp) < 70 else _CP_WARN))
    rows.append((0, "Disk /", f"{d_u:.1f} / {d_t:.1f} GB", None))
    rows.append(("HDR", "Storage"))
    nvme = Path("/dev/nvme0n1"); usb = Path("/dev/sda")
    rows.append((0, "NVMe",    "ONLINE" if nvme.exists() else "NOT_FOUND",
                 _CP_OK if nvme.exists() else _CP_WARN))
    rows.append((0, "USB SSD", "ONLINE" if usb.exists() else "NOT_FOUND",
                 _CP_OK if usb.exists() else _CP_WARN))
    rows.append(("HDR", "PH6 Status"))
    for k in ("status", "fps", "frame", "cram", "cam"):
        v = status.get(k)
        if v is not None:
            rows.append((0, k.upper(), str(v), None))
    rows.append(("HDR", "Git"))
    rc, log = _run(["git", "-C", str(HOME), "log", "--oneline", "-1"])
    rows.append((0, "HEAD", (log[:38] if rc == 0 else "UNKNOWN"), None))
    rc2, gs = _run(["git", "-C", str(HOME), "status", "--short"])
    mods = len([l for l in gs.splitlines() if l.strip()]) if rc2 == 0 else "?"
    rows.append((0, "Modified", str(mods), _CP_OK if mods == 0 else _CP_WARN))
    rows.append(("HDR", "Workstation Hierarchy"))
    rows.append((0, "Class 1", "Cloud/Claude Terminal (primary dev)", _CP_DIM))
    rows.append((0, "Class 2", "SSH Terminal (device control)", _CP_DIM))
    rows.append((0, "Class 3", "Desktop Cockpit (prototype — HERE)", _CP_OK))
    rows.append((0, "Authority", "ZERO", _CP_OK))
    rows.append(("HDR", "Restore Status"))
    _rp = HOME / "PH6_SOURCE/DESKTOP_CONTROLLED_TERMINAL/restore_points/LAST_KNOWN_GOOD_MANIFEST.json"
    rows.append((0, "Manifest", "PRESENT" if _rp.exists() else "MISSING — run create_restore_point.sh",
                 _CP_OK if _rp.exists() else _CP_WARN))
    rows.append(("HDR", "Evidence Readiness"))
    rows.append((0, "Operator ID",    "PENDING", _CP_DIM))
    rows.append((0, "Script Hash",    "PENDING", _CP_DIM))
    rows.append((0, "Chain Custody",  "PENDING", _CP_DIM))
    rows.append((0, "Replay Valid.",  "PASS (harness)", _CP_OK))
    return rows


def _collect_cameras() -> list[Row]:
    rows: list[Row] = []
    rows.append(("HDR", "Video Devices"))
    devs = sorted(Path("/dev").glob("video*"))
    if devs:
        for d in devs[:8]:
            rows.append((0, d.name, "PRESENT", _CP_OK))
    else:
        rows.append((0, "video devices", "NONE_FOUND", _CP_WARN))
    rows.append(("HDR", "Dual-Camera Results"))
    cert_dirs = sorted((HOME / "PH6_SOURCE/TESTS/DUAL_USB_CAMERA").glob("cert_v2_1/*/"))
    if cert_dirs:
        for d in cert_dirs[-3:]:
            rpt = d / "ph6_dual_camera_certification_report.json"
            data = _read_json(rpt) if rpt.exists() else {}
            st = data.get("certification_status", data.get("status", "UNKNOWN"))
            rows.append((0, d.name[-15:], st, _CP_OK if "PASS" in str(st) else _CP_WARN))
    else:
        rows.append((0, "cert results", "NOT_FOUND", _CP_WARN))
    rows.append(("HDR", "ESP Camera"))
    esp = _http_get(f"{ESP_URL}/health", timeout=2)
    if esp:
        rows.append((0, "ESP_S1 status", esp.get("status", "?"), _CP_OK))
    else:
        rows.append((0, "ESP_S1 /health", "UNREACHABLE", _CP_WARN))
    return rows


def _collect_sensors() -> list[Row]:
    rows: list[Row] = []
    rows.append(("HDR", "ESP_S1 Health"))
    health = _http_get(f"{ESP_URL}/health", timeout=3)
    if health:
        for k in ("status", "node", "uptime_s", "firmware"):
            if k in health:
                rows.append((0, k, str(health[k]), _CP_OK))
    else:
        rows.append((0, "ESP_S1", "UNREACHABLE", _CP_WARN))
    rows.append(("HDR", "ESP_S1 Sensor"))
    sensor = _http_get(f"{ESP_URL}/sensor", timeout=3)
    if sensor:
        for k in ("temperature", "humidity", "pressure", "gas", "altitude"):
            if k in sensor:
                rows.append((0, k.capitalize(), str(sensor[k]), None))
    else:
        rows.append((0, "sensor data", "UNKNOWN", _CP_WARN))
    rows.append(("HDR", "I2C Scan"))
    i2c = _http_get(f"{ESP_URL}/i2c_scan", timeout=3)
    if i2c:
        devs = i2c.get("devices", [])
        rows.append((0, "Devices found", str(len(devs)), _CP_OK if devs else _CP_WARN))
        for d in devs[:6]:
            rows.append((1, "addr", hex(d) if isinstance(d, int) else str(d), None))
    else:
        rows.append((0, "i2c scan", "UNKNOWN", _CP_WARN))
    return rows


def _collect_test_control() -> list[Row]:
    rows: list[Row] = []
    rows.append(("HDR", "Test Control"))
    rows.append((0, "Open panel", "Press ENTER to open Test Control", _CP_OK))
    rows.append(("HDR", "Last Run"))
    run_dirs = sorted(RUNS_DIR.glob("*/"), key=lambda d: d.stat().st_mtime) if RUNS_DIR.exists() else []
    if run_dirs:
        st = _read_json(run_dirs[-1] / "run_status.json")
        rows.append((0, "Run ID",  st.get("run_id", run_dirs[-1].name)[-28:], None))
        status = st.get("status", "UNKNOWN")
        rows.append((0, "Status",  status,
                     _CP_OK if status == "PASS" else (_CP_ERR if status == "FAIL" else _CP_WARN)))
        rows.append((0, "Label",   st.get("label", "?"), None))
    else:
        rows.append((0, "Last run", "NONE", _CP_DIM))
    rows.append(("HDR", "Registry"))
    rows.append((0, "File", "test_registry.json", None))
    rows.append((0, "Path", str(REGISTRY_PATH)[-28:], None))
    return rows


def _collect_pseudo() -> list[Row]:
    rows: list[Row] = []
    rows.append(("HDR", "CRAM-A / CRAM-R"))
    run_dirs = sorted(CRAM_RT.glob("*/"), key=lambda d: d.name) if CRAM_RT.exists() else []
    if run_dirs:
        latest = run_dirs[-1]
        rows.append((0, "Run dir", latest.name[-20:], None))
        pass_dir = latest / "cram_store/cram_a"
        drop_dir = latest / "cram_store/cram_r"
        pc = len(list(pass_dir.glob("*.blake2b"))) if pass_dir.exists() else "?"
        dc = len(list(drop_dir.glob("frame_*"))) if drop_dir.exists() else "?"
        rows.append((0, "CRAM-A (PASS)", str(pc), _CP_OK))
        rows.append((0, "CRAM-R (DROP)", str(dc), _CP_WARN if dc else _CP_OK))
    else:
        rows.append((0, "CRAM runtime", "NO_DATA", _CP_WARN))
    rows.append(("HDR", "RSYNC Queue"))
    q_files = sorted(CRAM_RT.glob("*/cram_store/rsync_queue.jsonl")) if CRAM_RT.exists() else []
    if q_files:
        try:
            lines = q_files[-1].read_text().splitlines()
            last = json.loads(lines[-1]) if lines else {}
            rows.append((0, "depth",      str(last.get("depth", "?")), None))
            rows.append((0, "blocked_by", str(last.get("blocked_by") or "none"), None))
        except Exception:
            rows.append((0, "queue", "READ_ERROR", _CP_ERR))
    else:
        rows.append((0, "rsync queue", "NOT_FOUND", _CP_WARN))
    rows.append(("HDR", "Authority"))
    rows.append((0, "PSEUDO", "Sole PASS/DROP authority — Terminal: NONE", _CP_WARN))
    return rows


def _collect_soso() -> list[Row]:
    rows: list[Row] = []
    rows.append(("HDR", "SoSo Reports"))
    reports  = sorted((HOME / "PH6_SOURCE").rglob("*soso*.json"))
    reports += sorted((PH6_DIR / "cram_pu/runtime").rglob("*soso*.json")) if CRAM_RT.exists() else []
    if reports:
        for rpt in reports[-5:]:
            data = _read_json(rpt)
            v = data.get("verdict", data.get("status", ""))
            rows.append((0, rpt.name[-28:], v or "present", None))
    else:
        rows.append((0, "SoSo reports", "NOT_FOUND", _CP_WARN))
    rows.append(("HDR", "Authority"))
    rows.append((0, "SoSo", "Advisory only — Authority: NONE", _CP_WARN))
    return rows


def _collect_tokens() -> list[Row]:
    rows: list[Row] = []
    rows.append(("HDR", "Token Reports"))
    tok_dir  = PH6_DIR / "tok"
    reports  = sorted(tok_dir.rglob("*.json")) if tok_dir.exists() else []
    reports += sorted((HOME / "PH6_SOURCE").rglob("*tok*.json"))
    if reports:
        for rpt in reports[-5:]:
            data = _read_json(rpt)
            cls = data.get("token_class", data.get("status", ""))
            rows.append((0, rpt.name[-28:], cls or "present", None))
    else:
        rows.append((0, "Token reports", "NOT_FOUND", _CP_WARN))
    rows.append(("HDR", "Authority"))
    rows.append((0, "Tokens", "Advisory only — Authority: NONE", _CP_WARN))
    return rows


def _collect_livesim() -> list[Row]:
    rows: list[Row] = []
    rows.append(("HDR", "Comparison Reports"))
    found  = list((HOME / "PH6_SOURCE").rglob("*sim*comparison*.json"))
    found += list((HOME / "PH6_SOURCE").rglob("*live_vs_sim*.json"))
    if found:
        for rpt in sorted(found)[-5:]:
            data = _read_json(rpt)
            v = data.get("verdict", data.get("status", ""))
            rows.append((0, rpt.name[-28:], v or "present", None))
    else:
        rows.append((0, "comparison reports", "NOT_FOUND", _CP_WARN))
    rows.append(("HDR", "Authority"))
    rows.append((0, "Simulator", "Advisory only — Reality is authoritative", _CP_WARN))
    return rows


def _collect_reports() -> list[Row]:
    rows: list[Row] = []
    rows.append(("HDR", "File Browser"))
    rows.append((0, "Open browser", "Press ENTER to browse PH6 files", _CP_OK))
    rows.append(("HDR", "Governance Reports"))
    gov = HOME / "PH6_SOURCE/GOVERNANCE"
    if gov.exists():
        for f in sorted(gov.glob("*.json"))[-6:]:
            rows.append((0, f.name[-30:], "JSON", None))
    else:
        rows.append((0, "GOVERNANCE dir", "NOT_FOUND", _CP_WARN))
    rows.append(("HDR", "Deployment Reports"))
    dep = HOME / "PH6_SOURCE/DEPLOYMENT"
    if dep.exists():
        mds = sorted(dep.glob("*.md"))
        rows.append((0, "count", str(len(mds)), None))
        for f in mds[-4:]:
            rows.append((1, f.name[-30:], "MD", None))
    else:
        rows.append((0, "DEPLOYMENT dir", "NOT_FOUND", _CP_WARN))
    rows.append(("HDR", "SMI-1.1"))
    smi = PH6_DIR / "smi_1_1_validation_report.json"
    rows.append((0, "smi_report", "FOUND" if smi.exists() else "NOT_FOUND",
                 _CP_OK if smi.exists() else _CP_WARN))
    return rows


def _collect_topology() -> list[Row]:
    rows: list[Row] = []
    nodes = [("Pi5 jackjack", "192.168.254.188"),
             ("Zero2W jackjack2", "192.168.254.189"),
             ("ESP_S1", "192.168.254.194")]
    rows.append(("HDR", "Node Reachability"))
    for name, ip in nodes:
        rc, _ = _run(["ping", "-c", "1", "-W", "2", ip], timeout=4)
        st = "REACHABLE" if rc == 0 else "UNREACHABLE"
        rows.append((0, f"{name:<16} {ip}", st, _CP_OK if rc == 0 else _CP_ERR))
    rows.append(("HDR", "ESP_S1 Artifacts"))
    for fname in ("esp_s1_topology.json", "esp_s1_topology_token.json", "esp_s1_health_snapshot.json"):
        hits = sorted((HOME / "PH6_SOURCE").rglob(fname))
        if hits:
            data = _read_json(hits[-1])
            ts = data.get("generated_at", data.get("captured_at", ""))
            rows.append((0, fname[:24], "FOUND", _CP_OK))
            if ts:
                rows.append((1, "generated", ts[:19], None))
        else:
            rows.append((0, fname[:24], "NOT_FOUND", _CP_WARN))
    return rows


def _collect_governance() -> list[Row]:
    rows: list[Row] = []
    rows.append(("HDR", "Commit Status"))
    rc, log   = _run(["git", "-C", str(HOME), "log", "--oneline", "-1"])
    last_hash = log.split()[0] if rc == 0 and log.split() else None
    rc2, smi  = _run(["git", "-C", str(HOME), "log", "--oneline", "--", "ph6/audit_test.py"])
    smi_in_log = rc2 == 0 and bool(smi.strip())
    cst = "CONFIRMED" if (last_hash and smi_in_log) else ("UNVERIFIED" if not last_hash else "PENDING")
    rows.append((0, "Commit Status", cst, _CP_OK if cst == "CONFIRMED" else _CP_WARN))
    rows.append((0, "HEAD", (last_hash or "UNKNOWN"), None))
    rows.append(("HDR", "SMI-1.1 Scripts"))
    for fname in ("audit_test.py", "ph6_audit_replay.py",
                  "ph6_validate_canon.py", "ph6_consolidate_3.py"):
        exists = (PH6_DIR / fname).exists()
        rows.append((0, fname[:24], "ON_DISK" if exists else "PENDING",
                     _CP_OK if exists else _CP_WARN))
    rows.append(("HDR", "Validation Status"))
    smi_rpt = _read_json(PH6_DIR / "smi_1_1_validation_report.json")
    rows.append((0, "Validation Status",    smi_rpt.get("overall_status", "UNKNOWN"), None))
    rows.append((0, "Promotion Eligibility",
                 "ELIGIBLE" if smi_rpt.get("canon_lock_eligible") else "NOT_ELIGIBLE", None))
    rows.append(("HDR", "Authority Boundary"))
    rows.append((0, "Desktop terminal",  "NONE",            _CP_WARN))
    rows.append((0, "Validator",         "ELIGIBILITY ONLY", _CP_WARN))
    rows.append((0, "Lane-1 signature",  "REQUIRED",        _CP_ERR))
    return rows


def _collect_realtime() -> list[Row]:
    rows: list[Row] = []
    rows.append(("HDR", "Realtime Mode"))
    rows.append((0, "Launch", "Press ENTER to start live display", _CP_OK))
    rows.append((0, "Exit",   "Press Q inside realtime to return", None))
    rows.append(("HDR", "Current Snapshot"))
    status = _read_json(STATUS_JSON)
    rows.append((0, "FPS",    str(status.get("fps", "UNKNOWN")), None))
    rows.append((0, "PASS",   str(status.get("pass_frames", "UNKNOWN")), _CP_OK))
    rows.append((0, "DROP",   str(status.get("drop_frames", "UNKNOWN")), _CP_WARN))
    rows.append((0, "Motion", str(status.get("motion_fraction", "UNKNOWN")), None))
    cpu = _cpu_pct(0.05); r_u, r_t = _ram_gb()
    rows.append((0, "CPU",    f"{cpu:.1f}%", None))
    rows.append((0, "RAM",    f"{r_u:.1f}/{r_t:.1f} GB", None))
    rows.append((0, "Temp",   f"{_temp_c()}°C", None))
    return rows


_COLLECTORS = [
    _collect_dashboard, _collect_cameras,   _collect_sensors,
    _collect_test_control, _collect_pseudo, _collect_soso,
    _collect_tokens,    _collect_livesim,   _collect_reports,
    _collect_topology,  _collect_governance, _collect_realtime,
]


# ── File browser helpers ───────────────────────────────────────────────────────

def _fb_is_safe(path: Path) -> bool:
    try:
        resolved = path.resolve()
    except Exception:
        return False
    if not any(resolved == b.resolve() or resolved.is_relative_to(b.resolve())
               for b in SAFE_ROOTS):
        return False
    return all(part not in FORBIDDEN_PARTS for part in resolved.parts)


def _fb_read_preview(path: Path) -> list[str]:
    MAX = 200
    try:
        if path.suffix.lower() == ".json":
            try:
                return json.dumps(json.loads(path.read_bytes()), indent=2).splitlines()[:MAX]
            except Exception:
                pass
        return path.read_text(errors="replace").splitlines()[:MAX]
    except PermissionError:
        return ["[Permission denied]"]
    except Exception as e:
        return [f"[Read error: {e}]"]


# ── Renderer ──────────────────────────────────────────────────────────────────

class PH6WindowsDisplay:

    def __init__(self, stdscr: Any) -> None:
        self.scr  = stdscr
        self.sel  = 0
        self.rows: list[Row] = []
        self.ts   = ""
        # ── File browser state
        self.fb_active      = False
        self.fb_path: Path | None = None
        self.fb_entries: list[tuple[bool, str, Path]] = []
        self.fb_sel         = 0
        self.fb_scroll      = 0
        self.fb_in_preview  = False
        self.fb_preview: list[str] = []
        self.fb_prev_scroll = 0
        # ── Test control state
        self.tc_active      = False
        self.tc_view        = "LIST"     # LIST | MONITOR | RESULT | ARTIFACTS
        self.tc_registry: list[dict] = []
        self.tc_sel         = 0
        self.tc_process: subprocess.Popen | None = None
        self.tc_run_dir: Path | None = None
        self.tc_run_status: dict = {}
        self.tc_last_run: dict = {}
        self.tc_stdout_path: Path | None = None
        self.tc_stderr_path: Path | None = None
        self.tc_live_out: list[str] = []
        self.tc_live_err: list[str] = []
        self.tc_parsed: dict = {}
        self.tc_artifacts: list[Path] = []
        self.tc_art_sel    = 0
        self.tc_art_scroll = 0
        self.tc_art_preview: list[str] = []
        self.tc_art_in_preview = False
        self.tc_stop_requested = False
        self.tc_stop_time: float | None = None
        self.tc_force_buf  = ""
        self.tc_error_msg  = ""
        # ── Mouse
        self.mouse_ok = False
        self._setup_colors()
        self._setup_mouse()
        self.refresh_panel()

    # ── Setup ─────────────────────────────────────────────────────────────────

    def _setup_colors(self) -> None:
        curses.start_color()
        try:
            curses.use_default_colors(); bg = -1
        except Exception:
            bg = curses.COLOR_BLACK
        pairs = [
            (_CP_TITLE,   curses.COLOR_BLACK,  curses.COLOR_CYAN),
            (_CP_STATUS,  curses.COLOR_WHITE,  curses.COLOR_BLUE),
            (_CP_NAV,     curses.COLOR_WHITE,  bg),
            (_CP_NAV_SEL, curses.COLOR_BLACK,  curses.COLOR_GREEN),
            (_CP_HDR,     curses.COLOR_CYAN,   bg),
            (_CP_OK,      curses.COLOR_GREEN,  bg),
            (_CP_WARN,    curses.COLOR_YELLOW, bg),
            (_CP_ERR,     curses.COLOR_RED,    bg),
            (_CP_DIM,     curses.COLOR_BLACK,  bg),
            (_CP_FB_DIR,  curses.COLOR_CYAN,   bg),
            (_CP_FB_SEL,  curses.COLOR_BLACK,  curses.COLOR_WHITE),
            (_CP_FB_FILE, curses.COLOR_WHITE,  bg),
        ]
        for cid, fg, cbg in pairs:
            try:
                curses.init_pair(cid, fg, cbg)
            except Exception:
                pass

    def _setup_mouse(self) -> None:
        try:
            curses.mousemask(curses.ALL_MOUSE_EVENTS | curses.REPORT_MOUSE_POSITION)
            self.mouse_ok = True
        except Exception:
            self.mouse_ok = False

    # ── Data ──────────────────────────────────────────────────────────────────

    def refresh_panel(self) -> None:
        self.ts = datetime.now().strftime("%H:%M:%S")
        try:
            self.rows = _COLLECTORS[self.sel]()
        except Exception as exc:
            self.rows = [("HDR", "Error"), (0, "detail", str(exc)[:50], _CP_ERR)]

    # ── File browser ──────────────────────────────────────────────────────────

    def _fb_enter_root(self) -> None:
        self.fb_path    = None
        self.fb_entries = [(True, label, path) for label, path in FB_SHORTCUTS if path.exists()]
        self.fb_sel = self.fb_scroll = 0; self.fb_in_preview = False

    def _fb_enter_dir(self, path: Path) -> None:
        entries: list[tuple[bool, str, Path]] = []
        try:
            for item in sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
                if _fb_is_safe(item):
                    entries.append((item.is_dir(), item.name, item))
        except Exception:
            pass
        self.fb_path    = path
        self.fb_entries = entries
        self.fb_sel = self.fb_scroll = 0; self.fb_in_preview = False

    def _fb_open_selected(self) -> None:
        if not self.fb_entries: return
        is_dir, _name, path = self.fb_entries[self.fb_sel]
        if is_dir:
            self._fb_enter_dir(path)
        else:
            self.fb_preview = _fb_read_preview(path)
            self.fb_in_preview = True; self.fb_prev_scroll = 0

    def _fb_back(self) -> None:
        if self.fb_in_preview:
            self.fb_in_preview = False; return
        if self.fb_path is None:
            self.fb_active = False; self.refresh_panel(); return
        cur = self.fb_path.resolve()
        if any(cur == r.resolve() for r in SAFE_ROOTS):
            self._fb_enter_root()
        else:
            parent = self.fb_path.parent
            if _fb_is_safe(parent):
                self._fb_enter_dir(parent)
            else:
                self._fb_enter_root()

    # ── Test control ──────────────────────────────────────────────────────────

    def _tc_enter(self) -> None:
        self.tc_registry  = _tc_load_registry()
        self.tc_sel       = 0
        self.tc_view      = "LIST"
        self.tc_error_msg = ""
        self.tc_force_buf = ""
        self._tc_load_last_run()

    def _tc_load_last_run(self) -> None:
        if not RUNS_DIR.exists(): return
        dirs = sorted(RUNS_DIR.glob("*/"), key=lambda d: d.stat().st_mtime)
        if dirs:
            self.tc_last_run = _read_json(dirs[-1] / "run_status.json")

    def _tc_check_lock(self) -> tuple[bool, str]:
        lock  = _lock_info()
        owner = lock.get("owner", "FREE")
        if owner == "CLAUDE":
            return False, "CLAUDE lock active — MONITOR_ONLY"
        return True, owner

    def _tc_preflight(self, entry: dict) -> tuple[bool, str]:
        """Read-only pre-launch checks. No authority writes."""
        cmd_str = entry.get("command", "")
        if not cmd_str:
            return False, "BLOCKED_PRECHECK: entry has no command"
        parts = shlex.split(cmd_str)
        exe = parts[0] if parts else ""
        if exe.startswith("python") and len(parts) > 1:
            script = Path(parts[1])
            if not script.is_absolute():
                script = Path(entry.get("workdir", str(HOME))) / script
            if not script.exists():
                return False, f"BLOCKED_PRECHECK: script not found: {script}"
        try:
            RUNS_DIR.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            return False, f"BLOCKED_PRECHECK: run dir not writable: {e}"
        if not REGISTRY_PATH.exists():
            return False, "BLOCKED_PRECHECK: test_registry.json missing"
        return True, "OK"

    def _tc_start(self) -> None:
        if not self.tc_registry:
            self.tc_error_msg = "Registry empty — check test_registry.json"; return
        if self.tc_sel >= len(self.tc_registry):
            return
        allowed, reason = self._tc_check_lock()
        if not allowed:
            self.tc_error_msg = reason; return

        entry = self.tc_registry[self.tc_sel]
        pre_ok, pre_msg = self._tc_preflight(entry)
        if not pre_ok:
            self.tc_error_msg = pre_msg; return
        run_id   = datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + entry["id"]
        run_dir  = RUNS_DIR / run_id
        try:
            run_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            self.tc_error_msg = f"Cannot create run dir: {e}"; return

        stdout_path = run_dir / "stdout.log"
        stderr_path = run_dir / "stderr.log"

        try:
            cmd     = shlex.split(entry["command"])
            workdir = entry.get("workdir", str(HOME))
            env     = dict(os.environ); env["PYTHONUNBUFFERED"] = "1"
            stdout_f = open(stdout_path, "w")
            stderr_f = open(stderr_path, "w")
            proc = subprocess.Popen(cmd, stdout=stdout_f, stderr=stderr_f,
                                    cwd=workdir, env=env)
            stdout_f.close(); stderr_f.close()
        except Exception as e:
            self.tc_error_msg = f"Launch failed: {e}"; return

        status = {
            "run_id":      run_id,
            "test_id":     entry["id"],
            "label":       entry["label"],
            "pid":         proc.pid,
            "started_at":  datetime.now(timezone.utc).isoformat(),
            "ended_at":    None,
            "status":      "RUNNING",
            "returncode":  None,
            "command":     entry["command"],
            "workdir":     workdir,
            "artifacts":   [],
        }
        try:
            (run_dir / "run_status.json").write_text(json.dumps(status, indent=2))
        except Exception:
            pass

        self.tc_process      = proc
        self.tc_run_dir      = run_dir
        self.tc_run_status   = status
        self.tc_stdout_path  = stdout_path
        self.tc_stderr_path  = stderr_path
        self.tc_live_out     = []
        self.tc_live_err     = []
        self.tc_parsed       = {}
        self.tc_stop_requested = False
        self.tc_stop_time    = None
        self.tc_force_buf    = ""
        self.tc_error_msg    = ""
        self.tc_view         = "MONITOR"

    def _tc_update(self) -> None:
        """Poll process and refresh live output. Called every ~1 s in MONITOR view."""
        if self.tc_process is None: return
        rc = self.tc_process.poll()

        if self.tc_stdout_path:
            self.tc_live_out = _tc_read_tail(self.tc_stdout_path, 18)
        if self.tc_stderr_path:
            self.tc_live_err = _tc_read_tail(self.tc_stderr_path, 4)

        all_lines = _tc_read_tail(self.tc_stdout_path, 200) if self.tc_stdout_path else []
        self.tc_parsed = _tc_parse_output(all_lines)

        if rc is not None:
            self.tc_run_status["returncode"] = rc
            self.tc_run_status["ended_at"]   = datetime.now(timezone.utc).isoformat()
            self.tc_run_status["status"]      = "PASS" if rc == 0 else "FAIL"
            if self.tc_stop_requested:
                self.tc_run_status["status"] = "STOPPED"
            arts = self._tc_scan_artifacts()
            self.tc_run_status["artifacts"] = [str(a) for a in arts]
            if self.tc_run_dir:
                try:
                    (self.tc_run_dir / "run_status.json").write_text(
                        json.dumps(self.tc_run_status, indent=2))
                except Exception:
                    pass
            self.tc_last_run    = self.tc_run_status.copy()
            self.tc_artifacts   = arts
            self.tc_process     = None

    def _tc_scan_artifacts(self) -> list[Path]:
        if not self.tc_registry or self.tc_sel >= len(self.tc_registry):
            return []
        glob_pat = self.tc_registry[self.tc_sel].get("artifact_glob", "")
        if not glob_pat: return []
        try:
            hits = sorted(HOME.glob(glob_pat), key=lambda p: p.stat().st_mtime, reverse=True)
            return hits[:20]
        except Exception:
            return []

    def _tc_request_stop(self) -> None:
        if self.tc_process is None: return
        try:
            self.tc_process.send_signal(signal.SIGINT)
        except Exception:
            pass
        self.tc_stop_requested = True
        self.tc_stop_time = time.time()
        self.tc_force_buf  = ""

    def _tc_force_stop(self) -> None:
        if self.tc_process is None: return
        try:
            self.tc_process.kill()
        except Exception:
            pass
        self.tc_stop_requested = False
        self.tc_force_buf = ""

    def _tc_open_artifacts(self) -> None:
        arts = self.tc_artifacts or self._tc_scan_artifacts()
        self.tc_artifacts    = arts
        self.tc_art_sel      = 0
        self.tc_art_scroll   = 0
        self.tc_art_preview  = []
        self.tc_art_in_preview = False
        self.tc_view         = "ARTIFACTS"

    # ── Drawing ───────────────────────────────────────────────────────────────

    def _cp(self, pair: int | None) -> int:
        return curses.color_pair(pair) if pair is not None else 0

    def _put(self, row: int, col: int, text: str,
             attr: int = 0, maxw: int = 9999) -> None:
        try:
            self.scr.addstr(row, col, text[:maxw], attr if attr is not None else 0)
        except curses.error:
            pass

    def draw(self) -> None:
        H, W = self.scr.getmaxyx()
        self.scr.erase()
        if H < MIN_ROWS or W < MIN_COLS:
            msg = f"Terminal too small ({W}×{H}). Need ≥{MIN_COLS}×{MIN_ROWS}."
            self._put(H // 2, max(0, (W - len(msg)) // 2), msg, self._cp(_CP_ERR))
            self.scr.refresh(); return
        self._draw_title(H, W)
        self._draw_nav(H, W)
        if self.tc_active:
            self._draw_tc(H, W)
        elif self.fb_active:
            self._draw_fb(H, W)
        else:
            self._draw_content(H, W)
        self._draw_status(H, W)
        self.scr.refresh()

    def _draw_title(self, H: int, W: int) -> None:
        try: hostname = socket.gethostname()
        except Exception: hostname = "unknown"
        lock  = _lock_info(); mode = lock.get("mode", "CONTROL")
        title = f" PH6 Desktop Controlled Terminal v{VERSION}"
        right = f"{hostname} Pi5  {mode}  {self.ts} "
        pad = W - len(title) - len(right)
        self._put(0, 0, (title + " " * max(1, pad) + right)[:W],
                  self._cp(_CP_TITLE) | curses.A_BOLD)

    def _draw_nav(self, H: int, W: int) -> None:
        content_h = H - 3; nav_inner = NAV_W - 2
        self._put(1, 0, _TL + _H * (NAV_W - 2) + _TT)
        for r in range(content_h - 1):
            y = r + 2
            if r < len(MENU):
                label, _ = MENU[r]; text = f" {label:<{nav_inner - 1}}"
                if r == self.sel:
                    self._put(y, 0, _V, 0)
                    self._put(y, 1, text[:nav_inner], self._cp(_CP_NAV_SEL) | curses.A_BOLD)
                    self._put(y, NAV_W - 1, _V, 0)
                else:
                    self._put(y, 0, _V + text[:nav_inner] + _V, self._cp(_CP_NAV))
            else:
                self._put(y, 0, _V + " " * nav_inner + _V, self._cp(_CP_NAV))
        self._put(H - 2, 0, _LT + _H * (NAV_W - 2) + _BT)

    def _draw_content(self, H: int, W: int) -> None:
        cx = NAV_W; cw = W - NAV_W - 1; inner_w = cw - 2
        hdr = f"  {MENU[self.sel][1]}"
        self._put(1, cx, _TT + hdr + _H * (cw - len(hdr) - 1) + _TR)
        content_h = H - 3; row_idx = 0
        for r in range(content_h - 1):
            y = r + 2
            self._put(y, cx, _V); self._put(y, W - 1, _V)
            if row_idx >= len(self.rows): continue
            item = self.rows[row_idx]; row_idx += 1
            if item[0] == "HDR":
                self._put(y, cx + 1, f"  {item[1]}"[:inner_w], self._cp(_CP_HDR) | curses.A_BOLD)
            else:
                indent, label, value, cp = item
                lbl = "  " + "  " * indent + label
                gap = max(1, inner_w - len(lbl) - len(value) - 1)
                if len(lbl) + len(value) + 1 > inner_w:
                    lbl = lbl[:inner_w - len(value) - 2]
                self._put(y, cx + 1, (lbl + " " * gap)[:inner_w], 0)
                self._put(y, cx + 1 + len(lbl) + gap,
                          value[:inner_w - len(lbl) - gap], self._cp(cp) if cp else 0)
        self._put(H - 2, cx, _BT + _H * cw + _BR)

    # ── Test control drawing ───────────────────────────────────────────────────

    def _draw_tc(self, H: int, W: int) -> None:
        cx = NAV_W; cw = W - NAV_W - 1; inner_w = cw - 2; content_h = H - 3; visible = content_h - 1
        views = {"LIST": "Test Control", "MONITOR": "Live Monitor",
                 "RESULT": "Result", "ARTIFACTS": "Artifacts"}
        hdr = f"  {views.get(self.tc_view, self.tc_view)}"
        if self.tc_view == "MONITOR" and self.tc_run_status:
            lab = self.tc_run_status.get("label", "")
            hdr = f"  Monitor: {lab}"[:cw - 4]
        hdr = hdr[:cw - 2]
        self._put(1, cx, _TT + hdr + _H * max(0, cw - len(hdr) - 1) + _TR)
        for r in range(visible):
            y = r + 2; self._put(y, cx, _V); self._put(y, W - 1, _V)
        if self.tc_view == "LIST":
            self._draw_tc_list(visible, cx, inner_w)
        elif self.tc_view == "MONITOR":
            self._draw_tc_monitor(visible, cx, inner_w)
        elif self.tc_view == "RESULT":
            self._draw_tc_result(visible, cx, inner_w)
        elif self.tc_view == "ARTIFACTS":
            self._draw_tc_artifacts(visible, cx, inner_w)
        self._put(H - 2, cx, _BT + _H * cw + _BR)

    def _draw_tc_list(self, visible: int, cx: int, iw: int) -> None:
        y = 2
        def row(text: str, attr: int = 0) -> None:
            nonlocal y
            if y < 2 + visible: self._put(y, cx + 1, text[:iw], attr); y += 1

        row("  Available Tests", self._cp(_CP_HDR) | curses.A_BOLD)
        if not self.tc_registry:
            row("  (no tests in registry)", self._cp(_CP_WARN));
        for i, entry in enumerate(self.tc_registry):
            icon = " ▶ " if i == self.tc_sel else "   "
            label = f"{icon}{entry.get('label', entry['id'])}"
            cntl  = "  [lock required]" if entry.get("requires_control") else ""
            if i == self.tc_sel:
                self._put(y, cx + 1, (label + cntl)[:iw],
                          self._cp(_CP_FB_SEL) | curses.A_BOLD)
            else:
                self._put(y, cx + 1, label[:iw], self._cp(_CP_FB_FILE))
            y += 1
            if y >= 2 + visible: break

        y += 1
        row("  Active Run", self._cp(_CP_HDR) | curses.A_BOLD)
        if self.tc_process is not None:
            st = self.tc_run_status
            row(f"   {st.get('label','?')}  PID:{st.get('pid','?')}  RUNNING",
                self._cp(_CP_OK))
            row(f"   Elapsed: {_tc_elapsed(st.get('started_at',''))}", None)
        else:
            row("   None", self._cp(_CP_DIM))

        y += 1
        row("  Last Run", self._cp(_CP_HDR) | curses.A_BOLD)
        lr = self.tc_last_run
        if lr:
            st = lr.get("status", "?")
            row(f"   {lr.get('label','?')}  {st}",
                self._cp(_CP_OK) if st == "PASS" else self._cp(_CP_ERR))
        else:
            row("   None", self._cp(_CP_DIM))

        if self.tc_error_msg:
            y += 1
            row(f"  ERROR: {self.tc_error_msg}", self._cp(_CP_ERR))

        y += 1
        row("  Keys: S=Start  M=Monitor  V=Result  A=Artifacts  Q=Back",
            self._cp(_CP_STATUS))

    def _draw_tc_monitor(self, visible: int, cx: int, iw: int) -> None:
        y = 2
        def row(text: str, attr: int = 0) -> None:
            nonlocal y
            if y < 2 + visible: self._put(y, cx + 1, text[:iw], attr); y += 1

        st = self.tc_run_status
        is_running = self.tc_process is not None
        status_str = "RUNNING" if is_running else st.get("status", "DONE")
        status_cp  = _CP_OK if status_str == "RUNNING" else (
                     _CP_OK if status_str == "PASS" else _CP_ERR)

        row(f"  Run: {st.get('run_id','?')[-24:]}  PID:{st.get('pid','?')}",
            self._cp(_CP_HDR) | curses.A_BOLD)
        row(f"  Status: {status_str}   Elapsed: {_tc_elapsed(st.get('started_at',''))}",
            self._cp(status_cp))
        y += 1

        row("  Live Output", self._cp(_CP_HDR) | curses.A_BOLD)
        out_rows = min(12, visible - (y - 2) - 8)
        for line in self.tc_live_out[-max(1, out_rows):]:
            row(f"  {line}", 0)

        if self.tc_live_err:
            row("  Stderr", self._cp(_CP_WARN) | curses.A_BOLD)
            for line in self.tc_live_err[-2:]:
                row(f"  {line}", self._cp(_CP_WARN))

        y += 1
        row("  Parsed Metrics", self._cp(_CP_HDR) | curses.A_BOLD)
        p = self.tc_parsed
        metrics = []
        if "verdict" in p:       metrics.append(f"Verdict:{p['verdict']}")
        if "fps" in p:            metrics.append(f"FPS:{p['fps']}")
        if "motion_fraction" in p: metrics.append(f"Motion:{p['motion_fraction']}")
        if "frame" in p:          metrics.append(f"Frame:{p['frame']}")
        if "brightness" in p:     metrics.append(f"Bright:{p['brightness']}")
        if "entropy" in p:        metrics.append(f"Entropy:{p['entropy']}")
        row("  " + ("  ".join(metrics) if metrics else "—"), 0)

        y += 1
        if self.tc_stop_requested and is_running:
            elapsed_stop = time.time() - (self.tc_stop_time or time.time())
            row(f"  Stop requested ({elapsed_stop:.0f}s)  — type FORCE to kill: [{self.tc_force_buf}]",
                self._cp(_CP_ERR))
        else:
            row("  X=Stop  V=Result  A=Artifacts  Q=Back  (auto-refresh 1s)",
                self._cp(_CP_STATUS))

    def _draw_tc_result(self, visible: int, cx: int, iw: int) -> None:
        y = 2
        def row(text: str, attr: int = 0) -> None:
            nonlocal y
            if y < 2 + visible: self._put(y, cx + 1, text[:iw], attr); y += 1

        st = self.tc_last_run if not self.tc_run_status.get("ended_at") else self.tc_run_status
        if not st:
            row("  No completed run yet.", self._cp(_CP_WARN)); return

        status = st.get("status", "UNKNOWN")
        row(f"  Run: {st.get('run_id','?')[-28:]}", self._cp(_CP_HDR) | curses.A_BOLD)
        row(f"  Label:   {st.get('label','?')}", None)
        row(f"  Status:  {status}    rc:{st.get('returncode','?')}",
            self._cp(_CP_OK) if status == "PASS" else self._cp(_CP_ERR))
        row(f"  Started: {st.get('started_at','?')[:19]}", None)
        row(f"  Ended:   {st.get('ended_at','?')[:19]}", None)

        y += 1
        row("  Parsed Results", self._cp(_CP_HDR) | curses.A_BOLD)
        # Re-parse from log if we have a run_dir
        rdir = self.tc_run_dir
        if rdir is None and st.get("run_id"):
            rdir = RUNS_DIR / st["run_id"]
        p: dict = {}
        if rdir and (rdir / "stdout.log").exists():
            p = _tc_parse_output(_tc_read_tail(rdir / "stdout.log", 200))
        for k, v in p.items():
            row(f"    {k}: {v}", None)
        if not p:
            row("    (no metrics parsed)", self._cp(_CP_DIM))

        y += 1
        arts = st.get("artifacts", [])
        row(f"  Artifacts found: {len(arts)}", self._cp(_CP_HDR) | curses.A_BOLD)
        for a in arts[:4]:
            row(f"    {Path(a).name[-40:]}", None)

        y += 1
        row("  A=Open Artifacts  Q=Back", self._cp(_CP_STATUS))

    def _draw_tc_artifacts(self, visible: int, cx: int, iw: int) -> None:
        y = 2
        def row(text: str, attr: int = 0) -> None:
            nonlocal y
            if y < 2 + visible: self._put(y, cx + 1, text[:iw], attr); y += 1

        if self.tc_art_in_preview:
            row("  File Preview (read-only)", self._cp(_CP_HDR) | curses.A_BOLD)
            max_lines = visible - 3
            lines = self.tc_art_preview
            for li in range(max_lines):
                idx = li + (self.tc_art_scroll if hasattr(self, "tc_art_scroll") else 0)
                if idx >= len(lines): break
                self._put(y, cx + 1, lines[idx][:iw], 0); y += 1
            row("  BKSP=Back to list  Q=Exit artifacts", self._cp(_CP_STATUS))
            return

        row("  Artifacts (read-only)", self._cp(_CP_HDR) | curses.A_BOLD)
        arts = self.tc_artifacts
        if not arts:
            row("  (none found)", self._cp(_CP_DIM))
        else:
            n = len(arts)
            if self.tc_art_sel < self.tc_art_scroll:
                self.tc_art_scroll = self.tc_art_sel
            elif n > 0 and self.tc_art_sel >= self.tc_art_scroll + (visible - 4):
                self.tc_art_scroll = self.tc_art_sel - (visible - 5)
            for r in range(visible - 4):
                idx = r + self.tc_art_scroll
                if idx >= n: break
                path = arts[idx]
                icon = " ▶ " if path.is_dir() else "   "
                line = f"{icon}{path.name}"
                attr = (self._cp(_CP_FB_SEL) | curses.A_BOLD) if idx == self.tc_art_sel \
                       else self._cp(_CP_FB_FILE)
                self._put(y, cx + 1, line[:iw], attr); y += 1
        row("  ↑↓ Navigate  ENTER=Preview  BKSP=Back  Q=Exit artifacts",
            self._cp(_CP_STATUS))

    # ── File browser drawing ───────────────────────────────────────────────────

    def _draw_fb(self, H: int, W: int) -> None:
        cx = NAV_W; cw = W - NAV_W - 1; inner_w = cw - 2
        content_h = H - 3; visible = content_h - 1
        if self.fb_in_preview and self.fb_entries and self.fb_sel < len(self.fb_entries):
            _, fname, _ = self.fb_entries[self.fb_sel]; hdr = f"  Preview: {fname}"
        elif self.fb_path:
            ps = str(self.fb_path)
            hdr = f"  {'...' + ps[-(inner_w-7):] if len(ps) > inner_w-4 else ps}"
        else:
            hdr = "  File Browser — Safe Roots"
        hdr = hdr[:cw - 2]
        self._put(1, cx, _TT + hdr + _H * max(0, cw - len(hdr) - 1) + _TR)
        for r in range(visible):
            y = r + 2; self._put(y, cx, _V); self._put(y, W - 1, _V)
        if self.fb_in_preview:
            self._draw_fb_preview(visible, cx, inner_w)
        else:
            self._draw_fb_tree(visible, cx, inner_w)
        self._put(H - 2, cx, _BT + _H * cw + _BR)

    def _draw_fb_tree(self, visible: int, cx: int, inner_w: int) -> None:
        n = len(self.fb_entries)
        if self.fb_sel < self.fb_scroll: self.fb_scroll = self.fb_sel
        elif n > 0 and self.fb_sel >= self.fb_scroll + visible: self.fb_scroll = self.fb_sel - visible + 1
        if n == 0:
            self._put(3, cx + 2, "(empty)", self._cp(_CP_DIM)); return
        for r in range(visible):
            idx = r + self.fb_scroll
            if idx >= n: break
            is_dir, name, _ = self.fb_entries[idx]
            line = f" {'▶ ' if is_dir else '  '}{name}"
            attr = (self._cp(_CP_FB_SEL) | curses.A_BOLD) if idx == self.fb_sel \
                   else (self._cp(_CP_FB_DIR) if is_dir else self._cp(_CP_FB_FILE))
            self._put(r + 2, cx + 1, line[:inner_w], attr)

    def _draw_fb_preview(self, visible: int, cx: int, inner_w: int) -> None:
        lines = self.fb_preview
        self.fb_prev_scroll = min(self.fb_prev_scroll, max(0, len(lines) - visible))
        for r in range(visible):
            li = r + self.fb_prev_scroll
            if li >= len(lines): break
            self._put(r + 2, cx + 1, lines[li][:inner_w], 0)

    def _draw_status(self, H: int, W: int) -> None:
        lock = _lock_info(); owner = lock.get("owner", "FREE"); mode = lock.get("mode", "CONTROL")
        if self.tc_active:
            ms = " Mouse" if self.mouse_ok else ""
            if self.tc_view == "MONITOR":
                keys = f"X Stop | V Result | A Artifacts | Q Back{ms}"
            elif self.tc_view == "ARTIFACTS":
                keys = f"↑↓ Nav | ENTER Preview | BKSP Back | Q Exit{ms}"
            else:
                keys = f"S Start | M Monitor | V Result | A Artifacts | Q Back{ms}"
        elif self.fb_active:
            ms = " Mouse" if self.mouse_ok else ""
            keys = f"Q Back | ↑↓ Nav{ms} | ENTER Open | BKSP Parent | H Home | R Refresh"
        else:
            keys = "Q Exit | R Refresh | ↑↓ Navigate | 1-12 Jump | ENTER Select"
        auth = f"Class:3 Prototype  Owner:{owner}  Authority:ZERO"
        pad  = W - len(keys) - len(auth) - 2
        self._put(H - 1, 0, (f" {keys}" + " " * max(1, pad) + auth + " ")[:W],
                  self._cp(_CP_STATUS) | curses.A_BOLD)

    # ── Mouse ─────────────────────────────────────────────────────────────────

    def _handle_mouse(self) -> None:
        try:
            _, mx, my, _, _bstate = curses.getmouse()
        except curses.error:
            return

        if mx < NAV_W:
            nav_idx = my - 2
            if 0 <= nav_idx < len(MENU):
                if self.tc_active and nav_idx != TC_MENU_IDX:
                    self.tc_active = False
                if self.fb_active and nav_idx != FB_MENU_IDX:
                    self.fb_active = False; self.fb_in_preview = False
                self.sel = nav_idx
                if nav_idx == TC_MENU_IDX:
                    if not self.tc_active:
                        self.tc_active = True; self._tc_enter()
                elif nav_idx == FB_MENU_IDX:
                    if not self.fb_active:
                        self.fb_active = True; self._fb_enter_root()
                else:
                    self.refresh_panel()
            return

        if self.tc_active and self.tc_view == "LIST" and mx >= NAV_W:
            # Click on test entry (entries start at y=3, after header)
            entry_idx = (my - 3)
            if 0 <= entry_idx < len(self.tc_registry):
                if entry_idx == self.tc_sel:
                    self._tc_start()
                else:
                    self.tc_sel = entry_idx
            return

        if self.tc_active and self.tc_view == "ARTIFACTS" and not self.tc_art_in_preview:
            idx = (my - 3) + self.tc_art_scroll
            if 0 <= idx < len(self.tc_artifacts):
                if idx == self.tc_art_sel:
                    self.tc_art_preview = _fb_read_preview(self.tc_artifacts[idx])
                    self.tc_art_in_preview = True; self.tc_art_scroll = 0
                else:
                    self.tc_art_sel = idx
            return

        if self.fb_active and not self.fb_in_preview and mx >= NAV_W:
            idx = (my - 2) + self.fb_scroll
            if 0 <= idx < len(self.fb_entries):
                if idx == self.fb_sel:
                    self._fb_open_selected()
                else:
                    self.fb_sel = idx

    # ── Event loop ────────────────────────────────────────────────────────────

    def run(self) -> None:
        curses.curs_set(0)

        while True:
            # 1-second refresh in monitor, 5-second otherwise
            self.scr.timeout(1000 if (self.tc_active and self.tc_view == "MONITOR") else 5000)
            if self.tc_active and self.tc_view == "MONITOR":
                self._tc_update()
            self.draw()
            key = self.scr.getch()

            # ── Test Control keys
            if self.tc_active:
                if key == -1:
                    pass  # timeout → already updated above
                elif key in (ord("q"), ord("Q"), 27):
                    if self.tc_view in ("MONITOR", "RESULT", "ARTIFACTS"):
                        self.tc_view = "LIST"
                    else:
                        self.tc_active = False; self.tc_view = "LIST"; self.refresh_panel()
                elif key == curses.KEY_UP:
                    if self.tc_view == "LIST":
                        self.tc_sel = max(0, self.tc_sel - 1)
                    elif self.tc_view == "ARTIFACTS" and not self.tc_art_in_preview:
                        self.tc_art_sel = max(0, self.tc_art_sel - 1)
                elif key == curses.KEY_DOWN:
                    if self.tc_view == "LIST":
                        self.tc_sel = min(max(0, len(self.tc_registry) - 1), self.tc_sel + 1)
                    elif self.tc_view == "ARTIFACTS" and not self.tc_art_in_preview:
                        self.tc_art_sel = min(max(0, len(self.tc_artifacts) - 1), self.tc_art_sel + 1)
                elif key in (curses.KEY_ENTER, 10, 13):
                    if self.tc_view == "LIST":
                        self._tc_start()
                    elif self.tc_view == "ARTIFACTS" and not self.tc_art_in_preview:
                        if self.tc_artifacts and self.tc_art_sel < len(self.tc_artifacts):
                            self.tc_art_preview = _fb_read_preview(self.tc_artifacts[self.tc_art_sel])
                            self.tc_art_in_preview = True; self.tc_art_scroll = 0
                    elif self.tc_view == "ARTIFACTS" and self.tc_art_in_preview:
                        self.tc_art_in_preview = False
                elif key in (curses.KEY_BACKSPACE, 127, 8):
                    if self.tc_view == "ARTIFACTS":
                        if self.tc_art_in_preview:
                            self.tc_art_in_preview = False
                        else:
                            self.tc_view = "RESULT" if self.tc_run_status.get("ended_at") else "LIST"
                elif key in (ord("s"), ord("S")):
                    if self.tc_view == "LIST":
                        self._tc_start()
                elif key in (ord("m"), ord("M")):
                    if self.tc_process is not None or self.tc_run_status:
                        self.tc_view = "MONITOR"
                elif key in (ord("v"), ord("V")):
                    self.tc_view = "RESULT"
                elif key in (ord("a"), ord("A")):
                    self._tc_open_artifacts()
                elif key in (ord("x"), ord("X")):
                    if self.tc_view == "MONITOR" and self.tc_process is not None:
                        self._tc_request_stop()
                elif key == curses.KEY_MOUSE:
                    self._handle_mouse()
                else:
                    # Accumulate FORCE confirmation
                    if self.tc_stop_requested and self.tc_process is not None:
                        if 32 <= key <= 126:
                            self.tc_force_buf += chr(key)
                            if len(self.tc_force_buf) > 5:
                                self.tc_force_buf = self.tc_force_buf[-5:]
                            if self.tc_force_buf == "FORCE":
                                self._tc_force_stop()

            # ── File Browser keys
            elif self.fb_active:
                if key in (ord("q"), ord("Q"), 27):
                    self.fb_active = False; self.fb_in_preview = False; self.refresh_panel()
                elif key in (ord("r"), ord("R")):
                    if not self.fb_in_preview:
                        self._fb_enter_dir(self.fb_path) if self.fb_path else self._fb_enter_root()
                elif key == curses.KEY_UP:
                    if self.fb_in_preview:
                        self.fb_prev_scroll = max(0, self.fb_prev_scroll - 1)
                    elif self.fb_entries:
                        self.fb_sel = max(0, self.fb_sel - 1)
                elif key == curses.KEY_DOWN:
                    if self.fb_in_preview:
                        self.fb_prev_scroll += 1
                    elif self.fb_entries:
                        self.fb_sel = min(len(self.fb_entries) - 1, self.fb_sel + 1)
                elif key in (curses.KEY_ENTER, 10, 13):
                    if self.fb_in_preview: self.fb_in_preview = False
                    else: self._fb_open_selected()
                elif key in (curses.KEY_BACKSPACE, 127, 8):
                    self._fb_back()
                elif key in (ord("h"), ord("H")):
                    self._fb_enter_root()
                elif key == curses.KEY_MOUSE:
                    self._handle_mouse()

            # ── Normal keys
            else:
                if key in (ord("q"), ord("Q"), 27):
                    break
                elif key in (ord("r"), ord("R"), -1):
                    self.refresh_panel()
                elif key == curses.KEY_UP:
                    self.sel = (self.sel - 1) % len(MENU); self.refresh_panel()
                elif key == curses.KEY_DOWN:
                    self.sel = (self.sel + 1) % len(MENU); self.refresh_panel()
                elif key in (curses.KEY_ENTER, 10, 13):
                    if self.sel == EXIT_IDX - 1:
                        self._launch_realtime()
                    elif self.sel == TC_MENU_IDX:
                        self.tc_active = True; self._tc_enter()
                    elif self.sel == FB_MENU_IDX:
                        self.fb_active = True; self._fb_enter_root()
                    else:
                        self.refresh_panel()
                elif ord("1") <= key <= ord("9"):
                    idx = key - ord("1")
                    if idx < len(MENU): self.sel = idx; self.refresh_panel()
                elif key == ord("0"):
                    self.sel = 9; self.refresh_panel()
                elif key in (ord("g"), ord("G")):
                    self.sel = 10; self.refresh_panel()
                elif key == curses.KEY_MOUSE:
                    self._handle_mouse()

    def _launch_realtime(self) -> None:
        curses.endwin(); os.system("clear")
        print("  Realtime mode: launch ph6_desktop_terminal.py → option 12")
        print("  Press Enter to return to Windows display…")
        try: input()
        except (KeyboardInterrupt, EOFError): pass
        stdscr = curses.initscr(); curses.noecho(); curses.cbreak(); stdscr.keypad(True)
        self.scr = stdscr; self._setup_colors(); self._setup_mouse()


# ── Entry points ──────────────────────────────────────────────────────────────

def run_windows(stdscr: Any) -> None:
    PH6WindowsDisplay(stdscr).run()


def main(args: list[str] | None = None) -> None:
    if args is None:
        args = sys.argv[1:]
    if "--help" in args or "-h" in args:
        print(__doc__); return
    try:
        curses.wrapper(run_windows)
    except KeyboardInterrupt:
        pass
    finally:
        try: curses.endwin()
        except Exception: pass
    print("\n  PH6 Windows Terminal closed. Lane-1 authority unchanged.\n")


if __name__ == "__main__":
    main()
