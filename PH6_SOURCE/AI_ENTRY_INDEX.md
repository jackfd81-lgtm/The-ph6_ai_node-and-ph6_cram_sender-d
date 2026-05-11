# PH6 / CRAM — AI Entry Index

```text
Document ID: PH6-AI-ENTRY-INDEX-1.0
Status: ACTIVE
Purpose: Human + AI routing map. Read this before editing anything.
```

---

## Start Here

Before touching any code, configuration, or doctrine:

1. Read this file.
2. Identify which path applies to your task.
3. Follow the reading order for that path.
4. Never start from a random code file.

---

## Reading Order

### Minimal ingest path (fast orientation)

```text
PH6_SOURCE/AI_ENTRY_INDEX.md               ← you are here
PH6_SOURCE/DRAFT/PH6-AI-INGEST-STACK-1.0.md
```

### Full canonical ingest path (engineering work)

```text
PH6_SOURCE/AI_ENTRY_INDEX.md
PH6_SOURCE/00_READ_FIRST_AAI_INGEST_INSTRUCTIONS_v2.0.md
PH6_SOURCE/DRAFT/PH6-MASTER-AI-INGEST-6.0.md
PH6_SOURCE/DRAFT/PH6-SYSTEM-OVERVIEW-v1.0.md
PH6_SOURCE/DRAFT/PH6-LIVING-CRAM-PSEUDO-SOSO-JEDI-v1.0.md
PH6_SOURCE/DRAFT/PH6-PSEUDO-SOSO-JEDI-UPDATE-v1.0.md
```

### Certification / replay path

```text
PH6_SOURCE/DRAFT/PH6-MASTER-AI-INGEST-6.0.md  (sections 12–26)
PH6_SOURCE/DRAFT/PH6-CLAUDE-PATCH-HANDOFF-1.0.md
```

### Governance / amendment path (only if amending doctrine or routing canon changes)

```text
PH6_SOURCE/DRAFT/PH6-CDG-1.0.md
```

### Token / Lane-2 advisory path (only if touching TOK / SoSo / Swarm)

```text
PH6_SOURCE/DRAFT/PH6-TOK-MASTER-UPDATE-1.0.md
PH6_SOURCE/DRAFT/PH6-TOKENS-LIVING-CRAM-v1.1.md
PH6_SOURCE/DRAFT/PH6-TOK-LIFECYCLE-PRUNE-1.0.md
PH6_SOURCE/DRAFT/PH6-TOK-SSMT-CERT-PATCH-v1.0.md
```

---

## Authority Warning

```text
Lane 1 = CRAM + PSEUDO. Sole authority. PASS/DROP belongs here only.

Lane 2 = TOK / SoSo / JEDI / Swarm / AI. Advisory only. Authority ZERO.
         Writes only to MRAM-S. Never writes CRAM-0, CRAM-A, or CRAM-R.

Lane 5 = RSYNC. Priority Zero. Must never be blocked.
```

---

## Current Open Items

```text
STOP-SHIP: OI-01 (Hailo hardware-gated) and OI-03 (real Pi-to-Pi transfer not verified).
HRG9: CLOSED at commit 2ef5fd6. Do not reopen.

Open gaps (do not close without evidence):
- MRAM-S advisory schema not formally registered
- Scientific metadata schema absent
- Resource-cage systemd units not in repo
- Drift Gate automated check absent
- CDG-1.0 (Book VI) pending Drift Gate seal
```

---

## Forbidden Changes (require explicit authorization)

```text
- PASS/DROP semantics
- PSEUDO-A authority
- Locked gate thresholds
- CRAM tier definitions
- EvidencePacket authority fields
- Lane 1 / Lane 2 boundary
- RSYNC priority doctrine
- HRG9 reference hash
- Canonical book structure
```

---

## Patch Workflow

```text
1. git status — confirm no staged runtime artifacts
2. Read relevant doctrine docs in order above
3. Inspect target files before modifying
4. Patch one contradiction group at a time
5. Add or update tests
6. Run: python3 -m pytest ph6/ -v
7. Run authority-leakage grep
8. Commit source + schema + docs + tests only
9. Push after tests pass
```

---

## Do Not Stage

```text
PH6_RECOVERY/
cram_pu_live_1_0/runtime/
ph6/cram_pu/runtime/
ph6/cram_pu/validation_runs/
usb3_nvme_calibration/
frame_filter (submodule)
ph6_status/status.json
```
