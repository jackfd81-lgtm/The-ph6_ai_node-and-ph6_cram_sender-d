# PH6-USB-CAM-PSEUDO-SOSO-TOK-12000-v1

USB camera 12,000-frame deterministic mapping test.

## Architecture

```
USB camera → PSEUDO-M (deterministic measurement)
           → PSEUDO-A (PASS/DROP, Lane 1 authority)
           → SoSo     (advisory continuity, Authority ZERO)
           → Tokens   (advisory symbolic map, Authority ZERO)
           → Reports / JSON / CSV
```

PSEUDO-A is the only PASS/DROP issuer. SoSo and Tokens are advisory.

## Files

| File | Purpose |
|------|---------|
| `run_usb_camera_12000.py` | Main runner — orchestrates full pipeline |
| `pseudo_measure.py` | PSEUDO-M measurement + PSEUDO-A verdict authority |
| `soso_mapper.py` | SoSo advisory continuity mapper |
| `token_mapper.py` | Token advisory symbolic compression |
| `replay_compare.py` | Post-run replay digest verifier |

## Usage

```bash
cd /home/jack
python3 PH6_SOURCE/TESTS/USB_CAMERA_12000/run_usb_camera_12000.py \
  --device /dev/video0 \
  --frames 12000 \
  --fps 15 \
  --width 640 \
  --height 480
```

Optional:
```bash
--save-sample-frames   # save JPEG every 1000 frames
--fps 30               # higher rate after stability confirmed
--width 1280 --height 720
```

## Output (written to `ph6/cram_pu/validation_runs/<run_id>/`)

| File | Contents |
|------|----------|
| `frames_index.csv` | Per-frame summary index |
| `pseudo_measurements.jsonl` | PSEUDO-M per-frame measurements |
| `pseudo_verdicts.jsonl` | PSEUDO-A PASS/DROP verdicts |
| `soso_continuity.jsonl` | SoSo advisory continuity records |
| `token_map.jsonl` | Token advisory records |
| `token_summary.json` | Token count summary |
| `drift_map.json` | SoSo drift event map |
| `replay_digest.json` | BLAKE2b-256 chain + summary digest |
| `camera_behavior_model.json` | Statistical camera model |
| `final_report.md` | Human-readable test report |

## Phases

| Phase | Frames | Purpose |
|-------|--------|---------|
| A | 0–1999 | Baseline camera behavior |
| B | 2000–3999 | Lighting/environment stability |
| C | 4000–5999 | Motion/scene variation |
| D | 6000–7999 | Temporal continuity stress |
| E | 8000–9999 | SoSo/token drift mapping |
| F | 10000–11999 | Replay/repeatability digest |

## Authority statement

PSEUDO-A is Lane 1. It alone issues PASS/DROP.
SoSo has Authority ZERO. Tokens have Authority ZERO.
No advisory output may override or mutate PSEUDO-A verdicts or thresholds.
