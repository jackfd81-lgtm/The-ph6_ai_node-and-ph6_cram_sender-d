# PH6 / CRAM — Repo Cleanup Classification

**Generated:** 2026-05-28T07:05:00Z
**Node:** jackjack (Pi 5, 192.168.254.188)
**Branch:** main

---

## Current Repo State

- Tracked files: clean — no staged or modified tracked files.
- Untracked entries: 72 at audit time.
- Governance drift scan: PASS (0 critical / 0 high / 0 warn).
- AI preflight: PASS.
- Python compileall (ph6/): PASS.

---

## Gap Register Status

**Register is STALE in two places. Human update required.**

### OI-01

| Field       | Register (current)              | Production clearance (2026-05-18)      |
|-------------|----------------------------------|----------------------------------------|
| Status      | OPEN                             | DESCOPED                               |
| STOP-SHIP?  | YES                              | Not applicable (descoped)              |
| Authority   | Human only                       | Operator declaration issued            |

Proposed register update (requires human authorization):
- Change `OI-01` row: Status → `DESCOPED`, STOP-SHIP? → `No`, Closure file → `GOVERNANCE/production_clearance_declaration_PH6-PROD-CLEAR-2026-05-18-001.md`

### OI-03 / OI-03A/B/C

| Field       | Register (current)              | Production clearance (2026-05-18)      |
|-------------|----------------------------------|----------------------------------------|
| Status      | OPEN                             | OI-03A CLOSED (1c1a430e47, 300 fr)    |
| Status      | OPEN                             | OI-03B CLOSED (e445e7a3be, 1200 fr)   |
| Status      | OPEN                             | OI-03C CLOSED (2e42ce3705, 3600 fr)   |
| Scope       | Real Pi-to-Pi transfer           | Bounded: rsync hash-continuity only   |

The production clearance closes OI-03 within the bounded single-node + rsync export scope. The broader "Campaign 02 / full Pi-to-Pi live transfer" (distributed streaming) remains OPEN and is NOT cleared.

Proposed register update (requires human authorization):
- Change `OI-03` row: Status → `CLOSED-BOUNDED`, STOP-SHIP? → `No`, Closure file → `GOVERNANCE/production_clearance_declaration_PH6-PROD-CLEAR-2026-05-18-001.md`, add note: "Bounded: rsync hash-continuity verified. Full distributed transfer (Campaign 02) remains open."
- Keep `Pi-to-Pi live transfer` row as `OPEN / YES` — not resolved by bounded clearance.

### GAP-16B — USB disconnect

Keep `OPEN / No` — still awaiting video-only 5+ min isolation test.

### Runtime discovery classification

Keep `DEFERRED / No` — intentional per operator decision.

**Claude must not apply register changes without explicit human approval on this session.**

---

## Untracked Artifact Classification

### PH6_SOURCE/CAMPAIGNS/
Classification: **SHOULD_COMMIT**

Contents:
- `CAMPAIGNS/LIFE_CRAM/lcc_01_campaign_matrix.json` — campaign index
- `CAMPAIGNS/LIFE_CRAM/LCC-01_REAL_CAMERA_LIVE_STREAM.md` — campaign spec
- `CAMPAIGNS/LIFE_CRAM/run_life_cram_lcc_01_live_camera.sh` — campaign runner

These are legitimate campaign governance documents. Referenced by the LIFE_CRAM evidence layer. Should be committed. No media files. No runtime output.

### PH6_SOURCE/CERTIFICATION/audit_patched.py
Classification: **SHOULD_COMMIT** (source file only)
Classification: **SHOULD_IGNORE** for `PH6_SOURCE/CERTIFICATION/__pycache__/`

`audit_patched.py` is a Lane-2 advisory audit module referenced in `builds/build_manifest.json` under validation and forensic builds. It is source code, not a runtime artifact. Commit the `.py`, not the `__pycache__/`.

### PH6_SOURCE/builds/
Classification: **SHOULD_COMMIT** (manifest + ingest text files + receipts)

Contents:
- `build_manifest.json` — generated build index referencing 80+ governance files
- `*.txt` ingest files — pre-compiled AI context packs (engineering, forensic, full_canon, governance, minimal, validation)
- `builds/receipts/*.json` — build receipts with BLAKE2b hashes

These are generated governance artifacts, not runtime evidence. They are referenced as authoritative build outputs. Commit all, excluding any future `__pycache__/` contamination.

### apply_closure_patch.py (root)
Classification: **NEEDS_REVIEW** → likely SHOULD_COMMIT as closure evidence

This script was already executed (it generated `GOVERNANCE/closure_status.json` and related files). It is the human-operator gate script for C07/OI-03A/B/C closure and OI-01 descope. Keeping it as evidence of the closure procedure is reasonable. Operator must confirm.

### apply_evc05_closure.py (root)
Classification: **NEEDS_REVIEW** → likely SHOULD_COMMIT as closure evidence

EVC-05 closure gate script. Similar to above — already executed. Operator must confirm.

### apply_production_clearance_declaration.py (root)
Classification: **NEEDS_REVIEW** → likely SHOULD_COMMIT as closure evidence

Script that generated the production clearance declaration already in the repo. This is the human-operator procedure record. Operator must confirm.

---

## Artifacts That Must Never Be Committed

| Path                               | Reason                                          |
|------------------------------------|-------------------------------------------------|
| ph6/cram_pu/runtime/               | Runtime evidence dirs — volatile, large         |
| ph6/cram_pu/validation_runs/       | Validation frame dumps — large evidence output  |
| ph6/validation_runs/               | Same as above                                   |
| validation_runs/ (root)            | Same as above                                   |
| cram_pu_live_1_0/runtime/          | Runtime output                                  |
| PH6_LOCAL_BACKUPS/                 | Backup archive — classified per doctrine        |
| PH6_RECOVERY/                      | Recovery archive — classified per doctrine      |
| .platformio/                       | PlatformIO ESP32 build cache                    |
| .cache/                            | Browser/playwright/camoufox/uv cache            |
| .npm/                              | npm package cache                               |
| frame_filter/logs/                 | Run logs with mp4/jsonl — large evidence        |
| Downloads/                         | Download artifacts                              |
| **/*.pyc                           | Python bytecode                                 |
| **/__pycache__/                    | Python bytecode directories                     |
| ph6_usb_camera_tests/ (media only) | Audio/video captures — but see note below       |
| ph6_video_tests/                   | mkv video captures                              |

---

## NEEDS_REVIEW Before Ignoring

| Path                                           | Why not auto-ignore                                  |
|------------------------------------------------|------------------------------------------------------|
| ph6_usb_camera_tests/                          | Contains source py files (`ph6_extended_stability_test.py`, `ph6_gap16b_isolation.py`) that may be evidence tools; audio captures should not be committed |
| ph6_esp32cam_tests/                            | May contain test scripts worth tracking             |
| ph6_esp32cam_validation/                       | May contain governance evidence scripts             |
| ph6_iphone_ingest/                             | Unknown source vs evidence — classify first          |
| ph6_smi11_drop/                               | Unknown — classify first                            |
| usb3_nvme_calibration/                         | Calibration data — may be evidence artifacts         |
| esp32cam_fw/                                   | ESP32 firmware source — may want to track           |
| esp32cam_ingest_300.py                         | Ingest script — likely SHOULD_COMMIT                 |
| ph6_console.py                                 | Console utility — likely SHOULD_COMMIT               |
| ph6_cram_lane1_evidence_chain_test.py (root)   | Evidence chain test — likely SHOULD_COMMIT          |
| *.mp4                                          | Some mp4s may be attached evidence artifacts         |

---

## Proposed .gitignore Entries (SAFE — not NEEDS_REVIEW)

See `PH6_SOURCE/DEPLOYMENT/PROPOSED_GITIGNORE_PATCH.txt` for the full proposed patch. Do not apply automatically.

---

## Next Engineering Gate

After gap register reconciliation and classification decisions:

1. `/var/ph6` runtime layout — create directory structure, set ownership
2. `/mnt/ph6_hotstore` role decision — mount USB3 NVMe or leave as local store
3. Systemd service deployment for PH6 / CRAM daemon
4. Pi 5 local PH6 validation run (300+ frames, real sensor)
5. Pi 5 ↔ Zero sentinel heartbeat integration
6. Zero 2 W hostname rename to `jackjack2` (non-blocking, when convenient)
