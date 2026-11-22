#!/usr/bin/env python3
"""
PH6 Local Desktop Interface v1

FastAPI dashboard for PH6 governance, tests, reports, and fleet status.

Safety rules enforced here:
- No camera, USB, CAN, video, or hardware commands.
- All subprocess commands are whitelisted — no user free-text execution.
- Settings saved atomically: write-tmp → fsync → replace → fsync-dir.
- Report path traversal is blocked.
- Destructive actions are blocked unless explicitly enabled in settings.
"""
from __future__ import annotations

import json
import os
import platform
import shutil
import socket
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# ── Paths ─────────────────────────────────────────────────────────────────────

_HERE       = Path(__file__).resolve().parent
_SETTINGS   = _HERE / "settings.json"
_LAST_TEST  = _HERE / "last_test_result.json"
_TEMPLATES  = _HERE / "templates"
_STATIC     = _HERE / "static"

# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(title="PH6 Local Desktop", docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory=str(_STATIC)), name="static")
templates = Jinja2Templates(directory=str(_TEMPLATES))


# ── Settings ──────────────────────────────────────────────────────────────────

_DEFAULTS: Dict[str, Any] = {
    "interface_name":        "PH6 Local Desktop",
    "bind_host":             "127.0.0.1",
    "bind_port":             8765,
    "repo_root":             "/home/jack",
    "ph6_source":            "/home/jack/PH6_SOURCE",
    "internal_test_script":  "/home/jack/ph6/cram_pu/ph6_internal_test.py",
    "report_dir":            "/home/jack/PH6_SOURCE/DEPLOYMENT",
    "zero_sentinel_ip":      "192.168.254.189",
    "camera_tests_enabled":  False,
    "usb_tests_enabled":     False,
    "can_hat_enabled":       False,
    "allow_destructive_actions": False,
}


def load_settings() -> Dict[str, Any]:
    if _SETTINGS.exists():
        try:
            data = json.loads(_SETTINGS.read_text(encoding="utf-8"))
            merged = {**_DEFAULTS, **data}
            return merged
        except Exception:
            pass
    return dict(_DEFAULTS)


def save_settings_atomic(data: Dict[str, Any]) -> None:
    tmp = _SETTINGS.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.flush()
        os.fsync(f.fileno())
    tmp.replace(_SETTINGS)
    dir_fd = os.open(str(_HERE), os.O_RDONLY)
    try:
        os.fsync(dir_fd)
    finally:
        os.close(dir_fd)


# ── System info ───────────────────────────────────────────────────────────────

def _read_proc_uptime() -> str:
    try:
        secs = float(Path("/proc/uptime").read_text().split()[0])
        d, r = divmod(int(secs), 86400)
        h, r = divmod(r, 3600)
        m    = r // 60
        return f"{d}d {h}h {m}m"
    except Exception:
        return "unknown"


def _read_meminfo() -> str:
    try:
        info: Dict[str, int] = {}
        for line in Path("/proc/meminfo").read_text().splitlines():
            k, v = line.split(":")
            info[k.strip()] = int(v.strip().split()[0])
        total = info["MemTotal"] // 1024
        avail = info["MemAvailable"] // 1024
        used  = total - avail
        pct   = int(used / total * 100)
        return f"{used} MB / {total} MB ({pct}%)"
    except Exception:
        return "unknown"


def _read_cpu_temp() -> str:
    try:
        raw = Path("/sys/class/thermal/thermal_zone0/temp").read_text().strip()
        return f"{int(raw) / 1000:.1f} °C"
    except Exception:
        return "unknown"


def _read_disk(repo_root: str) -> str:
    try:
        u = shutil.disk_usage(repo_root)
        total = u.total // (1024 ** 3)
        used  = u.used  // (1024 ** 3)
        pct   = int(u.used / u.total * 100)
        return f"{used} GB / {total} GB ({pct}%)"
    except Exception:
        return "unknown"


def _git_head(repo_root: str) -> str:
    try:
        r = subprocess.run(
            ["git", "log", "--oneline", "-1"],
            cwd=repo_root, capture_output=True, text=True, timeout=5
        )
        return r.stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def _git_dirty(repo_root: str) -> bool:
    try:
        r = subprocess.run(
            ["git", "status", "--short"],
            cwd=repo_root, capture_output=True, text=True, timeout=5
        )
        return bool(r.stdout.strip())
    except Exception:
        return False


def _local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "unknown"


def get_system_info(s: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "hostname":            platform.node(),
        "ip":                  _local_ip(),
        "uptime":              _read_proc_uptime(),
        "memory":              _read_meminfo(),
        "cpu_temp":            _read_cpu_temp(),
        "disk":                _read_disk(s["repo_root"]),
        "git_head":            _git_head(s["repo_root"]),
        "git_dirty":           _git_dirty(s["repo_root"]),
        "repo_root":           s["repo_root"],
        "ph6_source_exists":   Path(s["ph6_source"]).exists(),
        "internal_test_exists": Path(s["internal_test_script"]).exists(),
    }


# ── Safe subprocess runner ────────────────────────────────────────────────────

def _run(cmd: List[str], cwd: str, timeout: int = 90) -> Dict[str, Any]:
    try:
        r = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=False,
        )
        status = "PASS" if r.returncode == 0 else "FAIL"
        return {"returncode": r.returncode, "stdout": r.stdout, "stderr": r.stderr, "status": status}
    except subprocess.TimeoutExpired:
        return {"returncode": -1, "stdout": "", "stderr": "TIMEOUT", "status": "FAIL"}
    except Exception as e:
        return {"returncode": -1, "stdout": "", "stderr": str(e), "status": "FAIL"}


def _whitelisted_commands(s: Dict[str, Any]) -> Dict[str, List[str]]:
    return {
        "internal-test": [
            "python3", s["internal_test_script"],
            "--report-dir", s["report_dir"],
            "--node-id", "jackjack-pi5-interface",
        ],
        "governance": [
            "python3",
            str(Path(s["ph6_source"]) / "TOOLS" / "governance_drift_scan.py"),
            "--scan-root", s["ph6_source"],
        ],
        "preflight": [
            "python3",
            str(Path(s["ph6_source"]) / "TOOLS" / "ai_preflight_check.py"),
        ],
        "compileall": [
            "python3", "-m", "compileall", "-q", "ph6",
        ],
    }


# ── Last test result ──────────────────────────────────────────────────────────

def _load_last_test() -> Optional[Dict[str, Any]]:
    if _LAST_TEST.exists():
        try:
            return json.loads(_LAST_TEST.read_text(encoding="utf-8"))
        except Exception:
            pass
    return None


def _save_last_test(command: str, result: Dict[str, Any]) -> None:
    data = {
        "command":    command,
        "status":     result["status"],
        "returncode": result["returncode"],
        "run_at":     datetime.now(timezone.utc).isoformat(),
        "stdout_tail": result["stdout"][-2000:],
        "stderr_tail": result["stderr"][-500:],
    }
    _LAST_TEST.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    s = load_settings()
    return templates.TemplateResponse("index.html", {
        "request":   request,
        "page":      "dashboard",
        "info":      get_system_info(s),
        "settings":  s,
        "last_test": _load_last_test(),
    })


@app.get("/settings", response_class=HTMLResponse)
async def settings_get(request: Request, saved: bool = False):
    return templates.TemplateResponse("settings.html", {
        "request":  request,
        "page":     "settings",
        "settings": load_settings(),
        "saved":    saved,
    })


@app.post("/settings")
async def settings_post(
    request: Request,
    interface_name:          str  = Form("PH6 Local Desktop"),
    bind_host:               str  = Form("127.0.0.1"),
    bind_port:               int  = Form(8765),
    repo_root:               str  = Form("/home/jack"),
    ph6_source:              str  = Form("/home/jack/PH6_SOURCE"),
    internal_test_script:    str  = Form(""),
    report_dir:              str  = Form(""),
    zero_sentinel_ip:        str  = Form("192.168.254.189"),
    camera_tests_enabled:    Optional[str] = Form(None),
    usb_tests_enabled:       Optional[str] = Form(None),
    can_hat_enabled:         Optional[str] = Form(None),
    allow_destructive_actions: Optional[str] = Form(None),
):
    current = load_settings()
    current.update({
        "interface_name":          interface_name.strip(),
        "bind_host":               bind_host.strip(),
        "bind_port":               bind_port,
        "repo_root":               repo_root.strip(),
        "ph6_source":              ph6_source.strip(),
        "internal_test_script":    internal_test_script.strip() or current["internal_test_script"],
        "report_dir":              report_dir.strip() or current["report_dir"],
        "zero_sentinel_ip":        zero_sentinel_ip.strip(),
        "camera_tests_enabled":    camera_tests_enabled == "on",
        "usb_tests_enabled":       usb_tests_enabled == "on",
        "can_hat_enabled":         can_hat_enabled == "on",
        "allow_destructive_actions": allow_destructive_actions == "on",
    })
    save_settings_atomic(current)
    return RedirectResponse(url="/settings?saved=1", status_code=303)


@app.get("/tests", response_class=HTMLResponse)
async def tests_get(request: Request):
    return templates.TemplateResponse("tests.html", {
        "request":  request,
        "page":     "tests",
        "settings": load_settings(),
        "result":   None,
    })


def _run_test(key: str) -> HTMLResponse:
    from fastapi import Request as _Req
    pass


async def _run_and_render(request: Request, key: str) -> HTMLResponse:
    s       = load_settings()
    cmds    = _whitelisted_commands(s)
    cmd     = cmds.get(key)
    if not cmd:
        raise HTTPException(status_code=400, detail="Unknown command")
    result  = _run(cmd, cwd=s["repo_root"], timeout=120)
    result["command"] = key
    _save_last_test(key, result)
    return templates.TemplateResponse("tests.html", {
        "request":  request,
        "page":     "tests",
        "settings": s,
        "result":   result,
    })


@app.post("/run/internal-test", response_class=HTMLResponse)
async def run_internal_test(request: Request):
    return await _run_and_render(request, "internal-test")


@app.post("/run/governance", response_class=HTMLResponse)
async def run_governance(request: Request):
    return await _run_and_render(request, "governance")


@app.post("/run/preflight", response_class=HTMLResponse)
async def run_preflight(request: Request):
    return await _run_and_render(request, "preflight")


@app.post("/run/compileall", response_class=HTMLResponse)
async def run_compileall(request: Request):
    return await _run_and_render(request, "compileall")


@app.get("/reports", response_class=HTMLResponse)
async def reports_list(request: Request):
    s           = load_settings()
    report_dir  = Path(s["report_dir"])
    reports     = []
    if report_dir.exists():
        for p in sorted(report_dir.glob("*.md"), key=lambda x: x.stat().st_mtime, reverse=True):
            sz  = p.stat().st_size
            mod = datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc).strftime("%Y-%m-%d %H:%M Z")
            reports.append({"name": p.name, "size": f"{sz:,} B", "modified": mod})
    return templates.TemplateResponse("reports.html", {
        "request":        request,
        "page":           "reports",
        "reports":        reports,
        "report_dir":     str(report_dir),
        "report_content": None,
        "report_name":    None,
    })


@app.get("/reports/{filename}", response_class=HTMLResponse)
async def reports_view(request: Request, filename: str):
    s          = load_settings()
    report_dir = Path(s["report_dir"]).resolve()

    # Safety: only .md files, no path traversal
    if not filename.endswith(".md") or "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(status_code=403, detail="Access denied")

    target = (report_dir / filename).resolve()
    if not str(target).startswith(str(report_dir)):
        raise HTTPException(status_code=403, detail="Access denied")

    if not target.exists():
        raise HTTPException(status_code=404, detail="Report not found")

    content = target.read_text(encoding="utf-8", errors="replace")
    return templates.TemplateResponse("reports.html", {
        "request":        request,
        "page":           "reports",
        "reports":        [],
        "report_dir":     str(report_dir),
        "report_content": content,
        "report_name":    filename,
    })


@app.get("/fleet", response_class=HTMLResponse)
async def fleet(request: Request):
    s    = load_settings()
    pi5  = get_system_info(s)

    zero_ip = s["zero_sentinel_ip"]
    zero: Dict[str, Any] = {"ip": zero_ip, "reachable": False, "error": ""}

    try:
        r = subprocess.run(
            [
                "ssh", "-o", "ConnectTimeout=3", "-o", "BatchMode=yes",
                "-o", "StrictHostKeyChecking=no",
                f"jack@{zero_ip}",
                "hostname; cat /proc/device-tree/model 2>/dev/null || echo unknown; "
                "uname -m; uptime; command -v claude || echo 'OK: claude not installed'",
            ],
            capture_output=True, text=True, timeout=8, shell=False,
        )
        if r.returncode == 0:
            lines = [l.strip() for l in r.stdout.strip().splitlines() if l.strip()]
            zero["reachable"]       = True
            zero["hostname"]        = lines[0] if len(lines) > 0 else "unknown"
            zero["model"]           = lines[1] if len(lines) > 1 else "unknown"
            zero["arch"]            = lines[2] if len(lines) > 2 else "unknown"
            zero["uptime"]          = lines[3] if len(lines) > 3 else "unknown"
            zero["claude_status"]   = "not installed" if len(lines) > 4 and "not installed" in lines[4] else (lines[4] if len(lines) > 4 else "unknown")
            zero["hostname_warning"] = zero.get("hostname") == "jackjack"
        else:
            zero["error"] = r.stderr.strip()[:200]
    except subprocess.TimeoutExpired:
        zero["error"] = "SSH timeout (3s)"
    except Exception as e:
        zero["error"] = str(e)[:200]

    return templates.TemplateResponse("fleet.html", {
        "request":  request,
        "page":     "fleet",
        "pi5":      pi5,
        "zero":     zero,
        "settings": s,
    })


@app.get("/api/status")
async def api_status():
    s    = load_settings()
    info = get_system_info(s)
    return JSONResponse({
        "interface": s["interface_name"],
        "system":    info,
        "safety": {
            "camera_tests_enabled":    s["camera_tests_enabled"],
            "usb_tests_enabled":       s["usb_tests_enabled"],
            "can_hat_enabled":         s["can_hat_enabled"],
            "allow_destructive_actions": s["allow_destructive_actions"],
        },
        "last_test": _load_last_test(),
    })


@app.get("/api/settings")
async def api_settings():
    return JSONResponse(load_settings())
