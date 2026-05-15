# GAP-16: Microdia Integrated Audio+Video USB Contention

```text
GAP-ID:    GAP-16
Status:    CONFIRMED / SPLIT — GAP-16A + GAP-16B
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
         — no disconnect, no drops in clean run

GAP-16B: Intermittent physical/thermal USB instability
         — camera disconnect observed in prior runs and R2
         — not yet proven as contention-induced
         — suspected: cable seating or thermal event
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

## GAP-16B: Intermittent USB Disconnect — SPLIT REQUIRED

### Evidence (C01-GAP16-R2 — `gap16_r2_20260515T101657Z`)

```text
run_id:              20260515T101657Z
target_frames:       600
frames_passed:       351
disconnect_at_sec:   18.065
consecutive_fails:   30 (threshold reached)
audio_overruns:      5330
arecord_rc:          1
thermal:             49–50°C (stable range, not thermal throttle)
```

### Prior disconnect observations

| Run | Mode | Duration | Exit |
|---|---|---|---|
| run_20260514_231752 | video + audio | ~15s | camera_loss |
| run_20260514_232026 | video + audio | ~2s  | camera_loss |
| Extended stability 5-min test | video only | ~205s | VIDIOC_REQBUFS errno=19 |
| AV contention first run | video + audio | ~60s | camera_loss |
| C01-GAP16-R2 | video + audio | ~18s | CAMERA_DISCONNECT (30 consec fails) |

### Interpretation

Disconnect occurs in video-only and AV runs alike. Thermal data is stable
(49–50°C). Root cause is not confirmed — candidates are:
- USB cable / connector seating
- USB bus power transient under combined load
- Kernel UVC driver isochronous scheduling conflict (original hypothesis)

GAP-16B requires further isolation to distinguish cable fault from bus fault.

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

## Next Required Action

```text
GAP-16A: STABLE-CONFIRMED pending one additional clean AV run with no disconnect.
GAP-16B: Isolation test required:
         - Run video-only capture for 5+ minutes.
         - If disconnect occurs: cable/port fault (not contention).
         - If clean: disconnect is AV-load-induced (bus power issue).
```
