import wave
from pathlib import Path
import pytest

from ph6.cram_pu.multimodal import correlate, normalize_wav, soso_input, write_audio_intake

def wav(path: Path):
    with wave.open(str(path), "wb") as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(8000); f.writeframes(b"\x00\x00\xff\x7f" * 8)

def test_audio_evidence_and_correlation_are_deterministic(tmp_path):
    source = tmp_path / "source.wav"; wav(source)
    event = normalize_wav(source, audio_event_id="audio_0001", sensor_id="alsa:Device", capture_start_ns=10, capture_end_ns=20)
    assert event["verdict_status"] == "NOT_IMPLEMENTED_UNRATIFIED_AUDIO_POLICY"
    record = write_audio_intake(tmp_path / "cram_store", source, event)
    assert (tmp_path / "cram_store/audio_intake/audio_0001.json.blake2b").exists()
    correlation = correlate(session_id="run", camera_event_id="frame_1", camera_evidence_hash="a" * 64, camera_capture_ns=15, audio_record=record)
    advisory = soso_input(correlation, {"mean_brightness_fp": 1}, record)
    assert advisory["authority"] == "NONE" and advisory["affects_pass_drop"] is False

def test_invalid_correlation_is_rejected(tmp_path):
    source = tmp_path / "source.wav"; wav(source)
    event = normalize_wav(source, audio_event_id="audio_0001", sensor_id="alsa:Device", capture_start_ns=10, capture_end_ns=20)
    record = write_audio_intake(tmp_path / "cram_store", source, event)
    with pytest.raises(ValueError):
        correlate(session_id="run", camera_event_id="frame_1", camera_evidence_hash="a" * 64, camera_capture_ns=21, audio_record=record)
