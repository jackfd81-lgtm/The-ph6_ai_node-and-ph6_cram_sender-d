# PH6 Dual USB Camera — Presence Gate Report
**PROPOSED** — Hardware readiness gate. Not a PSEUDO-A frame verdict.

## Gate Status

**DUAL_CAMERA_PRESENCE_GATE_PASS**

| Camera | Node | Present | Capture Node Confirmed | Hold Label |
|--------|------|---------|----------------------|------------|
| CAMERA_A (DV20_USB) | /dev/video0 | True | True | — |
| CAMERA_B (STREAMING_CAM) | /dev/video2 | True | True | — |

```
CAMERA_A_PRESENT = true
CAMERA_B_PRESENT = true
CAMERA_A_CAPTURE_NODE_CONFIRMED = true
CAMERA_B_CAPTURE_NODE_CONFIRMED = true
```

**USB instability events detected in dmesg**: 2

  `[ 3768.536535] usb 3-1: USB disconnect, device number 2`
  `[ 3771.402277] usb 3-1: USB disconnect, device number 3`

## Camera A

- Node: `/dev/video0`
- Node exists: True
- V4L2 open: True
- Frames read: 3 / 3 required
- Gate pass: True
- Failure reason: none

## Camera B

- Node: `/dev/video2`
- Node exists: True
- V4L2 open: True
- Frames read: 3 / 3 required
- Gate pass: True
- Failure reason: none

## Note

This is a hardware readiness gate, not an authority verdict.
`DUAL_CAMERA_PRESENCE_GATE_PASS` / `DUAL_CAMERA_PRESENCE_GATE_HOLD` labels
are distinct from PSEUDO-A `PASS` / `DROP` frame verdicts.

---
*proposed_by: claude-code-lane2 | ratified_by: null*
