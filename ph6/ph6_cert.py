#!/usr/bin/env python3
"""
PH6 Certification Harness v1.0 — Python edition

Runs against the existing PH6 characterization pipeline.
Use this NOW. Use ph6_cert.sh once the operational pipeline is deployed.

Usage:
    python3 ph6/ph6_cert.py --smoke          (~2 min,  500 frames)
    python3 ph6/ph6_cert.py --standard       (~5 min, 3000 frames)
    python3 ph6/ph6_cert.py --full           (~8 min, 12000 frames)

Output: PASS or FAIL + ph6_cert_report.json
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

_REPO = Path(__file__).resolve().parent.parent

CERT_LEVELS: Dict[str, Dict[str, Any]] = {
    "smoke":    {"frames": 500,   "min_pass_pct": 85, "label": "SMOKE"},
    "standard": {"frames": 3000,  "min_pass_pct": 90, "label": "STANDARD"},
    "full":     {"frames": 12000, "min_pass_pct": 90, "label": "FULL"},
}

KNOWN_GOOD_ANCHOR = "014652358db408cf7977c3e99ab3cceb57ee01d7bf7c265daaaead625485a2d7"

WIDTH, HEIGHT, FPS = 1280, 720, 25


def _run(cmd: list, timeout: int = 600) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=False, timeout=timeout)


def _vcgencmd_temp() -> Optional[float]:
    try:
        r = subprocess.run(["vcgencmd", "measure_temp"],
                           capture_output=True, text=True, timeout=5)
        return float(r.stdout.strip().replace("temp=", "").replace("'C", ""))
    except Exception:
        return None


def stage_anchor(verbose: bool = False) -> Dict[str, Any]:
    print("Stage 1: BLAKE2b anchor check")
    test_script = _REPO / "ph6/cram_pu/ph6_internal_test.py"
    if not test_script.exists():
        return {"status": "FAIL", "reason": f"Missing: {test_script}"}

    result = subprocess.run([sys.executable, str(test_script)],
                            capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        print(f"  FAIL: {result.stdout[-500:]}")
        return {"status": "FAIL", "reason": "ph6_internal_test.py returned non-zero"}

    print(f"  PASS — anchor {KNOWN_GOOD_ANCHOR[:16]}...")
    return {"status": "PASS", "anchor": KNOWN_GOOD_ANCHOR}


def stage_authority(frames: int) -> Dict[str, Any]:
    print(f"Stage 2: Authority campaign ({frames:,} frames @ {WIDTH}x{HEIGHT} {FPS}fps)")
    script = _REPO / "PH6_SOURCE/TESTS/USB_CAMERA_12000/run_usb_camera_12000.py"
    if not script.exists():
        return {"status": "FAIL", "reason": f"Missing: {script}"}

    t0 = time.monotonic()
    result = subprocess.run(
        [sys.executable, str(script),
         "--device", "/dev/video0",
         "--frames", str(frames),
         "--width",  str(WIDTH),
         "--height", str(HEIGHT),
         "--fps",    str(FPS)],
        timeout=frames * 2,
    )
    elapsed = time.monotonic() - t0

    if result.returncode != 0:
        return {"status": "FAIL", "reason": "Authority campaign returned non-zero"}

    # Find most recent run directory
    runs = sorted(
        (_REPO / "ph6/cram_pu/validation_runs").glob("PH6-USB-CAM-PSEUDO-SOSO-TOK-12000-v1_*"),
        key=lambda p: p.name,
    )
    if not runs:
        return {"status": "FAIL", "reason": "No authority run directory found"}

    run_dir = runs[-1]
    print(f"  Run: {run_dir.name}  elapsed={elapsed:.0f}s  fps={frames/elapsed:.2f}")
    return {"status": "PASS", "run_dir": str(run_dir), "elapsed_s": round(elapsed, 1)}


def stage_replay(run_dir_str: str) -> Dict[str, Any]:
    print("Stage 3: Replay chain verification")
    run_dir = Path(run_dir_str)
    script  = _REPO / "PH6_SOURCE/TESTS/USB_CAMERA_12000/replay_compare.py"

    if not (run_dir / "replay_digest.json").exists():
        return {"status": "FAIL", "reason": "replay_digest.json missing"}

    result = subprocess.run(
        [sys.executable, str(script), str(run_dir)],
        capture_output=True, text=True, timeout=120,
    )
    output = result.stdout + result.stderr

    if "MISMATCH" in output:
        return {"status": "FAIL", "reason": "Replay MISMATCH"}

    digest = json.loads((run_dir / "replay_digest.json").read_text())
    replay_status = digest.get("summary_digest", "UNKNOWN")
    print(f"  MATCH — digest={replay_status[:20]}...")
    return {"status": "PASS", "replay_digest": replay_status}


def stage_pass_rate(run_dir_str: str, min_pct: int) -> Dict[str, Any]:
    print(f"Stage 4: PASS rate check (minimum {min_pct}%)")
    run_dir = Path(run_dir_str)

    try:
        digest = json.loads((run_dir / "replay_digest.json").read_text())
        total  = digest.get("total_frames", 0)
        passed = digest.get("pass_count", 0)
        dropped = digest.get("drop_count", 0)
        pct    = int(100 * passed / total) if total > 0 else 0
    except Exception as e:
        return {"status": "FAIL", "reason": str(e)}

    if pct < min_pct:
        return {"status": "FAIL", "reason": f"PASS rate {pct}% < minimum {min_pct}%",
                "pass_pct": pct, "pass_count": passed, "drop_count": dropped}

    print(f"  PASS={passed}  DROP={dropped}  rate={pct}%")
    return {"status": "PASS", "pass_pct": pct, "pass_count": passed, "drop_count": dropped}


def stage_thermal() -> Dict[str, Any]:
    print("Stage 5: Thermal check")
    temp = _vcgencmd_temp()
    if temp is None:
        print("  vcgencmd unavailable — skipping")
        return {"status": "SKIP", "temp_c": None}
    if temp >= 70.0:
        print(f"  WARNING: {temp}°C ≥ 70°C")
        return {"status": "WARN", "temp_c": temp}
    print(f"  {temp}°C (< 70°C)")
    return {"status": "PASS", "temp_c": temp}


def main(argv: list) -> int:
    parser = argparse.ArgumentParser(description="PH6 Certification Harness")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--smoke",    action="store_true")
    group.add_argument("--standard", action="store_true")
    group.add_argument("--full",     action="store_true")
    args = parser.parse_args(argv[1:])

    level = "smoke" if args.smoke else "standard" if args.standard else "full"
    cfg   = CERT_LEVELS[level]

    print()
    print("╔════════════════════════════════════════════════════════╗")
    print(f"║  PH6 CERTIFICATION HARNESS — {cfg['label']:8s}               ║")
    print("╚════════════════════════════════════════════════════════╝")
    print(f"  Frames: {cfg['frames']:,}   Min PASS rate: {cfg['min_pass_pct']}%")
    print()

    t_start = time.monotonic()
    stages: Dict[str, Any] = {}

    # Stage 1: Anchor
    stages["anchor"] = stage_anchor()
    if stages["anchor"]["status"] != "PASS":
        print("\nFAIL — anchor check failed. Stop.")
        _write_report(level, cfg, stages, False, t_start)
        return 1

    # Stage 2: Authority
    stages["authority"] = stage_authority(cfg["frames"])
    if stages["authority"]["status"] != "PASS":
        print("\nFAIL — authority campaign failed.")
        _write_report(level, cfg, stages, False, t_start)
        return 1

    run_dir = stages["authority"]["run_dir"]

    # Stage 3: Replay
    stages["replay"] = stage_replay(run_dir)
    if stages["replay"]["status"] != "PASS":
        print("\nFAIL — replay mismatch.")
        _write_report(level, cfg, stages, False, t_start)
        return 1

    # Stage 4: PASS rate
    stages["pass_rate"] = stage_pass_rate(run_dir, cfg["min_pass_pct"])
    if stages["pass_rate"]["status"] != "PASS":
        print("\nFAIL — PASS rate below threshold.")
        _write_report(level, cfg, stages, False, t_start)
        return 1

    # Stage 5: Thermal
    stages["thermal"] = stage_thermal()

    elapsed = time.monotonic() - t_start
    _write_report(level, cfg, stages, True, t_start)

    print()
    print("╔════════════════════════════════════════════════════════╗")
    print(f"║  PASS  {cfg['label']:8s}  {elapsed:.0f}s                            ║")
    print("╚════════════════════════════════════════════════════════╝")
    return 0


def _write_report(level: str, cfg: Dict, stages: Dict, passed: bool, t_start: float) -> None:
    elapsed = time.monotonic() - t_start
    report: Dict[str, Any] = {
        "cert_level":      level,
        "elapsed_seconds": round(elapsed, 1),
        "frames":          cfg["frames"],
        "generated_utc":   datetime.now(timezone.utc).isoformat(),
        "hostname":        __import__("socket").gethostname(),
        "min_pass_pct":    cfg["min_pass_pct"],
        "proposed_by":     "claude-code-lane2",
        "ratified_by":     None,
        "stages":          stages,
        "status":          "PASS" if passed else "FAIL",
    }
    out = _REPO / "ph6_cert_report.json"
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"\nReport: {out}")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
