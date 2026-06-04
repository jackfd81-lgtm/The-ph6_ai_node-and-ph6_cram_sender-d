# PH6 USB CAMERA 12,000-FRAME TEST REPORT

Test:          PH6-USB-CAM-PSEUDO-SOSO-TOK-12000-v1
Run ID:        PH6-USB-CAM-PSEUDO-SOSO-TOK-12000-v1_20260529T202849Z
Generated UTC: 2026-05-29T20:42:10.932866+00:00

## Authority

PSEUDO-A was the only PASS/DROP issuer.
SoSo remained advisory. Authority ZERO.
Tokens remained advisory. Authority ZERO.
No Lane 2 authority leakage detected.

## Capture

Device:           /dev/video0
Requested Frames: 12000
Captured Frames:  12000
Resolution:       640x480
Target FPS:       15
Measured Avg FPS: 14.999
Duration:         800.0s

## PSEUDO

PASS: 11933
DROP: 67

DROP Reasons:
  DIMENSION_CHANGE: 0
  EMPTY_FRAME: 0
  EXTREME_BLACK_FRAME: 1
  EXTREME_BLUR: 66
  EXTREME_WHITE_FRAME: 0
  FRAME_READ_FAILED: 0
  HASH_ERROR: 0
  MEASUREMENT_ERROR: 0
  TIMESTAMP_REVERSAL: 0

## SoSo

  STABLE: 8952
  WATCH: 2365
  DRIFTING: 504
  UNSTABLE: 173
  RESET_SUSPECTED: 6

## Tokens

  TOKEN_STABLE_SCENE: 8697
  TOKEN_LIGHT_SHIFT: 1696
  TOKEN_MOTION_PRESENT: 4120
  TOKEN_MOTION_LOW: 3398
  TOKEN_MOTION_HIGH: 722
  TOKEN_BLUR_LOW: 1143
  TOKEN_BLUR_HIGH: 1997
  TOKEN_TIMESTAMP_STABLE: 11990
  TOKEN_TIMESTAMP_JITTER: 10
  TOKEN_FRAME_DUPLICATE: 10
  TOKEN_FRAME_DROP_SUSPECT: 67
  TOKEN_AUTOFOCUS_SHIFT: 1198
  TOKEN_EXPOSURE_SHIFT: 1195
  TOKEN_USB_JITTER: 10
  TOKEN_CAMERA_RESET_SUSPECT: 6
  TOKEN_PSEUDO_DROP: 67
  TOKEN_SOSO_WATCH: 2365
  TOKEN_SOSO_DRIFT: 683

## Camera Behavior Model

  Brightness (luma):          mean=97.6325  std=35.0582  min=0.0  max=244.9535
  Blur (Laplacian variance):  mean=248.6099  std=403.5433  p50=174.6843  p95=801.3441
  Motion (motion_fraction):   mean=0.0351  std=0.0851  max=1.0
  Timestamp delta (ms):       mean=66.6692   std=2.6749   p95=68.142
  Drift events: 3083

## Replay

  Replay digest: 0bb103544a3786bda9d2a3d826171209af48bf5ab7920f39c8cc5d5c31aba3b7
  Replay status: MATCH

## Conclusion

This run IS suitable as a PH6 camera calibration baseline.
