# PH6 OI-03 Two-Pi Transfer Gate — Preflight Checklist

```text
Document ID:  PH6-OI03-TWO-PI-TRANSFER-PREFLIGHT
Status:       OPEN — awaiting second Pi 5
Date:         2026-05-15
Prerequisite: ESP32-CAM campaign CLOSED (e8149c9)
Next action:  Complete all checklist items before executing transfer
```

---

## Context

OI-03 is a STOP-SHIP gate. The loopback variant was proven (commit a95e552).
Real Pi-to-Pi transfer on physical hardware has not been executed.

This preflight document defines what must be confirmed before OI-03 transfer
begins. Do not alter PSEUDO logic, CRAM write semantics, RSYNC behavior, or
Lane authority while completing this checklist.

---

## Preflight Checklist

### 1. Identify Pi-1 (Ingest / Source Node)

- [ ] Hostname confirmed
- [ ] IP address confirmed
- [ ] Role: ingest node — captures frames, writes CRAM artifacts, holds source evidence directory
- [ ] Pi-1 is the current operational Pi running the ESP32-CAM pipeline

### 2. Identify Pi-2 (Receiver / Storage Verification Node)

- [ ] Hostname confirmed
- [ ] IP address confirmed
- [ ] Role: receiver node — accepts transfer, verifies hashes, does not write CRAM or make authority decisions
- [ ] Pi-2 is online and reachable

### 3. Network Reachability

- [ ] Pi-1 can ping Pi-2
- [ ] Pi-2 can ping Pi-1
- [ ] Both nodes are on the same network segment (or routing confirmed)
- [ ] Command: `ping -c 4 <Pi-2 IP>` from Pi-1 returns 0% loss

### 4. SSH Access

- [ ] Pi-1 can SSH to Pi-2 without password (key-based auth)
- [ ] SSH key for Pi-1 is installed in Pi-2 `~/.ssh/authorized_keys`
- [ ] Command: `ssh <pi2-user>@<Pi-2 IP> hostname` succeeds from Pi-1
- [ ] No interactive prompt required

### 5. Transfer Path Definition

- [ ] Transfer protocol: `rsync` over SSH
- [ ] rsync flags confirmed: `rsync -av --checksum` (checksum mode, not mtime)
- [ ] No raw frame JPGs transferred unless explicitly decided
- [ ] Transfer covers: manifest.json, frame_log.csv, postrun_summary.json
- [ ] Transfer does NOT alter source files on Pi-1

### 6. Source Evidence Directory

- [ ] Source path defined on Pi-1
- [ ] Candidate: `/home/jack/ph6_esp32cam_validation/run_20260515T082807Z` (C01)
- [ ] Candidate: `/home/jack/ph6_esp32cam_validation/run_20260515T084238Z` (C01E)
- [ ] Source directory contents listed and confirmed before transfer

### 7. Destination Evidence Directory

- [ ] Destination path defined on Pi-2
- [ ] Destination parent directory exists and is writable
- [ ] Suggested: `/home/<user>/ph6_transfer_receipts/<run_id>/`
- [ ] Pi-2 has sufficient disk space (confirm with `df -h`)

### 8. Pre-Transfer Hash Baseline (Pi-1)

- [ ] BLAKE2b hash taken of all artifacts to be transferred, recorded on Pi-1
- [ ] SHA256 hash taken as compatibility record (not canonical authority)
- [ ] Hash log saved to: `pre_transfer_hashes_pi1.txt`
- [ ] Command example:
  ```
  b2sum manifest.json frame_log.csv postrun_summary.json > pre_transfer_hashes_pi1.txt
  sha256sum manifest.json frame_log.csv postrun_summary.json >> pre_transfer_hashes_pi1.txt
  ```

### 9. Execute Transfer (rsync)

- [ ] rsync command staged and reviewed before execution
- [ ] Command form:
  ```
  rsync -av --checksum \
    /home/jack/ph6_esp32cam_validation/<run_id>/{manifest.json,frame_log.csv,postrun_summary.json} \
    <pi2-user>@<Pi-2 IP>:/home/<user>/ph6_transfer_receipts/<run_id>/
  ```
- [ ] rsync exits 0
- [ ] rsync output reviewed — no skipped or failed files

### 10. Post-Transfer Hash Verification (Pi-2)

- [ ] BLAKE2b hash taken of all transferred artifacts on Pi-2
- [ ] Hashes compared against Pi-1 baseline line-by-line
- [ ] All hashes match — no divergence
- [ ] Hash log saved to: `post_transfer_hashes_pi2.txt`
- [ ] Mismatch on any file = TRANSFER FAIL — do not proceed

### 11. No Evidence Loss Confirmation

- [ ] File count on Pi-2 matches file count sent from Pi-1
- [ ] File sizes match (cross-check with `ls -lh` on both nodes)
- [ ] No truncated or zero-byte files on Pi-2

### 12. Lane Authority Separation Confirmation

- [ ] Pi-1 role: ingest / source only — no PASS/DROP decisions made during transfer
- [ ] Pi-2 role: receiver / storage verification only — no PASS/DROP decisions made on receipt
- [ ] RSYNC is transport only — carries no authority, makes no verdicts
- [ ] No Lane 2 output (SoSo, TOK, Swarm, SSMT) is included in or influences the transfer
- [ ] No `verdict`, `result`, `motion_score`, or `motion_decay_score` fields introduced by the transfer process

### 13. Produce OI-03 Transfer Receipt

- [ ] Transfer receipt document created: `PH6-OI03-TRANSFER-RECEIPT-<date>.md`
- [ ] Receipt includes:
  - [ ] Transfer date/time UTC
  - [ ] Pi-1 hostname and IP
  - [ ] Pi-2 hostname and IP
  - [ ] Source run directory
  - [ ] Destination path
  - [ ] Files transferred (list)
  - [ ] Pre-transfer BLAKE2b hashes (Pi-1)
  - [ ] Post-transfer BLAKE2b hashes (Pi-2)
  - [ ] Hash match verdict: PASS or FAIL
  - [ ] rsync exit code
  - [ ] Lane authority separation statement
  - [ ] Final verdict: PASS / FAIL / INVALID
- [ ] Receipt committed to repo

---

## Explicit Non-Scope

This gate does NOT:

- Alter PSEUDO thresholds or logic
- Alter CRAM write semantics
- Alter RSYNC Priority Zero behavior
- Alter Lane 1 authority
- Promote Lane 2 outputs to authority status
- Re-open the ESP32-CAM evidence campaign

---

## Completion Criteria

| Criterion                                     | Threshold | Result |
|-----------------------------------------------|-----------|--------|
| Pi-2 identified and online                    | Required  |        |
| SSH key auth Pi-1 → Pi-2                      | Required  |        |
| rsync exits 0                                 | Required  |        |
| All BLAKE2b hashes match post-transfer        | Required  |        |
| No raw evidence loss                          | Required  |        |
| Lane authority separation confirmed           | Required  |        |
| Transfer receipt committed                    | Required  |        |

All criteria must be PASS before OI-03 is closed.

---

## Gate Status

```
OI-03: OPEN
Blocker: second Raspberry Pi 5 not yet available
Action required: none until Pi-2 is online
```

Do not attempt transfer until all preflight items above are checked.
