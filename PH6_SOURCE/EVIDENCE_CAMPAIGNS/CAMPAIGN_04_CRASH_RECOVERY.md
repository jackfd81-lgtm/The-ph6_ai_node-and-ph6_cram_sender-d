# Campaign 04 — Crash Recovery

```text
Campaign ID:  C04
Status:       OPEN
Phase:        PH6 / CRAM v3.1 — Evidence Closure Campaign
Priority:     4
Purpose:      Prove crash-consistency: the system recovers correctly after
              unexpected termination with no authoritative data corruption.
```

---

## Objective

Prove that if the system crashes or is forcibly terminated at any point during
a run, CRAM-A state remains consistent: no partial authoritative commits,
no corrupt evidence, correct tmp file handling, and deterministic replay
still works on the pre-crash data.

---

## Required Minimum

- Crash must be induced (or documented if natural) during active CRAM-A writes.
- Three crash scenarios must be tested.
- Post-crash state must be verified before replay is attempted.
- Replay must succeed on pre-crash evidence.

---

## Crash Scenarios

### Scenario A — Process kill during CRAM-A write
Forcibly kill the capture process (SIGKILL) during an active CRAM-A write.
Verify no partial authoritative commit exists.
Verify tmp files are either complete or abandoned (not partially renamed).

### Scenario B — Power cycle simulation
Simulate abrupt power loss (kill -9 or unplug if safe to test on hardware).
Verify CRAM-A state is recoverable after restart.
Verify audit chain is intact for all frames written before the crash.

### Scenario C — Disk full condition
Fill the target disk to capacity during a run.
Verify CRAM-A handles disk-full without corrupting existing evidence.
Verify RSYNC behavior under disk-full conditions.

---

## Atomic Write Contract Verification

For each crash scenario, verify the atomic write contract was upheld:

```text
Step 1: write_tmp     — tmp file written
Step 2: fsync_file    — tmp file synced to disk
Step 3: rename        — atomic rename to final name
Step 4: fsync_dir     — directory entry synced
```

After a crash, inspect for:
- tmp files that exist without corresponding final files → partial write (FAIL)
- final files that exist without valid hash receipts → corrupt write (FAIL)
- tmp files that were abandoned before rename with no final file → acceptable (PASS)

---

## Commands

```bash
# Pre-test drift scan
python3 PH6_SOURCE/TOOLS/governance_drift_scan.py --scan-root PH6_SOURCE

# Scenario A: kill during write
# [Replace with actual run command]
python3 ph6_console.py --full-stack &
PID=$!
sleep 5  # Let it run briefly
kill -9 $PID

# Post-crash state inspection
find . -name "*.tmp" -type f
ls -la <cram_write_path>

# Hash verification on surviving evidence
# [Replace with actual verification command]

# Replay on pre-crash data
python3 ph6/cram_pu/runtime/ --replay <pre_crash_stamp>

# Post-test drift scan
python3 PH6_SOURCE/TOOLS/governance_drift_scan.py --scan-root PH6_SOURCE
```

---

## Expected Artifacts

```text
For each scenario (A–C):
  crash_state_report_<scenario>_<stamp>.json
  tmp_file_inspection_<scenario>_<stamp>.txt
  post_crash_hash_verification_<scenario>_<stamp>.json
  replay_receipt_<scenario>_<stamp>.json
```

---

## PASS Criteria

- [ ] No partial authoritative CRAM-A commit found in any scenario
- [ ] All tmp files in abandoned state (no rename) or fully complete
- [ ] No corrupt evidence packets in any scenario
- [ ] Audit chain intact for all pre-crash frames in each scenario
- [ ] Replay on pre-crash data produces correct deterministic result_set_hash
- [ ] Disk-full scenario: RSYNC not corrupted, existing evidence intact
- [ ] Drift scan passes before and after all scenarios

---

## FAIL Criteria

- Any partial authoritative commit found (tmp renamed but hash missing)
- Any evidence packet corrupted by crash
- Replay produces different result_set_hash on identical pre-crash data
- Audit chain broken for frames that were written before the crash
- RSYNC corrupted any artifact during disk-full scenario

---

## Closure Evidence

```text
PH6_SOURCE/EVIDENCE_CAMPAIGNS/RECEIPTS/C04_CLOSURE_RECEIPT.md
```

Required contents:
- Scenario A–C results (PASS/FAIL per scenario)
- Crash state report paths
- Replay hash match confirmation per scenario
- Human sign-off
