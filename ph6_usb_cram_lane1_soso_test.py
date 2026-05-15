#!/usr/bin/env python3

import cv2
import os
import json
import time
import hashlib
import tempfile
from pathlib import Path
from datetime import datetime, timezone

# ============================================================
# PH6 USB CAM — CRAM / LANE 1 / PSEUDO / SOSO TEST
# ============================================================

VIDEO_DEVICE = 1          # Change to 1 or 2 if needed
TARGET_FRAMES = 300       # PH6 rule: under 300 frames is invalid
WIDTH = 640
HEIGHT = 480
FPS_TARGET = 24

RUN_ID = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

ROOT = Path(f"/tmp/ph6_usb_cam_test_{RUN_ID}")
CRAM_0 = ROOT / "cram-0"
CRAM_A = ROOT / "cram-a"
CRAM_R = ROOT / "cram-r"
MRAM_S = ROOT / "mram-s"
AUDIT = ROOT / "audit"
EXPORT = ROOT / "export"

for p in [CRAM_0, CRAM_A, CRAM_R, MRAM_S, AUDIT, EXPORT]:
    p.mkdir(parents=True, exist_ok=True)

audit_chain_file = AUDIT / "audit_chain.jsonl"


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def blake2b256(data: bytes) -> str:
    return hashlib.blake2b(data, digest_size=32).hexdigest()


def canonical_json(obj) -> bytes:
    return json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False
    ).encode("utf-8")


def atomic_write_json(path: Path, obj: dict):
    """
    PH6-style CRAM atomic write:
    write tmp -> fsync file -> rename -> fsync directory -> commit marker
    """
    data = canonical_json(obj)
    digest = blake2b256(data)

    tmp_fd, tmp_name = tempfile.mkstemp(
        prefix=path.name + ".",
        suffix=".tmp",
        dir=str(path.parent)
    )

    try:
        with os.fdopen(tmp_fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())

        os.rename(tmp_name, path)

        dir_fd = os.open(str(path.parent), os.O_DIRECTORY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)

        marker = path.with_suffix(path.suffix + ".blake2b")
        with open(marker, "w", encoding="utf-8") as f:
            f.write(digest + "\n")
            f.flush()
            os.fsync(f.fileno())

        dir_fd = os.open(str(path.parent), os.O_DIRECTORY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)

        return digest

    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def append_audit(event: dict, prev_hash: str):
    event_obj = {
        "schema": "ph6.audit_event.test.v1",
        "event_seq": event["event_seq"],
        "event_type": event["event_type"],
        "object_id": event["object_id"],
        "authority_hash": event["authority_hash"],
        "prev_event_hash": prev_hash,
        "timestamp_utc": utc_now(),
        "details": event.get("details", {}),
    }

    base = canonical_json(event_obj)
    event_hash = blake2b256(base)
    event_obj["event_hash"] = event_hash

    with open(audit_chain_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(event_obj, sort_keys=True) + "\n")
        f.flush()
        os.fsync(f.fileno())

    return event_hash


def pseudo_lane1_verdict(frame_index, gray, prev_gray):
    """
    Lane 1 / PSEUDO deterministic authority.
    No AI.
    No ML.
    No probabilistic model.

    Simple deterministic gates:
    - blur via Laplacian variance
    - motion_fraction via thresholded absdiff
    """

    blur_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())

    if prev_gray is None:
        motion_fraction = 0.0
    else:
        diff = cv2.absdiff(gray, prev_gray)
        _, thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
        motion_fraction = float(cv2.countNonZero(thresh)) / float(thresh.size)

    # Fixed deterministic thresholds for this test only
    blur_ok = blur_var >= 20.0
    motion_ok = motion_fraction <= 0.85

    verdict = "PASS" if blur_ok and motion_ok else "DROP"

    authority_packet = {
        "schema": "ph6.pseudo_lane1.usb_test.v1",
        "authority": "LANE_1_PSEUDO",
        "authority_zero": False,
        "frame_index": frame_index,
        "verdict": verdict,
        "metrics": {
            "laplacian_variance": f"{blur_var:.6f}",
            "motion_fraction": f"{motion_fraction:.6f}",
        },
        "thresholds": {
            "blur_min": "20.000000",
            "motion_fraction_max": "0.850000",
        },
        "timestamp_utc": utc_now(),
    }

    authority_hash = blake2b256(canonical_json(authority_packet))

    return verdict, authority_packet, authority_hash, motion_fraction, blur_var


def soso_advisory(frame_index, motion_fraction, blur_var, lane1_verdict):
    """
    SoSo advisory-only path.
    Authority ZERO.
    Cannot issue PASS/DROP.
    Cannot override Lane 1.
    Cannot write CRAM-A.
    """

    if blur_var < 20.0:
        note = "ADVISORY_BLUR_PRESSURE"
    elif motion_fraction > 0.50:
        note = "ADVISORY_MOTION_PRESSURE"
    else:
        note = "ADVISORY_STABLE"

    return {
        "schema": "ph6.soso.advisory_usb_test.v1",
        "authority": "ZERO",
        "authority_zero": True,
        "advisory_only": True,
        "replay_dependency": False,
        "frame_index": frame_index,
        "lane1_verdict_observed": lane1_verdict,
        "advisory_note": note,
        "metrics_observed": {
            "laplacian_variance": f"{blur_var:.6f}",
            "motion_fraction": f"{motion_fraction:.6f}",
        },
        "forbidden_fields_absent": [
            "verdict",
            "result",
            "pass",
            "drop"
        ],
        "timestamp_utc": utc_now(),
    }


def main():
    print("PH6 USB CAM CRAM / LANE 1 / PSEUDO / SOSO TEST")
    print("=================================================")
    print(f"Run ID: {RUN_ID}")
    print(f"Root:   {ROOT}")
    print(f"Device: /dev/video{VIDEO_DEVICE}")
    print()

    cap = cv2.VideoCapture(VIDEO_DEVICE, cv2.CAP_V4L2)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)
    cap.set(cv2.CAP_PROP_FPS, FPS_TARGET)

    if not cap.isOpened():
        print("FAIL: USB camera could not be opened.")
        print("Try changing VIDEO_DEVICE to 1 or 2.")
        return 1

    actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    actual_fps = cap.get(cv2.CAP_PROP_FPS)

    print(f"Camera opened: {actual_width}x{actual_height} @ reported {actual_fps} fps")
    print()

    prev_gray = None
    prev_event_hash = "GENESIS"

    pass_count = 0
    drop_count = 0
    soso_count = 0
    frame_count = 0
    failed_reads = 0

    start = time.time()

    for frame_index in range(TARGET_FRAMES):
        ok, frame = cap.read()

        if not ok or frame is None:
            failed_reads += 1
            print(f"Frame {frame_index}: READ_FAIL")
            continue

        frame_count += 1

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        verdict, authority_packet, authority_hash, motion_fraction, blur_var = pseudo_lane1_verdict(
            frame_index,
            gray,
            prev_gray
        )

        evidence_packet = {
            "schema": "ph6.cram.usb_frame_packet.v1",
            "run_id": RUN_ID,
            "frame_index": frame_index,
            "source": f"/dev/video{VIDEO_DEVICE}",
            "lane1_authority_hash": authority_hash,
            "lane1_verdict": verdict,
            "timestamp_utc": utc_now(),
            "metrics": authority_packet["metrics"],
        }

        # CRAM-0 raw metadata packet
        cram0_path = CRAM_0 / f"frame_{frame_index:06d}.json"
        atomic_write_json(cram0_path, evidence_packet)

        if verdict == "PASS":
            pass_count += 1
            target_path = CRAM_A / f"frame_{frame_index:06d}.json"
            atomic_write_json(target_path, evidence_packet)
        else:
            drop_count += 1
            target_path = CRAM_R / f"frame_{frame_index:06d}.json"
            atomic_write_json(target_path, evidence_packet)

        # SoSo advisory sidecar
        advisory_packet = soso_advisory(
            frame_index,
            motion_fraction,
            blur_var,
            verdict
        )

        soso_path = MRAM_S / f"soso_frame_{frame_index:06d}.json"
        atomic_write_json(soso_path, advisory_packet)
        soso_count += 1

        # Audit event
        prev_event_hash = append_audit(
            {
                "event_seq": frame_index,
                "event_type": "FRAME_EVALUATED",
                "object_id": f"frame_{frame_index:06d}",
                "authority_hash": authority_hash,
                "details": {
                    "lane1_verdict": verdict,
                    "soso_authority": "ZERO",
                    "cram_target": str(target_path),
                },
            },
            prev_event_hash
        )

        prev_gray = gray

        if frame_index % 50 == 0:
            print(
                f"Frame {frame_index:06d}: "
                f"{verdict} | blur={blur_var:.2f} | motion_fraction={motion_fraction:.4f}"
            )

    cap.release()

    duration = time.time() - start

    summary = {
        "schema": "ph6.usb_cam_test_summary.v1",
        "run_id": RUN_ID,
        "root": str(ROOT),
        "frames_target": TARGET_FRAMES,
        "frames_captured": frame_count,
        "failed_reads": failed_reads,
        "pass_count": pass_count,
        "drop_count": drop_count,
        "soso_advisory_count": soso_count,
        "duration_seconds": f"{duration:.6f}",
        "effective_fps": f"{frame_count / duration:.6f}" if duration > 0 else "0.000000",
        "lane1_authority": "PSEUDO_ONLY",
        "soso_authority": "ZERO",
        "valid_minimum_300_frames": frame_count >= 300,
        "cram_write_contract": "atomic_json_with_blake2b_marker",
        "final_audit_hash": prev_event_hash,
        "timestamp_utc": utc_now(),
    }

    atomic_write_json(EXPORT / "summary.json", summary)

    print()
    print("RESULT SUMMARY")
    print("==============")
    print(json.dumps(summary, indent=2, sort_keys=True))

    if frame_count < 300:
        print()
        print("FINAL VERDICT: INVALID")
        print("Reason: Fewer than 300 frames captured.")
        return 2

    if soso_count != frame_count:
        print()
        print("FINAL VERDICT: FAIL")
        print("Reason: SoSo advisory packet count does not match captured frame count.")
        return 3

    print()
    print("FINAL VERDICT: PASS")
    print("Meaning: USB cam + CRAM + Lane 1/PSEUDO + SoSo advisory path completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
