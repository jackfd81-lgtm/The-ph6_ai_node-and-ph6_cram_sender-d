#!/usr/bin/env python3
"""
Media Calibration Test — Raspberry Pi 5
Repeatable, deterministic quality metrics for images and videos.

Usage:
  python3 calibrate.py [--repeat N] [--limit N] [--images-only] [--videos-only]
                       [--output DIR]
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

MOUNT_POINT      = Path("/mnt/calibration_drive")
LOCAL_CORPUS     = Path("/home/jack/frame_filter/frames_ph6_full_20260429_143225")
LOCAL_VIDEO_ROOT = Path("/home/jack/frame_filter/logs")  # PH6 run_video.mp4 + spike clips
DEFAULT_OUT      = Path("/home/jack/calibration_test/output")

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
VIDEO_EXTS = {".mp4", ".mov", ".avi", ".mkv", ".m4v"}
AUDIO_EXTS = {".wav", ".mp3", ".m4a", ".flac"}

# Numeric metrics must agree within this tolerance across repeat runs.
# Images: 0.0 (exact). Videos: small FP rounding allowance.
IMAGE_TOLERANCE = 0.0
VIDEO_TOLERANCE = 1e-4


# ---------------------------------------------------------------------------
# Args
# ---------------------------------------------------------------------------

def parse_args():
    p = argparse.ArgumentParser(description="Media calibration test")
    p.add_argument("--repeat",      type=int, default=3,
                   help="Number of passes per file (default: 3)")
    p.add_argument("--limit",       type=int, default=None,
                   help="Max files per type for quick test runs")
    p.add_argument("--images-only", action="store_true")
    p.add_argument("--videos-only", action="store_true")
    p.add_argument("--output",      type=Path, default=DEFAULT_OUT)
    return p.parse_args()


# ---------------------------------------------------------------------------
# Mount check
# ---------------------------------------------------------------------------

def check_mount(mount_point: Path) -> dict:
    result = {"mount_point": str(mount_point), "mounted": False, "writable": False, "error": None}
    if not mount_point.exists():
        result["error"] = "Mount point does not exist"
        return result
    try:
        with open("/proc/mounts") as f:
            mounts = f.read()
        if str(mount_point) in mounts:
            result["mounted"] = True
            for line in mounts.splitlines():
                if str(mount_point) in line:
                    opts = line.split()[3]
                    result["mount_options"] = opts
                    result["writable"] = "ro" not in opts.split(",")
    except OSError as e:
        result["error"] = str(e)
    return result


# ---------------------------------------------------------------------------
# Media scanner
# ---------------------------------------------------------------------------

def scan_media(root: Path) -> dict:
    images, videos, audio = [], [], []
    for path in sorted(root.rglob("*")):  # sorted = deterministic order
        if not path.is_file():
            continue
        ext = path.suffix.lower()
        if ext in IMAGE_EXTS:
            images.append(path)
        elif ext in VIDEO_EXTS:
            videos.append(path)
        elif ext in AUDIO_EXTS:
            audio.append(path)
    return {"images": images, "videos": videos, "audio": audio}


def build_manifest(media: dict, root: Path) -> dict:
    def entry(p: Path):
        stat = p.stat()
        try:
            rel = str(p.relative_to(root))
        except ValueError:
            rel = str(p)  # file is outside the primary scan root
        return {
            "path": rel,
            "size_bytes": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        }
    return {
        "scan_root": str(root),
        "generated_at": datetime.now().isoformat(),
        "counts": {k: len(v) for k, v in media.items()},
        "images": [entry(p) for p in media["images"]],
        "videos": [entry(p) for p in media["videos"]],
        "audio":  [entry(p) for p in media["audio"]],
    }


# ---------------------------------------------------------------------------
# File hash (determinism anchor)
# ---------------------------------------------------------------------------

def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# Image metrics
# ---------------------------------------------------------------------------

def image_metrics(path: Path) -> dict:
    base = {"file": str(path.name), "abs_path": str(path), "error": None}
    if not HAS_CV2 or not HAS_NUMPY:
        base["error"] = "opencv / numpy not installed"
        return base

    img = cv2.imread(str(path))
    if img is None:
        base["error"] = "cv2 could not decode file"
        return base

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape

    brightness     = float(np.mean(gray))
    contrast       = float(np.std(gray))
    lap            = cv2.Laplacian(gray, cv2.CV_32F)
    blur_score     = float(lap.var())
    blurred        = cv2.medianBlur(gray, 3).astype(np.float32)
    noise_estimate = float(np.std(gray.astype(np.float32) - blurred))

    return {
        **base,
        "resolution":        f"{w}x{h}",
        "file_sha256":       file_sha256(path),
        "brightness":        round(brightness,     6),
        "contrast":          round(contrast,        6),
        "blur_laplacian_var": round(blur_score,     6),
        "noise_estimate":    round(noise_estimate,  6),
    }


# ---------------------------------------------------------------------------
# ffprobe helper
# ---------------------------------------------------------------------------

def _ffprobe(path: Path) -> dict:
    cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_streams", "-show_format", str(path),
    ]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return json.loads(out.stdout) if out.returncode == 0 else {}
    except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError):
        return {}


# ---------------------------------------------------------------------------
# Video metrics  — deterministic fixed-stride frame sampling
# ---------------------------------------------------------------------------

def _fixed_frame_indexes(nb_frames: int, sample_count: int = 10) -> list[int]:
    """Return fixed, evenly-spaced frame indexes — identical every call."""
    if nb_frames <= 0:
        return []
    if nb_frames <= sample_count:
        return list(range(nb_frames))
    step = nb_frames / sample_count
    return sorted({int(i * step) for i in range(sample_count)})


def video_metrics(path: Path, sample_count: int = 10) -> dict:
    base = {"file": str(path.name), "abs_path": str(path), "error": None}

    probe        = _ffprobe(path)
    streams      = probe.get("streams", [])
    fmt          = probe.get("format", {})
    video_stream = next((s for s in streams if s.get("codec_type") == "video"), None)
    audio_stream = next((s for s in streams if s.get("codec_type") == "audio"), None)

    # Detect empty containers before attempting any decode
    nb_streams = int(probe.get("format", {}).get("nb_streams", len(streams)))
    file_size  = path.stat().st_size
    if nb_streams == 0 or (file_size < 1024 and not streams):
        base["error"]      = "INVALID_EMPTY_CONTAINER"
        base["file_size"]  = file_size
        base["nb_streams"] = nb_streams
        return base

    if not video_stream:
        base["error"] = "no video stream found"
        base["has_audio"] = audio_stream is not None
        return base

    w      = video_stream.get("width",  0)
    h      = video_stream.get("height", 0)
    codec  = video_stream.get("codec_name", "unknown")
    duration = float(fmt.get("duration", 0) or video_stream.get("duration", 0) or 0)

    try:
        num, den = video_stream.get("r_frame_rate", "0/1").split("/")
        fps = round(int(num) / int(den), 6) if int(den) else 0.0
    except (ValueError, ZeroDivisionError):
        fps = 0.0

    nb_frames = int(video_stream.get("nb_frames", 0) or 0)
    if nb_frames == 0 and fps and duration:
        nb_frames = int(fps * duration)

    frame_indexes = _fixed_frame_indexes(nb_frames, sample_count)

    result = {
        **base,
        "resolution":          f"{w}x{h}",
        "codec":               codec,
        "fps":                 fps,
        "frame_count":         nb_frames,
        "duration_s":          round(duration, 6),
        "sampled_frame_indexes": frame_indexes,
        "has_audio":           audio_stream is not None,
    }

    if HAS_CV2 and HAS_NUMPY and frame_indexes:
        cap = cv2.VideoCapture(str(path))
        brightness_vals, contrast_vals, blur_vals, motion_vals = [], [], [], []
        prev_gray = None

        for idx in frame_indexes:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ok, frame = cap.read()
            if not ok or frame is None:
                continue
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            brightness_vals.append(float(np.mean(gray)))
            contrast_vals.append(float(np.std(gray)))
            blur_vals.append(float(cv2.Laplacian(gray, cv2.CV_32F).var()))
            if prev_gray is not None:
                motion_vals.append(float(np.mean(np.abs(gray.astype(np.float32) - prev_gray.astype(np.float32)))))
            prev_gray = gray

        cap.release()

        def _mean(lst):
            return round(sum(lst) / len(lst), 6) if lst else None

        result["brightness_mean"]        = _mean(brightness_vals)
        result["contrast_mean"]          = _mean(contrast_vals)
        result["blur_laplacian_var_mean"] = _mean(blur_vals)
        result["motion_level_mean"]       = _mean(motion_vals)

    if audio_stream:
        result["audio_metrics"] = _ffmpeg_audio_metrics(path)

    return result


# ---------------------------------------------------------------------------
# Audio metrics
# ---------------------------------------------------------------------------

def _ffmpeg_audio_metrics(path: Path) -> dict:
    cmd = [
        "ffmpeg", "-i", str(path),
        "-af", "volumedetect", "-vn", "-sn", "-dn", "-f", "null", "/dev/null",
    ]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return {"error": "ffmpeg unavailable"}

    metrics = {}
    for line in out.stderr.splitlines():
        if "mean_volume" in line:
            try:
                metrics["rms_db"] = float(line.split(":")[-1].replace("dB", "").strip())
            except ValueError:
                pass
        if "max_volume" in line:
            try:
                metrics["peak_db"] = float(line.split(":")[-1].replace("dB", "").strip())
            except ValueError:
                pass

    cmd2 = [
        "ffmpeg", "-i", str(path),
        "-af", "silencedetect=noise=-50dB:d=0.5",
        "-vn", "-sn", "-dn", "-f", "null", "/dev/null",
    ]
    try:
        out2   = subprocess.run(cmd2, capture_output=True, text=True, timeout=60)
        total_silence = sum(
            float(l.split("silence_duration:")[-1].strip())
            for l in out2.stderr.splitlines()
            if "silence_duration:" in l
        )
        probe    = _ffprobe(path)
        total_dur = float(probe.get("format", {}).get("duration", 0) or 0)
        if total_dur > 0:
            metrics["silence_ratio"] = round(total_silence / total_dur, 6)
    except (FileNotFoundError, subprocess.TimeoutExpired, ValueError):
        pass

    return metrics or {"error": "no audio metrics extracted"}


def audio_metrics(path: Path) -> dict:
    return {"file": str(path.name), **_ffmpeg_audio_metrics(path)}


# ---------------------------------------------------------------------------
# Repeatability engine
# ---------------------------------------------------------------------------

NUMERIC_IMAGE_KEYS = ["brightness", "contrast", "blur_laplacian_var", "noise_estimate"]
NUMERIC_VIDEO_KEYS = [
    "fps", "frame_count", "duration_s",
    "brightness_mean", "contrast_mean", "blur_laplacian_var_mean", "motion_level_mean",
]
EXACT_IMAGE_KEYS   = ["resolution", "file_sha256", "codec"]
EXACT_VIDEO_KEYS   = ["resolution", "codec", "sampled_frame_indexes"]


def _compare_runs(runs: list[dict], numeric_keys: list[str],
                  exact_keys: list[str], tolerance: float) -> dict:
    """Compare N metric dicts. Return per-key deltas and overall pass/fail."""
    if len(runs) < 2:
        return {"pass": True, "note": "only one run — nothing to compare"}

    key_results = {}
    overall_pass = True

    for k in exact_keys:
        vals = [r.get(k) for r in runs if r.get(k) is not None]
        if not vals:
            continue
        identical = all(v == vals[0] for v in vals)
        key_results[k] = {"identical": identical, "values": vals}
        if not identical:
            overall_pass = False

    for k in numeric_keys:
        vals = [r.get(k) for r in runs if isinstance(r.get(k), (int, float))]
        if not vals:
            continue
        mn, mx  = min(vals), max(vals)
        delta   = round(mx - mn, 9)
        passed  = delta <= tolerance
        key_results[k] = {
            "pass":      passed,
            "min":       mn,
            "max":       mx,
            "delta":     delta,
            "tolerance": tolerance,
            "values":    vals,
        }
        if not passed:
            overall_pass = False

    return {"pass": overall_pass, "keys": key_results}


def run_repeatability(path: Path, metric_fn, n_passes: int,
                      numeric_keys: list[str], exact_keys: list[str],
                      tolerance: float) -> dict:
    runs = [metric_fn(path) for _ in range(n_passes)]
    first_error = next((r.get("error") for r in runs if r.get("error")), None)
    comparison  = _compare_runs(runs, numeric_keys, exact_keys, tolerance)

    return {
        "file":       str(path.name),
        "abs_path":   str(path),
        "n_passes":   n_passes,
        "tolerance":  tolerance,
        "error":      first_error,
        "pass":       comparison.get("pass", False) and first_error is None,
        "comparison": comparison,
        "runs":       runs,
    }


# ---------------------------------------------------------------------------
# Report writer
# ---------------------------------------------------------------------------

def write_json(obj: dict, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(obj, f, indent=2)
    print(f"  wrote {path}")


def write_repeatability_report(image_results: list, video_results: list, path: Path):
    all_results = image_results + video_results
    n_pass = sum(1 for r in all_results if r["pass"])
    n_fail = sum(1 for r in all_results if not r["pass"])

    failed_keys: dict[str, int] = {}
    for r in all_results:
        for k, v in r.get("comparison", {}).get("keys", {}).items():
            if isinstance(v, dict):
                failed = not v.get("identical", True) or not v.get("pass", True)
                if failed:
                    failed_keys[k] = failed_keys.get(k, 0) + 1

    total = len(all_results)
    if total == 0:
        verdict = "NULL_RUN"
    elif n_fail == 0:
        verdict = "STABLE"
    else:
        verdict = "UNSTABLE"

    report = {
        "generated_at":         datetime.now().isoformat(),
        "total_files":          total,
        "tested_file_count":    total,
        "repeat_count":         all_results[0]["n_passes"] if all_results else 0,
        "passed":               n_pass,
        "failed":               n_fail,
        "verdict":              verdict,
        "failed_metric_counts": failed_keys,
        "image_results":        image_results,
        "video_results":        video_results,
    }
    write_json(report, path)
    return report


def write_summary(manifest: dict, quality: dict, repeat_report: dict, path: Path):
    imgs = quality.get("images", [])
    vids = quality.get("videos", [])
    auds = quality.get("audio",  [])

    def _avg(records, key):
        vals = [r[key] for r in records if isinstance(r.get(key), (int, float))]
        return round(sum(vals) / len(vals), 3) if vals else "n/a"

    n_total  = repeat_report.get("total_files", 0)
    n_pass   = repeat_report.get("passed", 0)
    n_fail   = repeat_report.get("failed", 0)
    verdict  = repeat_report.get("verdict", "n/a")
    repeat_n = repeat_report.get("repeat_count", 0)
    bad_keys = repeat_report.get("failed_metric_counts", {})

    lines = [
        "# Media Calibration Report",
        f"Generated: {datetime.now().isoformat()}",
        f"Scan root: {manifest['scan_root']}",
        "",
        "## Counts",
        f"- Images: {manifest['counts'].get('images', 0)}",
        f"- Videos: {manifest['counts'].get('videos', 0)}",
        f"- Audio:  {manifest['counts'].get('audio',  0)}",
        "",
        "## Image Quality (averages)",
        f"- Brightness: {_avg(imgs, 'brightness')}",
        f"- Contrast:   {_avg(imgs, 'contrast')}",
        f"- Blur score: {_avg(imgs, 'blur_laplacian_var')}",
        f"- Noise est.: {_avg(imgs, 'noise_estimate')}",
        "",
        "## Video Quality (averages)",
        f"- Brightness: {_avg(vids, 'brightness_mean')}",
        f"- Contrast:   {_avg(vids, 'contrast_mean')}",
        f"- Blur score: {_avg(vids, 'blur_laplacian_var_mean')}",
        f"- Motion:     {_avg(vids, 'motion_level_mean')}",
        "",
        "## Audio (averages)",
        f"- RMS dB:        {_avg(auds, 'rms_db')}",
        f"- Peak dB:       {_avg(auds, 'peak_db')}",
        f"- Silence ratio: {_avg(auds, 'silence_ratio')}",
        "",
        "## Repeatability / Determinism Check",
        f"- Repeat passes per file: {repeat_n}",
        f"- Files tested:           {n_total}",
        f"- Passed:                 {n_pass}",
        f"- Failed:                 {n_fail}",
    ]

    if bad_keys:
        lines.append("- Metrics with variance across runs:")
        for k, count in sorted(bad_keys.items(), key=lambda x: -x[1]):
            lines.append(f"    - `{k}`: {count} file(s) failed")
    else:
        lines.append("- Metrics with variance: none")

    lines += [
        f"- Verdict: **{verdict}**",
        "",
    ]

    if verdict == "NULL_RUN":
        lines.append(
            "> NULL RUN — no files were tested after filters were applied. "
            "Check --images-only / --videos-only flags and confirm media exists in the scan root."
        )
    elif verdict == "STABLE":
        lines.append(
            "> Corpus is deterministic — safe to use as a repeatability baseline."
        )
    else:
        lines.append(
            "> WARNING: corpus has non-deterministic files. "
            "Inspect `repeatability_report.json` and exclude unstable files."
        )

    lines += ["", "## Errors"]
    errors = [(r.get("file","?"), r["error"]) for r in imgs + vids + auds if r.get("error")]
    if errors:
        for fname, err in errors:
            lines.append(f"- `{fname}`: {err}")
    else:
        lines.append("- None")

    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"  wrote {path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    args = parse_args()
    out_dir = args.output
    print("=== Media Calibration Test ===")
    print(f"Repeat passes: {args.repeat}  |  Limit: {args.limit or 'none'}")

    # Determine scan root
    mount_status = check_mount(MOUNT_POINT)
    if mount_status["mounted"]:
        drive_home = MOUNT_POINT / "home"
        probe_root = drive_home if drive_home.exists() else MOUNT_POINT
        probe_media = scan_media(probe_root)
        if sum(len(v) for v in probe_media.values()) > 0:
            scan_root = probe_root
            print(f"Using mounted drive: {scan_root}")
        else:
            scan_root = LOCAL_CORPUS
            print(f"Drive home/ is empty — using local PH6 corpus: {scan_root}")
    else:
        scan_root = LOCAL_CORPUS
        print(f"Drive not mounted — using local PH6 corpus: {scan_root}")

    if not scan_root.exists():
        print(f"ERROR: scan root does not exist: {scan_root}")
        sys.exit(1)

    # Scan
    print("\nScanning media...")
    media = scan_media(scan_root)

    images = media["images"] if not args.videos_only else []
    videos = media["videos"] if not args.images_only else []
    audio  = media["audio"]

    # If the chosen corpus has no videos, try the PH6 logs directory
    if not videos and not args.images_only and LOCAL_VIDEO_ROOT.exists():
        vid_scan = scan_media(LOCAL_VIDEO_ROOT)
        if vid_scan["videos"]:
            print(f"  No videos in primary corpus — adding PH6 logs: {LOCAL_VIDEO_ROOT}")
            videos = vid_scan["videos"]

    if args.limit:
        images = images[: args.limit]
        videos = videos[: args.limit]

    print(f"  Images: {len(images)}  Videos: {len(videos)}  Audio: {len(audio)}")

    manifest = build_manifest(
        {"images": images, "videos": videos, "audio": audio}, scan_root
    )
    write_json(manifest, out_dir / "calibration_manifest.json")

    # Single-pass quality report (first pass of each file)
    print("\nComputing quality metrics (pass 1)...")
    img_quality = [image_metrics(p) for p in images]
    vid_quality = [video_metrics(p) for p in videos]
    aud_quality = [audio_metrics(p) for p in audio]

    quality_report = {
        "generated_at": datetime.now().isoformat(),
        "images": img_quality,
        "videos": vid_quality,
        "audio":  aud_quality,
    }
    write_json(quality_report, out_dir / "media_quality_report.json")

    # Repeatability — only if repeat > 1
    print(f"\nRepeatability testing ({args.repeat} passes per file)...")
    img_repeat, vid_repeat = [], []

    for i, p in enumerate(images, 1):
        print(f"  image {i}/{len(images)}: {p.name}", end="", flush=True)
        r = run_repeatability(p, image_metrics, args.repeat,
                              NUMERIC_IMAGE_KEYS, EXACT_IMAGE_KEYS, IMAGE_TOLERANCE)
        img_repeat.append(r)
        print(f"  {'PASS' if r['pass'] else 'FAIL'}")

    for i, p in enumerate(videos, 1):
        print(f"  video {i}/{len(videos)}: {p.name}", end="", flush=True)
        r = run_repeatability(p, video_metrics, args.repeat,
                              NUMERIC_VIDEO_KEYS, EXACT_VIDEO_KEYS, VIDEO_TOLERANCE)
        vid_repeat.append(r)
        print(f"  {'PASS' if r['pass'] else 'FAIL'}")

    repeat_report = write_repeatability_report(
        img_repeat, vid_repeat, out_dir / "repeatability_report.json"
    )

    print("\nWriting summary...")
    write_summary(manifest, quality_report, repeat_report, out_dir / "final_summary.md")

    n_fail = repeat_report["failed"]
    verdict = repeat_report["verdict"]
    print(f"\n=== Done === verdict: {verdict}  failures: {n_fail}")
    print(f"Output: {out_dir}")


if __name__ == "__main__":
    main()
