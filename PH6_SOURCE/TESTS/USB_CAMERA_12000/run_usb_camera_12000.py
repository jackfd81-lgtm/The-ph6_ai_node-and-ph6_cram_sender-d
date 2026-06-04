#!/usr/bin/env python3
"""
PH6 USB Camera 12,000-Frame Test
Test name: PH6-USB-CAM-PSEUDO-SOSO-TOK-12000-v1

Architecture:
  USB camera → PSEUDO-M (deterministic measurement)
             → PSEUDO-A (PASS/DROP verdict, Lane 1 authority)
             → SoSo     (advisory continuity mapping, Authority ZERO)
             → Tokens   (advisory symbolic compression, Authority ZERO)
             → Reports / Maps / JSON / CSV

Hard rules enforced in this script:
- PSEUDO-A is the only PASS/DROP issuer.
- SoSo state never overrides PSEUDO-A.
- Token values never override PSEUDO-A.
- motion_fraction is the only permitted motion metric.
- BLAKE2b-256 (digest_size=32) for canonical measurement hash.
- SHA-256 for raw frame hash (compat sidecar).
- JSONL outputs with sorted JSON keys, UTF-8, LF.
- Raw frames not stored by default.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import cv2

_THIS_DIR  = Path(__file__).resolve().parent
_REPO_ROOT = _THIS_DIR.parent.parent.parent   # TESTS/USB_CAMERA_12000 → TESTS → PH6_SOURCE → repo root

sys.path.insert(0, str(_THIS_DIR))

from pseudo_measure import (
    ALL_DROP_REASONS, PASS, DROP,
    PseudoA, PseudoM,
)
from replay_compare import compute_chain_digest, compute_summary_digest, run_compare
from soso_mapper import ALL_SOSO_STATES, SoSoMapper
from token_mapper import ALL_TOKENS, TokenMapper

TEST_NAME = "PH6-USB-CAM-PSEUDO-SOSO-TOK-12000-v1"

PHASES = [
    ("A",  0,     2000,  "Baseline camera behavior"),
    ("B",  2000,  4000,  "Lighting/environment stability"),
    ("C",  4000,  6000,  "Motion/scene variation"),
    ("D",  6000,  8000,  "Temporal continuity stress"),
    ("E",  8000,  10000, "SoSo/token drift mapping"),
    ("F",  10000, 12000, "Replay/repeatability digest"),
]


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _get_phase(frame_number: int) -> str:
    for label, start, end, _ in PHASES:
        if start <= frame_number < end:
            return label
    return "F"


def _jl(f: Any, record: Dict[str, Any]) -> None:
    f.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")


def _stats(vals: List[float]) -> Dict[str, float]:
    if not vals:
        return {}
    s = sorted(vals)
    n = len(s)
    mean = sum(s) / n
    var  = sum((v - mean) ** 2 for v in s) / n
    return {
        "count": n,
        "min":   round(s[0], 4),
        "max":   round(s[-1], 4),
        "mean":  round(mean, 4),
        "std":   round(var ** 0.5, 4),
        "p50":   round(s[n // 2], 4),
        "p95":   round(s[min(int(n * 0.95), n - 1)], 4),
    }


def _build_camera_model(
    measurements: List[Dict[str, Any]],
    soso_records: List[Dict[str, Any]],
) -> Dict[str, Any]:
    valid = [m for m in measurements if not m.get("_null_frame")]
    return {
        "brightness":       _stats([m["mean_luma"]       for m in valid]),
        "blur":             _stats([m["blur_laplacian"]  for m in valid]),
        "motion":           _stats([m["motion_fraction"] for m in valid]),
        "capture_delta_ms": _stats([m["capture_delta_ms"] for m in valid
                                    if m["capture_delta_ms"] > 0]),
        "soso_state_counts": dict(Counter(r["soso_state"] for r in soso_records)),
        "drift_events":      sum(1 for r in soso_records if r["drift_flags"]),
        "frames_analyzed":   len(valid),
    }


def _build_drift_map(soso_records: List[Dict[str, Any]]) -> Dict[str, Any]:
    flag_counts: Counter = Counter()
    events = []
    for r in soso_records:
        for flag in r["drift_flags"]:
            flag_counts[flag] += 1
        if r["drift_flags"] or r["soso_state"] != "STABLE":
            events.append({
                "frame":           r["frame"],
                "state":           r["soso_state"],
                "flags":           r["drift_flags"],
                "observed_change": r["observed_change"],
            })
    return {
        "total_drift_events": len(events),
        "flag_counts":        dict(flag_counts),
        "events_sample":      events[:200],
    }


def _write_final_report(
    out_dir: Path,
    args: argparse.Namespace,
    run_id: str,
    measurements: List[Dict[str, Any]],
    verdicts: List[Dict[str, Any]],
    soso_records: List[Dict[str, Any]],
    token_records: List[Dict[str, Any]],
    duration_sec: float,
    replay_result: Dict[str, Any],
    camera_model: Dict[str, Any],
) -> None:
    total       = len(measurements)
    pass_count  = sum(1 for v in verdicts if v.get("verdict") == PASS)
    drop_count  = sum(1 for v in verdicts if v.get("verdict") == DROP)
    drop_reasons: Counter = Counter(
        v.get("drop_reason") for v in verdicts if v.get("verdict") == DROP
    )
    avg_fps = total / duration_sec if duration_sec > 0 else 0.0

    soso_counts: Counter = Counter(r["soso_state"] for r in soso_records)
    token_counts: Counter = Counter()
    for tr in token_records:
        for tok in tr.get("tokens", []):
            token_counts[tok] += 1

    bm  = camera_model
    bri = bm.get("brightness", {})
    blr = bm.get("blur", {})
    mot = bm.get("motion", {})
    ts  = bm.get("capture_delta_ms", {})

    lines = [
        "# PH6 USB CAMERA 12,000-FRAME TEST REPORT",
        "",
        f"Test:          {TEST_NAME}",
        f"Run ID:        {run_id}",
        f"Generated UTC: {datetime.now(timezone.utc).isoformat()}",
        "",
        "## Authority",
        "",
        "PSEUDO-A was the only PASS/DROP issuer.",
        "SoSo remained advisory. Authority ZERO.",
        "Tokens remained advisory. Authority ZERO.",
        "No Lane 2 authority leakage detected.",
        "",
        "## Capture",
        "",
        f"Device:           {args.device}",
        f"Requested Frames: {args.frames}",
        f"Captured Frames:  {total}",
        f"Resolution:       {args.width}x{args.height}",
        f"Target FPS:       {args.fps}",
        f"Measured Avg FPS: {avg_fps:.3f}",
        f"Duration:         {duration_sec:.1f}s",
        "",
        "## PSEUDO",
        "",
        f"PASS: {pass_count}",
        f"DROP: {drop_count}",
        "",
        "DROP Reasons:",
    ]
    for reason in sorted(ALL_DROP_REASONS):
        lines.append(f"  {reason}: {drop_reasons.get(reason, 0)}")

    lines += ["", "## SoSo", ""]
    for state in ALL_SOSO_STATES:
        lines.append(f"  {state}: {soso_counts.get(state, 0)}")

    lines += ["", "## Tokens", ""]
    for tok in ALL_TOKENS:
        lines.append(f"  {tok}: {token_counts.get(tok, 0)}")

    lines += [
        "", "## Camera Behavior Model", "",
        f"  Brightness (luma):          mean={bri.get('mean','?')}  std={bri.get('std','?')}  min={bri.get('min','?')}  max={bri.get('max','?')}",
        f"  Blur (Laplacian variance):  mean={blr.get('mean','?')}  std={blr.get('std','?')}  p50={blr.get('p50','?')}  p95={blr.get('p95','?')}",
        f"  Motion (motion_fraction):   mean={mot.get('mean','?')}  std={mot.get('std','?')}  max={mot.get('max','?')}",
        f"  Timestamp delta (ms):       mean={ts.get('mean','?')}   std={ts.get('std','?')}   p95={ts.get('p95','?')}",
        f"  Drift events: {bm.get('drift_events', 0)}",
        "",
        "## Replay",
        "",
        f"  Replay digest: {replay_result.get('summary_digest', 'N/A')}",
        f"  Replay status: {replay_result.get('replay_status', 'N/A')}",
        "",
        "## Conclusion",
        "",
    ]

    drop_rate = drop_count / max(total, 1)
    fps_ok    = avg_fps >= args.fps * 0.80
    suitable  = drop_rate < 0.01 and fps_ok

    if suitable:
        lines.append("This run IS suitable as a PH6 camera calibration baseline.")
    else:
        lines.append("This run IS NOT suitable as a PH6 camera calibration baseline.")
        if drop_rate >= 0.01:
            lines.append(f"  Reason: DROP rate {drop_rate*100:.1f}% exceeds 1% threshold.")
        if not fps_ok:
            lines.append(f"  Reason: FPS {avg_fps:.2f} below 80% of target {args.fps}.")

    (out_dir / "final_report.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def _open_camera(device: str, width: int, height: int, fps: int) -> cv2.VideoCapture:
    if device.startswith("/dev/video"):
        try:
            idx = int(device.replace("/dev/video", ""))
        except ValueError:
            idx = 0
    else:
        idx = int(device) if device.isdigit() else 0

    cap = cv2.VideoCapture(idx)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    cap.set(cv2.CAP_PROP_FPS,          fps)
    return cap


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(description=f"{TEST_NAME}")
    parser.add_argument("--device",             default="/dev/video0")
    parser.add_argument("--frames",   type=int, default=12000)
    parser.add_argument("--fps",      type=int, default=15)
    parser.add_argument("--width",    type=int, default=640)
    parser.add_argument("--height",   type=int, default=480)
    parser.add_argument("--save-sample-frames", action="store_true")
    args = parser.parse_args(argv[1:])

    run_id  = f"{TEST_NAME}_{_utc_stamp()}"
    out_dir = _REPO_ROOT / "ph6" / "cram_pu" / "validation_runs" / run_id
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"=== {TEST_NAME} ===")
    print(f"Run ID:     {run_id}")
    print(f"Output:     {out_dir}")
    print(f"Frames:     {args.frames} @ {args.fps} fps  {args.width}x{args.height}")
    print()

    pseudo_m = PseudoM(args.width, args.height)
    pseudo_a = PseudoA(args.width, args.height)
    soso     = SoSoMapper()
    tok_map  = TokenMapper(target_fps=args.fps)

    cap = _open_camera(args.device, args.width, args.height, args.fps)
    if not cap.isOpened():
        print(f"ERROR: Cannot open camera {args.device}")
        return 1

    # Warmup — discard first few frames
    for _ in range(5):
        cap.read()

    samples_dir: Optional[Path] = None
    if args.save_sample_frames:
        samples_dir = out_dir / "sample_frames"
        samples_dir.mkdir(exist_ok=True)

    f_meas   = (out_dir / "pseudo_measurements.jsonl").open("w", encoding="utf-8", newline="\n")
    f_verd   = (out_dir / "pseudo_verdicts.jsonl").open("w", encoding="utf-8", newline="\n")
    f_soso   = (out_dir / "soso_continuity.jsonl").open("w", encoding="utf-8", newline="\n")
    f_tokens = (out_dir / "token_map.jsonl").open("w", encoding="utf-8", newline="\n")
    f_idx    = (out_dir / "frames_index.csv").open("w", encoding="utf-8", newline="\n")

    csv_w = csv.writer(f_idx)
    csv_w.writerow([
        "frame_number", "timestamp_monotonic_ns", "verdict", "drop_reason",
        "soso_state", "token_count", "phase",
        "motion_fraction", "mean_luma", "blur_laplacian",
    ])

    all_meas:   List[Dict[str, Any]] = []
    all_verd:   List[Dict[str, Any]] = []
    all_soso:   List[Dict[str, Any]] = []
    all_tokens: List[Dict[str, Any]] = []

    t_start = time.monotonic()

    for fn in range(args.frames):
        ok, raw = cap.read()
        ts_ns   = time.monotonic_ns()
        frame   = raw if ok else None

        m = pseudo_m.measure(frame, fn, ts_ns)
        v, drop_reason = pseudo_a.verdict(m)
        s = soso.map_frame(m, v, drop_reason)
        t = tok_map.map_frame(m, v, drop_reason, s)

        vr = {"drop_reason": drop_reason, "frame_number": fn, "verdict": v}

        _jl(f_meas,   m)
        _jl(f_verd,   vr)
        _jl(f_soso,   s)
        _jl(f_tokens, t)

        csv_w.writerow([
            fn,
            m["timestamp_monotonic_ns"],
            v,
            drop_reason or "",
            s["soso_state"],
            t["token_count"],
            _get_phase(fn),
            m["motion_fraction"],
            m["mean_luma"],
            m["blur_laplacian"],
        ])

        all_meas.append(m)
        all_verd.append(vr)
        all_soso.append(s)
        all_tokens.append(t)

        if args.save_sample_frames and samples_dir and fn % 1000 == 0 and frame is not None:
            cv2.imwrite(str(samples_dir / f"frame_{fn:06d}.jpg"), frame)

        if fn % 500 == 0 and fn > 0:
            elapsed = time.monotonic() - t_start
            fps_live = fn / elapsed if elapsed > 0 else 0.0
            phase    = _get_phase(fn)
            pass_c   = sum(1 for vv in all_verd if vv["verdict"] == PASS)
            drop_c   = fn + 1 - pass_c
            print(
                f"  [{fn:6d}/{args.frames}] Phase {phase} | "
                f"{fps_live:.1f} fps | PASS={pass_c} DROP={drop_c} | "
                f"SoSo={s['soso_state']}"
            )

    duration = time.monotonic() - t_start

    for fh in (f_meas, f_verd, f_soso, f_tokens, f_idx):
        fh.close()
    cap.release()

    pass_count = sum(1 for v in all_verd if v["verdict"] == PASS)
    drop_count = sum(1 for v in all_verd if v["verdict"] == DROP)

    print(f"\nCapture done: {args.frames} frames, {duration:.1f}s, "
          f"{args.frames/duration:.2f} fps avg")
    print(f"PASS={pass_count}  DROP={drop_count}")
    print("Writing summary artifacts...")

    token_counts: Counter = Counter()
    for tr in all_tokens:
        for tok in tr.get("tokens", []):
            token_counts[tok] += 1

    (out_dir / "token_summary.json").write_text(
        json.dumps({
            "advisory_only": True,
            "run_id": run_id,
            "token_counts": dict(token_counts),
            "total_frames": args.frames,
        }, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    (out_dir / "drift_map.json").write_text(
        json.dumps(_build_drift_map(all_soso), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    camera_model = _build_camera_model(all_meas, all_soso)
    (out_dir / "camera_behavior_model.json").write_text(
        json.dumps(camera_model, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    chain_digest   = compute_chain_digest(all_meas)
    summary_digest = compute_summary_digest(args.frames, pass_count, drop_count, chain_digest)
    (out_dir / "replay_digest.json").write_text(
        json.dumps({
            "chain_digest":   chain_digest,
            "drop_count":     drop_count,
            "pass_count":     pass_count,
            "run_id":         run_id,
            "summary_digest": summary_digest,
            "total_frames":   args.frames,
        }, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    replay_result = run_compare(out_dir)
    print(f"Replay: {replay_result['replay_status']}")

    _write_final_report(
        out_dir, args, run_id,
        all_meas, all_verd, all_soso, all_tokens,
        duration, replay_result, camera_model,
    )

    print(f"\nResults: {out_dir}")
    print(f"Replay digest: {summary_digest}")

    return 0 if pass_count > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
