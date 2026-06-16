# PH6 Desktop Controlled Terminal v1.2

```
Classification:  PROPOSED — awaiting operator ratification
Status:          DRAFT
Proposed by:     claude-code-lane2
Proposed at UTC: 2026-06-05T00:00:00Z
Ratified by:     null
```

## Purpose

Terminal-controlled observer console for PH6 operations. This is the bridge between the
raw PH6 runtime and a future full GUI desktop. It is **not authority**. It displays, 
launches safe diagnostics, and surfaces evidence for operator review.

## Run

```bash
python3 PH6_SOURCE/DESKTOP_CONTROLLED_TERMINAL/ph6_desktop_terminal.py
```

Requires Python 3.9+. Standard library only. No GUI dependencies. No Claude API required.
Works offline. Works over SSH.

## Main Menu

| # | Panel | Description |
|---|-------|-------------|
| 1 | System Dashboard | Status JSON, node health, git, storage |
| 2 | Camera Diagnostics | Video devices, dual-camera test results, ESP camera |
| 3 | Sensor Diagnostics | ESP_S1 /health /sensor /i2c_scan |
| 4 | Run PH6 Test | Runs ph6_internal_test.py (20 checks) |
| 5 | PSEUDO Results | CRAM-A/CRAM-R counts, rsync queue |
| 6 | SoSo Results | SoSo JSON reports |
| 7 | Token Results | Token JSON reports |
| 8 | Live-vs-Simulator | Comparison reports |
| 9 | Reports | Governance + deployment report index |
| 10 | Topology | Node ping + ESP_S1 artifacts + dynamic discovery |
| 11 | Governance Center | SMI-1.1 validation submenu |
| 12 | Realtime Mode | 1-second live metrics (curses) — press Q to exit |
| 13 | Exit | Releases session lock, saves session report |

## Governance Center Submenu

| # | Action | Allowed in v1.2 |
|---|--------|----------------|
| 1 | Audit Replay | YES — runs ph6_audit_replay.py |
| 2 | Canon Validator | YES — runs ph6_validate_canon.py |
| 3 | Five-Book Dry Run | YES (--dry-run only) |
| 4 | Secret Scan | YES — inline pattern scan |
| 5 | Commit Readiness | YES — SMI-1.1 gate summary |
| 6 | Commit Confirmation | YES — live git log check |
| 7 | Authority Boundary Check | YES — static display |
| 8 | Return | — |

## Session Lock

Lock file: `/var/ph6/session.lock` (JSON)

| State | Desktop Mode | Claude Mode |
|-------|-------------|-------------|
| FREE → Desktop acquires | CONTROL | — |
| DESKTOP owns lock | CONTROL | READ_ONLY |
| CLAUDE owns lock | MONITOR_ONLY | CONTROL |

Lock is atomic (`O_CREAT\|O_EXCL`). Stale locks reclaimed only if owning PID is dead.

## Forbidden in v1.2

- Real Five-Book distribution (no `--dry-run`)
- Canon lock
- Source deletion
- Doctrine rewrite
- Automatic commit
- Signature bypass

## Phase 6B — Deferred Features (DEFERRED_PHASE_6B)

The following features are valid PH6 objectives. They are not rejected. They are deferred
until Phase 6A is committed and stable.

| Feature | Description | Authority |
|---------|-------------|-----------|
| Characterization Center | Surface USB_CAMERA_12000, thermal, dual-camera campaign evidence | NONE — display only |
| Tricorder Mode | Observe/measure/record/compare across camera, audio, ESP_S1, reports | NONE — display only |
| AI Advisory placeholder | Lane-2 summary panel | ZERO — advisory only |
| Fleet View placeholder | Multi-node status grid | NONE — display only |
| Multi-Node Replay placeholder | Cross-node audit replay comparison | NONE — display only |
| Environmental Modeling placeholder | ESP_S1 + historical sensor data view | NONE — display only |

All Phase 6B items are advisory/observational only. None acquire authority.

## SMI-1.1 Dependency

Phase 6A commit requires Commit 1 (SMI-1.1) to be confirmed first:

```bash
git log --oneline -1   # must show SMI-1.1 commit
```

If SMI-1.1 scripts are absent, the terminal correctly displays:

```
SMI-1.1 Status:      PENDING
Governance Scripts:  SCRIPT_NOT_FOUND
Commit Status:       UNVERIFIED
```

## Session Reports

Each session saves a JSON report to `reports/terminal_session_YYYYMMDDTHHMMSSZ.json`.

## Configuration

Edit `terminal_config.json` to change node IPs, timeouts, and path overrides.

## Authority

```
Desktop terminal authority: NONE
Lane-2 (AI) authority:      ZERO
Jack / Lane-1 signature:    REQUIRED for canon promotion
```

---

```json
{
  "proposed_by": "claude-code-lane2",
  "proposed_at_utc": "2026-06-05T00:00:00Z",
  "api_call_log_ref": "session-20260605",
  "phase": "6A",
  "phase_6b_deferred": ["characterization_center", "tricorder_mode",
                        "ai_advisory_placeholder", "fleet_view_placeholder",
                        "multi_node_replay_placeholder",
                        "environmental_modeling_placeholder"],
  "ratified_by": null
}
```
