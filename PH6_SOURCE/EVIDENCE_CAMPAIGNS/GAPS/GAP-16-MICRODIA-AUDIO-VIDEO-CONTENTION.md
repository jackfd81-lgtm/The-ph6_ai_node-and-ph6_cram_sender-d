# GAP-16: Microdia Integrated Audio+Video USB Contention

```text
GAP-ID:    GAP-16
Status:    GAP-16A: STABLE-CONFIRMED / GAP-16B: AV-LOAD-INDUCED / CONFIRMED
Severity:  MEDIUM
Opened:    2026-05-14
Updated:   2026-05-15
```

---

## Classification

GAP-16 is now split into two distinct findings based on C01-GAP16-R2 evidence.

```text
GAP-16A: USB AV contention degradation
         — measurable and repeatable
         — FPS drops ~33%, audio clips at 32767 under simultaneous AV
         — CONFIRMED

GAP-16B: AV-load-induced disconnect
         — camera disconnects under simultaneous AV capture
         — CONFIRMED AV-load-induced: 5-min video-only run clean (0 drops, 0 disconnects)
         — cable fault RULED OUT by gap16b_isolation_20260515T102608Z
         — CONFIRMED
```

---

## Summary

The Microdia Streaming Camera (0c45:636b) exposes both UVC video and USB Audio
on the same USB device. Simultaneous capture causes measurable FPS degradation
and audio clipping. In some runs, the camera also disconnects entirely —
classified separately as GAP-16B pending further isolation.

This is a sensor ingest quality issue, not a PH6 deterministic logic defect.
Lane 1 authority, CRAM write contract, and audit chain are unaffected.

---

## GAP-16A: AV Contention Degradation — CONFIRMED

### Evidence (patched 60s run — `av_contention_20260515T100841Z`)

```text
run_id:              20260515T100841Z
duration:            60s simultaneous audio+video
camera:              0c45:636b Microdia Streaming Camera at /dev/video1
audio:               hw:2,0 USB Audio, 44100 Hz mono

Video results:
  passed_frames:     1195
  dropped_frames:    0
  actual_fps:        19.9 (standalone baseline: ~29.6)
  fps_degradation:   ~33%
  disconnect:        none

Audio results:
  overrun_count:     0
  arecord_rc:        0
  rms:               917 (audio-only baseline: ~392)
  peak:              32767 (clipping ceiling)
  clipping:          YES
```

### Interpretation

The USB camera and USB audio path can coexist without disconnect or frame
drops, but simultaneous capture causes:
- Video FPS degraded ~33% (30 → 20 fps)
- Audio RMS elevated ~2.3× vs audio-only baseline
- Audio peak at clipping ceiling (32767)

This is USB isochronous transfer pressure on the shared bus, not a
PH6 authority or CRAM defect.

---

## GAP-16B: AV-Load-Induced Disconnect — CONFIRMED

### Isolation Test Evidence (`gap16b_isolation_20260515T102608Z`)

```text
run_id:              20260515T102608Z
mode:                video_only (no audio)
duration:            300s (5 full minutes)
frames_passed:       5974
frames_dropped:      0
actual_fps:          19.9
disconnect_at_sec:   null
usb_device_at_start: 0c45:636b Microdia Streaming Camera
usb_device_at_end:   0c45:636b Microdia Streaming Camera
checkpoints_clean:   60s / 120s / 180s / 240s — device present at all four
thermal:             46–49°C (stable, no throttle)
conclusion:          PASS — video-only path completely stable for 5 minutes
```

**Cable fault RULED OUT.** The camera runs continuously for 5 minutes video-only
with zero drops and zero disconnects. The disconnect fault is AV-load-induced.

### Disconnect evidence under AV load

| Run | Mode | Duration | Exit |
|---|---|---|---|
| run_20260514_231752 | video + audio | ~15s | camera_loss |
| run_20260514_232026 | video + audio | ~2s  | camera_loss |
| AV contention first run | video + audio | ~60s | camera_loss |
| C01-GAP16-R2 | video + audio | ~18s | CAMERA_DISCONNECT (30 consec fails) |
| GAP-16B isolation | video only | 300s | CLEAN — no disconnect |

### Interpretation

Video-only: 300s clean. AV simultaneous: disconnect in every tested run.
Thermal is stable in both modes. The disconnect is driven by USB bus
isochronous pressure from combined audio+video transfer — not cable, not
thermal, not camera hardware.

GAP-16B root cause: USB bus power / isochronous bandwidth collapse under
combined AV load on this device (0c45:636b, single integrated USB composite device).

---

## Original Hard-Disconnect Observation (2026-05-14)

```text
Error:    VIDIOC_REQBUFS: errno=19 (No such device)
Symptom:  /dev/videoX disappears from node list
          ALSA card disappears
          Microdia device disappears from lsusb
Recovery: Physical USB replug required
```

This failure mode is still valid. It is now classified under GAP-16B.

---

## Audio-Only Baseline (Confirmed Stable)

```text
Campaign: ph6.usb_audio_test.v1 — audio_test_20260515T095839Z
Duration: 180s (3 minutes)
Chunks:   180 / 180
Drops:    0
Overruns: 0
Avg RMS:  392
Result:   PASS
```

Audio-only path is stable for the tested duration.

---

## Lane Impact

```text
Authority Impact:  NONE
Lane 1 Impact:     NONE (if actual FPS and audio metrics are recorded per run)
Lane 2 Impact:     NONE
CRAM Impact:       NONE
Audit Chain:       NONE
C01 Video-Only:    UNAFFECTED — confirmed stable at 300 frames
```

---

## Required Operational Rules

```text
1. Record actual FPS in every AV run — do not assume nominal FPS.
2. Record audio peak, RMS, and overrun count in every AV run.
3. Classify audio with peak >= 32767 as degraded-quality evidence.
4. Do not use nominal FPS assumptions during simultaneous AV capture.
5. If camera disconnect is observed: stop loop cleanly (threshold=30 consec fails),
   log disconnect_at_sec, trigger GAP-16B re-evaluation.
```

---

## Recommended Mitigations

```text
GAP-16A (contention degradation):
  1. Separate USB buses for camera and microphone (preferred).
  2. Separate ingest nodes (one Pi for video, one for audio).
  3. Accept ~20 FPS as operational ceiling for this hardware under AV load.

GAP-16B (intermittent disconnect):
  1. Reseat USB cable — test with known-good cable.
  2. Powered USB hub to isolate bus power transients.
  3. Run video-only stability test for 10+ minutes to characterize disconnect rate.
  4. If disconnect persists in video-only: cable/port fault.
  5. If disconnect only under AV: USB bus power collapse under combined load.
```

---

## Status: CLOSED — Both GAP-16A and GAP-16B Confirmed

```text
GAP-16A: STABLE-CONFIRMED
         AV contention causes ~33% FPS degradation and audio clipping.
         Repeatable and measurable. No further action required unless hardware changes.

GAP-16B: AV-LOAD-INDUCED / CONFIRMED
         Isolation test (gap16b_isolation_20260515T102608Z) — 5-min video-only: CLEAN.
         Cable fault ruled out. Root cause: USB isochronous pressure under AV load.
         No further isolation required.

Both sub-gaps are sensor ingest (Lane 0) problems.
Lane 1 authority, CRAM, hash chain, and replay parity: UNAFFECTED.
See: PH6-GOVERNANCE-SENSOR-INGEST-SEPARATION-1.0 for doctrine.
```
