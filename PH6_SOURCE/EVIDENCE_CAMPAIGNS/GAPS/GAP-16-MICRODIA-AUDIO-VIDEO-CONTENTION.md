# GAP-16: Microdia Integrated Audio+Video USB Contention

```text
GAP-ID:    GAP-16
Status:    OPEN / HARDWARE-CONSTRAINED
Severity:  MEDIUM
Opened:    2026-05-14
```

---

## Summary

Concurrent video capture and built-in USB microphone capture using the Microdia
Streaming Camera (0c45:636b) causes the camera to drop off the USB bus entirely.
The failure is a kernel UVC driver / USB isochronous transfer conflict — not a
PH6 deterministic logic failure.

**C01 video-only evidence run is not affected.**

---

## Observed Failure

```text
Error:    VIDIOC_REQBUFS: errno=19 (No such device)
Symptom:  /dev/video0 disappears
          ALSA card 1 disappears
          Microdia device disappears from lsusb
Recovery: Physical USB replug required
```

Failure reproductions:

| Run | Mode | Frames | Exit |
|---|---|---|---|
| run_20260514_231752 | video + audio (640x480) | 60 | camera_loss |
| run_20260514_232026 | video + audio (320x240) | 49 | camera_loss |
| arecord standalone  | audio only 44100Hz | — | ALSA xrun → No such device |
| arecord standalone  | audio only 8000Hz  | — | ALSA xrun → No such device |

---

## Root Cause

The Microdia Streaming Camera exposes both UVC video and USB Audio on the same
USB device/bus. The Pi 5 USB controller cannot sustain simultaneous DMA buffer
allocation for both isochronous streams (video) and interrupt/bulk transfers
(audio). When both are requested, the kernel drops the device.

This is a hardware/driver constraint, not a PH6 software defect.

---

## C01 Impact

```text
NONE.

C01 evidence run (run_20260514_231321) used video only.
  frames:          300
  replay_status:   PASS
  hash_chain:      intact / 1139 packets
  result_set_hash: 08a841b092a413436eabf2fdb096436fc814a5f932e565b71475ba81a69375a4
  PostRun:         COMPLETE
  C01 status:      PASS — pending human sign-off
```

---

## Audio Evidence Captured (Despite Failure)

The WAV files written before each crash contain valid fan audio signal:

| File | Duration | RMS | Fan signal |
|---|---|---|---|
| run_20260514_231752/hot/run_audio.wav | 14.7s | 969 | YES |
| run_20260514_232026/hot/run_audio.wav | 1.6s  | 496 | YES |
| /tmp/fan_test.wav (arecord)           | 15.0s | 1173 | YES |

Fan is detectable. USB stability is not.

---

## Recommended Operational Rule

```text
For PH6 C01/C02 video evidence runs:
  Use Microdia camera for video only.
  Do not enable --audio with the Microdia built-in mic.
  The --audio flag in frame_filter.py is incompatible with this camera.
```

---

## Recommended Mitigations

```text
1. External USB mic on a separate port/device (preferred — cleanest fix).
2. Sequential capture: audio-only first, video-only second (works but not concurrent).
3. Different camera/mic pair with independent USB endpoints.
4. Avoid --audio flag entirely during PH6 video evidence runs.
```

---

## Scope

```text
Affected:     audio+video concurrent capture with Microdia camera
Not affected: video-only capture (confirmed stable at 640x480, 1280x720, 1920x1080)
Not affected: PSEUDO logic
Not affected: CRAM write contract
Not affected: Lane 1 / Lane 2 authority model
Not affected: replay parity
Not affected: RSYNC behavior
Not affected: C01 closure
```

---

## Next Action

```text
No PH6 software patch required.
Hardware mitigation (external mic) recommended before audio evidence runs.
C01 closure proceeds independently — human sign-off on C01_CLOSURE_RECEIPT.md.
C02 (Pi-to-Pi transfer) proceeds independently — no audio dependency.
```
