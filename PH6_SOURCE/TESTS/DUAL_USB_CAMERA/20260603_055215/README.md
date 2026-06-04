# PH6 Dual USB Camera Test — 20260603_055215
PROPOSED — Lane-2 advisory only.

## Files

| File | Description |
|------|-------------|
| camera_inventory.md / .json | Device mapping and capability summary |
| dual_smoke_report.md / .json | Phase 1: 300-frame smoke test |
| same_vision_test_report.md / .json | Phase 2: 1200-frame same profile test |
| opposite_role_test_report.md / .json | Phase 3: role-swap test, 2 passes |
| complementary_test_report.md / .json | Phase 4: A=640x480, B=1280x720 |
| PH6_DUAL_USB_CAMERA_FINAL_REPORT.md / .json | Final engineering report |
| v4l2_*.txt, formats_*.txt, udevadm_*.txt | Raw capability logs |
| lsusb_cameras.txt | USB device inventory |

## Camera Mapping

| Label | Node | USB ID | Manufacturer |
|-------|------|--------|-------------|
| CAMERA_A | /dev/video0 | 4c4a:4a55 | Jieli Technology (DV20 USB) |
| CAMERA_B | /dev/video2 | 0c45:636b | Microdia (Streaming Cam) |

*proposed_by: claude-code-lane2 | ratified_by: null*
