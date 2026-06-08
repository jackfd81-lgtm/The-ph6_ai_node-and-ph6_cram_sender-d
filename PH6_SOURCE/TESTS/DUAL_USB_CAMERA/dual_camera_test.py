"""
dual_camera_test.py — PH6 Dual USB Camera Characterisation Test
Lane-2 PROPOSED. Operator ratification required before promotion.

Tests:
  Phase 0 — Camera inventory (done externally; recorded separately)
  Phase 1 — Smoke test      : 300 frames, 640x480, 15fps, MJPEG, both cameras
  Phase 2 — Same Vision     : 1200 frames, same profile, both cameras
  Phase 3 — Opposite Role   : 2 passes, 1200 frames each, roles swapped
  Phase 4 — Complementary   : Cam-A 640x480, Cam-B 1280x720, 1200 frames

CANON RULES:
  - BLAKE2b-256 (digest_size=32) is sole authority hash
  - motion_fraction only; motion_score / motion_decay_score FORBIDDEN
  - PASS/DROP only verdicts
  - No camera output treated as truth; cameras = bounded measurement devices
  - Lane-2 (AI) has zero authority; all verdicts = PROPOSED
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import sys
import threading
import time
from datetime import datetime, timezone
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import cv2
import numpy as np

# ---------------------------------------------------------------------------
# CRAM gate constants — copied from ph6_cram_sim.py (single source of truth)
# ---------------------------------------------------------------------------
GATE_ENTROPY_MIN: float = 6.0
GATE_LAPLACIAN_MIN: float = 100.0
GATE_MOTION_FRAC_MIN: float = 0.01
GATE_MOTION_FRAC_MAX: float = 0.75

PROPOSED_BY = "claude-code-lane2"
PROPOSED_AT = "2026-06-03T00:00:00Z"

# ---------------------------------------------------------------------------
# Camera assignment
# ---------------------------------------------------------------------------
CAMERA_A_NODE = "/dev/video0"  # DV20 USB — Jieli Technology 4c4a:4a55
CAMERA_A_NAME = "DV20_USB"
CAMERA_A_USB_ID = "4c4a:4a55"

CAMERA_B_NODE = "/dev/video2"  # Streaming Cam — Microdia 0c45:636b
CAMERA_B_NAME = "STREAMING_CAM"
CAMERA_B_USB_ID = "0c45:636b"

# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

def compute_entropy(gray: np.ndarray) -> float:
    hist = cv2.calcHist([gray], [0], None, [256], [0, 256]).flatten()
    hist = hist[hist > 0]
    prob = hist / hist.sum()
    return float(-np.sum(prob * np.log2(prob)))


def compute_laplacian_var(gray: np.ndarray) -> float:
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def compute_motion_fraction(gray: np.ndarray, prev_gray: np.ndarray | None,
                            threshold: int = 25) -> float:
    if prev_gray is None:
        return 0.0
    diff = cv2.absdiff(gray, prev_gray)
    return float(np.count_nonzero(diff > threshold)) / gray.size


def gate(entropy: float, laplacian_var: float, motion_fraction: float) -> str:
    ok = (
        entropy >= GATE_ENTROPY_MIN
        and laplacian_var >= GATE_LAPLACIAN_MIN
        and GATE_MOTION_FRAC_MIN <= motion_fraction <= GATE_MOTION_FRAC_MAX
    )
    return "PASS" if ok else "DROP"


def drop_reason(entropy: float, laplacian_var: float, motion_fraction: float) -> str:
    reasons = []
    if entropy < GATE_ENTROPY_MIN:
        reasons.append(f"entropy_low({entropy:.3f}<{GATE_ENTROPY_MIN})")
    if laplacian_var < GATE_LAPLACIAN_MIN:
        reasons.append(f"blur({laplacian_var:.1f}<{GATE_LAPLACIAN_MIN})")
    if motion_fraction < GATE_MOTION_FRAC_MIN:
        reasons.append(f"motion_low({motion_fraction:.4f}<{GATE_MOTION_FRAC_MIN})")
    if motion_fraction > GATE_MOTION_FRAC_MAX:
        reasons.append(f"motion_high({motion_fraction:.4f}>{GATE_MOTION_FRAC_MAX})")
    return "|".join(reasons) if reasons else "NONE"


def blake2b256(data: bytes) -> str:
    return hashlib.blake2b(data, digest_size=32).hexdigest()

# ---------------------------------------------------------------------------
# Single-camera capture worker
# ---------------------------------------------------------------------------

@dataclass
class FrameRecord:
    frame_idx: int
    ts: float
    entropy: float
    laplacian_var: float
    motion_fraction: float
    verdict: str
    reason: str
    frame_hash: str


@dataclass
class CaptureResult:
    camera_name: str
    node: str
    width: int
    height: int
    fps_target: float
    pixel_format: str
    frames_attempted: int = 0
    frames_captured: int = 0
    open_ok: bool = False
    error: str = ""
    records: list[FrameRecord] = field(default_factory=list)
    t_start: float = 0.0
    t_end: float = 0.0
    role: str = "unspecified"

    # computed after capture
    fps_achieved: float = 0.0
    pass_count: int = 0
    drop_count: int = 0
    drop_rate: float = 0.0
    drop_reasons: dict[str, int] = field(default_factory=dict)
    entropy_min: float = 0.0
    entropy_max: float = 0.0
    entropy_mean: float = 0.0
    laplacian_min: float = 0.0
    laplacian_max: float = 0.0
    laplacian_mean: float = 0.0
    motion_min: float = 0.0
    motion_max: float = 0.0
    motion_mean: float = 0.0
    jitter_mean_ms: float = 0.0
    jitter_max_ms: float = 0.0

    def summarise(self) -> None:
        if not self.records:
            return
        self.pass_count = sum(1 for r in self.records if r.verdict == "PASS")
        self.drop_count = sum(1 for r in self.records if r.verdict == "DROP")
        self.drop_rate = self.drop_count / len(self.records) if self.records else 0.0

        for r in self.records:
            if r.verdict == "DROP":
                for part in r.reason.split("|"):
                    key = part.split("(")[0] if "(" in part else part
                    self.drop_reasons[key] = self.drop_reasons.get(key, 0) + 1

        ent = [r.entropy for r in self.records]
        lap = [r.laplacian_var for r in self.records]
        mot = [r.motion_fraction for r in self.records]

        self.entropy_min, self.entropy_max = min(ent), max(ent)
        self.entropy_mean = sum(ent) / len(ent)
        self.laplacian_min, self.laplacian_max = min(lap), max(lap)
        self.laplacian_mean = sum(lap) / len(lap)
        self.motion_min, self.motion_max = min(mot), max(mot)
        self.motion_mean = sum(mot) / len(mot)

        ts_list = [r.ts for r in self.records]
        if len(ts_list) > 1:
            deltas = [(ts_list[i+1] - ts_list[i]) * 1000 for i in range(len(ts_list)-1)]
            self.jitter_mean_ms = sum(deltas) / len(deltas)
            self.jitter_max_ms = max(deltas)

        elapsed = self.t_end - self.t_start
        if elapsed > 0:
            self.fps_achieved = self.frames_captured / elapsed

    def to_dict(self) -> dict:
        return {
            "camera_name": self.camera_name,
            "node": self.node,
            "role": self.role,
            "width": self.width,
            "height": self.height,
            "fps_target": self.fps_target,
            "pixel_format": self.pixel_format,
            "open_ok": self.open_ok,
            "error": self.error,
            "frames_attempted": self.frames_attempted,
            "frames_captured": self.frames_captured,
            "fps_achieved": round(self.fps_achieved, 3),
            "pass_count": self.pass_count,
            "drop_count": self.drop_count,
            "drop_rate": round(self.drop_rate, 4),
            "drop_reasons": self.drop_reasons,
            "entropy_min": round(self.entropy_min, 4),
            "entropy_max": round(self.entropy_max, 4),
            "entropy_mean": round(self.entropy_mean, 4),
            "laplacian_min": round(self.laplacian_min, 2),
            "laplacian_max": round(self.laplacian_max, 2),
            "laplacian_mean": round(self.laplacian_mean, 2),
            "motion_min": round(self.motion_min, 6),
            "motion_max": round(self.motion_max, 6),
            "motion_mean": round(self.motion_mean, 6),
            "jitter_mean_ms": round(self.jitter_mean_ms, 2),
            "jitter_max_ms": round(self.jitter_max_ms, 2),
            "elapsed_s": round(self.t_end - self.t_start, 3),
        }


def run_capture(
    node: str,
    name: str,
    width: int,
    height: int,
    fps: float,
    n_frames: int,
    result: CaptureResult,
    role: str = "unspecified",
) -> None:
    result.role = role
    cap = cv2.VideoCapture(node, cv2.CAP_V4L2)
    if not cap.isOpened():
        result.error = f"failed to open {node}"
        return

    # Request MJPEG
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    cap.set(cv2.CAP_PROP_FPS, fps)

    # Verify negotiated
    actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    result.width = actual_w
    result.height = actual_h
    result.open_ok = True

    prev_gray: np.ndarray | None = None
    result.t_start = time.monotonic()

    for idx in range(n_frames):
        result.frames_attempted += 1
        ret, frame = cap.read()
        if not ret or frame is None:
            dr = FrameRecord(
                frame_idx=idx, ts=time.monotonic(),
                entropy=0.0, laplacian_var=0.0, motion_fraction=0.0,
                verdict="DROP", reason="read_failure",
                frame_hash="",
            )
            result.records.append(dr)
            continue

        result.frames_captured += 1
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        ent = compute_entropy(gray)
        lap = compute_laplacian_var(gray)
        mf = compute_motion_fraction(gray, prev_gray)
        verd = gate(ent, lap, mf)
        reason = drop_reason(ent, lap, mf) if verd == "DROP" else "NONE"
        fhash = blake2b256(frame.tobytes())

        dr = FrameRecord(
            frame_idx=idx, ts=time.monotonic(),
            entropy=ent, laplacian_var=lap, motion_fraction=mf,
            verdict=verd, reason=reason, frame_hash=fhash,
        )
        result.records.append(dr)
        prev_gray = gray

    result.t_end = time.monotonic()
    cap.release()
    result.summarise()


def dual_capture(
    cfg_a: dict, cfg_b: dict,
    n_frames: int,
    role_a: str = "unspecified",
    role_b: str = "unspecified",
) -> tuple[CaptureResult, CaptureResult]:
    res_a = CaptureResult(
        camera_name=cfg_a["name"], node=cfg_a["node"],
        width=cfg_a["width"], height=cfg_a["height"],
        fps_target=cfg_a["fps"], pixel_format="MJPG",
    )
    res_b = CaptureResult(
        camera_name=cfg_b["name"], node=cfg_b["node"],
        width=cfg_b["width"], height=cfg_b["height"],
        fps_target=cfg_b["fps"], pixel_format="MJPG",
    )
    t_a = threading.Thread(
        target=run_capture,
        args=(cfg_a["node"], cfg_a["name"], cfg_a["width"], cfg_a["height"],
              cfg_a["fps"], n_frames, res_a, role_a),
        daemon=True,
    )
    t_b = threading.Thread(
        target=run_capture,
        args=(cfg_b["node"], cfg_b["name"], cfg_b["width"], cfg_b["height"],
              cfg_b["fps"], n_frames, res_b, role_b),
        daemon=True,
    )
    t_a.start()
    t_b.start()
    t_a.join()
    t_b.join()
    return res_a, res_b

# ---------------------------------------------------------------------------
# Report writers
# ---------------------------------------------------------------------------

def write_json(path: Path, obj: Any) -> None:
    path.write_text(json.dumps(obj, indent=2, default=str))


def result_md_block(r: CaptureResult) -> str:
    d = r.to_dict()
    return f"""
### {r.camera_name} ({r.node}) — role: {r.role}

| Metric | Value |
|--------|-------|
| Open OK | {d['open_ok']} |
| Resolution | {d['width']}x{d['height']} |
| FPS target | {d['fps_target']} |
| FPS achieved | {d['fps_achieved']} |
| Frames attempted | {d['frames_attempted']} |
| Frames captured | {d['frames_captured']} |
| PASS count | {d['pass_count']} |
| DROP count | {d['drop_count']} |
| DROP rate | {d['drop_rate']:.1%} |
| Entropy mean (min/max) | {d['entropy_mean']:.3f} ({d['entropy_min']:.3f} / {d['entropy_max']:.3f}) |
| Laplacian mean (min/max) | {d['laplacian_mean']:.1f} ({d['laplacian_min']:.1f} / {d['laplacian_max']:.1f}) |
| Motion mean (min/max) | {d['motion_mean']:.4f} ({d['motion_min']:.4f} / {d['motion_max']:.4f}) |
| Jitter mean / max (ms) | {d['jitter_mean_ms']:.1f} / {d['jitter_max_ms']:.1f} |
| DROP reasons | {d['drop_reasons']} |
| Error | {d['error'] or 'none'} |
""".strip()

# ---------------------------------------------------------------------------
# Camera Presence Gate — must pass before any test phase runs
# ---------------------------------------------------------------------------

# USB kernel log patterns that indicate hardware instability
_USB_RESET_PATTERNS = [
    "USB disconnect",
    "reset high-speed USB device",
    "Cannot enable",
    "Maybe the USB cable is bad",
    "device descriptor read error",
    "unable to enumerate USB device",
    "ENODEV",
]

_MAX_GATE_RETRIES = 3


def _run_detection_commands(logs_dir: Path) -> dict[str, str]:
    """
    Run system detection commands and save each output to logs_dir.
    Returns mapping of label → output string.
    """
    import subprocess

    commands = {
        "lsusb":          (["lsusb"],                         "presence_gate_lsusb.txt"),
        "lsusb_tree":     (["lsusb", "-t"],                   "presence_gate_lsusb_tree.txt"),
        "v4l2_devices":   (["v4l2-ctl", "--list-devices"],    "presence_gate_v4l2_devices.txt"),
        "video_nodes":    (["ls", "-l", "/dev/video"],        "presence_gate_video_nodes.txt"),
        "dmesg_tail":     (["dmesg"],                         "presence_gate_dmesg_tail.txt"),
    }

    outputs: dict[str, str] = {}
    for label, (cmd, fname) in commands.items():
        try:
            if label == "video_nodes":
                # ls -l /dev/video* requires shell glob
                result = subprocess.run(
                    "ls -l /dev/video*", shell=True, capture_output=True, text=True, timeout=10
                )
            elif label == "dmesg_tail":
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                # keep only last 120 lines for the gate record; save full log
                lines = result.stdout.splitlines()
                result_text = "\n".join(lines[-120:])
                (logs_dir / fname).write_text(result.stdout)
                outputs[label] = result_text
                continue
            else:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            text = result.stdout + result.stderr
            (logs_dir / fname).write_text(text)
            outputs[label] = text
        except Exception as exc:
            outputs[label] = f"ERROR: {exc}"
            (logs_dir / fname).write_text(outputs[label])

    return outputs


def _scan_usb_resets(dmesg_text: str) -> list[str]:
    """Return list of matched USB-instability lines from dmesg output."""
    hits = []
    for line in dmesg_text.splitlines():
        if any(pat in line for pat in _USB_RESET_PATTERNS):
            hits.append(line.strip())
    return hits


def _probe_camera(node: str, name: str) -> dict:
    """
    Hard check: node exists, V4L2 opens, and at least 3 frames read cleanly.
    """
    result: dict = {
        "node": node,
        "name": name,
        "node_exists": False,
        "open_ok": False,
        "frames_read": 0,
        "gate_pass": False,
        "failure_reason": "",
        "hold_label": "",
    }

    if not os.path.exists(node):
        result["failure_reason"] = f"device_node_absent: {node} not in /dev"
        result["hold_label"] = (
            "CAMERA_A_MISSING_HOLD" if name == CAMERA_A_NAME else "CAMERA_B_MISSING_HOLD"
        )
        return result
    result["node_exists"] = True

    cap = cv2.VideoCapture(node, cv2.CAP_V4L2)
    if not cap.isOpened():
        result["failure_reason"] = f"v4l2_open_failed: could not open {node}"
        result["hold_label"] = (
            "CAMERA_A_MISSING_HOLD" if name == CAMERA_A_NAME else "CAMERA_B_MISSING_HOLD"
        )
        return result
    result["open_ok"] = True

    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 15)

    for _ in range(5):
        ret, frame = cap.read()
        if ret and frame is not None:
            result["frames_read"] += 1
        if result["frames_read"] >= 3:
            break
    cap.release()

    if result["frames_read"] < 3:
        result["failure_reason"] = (
            f"insufficient_frames: read {result['frames_read']}/3 "
            f"(ENODEV / USB reset likely)"
        )
        result["hold_label"] = (
            "CAMERA_A_USB_STABILITY_HOLD"
            if name == CAMERA_A_NAME
            else "CAMERA_B_USB_STABILITY_HOLD"
        )
        return result

    result["gate_pass"] = True
    return result


def _write_gate_report(out_dir: Path, gate_status: str, probe_a: dict, probe_b: dict,
                       usb_hits: list[str], attempt: int) -> None:
    record = {
        "gate": "camera_presence_gate",
        "gate_status": gate_status,
        "gate_pass": gate_status == "DUAL_CAMERA_PRESENCE_GATE_PASS",
        "attempt": attempt,
        "camera_a": probe_a,
        "camera_b": probe_b,
        "usb_reset_events_detected": len(usb_hits),
        "usb_reset_lines": usb_hits[:20],  # cap to 20 lines in JSON
        "proposed_by": PROPOSED_BY,
        "proposed_at_utc": PROPOSED_AT,
        "ratified_by": None,
    }
    write_json(out_dir / "camera_presence_gate.json", record)

    # Derive per-camera status labels
    a_status = "PRESENT" if probe_a["gate_pass"] else probe_a.get("hold_label", "HOLD")
    b_status = "PRESENT" if probe_b["gate_pass"] else probe_b.get("hold_label", "HOLD")
    stability_note = ""
    if usb_hits:
        stability_note = (
            f"\n**USB instability events detected in dmesg**: {len(usb_hits)}\n\n"
            + "\n".join(f"  `{h}`" for h in usb_hits[:10])
        )

    md = f"""# PH6 Dual USB Camera — Presence Gate Report
**PROPOSED** — Hardware readiness gate. Not a PSEUDO-A frame verdict.

## Gate Status

**{gate_status}**

| Camera | Node | Present | Capture Node Confirmed | Hold Label |
|--------|------|---------|----------------------|------------|
| CAMERA_A ({CAMERA_A_NAME}) | {probe_a['node']} | {probe_a['node_exists']} | {probe_a['open_ok']} | {probe_a.get('hold_label') or '—'} |
| CAMERA_B ({CAMERA_B_NAME}) | {probe_b['node']} | {probe_b['node_exists']} | {probe_b['open_ok']} | {probe_b.get('hold_label') or '—'} |

```
CAMERA_A_PRESENT = {str(probe_a['node_exists']).lower()}
CAMERA_B_PRESENT = {str(probe_b['node_exists']).lower()}
CAMERA_A_CAPTURE_NODE_CONFIRMED = {str(probe_a['open_ok']).lower()}
CAMERA_B_CAPTURE_NODE_CONFIRMED = {str(probe_b['open_ok']).lower()}
```
{stability_note}

## Camera A

- Node: `{probe_a['node']}`
- Node exists: {probe_a['node_exists']}
- V4L2 open: {probe_a['open_ok']}
- Frames read: {probe_a['frames_read']} / 3 required
- Gate pass: {probe_a['gate_pass']}
- Failure reason: {probe_a['failure_reason'] or 'none'}

## Camera B

- Node: `{probe_b['node']}`
- Node exists: {probe_b['node_exists']}
- V4L2 open: {probe_b['open_ok']}
- Frames read: {probe_b['frames_read']} / 3 required
- Gate pass: {probe_b['gate_pass']}
- Failure reason: {probe_b['failure_reason'] or 'none'}

## Note

This is a hardware readiness gate, not an authority verdict.
`DUAL_CAMERA_PRESENCE_GATE_PASS` / `DUAL_CAMERA_PRESENCE_GATE_HOLD` labels
are distinct from PSEUDO-A `PASS` / `DROP` frame verdicts.

---
*proposed_by: {PROPOSED_BY} | ratified_by: null*
"""
    (out_dir / "camera_presence_gate.md").write_text(md)


def camera_presence_gate(out_dir: Path) -> None:
    """
    Dual-camera hardware presence gate.

    Runs before every test phase. Checks:
      1. System detection commands (lsusb, v4l2-ctl, dmesg) — saved to logs/
      2. dmesg scanned for USB reset / instability events
      3. Each camera node exists, opens under V4L2, and delivers ≥3 frames

    If either camera fails: prints operator instructions, offers bounded retry
    (max 3), writes gate report, then calls sys.exit(1).

    Gate labels used (not PSEUDO-A verdicts):
      DUAL_CAMERA_PRESENCE_GATE_PASS
      DUAL_CAMERA_PRESENCE_GATE_HOLD
      CAMERA_A_MISSING_HOLD
      CAMERA_B_MISSING_HOLD
      CAMERA_A_USB_STABILITY_HOLD
      CAMERA_B_USB_STABILITY_HOLD
      USB_CAMERA_STABILITY_HOLD
    """
    logs_dir = out_dir / "logs"
    logs_dir.mkdir(exist_ok=True)

    for attempt in range(1, _MAX_GATE_RETRIES + 2):  # +2: initial run + 3 retries
        print(f"\n[GATE] === Dual-Camera Presence Gate — attempt {attempt} ===")

        # Run and save detection commands
        print("[GATE] Running detection commands ...")
        det = _run_detection_commands(logs_dir)

        # Scan dmesg for USB instability
        usb_hits = _scan_usb_resets(det.get("dmesg_tail", ""))
        if usb_hits:
            print(f"[GATE] WARNING — {len(usb_hits)} USB instability event(s) in dmesg:")
            for line in usb_hits[:5]:
                print(f"       {line}")
            if len(usb_hits) > 5:
                print(f"       ... and {len(usb_hits) - 5} more (see logs/presence_gate_dmesg_tail.txt)")

        # Probe each camera
        probe_a = _probe_camera(CAMERA_A_NODE, CAMERA_A_NAME)
        probe_b = _probe_camera(CAMERA_B_NODE, CAMERA_B_NAME)

        for probe in (probe_a, probe_b):
            status = "PASS" if probe["gate_pass"] else probe.get("hold_label", "HOLD")
            detail = probe["failure_reason"] if not probe["gate_pass"] else f"frames_read={probe['frames_read']}"
            print(f"[GATE] {probe['name']} ({probe['node']}): {status}  {detail}")

        both_pass = probe_a["gate_pass"] and probe_b["gate_pass"]

        # Determine overall gate status label
        if both_pass:
            gate_status = "DUAL_CAMERA_PRESENCE_GATE_PASS"
        else:
            if usb_hits:
                gate_status = "USB_CAMERA_STABILITY_HOLD"
            else:
                gate_status = "DUAL_CAMERA_PRESENCE_GATE_HOLD"

        _write_gate_report(out_dir, gate_status, probe_a, probe_b, usb_hits, attempt)

        if both_pass:
            print("[GATE] Both cameras present and capturable.")
            print(f"[GATE] {gate_status} — proceeding to tests.")
            return

        # Gate failed — print operator instructions
        failed = [p for p in (probe_a, probe_b) if not p["gate_pass"]]
        failed_names = ", ".join(p["name"] for p in failed)

        print(f"""
[GATE] ============================================================
[GATE] DUAL_CAMERA_PRESENCE_GATE = HOLD

Only {sum(1 for p in (probe_a, probe_b) if p['gate_pass'])}/2 valid USB cameras detected.
Missing or unstable: {failed_names}

Recommended actions:
  1. Unplug and reconnect Camera B.
  2. Try a different USB port.
  3. Replace the USB cable.
  4. If the camera resets again, use a powered USB hub.
  5. Re-run the presence gate before starting the test.

No dual-camera test will run until both cameras are detected.
[GATE] ============================================================""")

        if attempt > _MAX_GATE_RETRIES:
            break

        # Offer retry
        print(f"\n[GATE] Retry {attempt}/{_MAX_GATE_RETRIES}: reseat/reconnect both cameras.")
        try:
            input("[GATE] Press ENTER when ready to retry, or Ctrl+C to abort: ")
        except KeyboardInterrupt:
            print("\n[GATE] Aborted by operator.")
            break
        import time as _time
        print("[GATE] Waiting 5 seconds ...")
        _time.sleep(5)

    # All retries exhausted or operator aborted
    gate_status = "DUAL_CAMERA_PRESENCE_GATE_HOLD"
    _write_gate_report(out_dir, gate_status, probe_a, probe_b, usb_hits, attempt)
    print("[GATE] HARD ABORT — gate retries exhausted. Fix hardware and re-run.")
    print("[GATE] Gate report written to camera_presence_gate.json / .md")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Phase 1 — Smoke test
# ---------------------------------------------------------------------------

BASELINE = {"width": 640, "height": 480, "fps": 15}

def phase_smoke(out_dir: Path) -> dict:
    print("[SMOKE] Starting 300-frame dual smoke test at 640x480 @ 15fps MJPEG ...")
    cfg_a = {"node": CAMERA_A_NODE, "name": CAMERA_A_NAME, **BASELINE}
    cfg_b = {"node": CAMERA_B_NODE, "name": CAMERA_B_NAME, **BASELINE}
    ra, rb = dual_capture(cfg_a, cfg_b, n_frames=300,
                          role_a="smoke_test", role_b="smoke_test")

    both_open = ra.open_ok and rb.open_ok
    bw_ok = not (ra.frames_captured == 0 and rb.frames_captured == 0)

    summary = {
        "phase": "smoke_test",
        "n_frames": 300,
        "profile": "640x480@15fps MJPG",
        "both_cameras_open": both_open,
        "usb_bandwidth_ok": bw_ok,
        "camera_a": ra.to_dict(),
        "camera_b": rb.to_dict(),
        "verdict": "SMOKE_PASS" if (both_open and bw_ok and ra.frames_captured > 250 and rb.frames_captured > 250) else "SMOKE_HOLD",
        "proposed_by": PROPOSED_BY,
        "proposed_at_utc": PROPOSED_AT,
        "ratified_by": None,
    }

    write_json(out_dir / "dual_smoke_report.json", summary)
    md = f"""# PH6 Dual USB Camera — Smoke Test Report
PROPOSED — Lane-2 advisory only. Operator ratification required.

**Verdict**: {summary['verdict']}
**Both cameras open**: {both_open}
**USB bandwidth OK**: {bw_ok}
**Profile**: {summary['profile']}

{result_md_block(ra)}

---

{result_md_block(rb)}

---
*proposed_by: {PROPOSED_BY} | ratified_by: null*
"""
    (out_dir / "dual_smoke_report.md").write_text(md)
    print(f"[SMOKE] {summary['verdict']}  A={ra.frames_captured}/300 B={rb.frames_captured}/300")
    return summary

# ---------------------------------------------------------------------------
# Phase 2 — Same Vision
# ---------------------------------------------------------------------------

def phase_same_vision(out_dir: Path) -> dict:
    print("[SAME_VISION] 1200 frames @ 640x480 @ 15fps MJPEG ...")
    cfg_a = {"node": CAMERA_A_NODE, "name": CAMERA_A_NAME, **BASELINE}
    cfg_b = {"node": CAMERA_B_NODE, "name": CAMERA_B_NAME, **BASELINE}
    ra, rb = dual_capture(cfg_a, cfg_b, n_frames=1200,
                          role_a="same_vision", role_b="same_vision")

    summary = {
        "phase": "same_vision_test",
        "n_frames": 1200,
        "profile": "640x480@15fps MJPG",
        "camera_a": ra.to_dict(),
        "camera_b": rb.to_dict(),
        "stability_delta": {
            "fps_diff": abs(ra.fps_achieved - rb.fps_achieved),
            "drop_rate_diff": abs(ra.drop_rate - rb.drop_rate),
            "entropy_mean_diff": abs(ra.entropy_mean - rb.entropy_mean),
            "laplacian_mean_diff": abs(ra.laplacian_mean - rb.laplacian_mean),
        },
        "proposed_by": PROPOSED_BY,
        "proposed_at_utc": PROPOSED_AT,
        "ratified_by": None,
    }

    write_json(out_dir / "same_vision_test_report.json", summary)
    delta = summary["stability_delta"]
    md = f"""# PH6 Dual USB Camera — Same Vision Test Report
PROPOSED — Lane-2 advisory only. Operator ratification required.

**Profile**: {summary['profile']} | **Frames**: 1200 per camera

## Stability Delta (A vs B)

| Metric | Delta |
|--------|-------|
| FPS diff | {delta['fps_diff']:.3f} |
| DROP rate diff | {delta['drop_rate_diff']:.1%} |
| Entropy mean diff | {delta['entropy_mean_diff']:.4f} |
| Laplacian mean diff | {delta['laplacian_mean_diff']:.1f} |

## Camera A

{result_md_block(ra)}

## Camera B

{result_md_block(rb)}

---
*proposed_by: {PROPOSED_BY} | ratified_by: null*
"""
    (out_dir / "same_vision_test_report.md").write_text(md)
    print(f"[SAME_VISION] A drop={ra.drop_rate:.1%} B drop={rb.drop_rate:.1%}")
    return summary

# ---------------------------------------------------------------------------
# Phase 3 — Opposite Role
# ---------------------------------------------------------------------------

def phase_opposite_role(out_dir: Path) -> dict:
    print("[OPP_ROLE] Pass 1: A=primary B=context ...")
    cfg_a = {"node": CAMERA_A_NODE, "name": CAMERA_A_NAME, **BASELINE}
    cfg_b = {"node": CAMERA_B_NODE, "name": CAMERA_B_NAME, **BASELINE}

    ra1, rb1 = dual_capture(cfg_a, cfg_b, n_frames=1200,
                            role_a="primary_measurement", role_b="environmental_context")
    print("[OPP_ROLE] Pass 2: A=context B=primary ...")
    ra2, rb2 = dual_capture(cfg_a, cfg_b, n_frames=1200,
                            role_a="environmental_context", role_b="primary_measurement")

    def primary_score(r: CaptureResult) -> float:
        # Higher = better for primary measurement
        # Rewards: high laplacian, high entropy, low drop rate, stable fps
        if not r.open_ok or r.frames_captured == 0:
            return 0.0
        return (
            r.laplacian_mean / 1000.0
            + r.entropy_mean / 8.0
            + (1.0 - r.drop_rate)
            + min(r.fps_achieved / r.fps_target, 1.0)
        ) / 4.0

    score_a_p1 = primary_score(ra1)
    score_b_p2 = primary_score(rb2)

    if score_a_p1 >= score_b_p2:
        recommended_primary = CAMERA_A_NAME
        recommended_context = CAMERA_B_NAME
    else:
        recommended_primary = CAMERA_B_NAME
        recommended_context = CAMERA_A_NAME

    summary = {
        "phase": "opposite_role_test",
        "n_frames_per_pass": 1200,
        "profile": "640x480@15fps MJPG",
        "pass_1": {
            "camera_a_role": "primary_measurement",
            "camera_b_role": "environmental_context",
            "camera_a": ra1.to_dict(),
            "camera_b": rb1.to_dict(),
        },
        "pass_2": {
            "camera_a_role": "environmental_context",
            "camera_b_role": "primary_measurement",
            "camera_a": ra2.to_dict(),
            "camera_b": rb2.to_dict(),
        },
        "primary_score_a_as_primary": round(score_a_p1, 4),
        "primary_score_b_as_primary": round(score_b_p2, 4),
        "recommended_primary": recommended_primary,
        "recommended_context": recommended_context,
        "advisory_note": "PROPOSED role assignment — Lane-2 advisory only; Lane-1 authority not exercised",
        "proposed_by": PROPOSED_BY,
        "proposed_at_utc": PROPOSED_AT,
        "ratified_by": None,
    }

    write_json(out_dir / "opposite_role_test_report.json", summary)
    md = f"""# PH6 Dual USB Camera — Opposite Role Test Report
PROPOSED — Lane-2 advisory only. Operator ratification required.

**Profile**: {summary['profile']} | **Frames**: 1200 per camera per pass

## Role Recommendation (PROPOSED)

| | Score | Recommended Role |
|-|-------|-----------------|
| {CAMERA_A_NAME} as primary | {score_a_p1:.4f} | {'PRIMARY' if recommended_primary == CAMERA_A_NAME else 'CONTEXT'} |
| {CAMERA_B_NAME} as primary | {score_b_p2:.4f} | {'PRIMARY' if recommended_primary == CAMERA_B_NAME else 'CONTEXT'} |

**PROPOSED PRIMARY**: {recommended_primary}
**PROPOSED CONTEXT**: {recommended_context}

> Advisory note: {summary['advisory_note']}

## Pass 1: A=primary, B=context

{result_md_block(ra1)}

---

{result_md_block(rb1)}

## Pass 2: A=context, B=primary

{result_md_block(ra2)}

---

{result_md_block(rb2)}

---
*proposed_by: {PROPOSED_BY} | ratified_by: null*
"""
    (out_dir / "opposite_role_test_report.md").write_text(md)
    print(f"[OPP_ROLE] PROPOSED primary={recommended_primary} context={recommended_context}")
    return summary

# ---------------------------------------------------------------------------
# Phase 4 — Complementary
# ---------------------------------------------------------------------------

def phase_complementary(out_dir: Path) -> dict:
    print("[COMPLEMENTARY] A=640x480 detail, B=1280x720 wide/context ...")
    cfg_a = {"node": CAMERA_A_NODE, "name": CAMERA_A_NAME,
             "width": 640, "height": 480, "fps": 15}
    cfg_b = {"node": CAMERA_B_NODE, "name": CAMERA_B_NAME,
             "width": 1280, "height": 720, "fps": 15}

    ra, rb = dual_capture(cfg_a, cfg_b, n_frames=1200,
                          role_a="detail_measurement", role_b="wide_context")

    # Note actual negotiated resolution for Camera B
    b_resolution_note = (
        f"Camera B negotiated: {rb.width}x{rb.height} "
        f"(requested 1280x720)"
    )

    summary = {
        "phase": "complementary_test",
        "n_frames": 1200,
        "camera_a_profile": "640x480@15fps MJPG (detail/measurement)",
        "camera_b_profile": "1280x720@15fps MJPG (wide/context)",
        "camera_a": ra.to_dict(),
        "camera_b": rb.to_dict(),
        "resolution_note": b_resolution_note,
        "authority_isolation_note": (
            "Camera B advisory metrics do NOT influence Camera A PASS/DROP. "
            "Each camera runs its own PSEUDO-A lane independently."
        ),
        "proposed_by": PROPOSED_BY,
        "proposed_at_utc": PROPOSED_AT,
        "ratified_by": None,
    }

    write_json(out_dir / "complementary_test_report.json", summary)
    md = f"""# PH6 Dual USB Camera — Complementary Test Report
PROPOSED — Lane-2 advisory only. Operator ratification required.

**Camera A**: {summary['camera_a_profile']}
**Camera B**: {summary['camera_b_profile']}
**Resolution note**: {b_resolution_note}

> {summary['authority_isolation_note']}

## Camera A — Detail / Measurement

{result_md_block(ra)}

---

## Camera B — Wide / Context

{result_md_block(rb)}

---
*proposed_by: {PROPOSED_BY} | ratified_by: null*
"""
    (out_dir / "complementary_test_report.md").write_text(md)
    print(f"[COMPLEMENTARY] A={ra.frames_captured}/1200 B={rb.frames_captured}/1200  "
          f"B_res={rb.width}x{rb.height}")
    return summary

# ---------------------------------------------------------------------------
# Camera inventory
# ---------------------------------------------------------------------------

def write_inventory(out_dir: Path) -> None:
    inventory = {
        "inventory_utc": "2026-06-03T05:52:15Z",
        "cameras": [
            {
                "label": "CAMERA_A",
                "node_primary": CAMERA_A_NODE,
                "node_secondary": "/dev/video1",
                "name": CAMERA_A_NAME,
                "usb_id": CAMERA_A_USB_ID,
                "manufacturer": "Jieli Technology",
                "bus": "USB 2.0 (xhci-hcd.1)",
                "formats": {
                    "MJPG": ["640x480@30fps", "640x480@10fps", "1280x720@30fps", "1280x720@10fps"],
                    "YUYV": ["640x480@10fps", "320x240@30fps", "320x240@10fps"],
                },
                "safe_baseline": "640x480@15fps MJPG",
                "max_mjpg": "1280x720@30fps",
                "notes": "Limited YUYV; /dev/video1 has no formats (metadata/control only)",
            },
            {
                "label": "CAMERA_B",
                "node_primary": CAMERA_B_NODE,
                "node_secondary": "/dev/video3",
                "name": CAMERA_B_NAME,
                "usb_id": CAMERA_B_USB_ID,
                "manufacturer": "Microdia",
                "bus": "USB 2.0 (xhci-hcd.0)",
                "formats": {
                    "MJPG": [
                        "1920x1080@30fps", "1280x1024@30fps", "1280x960@30fps",
                        "1280x720@30fps", "1024x768@30fps", "848x480@30fps",
                        "800x600@30fps", "640x480@30fps", "320x240@30fps",
                        "176x144@30fps", "160x120@30fps",
                    ],
                    "YUYV": ["640x480@30fps", "1920x1080@5fps", "1280x720@10fps"],
                },
                "safe_baseline": "640x480@15fps MJPG",
                "max_mjpg": "1920x1080@30fps",
                "notes": "Highly capable; /dev/video3 has no formats (metadata/control only)",
            },
        ],
        "stable_mapping_note": (
            "Mapping confirmed by USB-ID and udevadm. "
            "video0/video2 are the real capture streams. "
            "video1/video3 are metadata/control nodes with no capture formats."
        ),
        "proposed_by": PROPOSED_BY,
        "ratified_by": None,
    }

    write_json(out_dir / "camera_inventory.json", inventory)

    md = f"""# PH6 Dual USB Camera Inventory
PROPOSED — Lane-2 advisory only.

## Device Mapping

| Label | Node | USB ID | Manufacturer | Max MJPG | Safe Baseline |
|-------|------|--------|-------------|----------|--------------|
| CAMERA_A | /dev/video0 | 4c4a:4a55 | Jieli Technology (DV20 USB) | 1280x720@30fps | 640x480@15fps MJPG |
| CAMERA_B | /dev/video2 | 0c45:636b | Microdia (Streaming Cam) | 1920x1080@30fps | 640x480@15fps MJPG |

## Stable Mapping Note

Mapping confirmed by USB-ID and udevadm.
`/dev/video1` and `/dev/video3` are metadata/control nodes (no capture formats).
`/dev/video0` and `/dev/video2` are the real capture streams.

## Camera A — DV20 USB (Jieli Technology 4c4a:4a55)

**MJPG**: 640x480@30fps, 1280x720@30fps
**YUYV**: 640x480@10fps, 320x240@30fps
**Note**: Limited YUYV capability; MJPG preferred.

## Camera B — Streaming Cam (Microdia 0c45:636b)

**MJPG**: 1920x1080, 1280x1024, 1280x960, 1280x720, 1024x768, 848x480, 800x600, 640x480, 320x240, 176x144, 160x120 — all @30fps
**YUYV**: 640x480@30fps (5fps at high res)
**Note**: Highly capable; both USB buses are separate (no shared bandwidth contention).

---
*proposed_by: {PROPOSED_BY} | ratified_by: null*
"""
    (out_dir / "camera_inventory.md").write_text(md)

# ---------------------------------------------------------------------------
# Final report
# ---------------------------------------------------------------------------

def write_final_report(
    out_dir: Path,
    smoke: dict,
    same_vision: dict,
    opp_role: dict,
    comp: dict,
) -> None:
    ra_sv = same_vision["camera_a"]
    rb_sv = same_vision["camera_b"]
    ra_c = comp["camera_a"]
    rb_c = comp["camera_b"]

    rec_primary = opp_role["recommended_primary"]
    rec_context = opp_role["recommended_context"]

    # Derive clearance labels
    def clearance_label(name: str) -> str:
        if rec_primary == name:
            return "CAMERA_A_RECOMMENDED_PRIMARY" if name == CAMERA_A_NAME else "CAMERA_B_RECOMMENDED_PRIMARY"
        return "CAMERA_A_RECOMMENDED_CONTEXT" if name == CAMERA_A_NAME else "CAMERA_B_RECOMMENDED_CONTEXT"

    label_a = clearance_label(CAMERA_A_NAME)
    label_b = clearance_label(CAMERA_B_NAME)

    dual_op_verdict = "DUAL_CAMERA_OPERATION_PROVISIONAL_PASS"
    if smoke["verdict"] != "SMOKE_PASS":
        dual_op_verdict = "DUAL_CAMERA_OPERATION_HOLD"
    if not smoke["usb_bandwidth_ok"]:
        dual_op_verdict = "USB_BANDWIDTH_HOLD"

    final = {
        "report": "PH6_DUAL_USB_CAMERA_FINAL_REPORT",
        "generated_utc": "2026-06-03T00:00:00Z",
        "camera_a": {"label": label_a, "node": CAMERA_A_NODE, "usb_id": CAMERA_A_USB_ID},
        "camera_b": {"label": label_b, "node": CAMERA_B_NODE, "usb_id": CAMERA_B_USB_ID},
        "dual_operation_verdict": dual_op_verdict,
        "smoke_verdict": smoke["verdict"],
        "usb_bandwidth_ok": smoke["usb_bandwidth_ok"],
        "same_vision_drop_rate_a": ra_sv["drop_rate"],
        "same_vision_drop_rate_b": rb_sv["drop_rate"],
        "complementary_resolution_b_actual": f"{rb_c['width']}x{rb_c['height']}",
        "recommended_primary": rec_primary,
        "recommended_context": rec_context,
        "proposed_by": PROPOSED_BY,
        "proposed_at_utc": PROPOSED_AT,
        "ratified_by": None,
    }
    write_json(out_dir / "PH6_DUAL_USB_CAMERA_FINAL_REPORT.json", final)

    md = f"""# PH6 Dual USB Camera — Final Engineering Report
**PROPOSED** — Lane-2 advisory only. Operator ratification required before any promotion.

---

## 1. Camera Inventory

| Label | Node | USB ID | Manufacturer |
|-------|------|--------|-------------|
| CAMERA_A | /dev/video0 | 4c4a:4a55 | Jieli Technology (DV20 USB) |
| CAMERA_B | /dev/video2 | 0c45:636b | Microdia (Streaming Cam) |

## 2. Device Mapping

Stable. Confirmed by USB-ID and udevadm.
`/dev/video1`, `/dev/video3` are metadata/control nodes — no capture.

## 3. Supported Modes

| Camera | Best MJPG | Safe Baseline |
|--------|-----------|--------------|
| CAMERA_A (DV20) | 1280x720@30fps | 640x480@15fps |
| CAMERA_B (Streaming Cam) | 1920x1080@30fps | 640x480@15fps |

## 4. Selected Safe Modes

- Smoke / Same Vision / Opposite Role: **640x480 @ 15fps MJPG** (both cameras)
- Complementary: Camera A **640x480 @ 15fps MJPG**, Camera B **1280x720 @ 15fps MJPG**

## 5. Same Vision Test Results

| Metric | CAMERA_A | CAMERA_B |
|--------|----------|----------|
| FPS achieved | {ra_sv['fps_achieved']} | {rb_sv['fps_achieved']} |
| PASS count | {ra_sv['pass_count']} | {rb_sv['pass_count']} |
| DROP count | {ra_sv['drop_count']} | {rb_sv['drop_count']} |
| DROP rate | {ra_sv['drop_rate']:.1%} | {rb_sv['drop_rate']:.1%} |
| Entropy mean | {ra_sv['entropy_mean']} | {rb_sv['entropy_mean']} |
| Laplacian mean | {ra_sv['laplacian_mean']} | {rb_sv['laplacian_mean']} |
| Motion mean | {ra_sv['motion_mean']} | {rb_sv['motion_mean']} |

## 6. Opposite Role Test Results

Recommended primary (PROPOSED): **{rec_primary}**
Recommended context (PROPOSED): **{rec_context}**

Primary score A-as-primary: {opp_role['primary_score_a_as_primary']}
Primary score B-as-primary: {opp_role['primary_score_b_as_primary']}

## 7. Complementary Test Results

| Camera | Role | Resolution (actual) | FPS achieved | DROP rate |
|--------|------|-------------------|-------------|----------|
| CAMERA_A | detail/measurement | {ra_c['width']}x{ra_c['height']} | {ra_c['fps_achieved']} | {ra_c['drop_rate']:.1%} |
| CAMERA_B | wide/context | {rb_c['width']}x{rb_c['height']} | {rb_c['fps_achieved']} | {rb_c['drop_rate']:.1%} |

## 8. Best Role Assignment (PROPOSED)

| Camera | PROPOSED Role |
|--------|--------------|
| {CAMERA_A_NAME} (/dev/video0) | {'Primary measurement' if rec_primary == CAMERA_A_NAME else 'Environmental context'} |
| {CAMERA_B_NAME} (/dev/video2) | {'Primary measurement' if rec_primary == CAMERA_B_NAME else 'Environmental context'} |

## 9. Failure Modes Observed

*(See individual phase reports for per-frame DROP reason distributions.)*

## 10. USB Bandwidth Issues

Cameras are on separate USB buses (xhci-hcd.0 and xhci-hcd.1).
USB bandwidth conflict risk: LOW.
Smoke test USB bandwidth OK: {smoke['usb_bandwidth_ok']}

## 11. Format Negotiation Issues

Camera A: YUYV capability limited — MJPG preferred at all resolutions.
Camera B: MJPG up to 1920x1080@30fps; YUYV viable at 640x480.
Both cameras: `/dev/video1`, `/dev/video3` have no capture formats (metadata/control only).

## 12. Recommended Next Test

1. Increase Camera B to 1920x1080 MJPG and re-run Same Vision at that resolution
2. Evaluate Camera A YUYV at 640x480@10fps for low-bandwidth ingest scenario
3. Run 12,000-frame endurance test once provisional pass confirmed by operator

## 13. Camera Clearance Assessment (PROPOSED)

| Camera | Primary Measurement | Context Measurement | Advisory Only | Not Recommended |
|--------|--------------------|--------------------|--------------|-----------------|
| CAMERA_A (DV20) | {'**YES (PROPOSED)**' if rec_primary == CAMERA_A_NAME else 'candidate'} | {'**YES (PROPOSED)**' if rec_context == CAMERA_A_NAME else 'candidate'} | — | — |
| CAMERA_B (Streaming Cam) | {'**YES (PROPOSED)**' if rec_primary == CAMERA_B_NAME else 'candidate'} | {'**YES (PROPOSED)**' if rec_context == CAMERA_B_NAME else 'candidate'} | — | — |

## 14. Dual Camera Operation Verdict

**{dual_op_verdict}**

---
*proposed_by: {PROPOSED_BY} | proposed_at_utc: {PROPOSED_AT} | ratified_by: null*
"""
    (out_dir / "PH6_DUAL_USB_CAMERA_FINAL_REPORT.md").write_text(md)
    print(f"\n[FINAL] Verdict: {dual_op_verdict}")
    print(f"[FINAL] Recommended primary: {rec_primary}")
    print(f"[FINAL] Recommended context: {rec_context}")


# ---------------------------------------------------------------------------
# README
# ---------------------------------------------------------------------------

def write_readme(out_dir: Path) -> None:
    (out_dir / "README.md").write_text(f"""# PH6 Dual USB Camera Test — {out_dir.name}
PROPOSED — Lane-2 advisory only.

## Files

| File | Description |
|------|-------------|
| camera_inventory.md / .json | Device mapping and capability summary |
| dual_smoke_report.md / .json | Phase 1: 300-frame smoke test |
| same_vision_test_report.md / .json | Phase 2: 1200-frame same profile test |
| opposite_role_test_report.md / .json | Phase 3: role-swap test, 2 passes |
| complementary_test_report.md / .json | Phase 4: A=640x480, B=1280x720 |
| PH6_DUAL_USB_CAMERA_FINAL_REPORT.md / .json | Final engineering report |
| v4l2_*.txt, formats_*.txt, udevadm_*.txt | Raw capability logs |
| lsusb_cameras.txt | USB device inventory |

## Camera Mapping

| Label | Node | USB ID | Manufacturer |
|-------|------|--------|-------------|
| CAMERA_A | /dev/video0 | 4c4a:4a55 | Jieli Technology (DV20 USB) |
| CAMERA_B | /dev/video2 | 0c45:636b | Microdia (Streaming Cam) |

*proposed_by: {PROPOSED_BY} | ratified_by: null*
""")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

EVIDENCE_REPORT_NAMES = (
    "PH6_DUAL_USB_CAMERA_FINAL_REPORT.json",
    "dual_smoke_report.json",
    "same_vision_test_report.json",
    "opposite_role_test_report.json",
    "complementary_test_report.json",
)


def main() -> None:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_dir = Path(f"/home/jack/PH6_SOURCE/TESTS/DUAL_USB_CAMERA/{run_id}")

    if out_dir.exists() and any((out_dir / name).exists() for name in EVIDENCE_REPORT_NAMES):
        raise RuntimeError(f"EVIDENCE_DIRECTORY_ALREADY_EXISTS: {out_dir}")

    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"[INIT] Output dir: {out_dir}")
    print(f"[INIT] CAMERA_A = {CAMERA_A_NODE} ({CAMERA_A_NAME})")
    print(f"[INIT] CAMERA_B = {CAMERA_B_NODE} ({CAMERA_B_NAME})")

    # Hard presence gate — must pass before any test phase runs.
    # If either camera is absent, mis-enumerated, or can't deliver 3 frames,
    # the run aborts here with a written gate record and exit code 1.
    camera_presence_gate(out_dir)

    write_inventory(out_dir)
    write_readme(out_dir)

    smoke = phase_smoke(out_dir)

    same_v = phase_same_vision(out_dir)
    opp_r = phase_opposite_role(out_dir)
    comp = phase_complementary(out_dir)

    write_final_report(out_dir, smoke, same_v, opp_r, comp)

    print(f"\n[DONE] All reports written to {out_dir}")
    print("[DONE] PROPOSED — awaiting operator ratification.")


if __name__ == "__main__":
    main()
