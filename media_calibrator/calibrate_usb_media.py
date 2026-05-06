#!/usr/bin/env python3
import argparse
import hashlib
import json
import math
import os
import shutil
import subprocess
import time
from pathlib import Path

import cv2
import numpy as np


IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}
VIDEO_EXTS = {".mp4", ".mov", ".avi", ".mkv", ".m4v", ".webm", ".3gp"}


def blake2b_file(path: Path, chunk_size=1024 * 1024) -> str:
    h = hashlib.blake2b(digest_size=32)
    with path.open("rb") as f:
        while True:
            b = f.read(chunk_size)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def entropy_gray(gray: np.ndarray) -> float:
    hist = cv2.calcHist([gray], [0], None, [256], [0, 256]).ravel()
    total = hist.sum()
    if total <= 0:
        return 0.0
    p = hist / total
    p = p[p > 0]
    return float(-(p * np.log2(p)).sum())


def frame_metrics(frame: np.ndarray) -> dict:
    if frame is None:
        return {"valid": False}
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if len(frame.shape) == 3 else frame
    return {
        "valid": True,
        "width": int(frame.shape[1]),
        "height": int(frame.shape[0]),
        "channels": int(frame.shape[2]) if len(frame.shape) == 3 else 1,
        "brightness_mean": round(float(np.mean(gray)), 6),
        "brightness_min": int(np.min(gray)),
        "brightness_max": int(np.max(gray)),
        "laplacian_variance": round(float(cv2.Laplacian(gray, cv2.CV_64F).var()), 6),
        "entropy": round(entropy_gray(gray), 6),
        "frame_signature": hashlib.blake2b(gray.tobytes(), digest_size=16).hexdigest(),
    }


def analyze_image(path: Path) -> dict:
    img = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    if img is None:
        return {"ok": False, "error": "OpenCV could not read image"}
    if len(img.shape) == 2:
        frame = img
    elif img.shape[2] == 4:
        frame = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    else:
        frame = img
    return {"ok": True, "type": "image", "metrics": frame_metrics(frame)}


def ffprobe_json(path: Path) -> dict:
    try:
        cmd = [
            "ffprobe", "-v", "quiet",
            "-print_format", "json",
            "-show_format", "-show_streams",
            str(path),
        ]
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        if p.returncode != 0:
            return {"available": False, "error": p.stderr.strip()}
        return {"available": True, "data": json.loads(p.stdout)}
    except Exception as e:
        return {"available": False, "error": repr(e)}


def audio_rms(path: Path) -> dict:
    """Extract audio RMS via ffmpeg volumedetect filter."""
    try:
        cmd = [
            "ffmpeg", "-i", str(path),
            "-af", "volumedetect",
            "-vn", "-f", "null", "-",
        ]
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        combined = p.stderr
        rms = None
        for line in combined.splitlines():
            if "mean_volume" in line:
                # e.g. "  mean_volume: -18.3 dB"
                parts = line.split(":")
                if len(parts) == 2:
                    try:
                        rms = float(parts[1].strip().split()[0])
                    except ValueError:
                        pass
        return {"rms_db": rms, "available": rms is not None}
    except Exception as e:
        return {"rms_db": None, "available": False, "error": repr(e)}


def analyze_video(path: Path, include_audio: bool = True) -> dict:
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        return {"ok": False, "error": "OpenCV could not open video"}

    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)

    if frame_count > 0:
        positions = sorted(set([
            0,
            frame_count // 4,
            frame_count // 2,
            (frame_count * 3) // 4,
            max(frame_count - 1, 0),
        ]))
    else:
        positions = [0]

    sampled = []
    for pos in positions:
        cap.set(cv2.CAP_PROP_POS_FRAMES, pos)
        ret, frame = cap.read()
        if ret:
            sampled.append({"frame_index": int(pos), "metrics": frame_metrics(frame)})
        else:
            sampled.append({"frame_index": int(pos), "metrics": {"valid": False}})
    cap.release()

    probe = ffprobe_json(path)
    audio_present = False
    audio_streams = []
    duration = None

    if probe.get("available"):
        data = probe.get("data", {})
        fmt = data.get("format", {})
        try:
            duration = float(fmt["duration"]) if fmt.get("duration") else None
        except Exception:
            duration = None
        for stream in data.get("streams", []):
            if stream.get("codec_type") == "audio":
                audio_present = True
                audio_streams.append({
                    "codec": stream.get("codec_name"),
                    "sample_rate": stream.get("sample_rate"),
                    "channels": stream.get("channels"),
                    "duration": stream.get("duration"),
                })

    rms_info = {}
    if include_audio and audio_present:
        rms_info = audio_rms(path)

    return {
        "ok": True,
        "type": "video",
        "width": width,
        "height": height,
        "fps": round(fps, 6),
        "frame_count": frame_count,
        "duration": duration,
        "sampled_frame_positions": positions,
        "sampled_frames": sampled,
        "audio_present": audio_present,
        "audio_streams": audio_streams,
        "audio_rms": rms_info if rms_info else None,
    }


def analyze_file(path: Path, include_audio: bool = True) -> dict:
    ext = path.suffix.lower()
    base = {
        "path": str(path),
        "name": path.name,
        "ext": ext,
        "size_bytes": path.stat().st_size,
        "file_hash_blake2b256": blake2b_file(path),
    }
    if ext in IMAGE_EXTS:
        result = analyze_image(path)
    elif ext in VIDEO_EXTS:
        result = analyze_video(path, include_audio=include_audio)
    else:
        result = {"ok": False, "error": "unsupported extension"}
    base.update(result)
    return base


def stable_media_list(source: Path, do_images: bool, do_videos: bool):
    exts = set()
    if do_images:
        exts |= IMAGE_EXTS
    if do_videos:
        exts |= VIDEO_EXTS
    files = [p for p in source.rglob("*") if p.is_file() and p.suffix.lower() in exts]
    return sorted(files, key=lambda x: str(x).lower())


def normalize_for_repeatability(record: dict) -> dict:
    keep = dict(record)
    keep.pop("path", None)
    return keep


def select_25_percent(records, percent: int):
    valid = [r for r in records if r.get("ok")]
    if not valid:
        return []
    n = max(1, math.ceil(len(valid) * percent / 100.0))

    images = [r for r in valid if r.get("type") == "image"]
    videos = [r for r in valid if r.get("type") == "video"]

    selected = []
    if images:
        selected.append(images[0])
    if videos and len(selected) < n:
        selected.append(videos[0])

    # Fill remaining slots: sort by type, size, hash for determinism + diversity
    remaining = [r for r in valid if r not in selected]
    remaining = sorted(
        remaining,
        key=lambda r: (
            r.get("type", ""),
            r.get("size_bytes", 0),
            r.get("file_hash_blake2b256", ""),
        ),
    )
    for r in remaining:
        if len(selected) >= n:
            break
        selected.append(r)
    return selected[:n]


def copy_selected(selected, dest_selected: Path):
    dest_selected.mkdir(parents=True, exist_ok=True)
    copied = []
    for r in selected:
        src = Path(r["path"])
        target = dest_selected / src.name
        if target.exists():
            target = dest_selected / f"{src.stem}_{r['file_hash_blake2b256'][:12]}{src.suffix}"
        shutil.copy2(src, target)
        copied.append({
            "source": str(src),
            "copied_to": str(target),
            "hash": r["file_hash_blake2b256"],
            "size_bytes": r["size_bytes"],
            "type": r.get("type"),
        })
    return copied


def main():
    ap = argparse.ArgumentParser(description="Deterministic media calibration test")
    ap.add_argument("--source", required=True, help="Source (thumb drive) path — treated READ-ONLY")
    ap.add_argument("--dest", required=True, help="Destination (NVMe/USB3) base path")
    ap.add_argument("--repeat", type=int, default=3, help="Number of repeat passes (default 3)")
    ap.add_argument("--select-percent", type=int, default=25, help="Calibration subset percentage (default 25)")
    ap.add_argument("--images", action="store_true", default=False)
    ap.add_argument("--videos", action="store_true", default=False)
    ap.add_argument("--audio", action="store_true", default=False)
    args = ap.parse_args()

    # Default: both if neither explicitly set
    do_images = args.images or (not args.images and not args.videos)
    do_videos = args.videos or (not args.images and not args.videos)

    source = Path(args.source).resolve()
    dest_root = Path(args.dest).resolve()

    if not source.exists():
        raise SystemExit(f"FAIL: Source not found: {source}")

    # Safety: never write to source
    dest_root.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    out = dest_root / f"calibration_run_{stamp}"
    out.mkdir(parents=True, exist_ok=False)

    print(f"=== Media Calibration Test ===")
    print(f"Source  : {source}")
    print(f"Output  : {out}")
    print(f"Passes  : {args.repeat}")
    print(f"Select  : {args.select_percent}%")
    print(f"Images  : {do_images}  Videos: {do_videos}  Audio: {args.audio}")
    print()

    media = stable_media_list(source, do_images, do_videos)
    print(f"Media files found: {len(media)}")
    for p in media:
        print(f"  {p}")
    print()

    manifest = {
        "source": str(source),
        "dest": str(out),
        "repeat": args.repeat,
        "select_percent": args.select_percent,
        "media_count": len(media),
        "media_files": [str(p) for p in media],
    }

    all_passes = []
    for pass_i in range(args.repeat):
        print(f"Pass {pass_i + 1}/{args.repeat} ...")
        pass_records = []
        for p in media:
            print(f"  {p.name}", end=" ", flush=True)
            try:
                rec = analyze_file(p, include_audio=args.audio)
                status = "ok" if rec.get("ok") else f"ERR:{rec.get('error','?')}"
                print(status)
                pass_records.append(rec)
            except Exception as e:
                print(f"EXCEPTION:{e}")
                pass_records.append({
                    "path": str(p), "name": p.name, "ok": False, "error": repr(e),
                })
        all_passes.append(pass_records)

    print()
    print("Checking repeatability ...")
    first = all_passes[0] if all_passes else []
    mismatches = []
    for idx, base in enumerate(first):
        base_norm = normalize_for_repeatability(base)
        for pass_i in range(1, len(all_passes)):
            other = all_passes[pass_i][idx]
            other_norm = normalize_for_repeatability(other)
            if base_norm != other_norm:
                mismatches.append({
                    "file": base.get("path"),
                    "pass_a": 0,
                    "pass_b": pass_i,
                    "reason": "metric/hash mismatch",
                })
                print(f"  MISMATCH: {base.get('name')} pass 0 vs pass {pass_i}")

    print()
    print(f"Selecting {args.select_percent}% representative subset ...")
    selected = select_25_percent(first, args.select_percent)
    copied = copy_selected(selected, out / "selected_25_percent")
    print(f"  Copied {len(copied)} files to {out / 'selected_25_percent'}")

    repeatability = {
        "repeat_count": args.repeat,
        "files_tested": len(media),
        "mismatch_count": len(mismatches),
        "deterministic": len(mismatches) == 0,
        "mismatches": mismatches,
    }
    quality = {"records": first}
    selected_manifest = {
        "selected_count": len(selected),
        "source_count": len(first),
        "copied": copied,
    }

    if len(media) == 0:
        verdict = "WARN"
        verdict_msg = "No image/video media found."
    elif len(mismatches) == 0:
        verdict = "PASS"
        verdict_msg = "Deterministic repeatability confirmed across all tested media."
    else:
        verdict = "FAIL"
        verdict_msg = f"{len(mismatches)} repeatability mismatch(es) detected."

    summary_lines = [
        "# Media Calibration Summary",
        "",
        f"Source: `{source}`",
        f"Output: `{out}`",
        f"Files found: {len(media)}",
        f"Repeat passes: {args.repeat}",
        f"Deterministic: {repeatability['deterministic']}",
        f"Mismatches: {len(mismatches)}",
        f"Selected/copied ({args.select_percent}%): {len(copied)}",
        "",
        "## Verdict",
        f"{verdict} — {verdict_msg}",
    ]

    (out / "calibration_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (out / "media_quality_report.json").write_text(json.dumps(quality, indent=2), encoding="utf-8")
    (out / "repeatability_report.json").write_text(json.dumps(repeatability, indent=2), encoding="utf-8")
    (out / "selected_25_percent_manifest.json").write_text(json.dumps(selected_manifest, indent=2), encoding="utf-8")
    (out / "final_summary.md").write_text("\n".join(summary_lines) + "\n", encoding="utf-8")

    print("=== Results ===")
    print(f"Files found      : {len(media)}")
    print(f"Repeat passes    : {args.repeat}")
    print(f"Deterministic    : {repeatability['deterministic']}")
    print(f"Mismatches       : {len(mismatches)}")
    print(f"Selected/copied  : {len(copied)}")
    print()
    print(f"VERDICT: {verdict}")
    print(f"Output folder    : {out}")


if __name__ == "__main__":
    main()
