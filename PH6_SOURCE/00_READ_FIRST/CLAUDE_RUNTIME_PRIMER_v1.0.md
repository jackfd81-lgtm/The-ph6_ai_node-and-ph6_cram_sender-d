# CLAUDE RUNTIME PRIMER v1.0

```text
Document ID: PH6-CLAUDE-RUNTIME-PRIMER-1.0
Status:      ACTIVE
Purpose:     AI bootstrap layer — load before any campaign file
Target:      Claude Terminal / Raspberry Pi 5 8GB
```

---

# 1. AUTHORITY MODEL

```text
Lane 1   = CRAM + PSEUDO    — sole authority — PASS/DROP belongs here only
Lane 2   = TOK / SoSo / AI  — advisory only  — Authority ZERO
Lane 5   = RSYNC            — Priority Zero  — must never be blocked

Lane 2 writes: MRAM-S only
Lane 2 forbidden: CRAM-A, CRAM-R, CRAM-0, PASS, DROP, verdict fields
```

---

# 2. INVARIANTS

```text
INV-01  Lane 1 is sole authority
INV-02  Lane 2 is Authority ZERO
INV-03  PSEUDO controls PASS/DROP
INV-04  RSYNC is Priority Zero
INV-05  CRAM write contract is immutable
INV-06  Replay must remain deterministic
INV-07  Thresholds are frozen
INV-08  TOK cannot influence verdicts
INV-09  Swarm cannot influence verdicts
INV-10  Evidence overrides theory
INV-11  No campaign PASS without artifacts
INV-12  No runtime under 300 frames unless crash occurs
INV-13  MRAM-S is advisory only
INV-14  CRAM-A is authoritative truth
INV-15  Doctrine expansion is frozen during evidence campaigns
```

---

# 3. ACTIVE CAMPAIGN

```text
Campaign:  C01
Objective: 300-frame full-stack coherence test
Status:    OPEN
Priority:  1

Config:
  PSEUDO = ON
  SoSo   = ON
  TOK    = ON
  Swarm  = OFF

Expected artifacts:
  logs/run_<stamp>/manifest.json
  postrun_report_<stamp>.json
  replay_receipt_<stamp>.json
  hash_chain_receipt_<stamp>.blake2b

Runtime card: PH6_SOURCE/03_CAMPAIGNS/C01_RUNTIME_CARD.md
```

---

# 4. STOP-SHIP ITEMS

```text
OI-01  Hailo hardware integration — ON HOLD (new Pi 5 required)
OI-03  Real Pi-to-Pi transfer — NOT VERIFIED — next actionable gate after C01
```

Do not close OI-01 or OI-03 without physical evidence and receipts.

---

# 5. FORBIDDEN ACTIONS

```text
- invent architecture
- create doctrine
- reinterpret authority
- modify thresholds
- modify PASS/DROP semantics
- modify replay logic
- modify CRAM write contract
- block RSYNC
- refactor unrelated systems
- infer success without receipts
- load entire doctrine corpus
```

---

# 6. ANTI-HALLUCINATION RULES

```text
If evidence is missing     → state MISSING
If verification absent     → state UNVERIFIED
If proof does not exist    → state NOT PROVEN

Evidence chain:  CLAIM → ARTIFACT → HASH → RECEIPT
Forbidden chain: CLAIM → INTERPRETATION

Never infer:
- runtime success from architecture
- closure from partial evidence
- replay parity without receipts
```

---

# 7. CANONICAL HASH ALGORITHM

```text
BLAKE2b-256
Marker: .blake2b
SHA256: COMPATIBILITY_ONLY — never canonical authority
```

---

# 8. EXECUTION POSTURE

```text
When uncertain:
  STOP
  REPORT
  ASK

Prefer:
  small patches
  diff-oriented changes
  artifact-backed claims
  deterministic outputs
  minimal side effects
```

---

# 9. NEXT STEP

```text
Execute C01.
See: PH6_SOURCE/03_CAMPAIGNS/C01_RUNTIME_CARD.md
```

---

# 10. DO NOT LOAD

```text
PH6_RECOVERY/
cram_pu_live_1_0/runtime/
ph6/cram_pu/runtime/
ph6/cram_pu/validation_runs/
usb3_nvme_calibration/
Obsolete DRAFT files
Old debate / philosophy docs
```
