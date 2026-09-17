"""Deterministic audio-intake and camera/audio-correlation primitives.

Audio remains CRAM-0 ``MEASURED`` evidence: no audio PASS/DROP policy is
ratified, so this module cannot write CRAM-A or CRAM-R and cannot mint RTs.
"""
from __future__ import annotations

import array
import hashlib
import math
import os
import wave
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ph6.cram_pu.schemas.canonical import blake2b_256, canonical_json, fp_int

PROFILE = {
    "schema": "ph6.audio.measurement_profile.v1",
    "profile_id": "PH6-AUDIO-PCM-S16LE-MEASURE-v1",
    "measurement_status": "UNRATIFIED_NO_PASS_DROP",
    "metrics": ["rms_fp", "peak_fp", "clipping_count", "silence_fraction_fp", "alsa_overrun_count"],
    "silence_measurement_abs_lt": 500,
    "clipping_measurement_abs_ge": 32767,
}
PROFILE_HASH = blake2b_256(canonical_json(PROFILE))
CORRELATION_RULE = "ph6.camera_timestamp_within_audio_window.v1"


def _utc_from_ns(value: int) -> str:
    return datetime.fromtimestamp(value / 1_000_000_000, timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _atomic_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    fd = os.open(str(tmp), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)
    try:
        os.write(fd, data); os.fsync(fd)
    finally:
        os.close(fd)
    os.replace(tmp, path)
    dfd = os.open(str(path.parent), os.O_RDONLY)
    try: os.fsync(dfd)
    finally: os.close(dfd)


def _atomic_json(path: Path, obj: dict) -> None:
    _atomic_bytes(path, canonical_json(obj) + b"\n")


def normalize_wav(path: Path, *, audio_event_id: str, sensor_id: str,
                  capture_start_ns: int, capture_end_ns: int,
                  alsa_overrun_count: int = 0) -> dict:
    """Normalize a PCM S16_LE WAV without deriving any authority verdict."""
    raw_file = path.read_bytes()
    with wave.open(str(path), "rb") as wav:
        channels, rate, width, frames = wav.getnchannels(), wav.getframerate(), wav.getsampwidth(), wav.getnframes()
        raw_samples = wav.readframes(frames)
    if width != 2:
        raise ValueError("only PCM S16_LE WAV is supported by the established audio capture path")
    if capture_end_ns < capture_start_ns:
        raise ValueError("audio capture end precedes start")
    samples = array.array("h"); samples.frombytes(raw_samples)
    if samples.itemsize != 2:
        raise ValueError("host does not expose 16-bit PCM array")
    values = [abs(x) for x in samples]
    count = len(values)
    sum_sq = sum(x * x for x in values)
    rms = math.sqrt(sum_sq / count) if count else 0.0
    peak = max(values, default=0)
    silence = sum(x < PROFILE["silence_measurement_abs_lt"] for x in values) / count if count else 0.0
    payload_hash = blake2b_256(raw_file)
    event = {
        "schema": "ph6.audio.event.v1",
        "audio_event_id": audio_event_id,
        "sensor_id": sensor_id,
        "media_type": "AUDIO",
        "capture_start_utc": _utc_from_ns(capture_start_ns),
        "capture_end_utc": _utc_from_ns(capture_end_ns),
        "capture_start_ns": capture_start_ns,
        "capture_end_ns": capture_end_ns,
        "sample_rate_hz": rate,
        "channels": channels,
        "sample_format": "S16_LE",
        "duration_ns": frames * 1_000_000_000 // rate if rate else 0,
        "payload_hash": payload_hash,
        "hash_algorithm": "BLAKE2b-256",
        "measurement_profile_id": PROFILE["profile_id"],
        "measurement_profile_hash": PROFILE_HASH,
        "measurements": {"rms_fp": fp_int(rms), "peak_fp": fp_int(peak),
                         "clipping_count": sum(x >= PROFILE["clipping_measurement_abs_ge"] for x in values),
                         "silence_fraction_fp": fp_int(silence), "alsa_overrun_count": alsa_overrun_count},
        "quality_facts": {"clipping_detected": peak >= PROFILE["clipping_measurement_abs_ge"]},
        "measurement_status": "MEASURED",
        "verdict_status": "NOT_IMPLEMENTED_UNRATIFIED_AUDIO_POLICY",
        "authority": "LANE_1",
    }
    event["event_hash"] = blake2b_256(canonical_json(event))
    return event


def write_audio_intake(cram_store: Path, wav_path: Path, event: dict) -> dict:
    """Write CRAM-0 audio evidence atomically; deliberately not a CRAM-A commit."""
    if event.get("verdict_status") != "NOT_IMPLEMENTED_UNRATIFIED_AUDIO_POLICY":
        raise ValueError("audio intake cannot accept an authority verdict")
    root = cram_store / "audio_intake"
    event_id = event["audio_event_id"]
    payload_path, record_path = root / f"{event_id}.wav", root / f"{event_id}.json"
    _atomic_bytes(payload_path, wav_path.read_bytes())
    record = {**event, "cram_tier": "CRAM-0", "payload_path": payload_path.name,
              "evidence_id": f"cram0:audio:{event_id}"}
    record["evidence_hash"] = blake2b_256(canonical_json(record))
    _atomic_json(record_path, record)
    _atomic_bytes(record_path.with_name(record_path.name + ".blake2b"), (record["evidence_hash"] + "\n").encode())
    return record


def correlate(*, session_id: str, camera_event_id: str, camera_evidence_hash: str,
              camera_capture_ns: int, audio_record: dict) -> dict:
    start, end = audio_record["capture_start_ns"], audio_record["capture_end_ns"]
    if not start <= camera_capture_ns <= end:
        raise ValueError("camera acquisition timestamp is outside the audio capture window")
    core = {"schema": "ph6.multimodal.correlation.v1", "session_id": session_id,
            "camera_event_id": camera_event_id, "camera_evidence_hash": camera_evidence_hash,
            "audio_event_id": audio_record["audio_event_id"], "audio_evidence_hash": audio_record["evidence_hash"],
            "camera_capture_ns": camera_capture_ns, "audio_window_start_ns": start,
            "audio_window_end_ns": end, "correlation_rule": CORRELATION_RULE,
            "authority": "LANE_1", "affects_pass_drop": False}
    core["correlation_id"] = "corr_" + blake2b_256(canonical_json(core))[:24]
    return core


def write_correlation(mram_s: Path, correlation: dict, advisory_input: dict) -> Path:
    """Persist linkage only in MRAM-S; it cannot alter either evidence item."""
    payload = {"schema": "ph6.mram_s.multimodal_linkage.v1", "authority": "NONE",
               "advisory_only": True, "correlation": correlation, "soso_input": advisory_input,
               "affects_pass_drop": False, "affects_cram_commit": False}
    path = mram_s / "correlations" / f"{correlation['correlation_id']}.json"
    _atomic_json(path, payload)
    return path


def soso_input(correlation: dict, camera_metrics: dict, audio_record: dict) -> dict:
    """Read-only advisory envelope; this is input, not a SoSo implementation."""
    return {"schema": "ph6.soso.multimodal_input.v1", "authority": "NONE", "advisory_only": True,
            "correlation_id": correlation["correlation_id"],
            "camera": {"event_id": correlation["camera_event_id"], "evidence_hash": correlation["camera_evidence_hash"], "measurements": camera_metrics},
            "audio": {"event_id": audio_record["audio_event_id"], "evidence_hash": audio_record["evidence_hash"],
                      "measurements": audio_record["measurements"], "quality_facts": audio_record["quality_facts"],
                      "measurement_profile_hash": audio_record["measurement_profile_hash"]},
            "affects_pass_drop": False, "affects_cram_commit": False, "affects_thresholds": False}
