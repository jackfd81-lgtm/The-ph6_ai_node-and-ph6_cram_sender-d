# Campaign 02 — Pi-to-Pi Live Transfer

```text
Campaign ID:  C02
Status:       OPEN
Phase:        PH6 / CRAM v3.1 — Evidence Closure Campaign
Priority:     2
Purpose:      Close OI-03: prove real Pi-to-Pi live transfer operates correctly.
Gap Closed:   OI-03 (if this campaign passes)
```

---

## Objective

Prove that CRAM-A data and audit artifacts can be transferred from one real
Raspberry Pi node to another Raspberry Pi node under live conditions.

This is not a simulation. Not a laptop-to-laptop transfer. Not a synthetic test.
Two real Pi nodes. Real data. Real RSYNC export path.

---

## Required Minimum

- Two physical Raspberry Pi nodes (not simulated, not virtual)
- Source Pi: running capture with CRAM-A writes active
- Destination Pi: receiving via RSYNC export path
- Transfer must complete without corruption
- Hash verification must pass on destination
- Replay must succeed on destination using transferred artifacts

---

## Proof Chain

```text
Source Pi (capture active)
  → CRAM-A writes to local storage
  → RSYNC exports to destination Pi
  → Destination Pi receives artifacts
  → Hash verification on destination
  → Replay verification on destination
  → result_set_hash matches source
```

---

## Commands

```bash
# Source Pi: verify CRAM-A writes are active
git status --short
python3 PH6_SOURCE/TOOLS/governance_drift_scan.py --scan-root PH6_SOURCE

# Source Pi: run capture
# [Replace with actual run command]
python3 ph6_console.py --frames 300 --rsync-target <destination_pi_ip>

# Destination Pi: verify receipt
rsync --checksum --dry-run <source>:<path>/ <destination_path>/

# Destination Pi: hash verification
# [Replace with actual hash verification command]

# Destination Pi: replay verification
python3 ph6/cram_pu/runtime/ --replay <run_stamp>
```

---

## Expected Artifacts

```text
Source Pi:
  logs/run_<stamp>/
  CRAM-A writes complete with hash receipts

Destination Pi:
  rsync_transfer_log_<stamp>.txt
  hash_verification_report_<stamp>.json
  replay_receipt_<stamp>.json (matching source result_set_hash)
```

---

## PASS Criteria

- [ ] Two physical Pi nodes used (not simulated)
- [ ] frames_processed >= 300 on source
- [ ] RSYNC transfer completed without interruption
- [ ] Hash verification passes on destination for all transferred files
- [ ] Replay on destination produces identical result_set_hash as source run
- [ ] No RSYNC blocking during transfer
- [ ] No CRAM-A write corruption on either node

---

## FAIL Criteria

- Either node is not a real Raspberry Pi
- Transfer corrupted any artifact (hash mismatch on destination)
- Replay on destination produces different result_set_hash
- RSYNC was blocked or resource-starved during the run
- Any partial CRAM-A write remained incomplete

---

## Gap Closure

A passing Campaign 02 closes **OI-03**.

OI-03 status must only be updated to CLOSED in `GAP_REGISTER_v3.0.md` when:
1. This campaign receipt exists at `RECEIPTS/C02_CLOSURE_RECEIPT.md`
2. A human has reviewed and signed off on the receipt
3. The source and destination Pi serial numbers / identifiers are documented

AI must not mark OI-03 CLOSED. Human authorization required.

---

## Closure Evidence

```text
PH6_SOURCE/EVIDENCE_CAMPAIGNS/RECEIPTS/C02_CLOSURE_RECEIPT.md
```

Required contents:
- Source Pi identifier
- Destination Pi identifier
- Run stamp
- Frame count
- Transfer log path
- Hash verification: PASS
- Replay hash match: PASS
- Human sign-off
