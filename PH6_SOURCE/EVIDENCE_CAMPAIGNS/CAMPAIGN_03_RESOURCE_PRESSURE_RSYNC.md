# Campaign 03 — Resource Pressure / RSYNC Non-Blocking

```text
Campaign ID:  C03
Status:       OPEN
Phase:        PH6 / CRAM v3.1 — Evidence Closure Campaign
Priority:     3
Purpose:      Prove RSYNC Priority Zero holds under real system resource pressure.
```

---

## Objective

Prove that RSYNC export remains non-blocking and non-starved under concurrent
CPU, disk, capture, and Lane 2 advisory load.

The core invariant being verified:

```
RSYNC must not be blocked by analysis, AI, SoSo, TOK, replay,
dashboard, or compression — regardless of system load.
```

---

## Required Minimum

- Minimum 300 frames processed under each pressure scenario.
- All five pressure scenarios must be tested.
- RSYNC must remain active throughout all scenarios.
- RSYNC transfer latency must be measured and logged for each scenario.

---

## Pressure Scenarios

### Scenario A — CPU pressure
Run PSEUDO + SoSo/TOK advisory at high frame rate while RSYNC is active.
Verify RSYNC is not deprioritized.

### Scenario B — Disk I/O pressure
Run CRAM-A writes at high write rate while RSYNC is active.
Verify RSYNC is not blocked waiting for disk.

### Scenario C — Capture pressure
Run capture at maximum sustainable rate while RSYNC is active.
Verify RSYNC is not resource-starved.

### Scenario D — Export pipeline pressure
Run RSYNC while the export queue is large (backlog condition).
Verify RSYNC does not stall or time out.

### Scenario E — Lane 2 advisory pressure
Run SoSo/TOK advisory inference at high rate while RSYNC is active.
Verify RSYNC is not slowed by AI inference load.

---

## Commands

```bash
# Pre-run drift scan
python3 PH6_SOURCE/TOOLS/governance_drift_scan.py --scan-root PH6_SOURCE

# Monitor RSYNC during run (separate terminal)
# [Replace with actual RSYNC monitoring command]
watch -n 1 'ps aux | grep rsync'

# Monitor CPU/disk during run
iostat -x 1
top -b -n 1

# Post-run drift scan
python3 PH6_SOURCE/TOOLS/governance_drift_scan.py --scan-root PH6_SOURCE
```

---

## Expected Artifacts

```text
For each scenario (A–E):
  resource_log_<scenario>_<stamp>.json    (CPU, disk, memory metrics)
  rsync_log_<scenario>_<stamp>.txt        (RSYNC activity log)
  rsync_not_blocked_<scenario>.flag       (boolean PASS flag file)
```

---

## PASS Criteria

- [ ] All five scenarios completed with >= 300 frames each
- [ ] RSYNC was not blocked in any scenario
- [ ] RSYNC was not deprioritized below normal operation in any scenario
- [ ] No RSYNC timeout or stall in any scenario
- [ ] SoSo/TOK advisory remained Authority ZERO throughout
- [ ] Drift scan passes before and after all scenarios

---

## FAIL Criteria

- RSYNC blocked or stalled during any scenario
- RSYNC transfer rate dropped below acceptable threshold due to AI/analysis load
- Any Lane 2 component caused RSYNC to pause or fail
- Any scenario completed with fewer than 300 frames (without crash evidence)

---

## Closure Evidence

```text
PH6_SOURCE/EVIDENCE_CAMPAIGNS/RECEIPTS/C03_CLOSURE_RECEIPT.md
```

Required contents:
- Scenario A–E results (PASS/FAIL per scenario)
- RSYNC log paths
- Resource metric log paths
- Human sign-off
