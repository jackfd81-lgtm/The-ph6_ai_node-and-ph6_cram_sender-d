# PH6 Prototype Workstation Priority Doctrine

**Schema:** ph6.governance.workstation_priority.v2  
**Status:** ACTIVE — prototype phase  
**Authority:** ZERO (Lane-2 advisory document)  
**Proposed by:** claude-code-lane2 | **Ratified by:** null

---

## Workstation Class Assignment

```
CLASS 1
Claude / Cloud Terminal
Development Authority

CLASS 2
SSH Terminal
Operational Authority

CLASS 3
PH6 Desktop Controlled Terminal
Prototype Operator Cockpit
```

Class is not a rank of importance — it is a scope boundary. Class 3 is not subordinate to Class 1 in purpose; it is bounded in authority. The cockpit's job is to provide a controlled operational surface for the system that Class 1 and Class 2 build and maintain.

---

## Desktop Definition: Controlled Operational Cockpit

The PH6 Desktop is not a passive UI. It is a **Controlled Operational Cockpit**.

```
Desktop = Controlled Operational Cockpit
Authority = ZERO
```

### Desktop CAN

```
Launch approved tests (test_registry.json gated)
Monitor running tests (live output, tail)
Review evidence (artifacts, logs, replay outputs)
Inspect topology (node health, device state)
View governance (scan results, canon docs)
Review replay (CRAM parity, harness output)
Review CRAM artifacts (PASS/DROP records)
Run registered diagnostic commands
Run restore from last known good (with operator confirm)
```

### Desktop CANNOT

```
Change authority
Change governance
Change canon
Commit to git
Push to remote
Mutate evidence in CRAM-A
Write to audit chain
Issue PASS or DROP verdicts
Execute unregistered commands
Perform autonomous takeover
```

The boundary is: **launch and observe, never decide and write.**

---

## Zone Structure

The desktop is divided into four command zones.

```
ZONE A — Operations
ZONE B — Evidence
ZONE C — Governance
ZONE D — Future (Phase 6A: visible, disabled)
```

### ZONE A — Operations

```
Dashboard
Camera Diagnostics
Sensor Diagnostics
Test Control
Realtime
```

### ZONE B — Evidence

```
Evidence Browser
PSEUDO
SoSo
Tokens
Live-vs-Simulator
Reports
```

### ZONE C — Governance

```
Topology
Governance Center
Restore Status
```

### ZONE D — Future (Phase 6A: visible and disabled)

```
Characterization Center
Tricorder Mode
Courtroom Readiness
```

Zone D items are visible in the menu but non-interactive during Phase 6A. They communicate the planned roadmap to the operator without implying capability that does not yet exist.

---

## PH6 Status Banner

Every screen displays:

```
PH6 Desktop Controlled Terminal

Class: 3
Role: Prototype Operator Cockpit
Authority: ZERO

Controller: DESKTOP
Mode: CONTROL

One Controller / Many Observers
```

This banner is non-negotiable. It immediately communicates system state to any observer — operator, reviewer, or auditor.

---

## Zone A: Test Control Panel

The Test Control panel is the primary operational surface for Zone A.

**Display:**

```
Available Tests   (from test_registry.json)
Running Tests     (current active test, if any)
Last Result       (verdict, duration, artifact path)
Artifacts         (quick-view of last run output)
```

**Actions:**

```
Start             (launch from registry)
Monitor           (tail stdout/stderr)
View Results      (open run_status.json)
Open Artifacts    (navigate to output directory)
Request Stop      (SIGINT to process)
Force Stop        (SIGKILL after timeout)
```

No test can be launched outside the registry. The preflight gate checks script existence, output path writeability, and governance root before any launch.

---

## Zone B: Evidence Browser

The Evidence Browser (formerly "Reports") is the primary operational surface for Zone B.

It handles all of the following as evidence:

```
Reports          (markdown + JSON run summaries)
Artifacts        (frame packets, measurements)
Topology         (node/device records)
Governance       (scan receipts, baselines)
Camera Runs      (dual camera outputs, context frames)
Logs             (stdout archives, session logs)
Replay Outputs   (CRAM parity records)
```

"Evidence Browser" is the correct name because this panel manages evidence management, not report viewing.

---

## Zone D: Characterization Center (Phase 6B)

Moves into Phase 6B immediately after the desktop stabilizes.

**Scope:**

```
USB_CAMERA_12000
Stage 2 Thermal
Stage 3 Characterization
Stage 4 Scan
Dual Camera
```

**Metrics tracked:**

```
Motion
Brightness
Entropy
Drops
Replay
Calibration
```

This is one of the strongest parts of PH6 work. The Characterization Center deserves its own panel with metric history, not inline test output.

---

## Zone D: Tricorder Mode (Reserved, Disabled)

Reserved for a future phase. Disabled until the desktop stabilizes.

**Purpose:**

```
Observe
Measure
Record
Review
Compare
```

**Data sources:**

```
Camera
Audio
Environment
ESP_S1
Replay
Topology
```

**Invariants:**

```
No authority.
No automation.
No decision making.
```

Tricorder Mode is an observer instrument, not a measurement authority.

---

## Zone D: Courtroom Readiness Panel (Phase 6B Placeholder)

A placeholder panel is visible in Phase 6A. It is informational only.

**Display:**

```
Courtroom Readiness

Operator Identity      PENDING
Method Registry        PENDING
Calibration Records    PENDING
Chain of Custody       PENDING
Replay Validation      PASS
```

This communicates evidence readiness gaps to the operator without claiming admissibility.

---

## Implementation Order

```
1.  Fix curses crash
2.  Stabilize Windows interface
3.  Implement Test Control (Zone A)
4.  Implement Evidence Browser (Zone B)
5.  Implement Command Registry Policy
6.  Add Workstation Priority panel
7.  Add Restore Status panel
8.  Add Characterization Center (Zone D → Phase 6B)
9.  Add Courtroom Readiness panel (Zone D → Phase 6B)
10. Add Tricorder Mode (Zone D → Phase 6B)
11. Add Future Node/Fleet support
```

---

## Recovery Authority

When the desktop interface breaks:

```
Class 1 (Cloud/Claude Terminal) → diagnose and patch
Class 2 (SSH Terminal)          → direct device recovery
Class 3 (Desktop)               → restore from last known good only
```

Desktop never recovers itself autonomously. Recovery flows up the class hierarchy.

---

## System Flow (Current Prototype)

```
Operator starts in Cloud Terminal / SSH
  ↓ restore point verified
  ↓ test method selected from registry
  ↓ preflight checks script, device, output path, governance root
  ↓ sensor capture begins
  ↓ PSEUDO deterministic measurement → PASS/DROP
  ↓ CRAM preserves evidence packet and hashes
  ↓ replay validates reproducibility
  ↓ SoSo/AI produces advisory interpretation only
  ↓ governance scan checks policy drift
  ↓ report generated (human + JSON + manifest)
  ↓ operator ratifies
  ↓ manual commit/push if appropriate
```

Desktop role today: **launch, observe, monitor, inspect.**
Cloud/SSH role today: **develop, repair, ratify, commit.**

---

## Final PH6 Position

```
Claude Terminal
= Class 1 Development Authority

SSH Terminal
= Class 2 Operational Authority

PH6 Desktop
= Class 3 Prototype Operator Cockpit
  Authority: ZERO

CRAM
= Preservation Authority

PSEUDO
= Measurement Authority

SoSo
= Advisory (Authority ZERO)

Tokens
= Advisory (Authority ZERO)

Simulator
= Advisory (Authority ZERO)

Desktop
= Operational Cockpit
  Authority ZERO
```

---

## Storage Doctrine

**Git is the prototype source/version-control layer. It is not the final production evidence-storage authority.**

```
Git tracks: prototype code and development history.

PH6 evidence authority comes from: CRAM chain, artifact manifests,
hashes, replay records, operator logs, storage manifests,
and chain-of-custody records.
```

Production PH6 must support multiple storage backends:

| Storage Type | Role |
|---|---|
| Internal NVMe/SSD | Local primary evidence/device storage |
| External USB SSD/NVMe | Backup, export, field evidence |
| Removable media | Field collection, offline archive |
| Cloud object storage | Remote archive, sync, disaster recovery |
| Git | Prototype source control; optional metadata only |
| CRAM store | Evidence preservation authority |
| Offline archive | Courtroom/evidence retention package |

Evidence authority must be backend-agnostic. Any storage layer may fail or be unavailable; the CRAM chain and manifests must remain the authoritative record regardless.

---

*Lane-2 advisory document. No authority changes. Operator ratification required.*
