# PH6 / CRAM — Desktop Controlled Terminal Doctrine

**Document ID:** PH6-DESKTOP-CLASS3-PROTOTYPE-DOCTRINE-v1.2
**Status:** PROPOSED — Awaiting Operator Ratification (gate matrix in Section 11 must pass before ACTIVE)
**Classification:** Implementation / Operator Interface Doctrine
**Authority Level:** ZERO
**Canonical Home:** `PH6_SOURCE/DESKTOP_CONTROLLED_TERMINAL/` (Class 3 interface doctrine — explicitly NOT Book V; Book V remains quarantined for advisory swarm/token research only)
**Applies To:** PH6 Desktop Interface / Desktop Controlled Terminal / Prototype Cockpit
**Supersedes:** `PH6_DESKTOP_CLASS3_PROTOTYPE_DOCTRINE_v1.1.md` (staged, not yet ratified/committed — corrects its Maturity Panel and CAN/CANNOT framing to match current PH6 Desktop reality; v1.1's hierarchy, evidence-chain, authority-boundary, session-lock, and gate-matrix sections carry forward unchanged below)

```json
{"proposed_by":"claude-code-lane2","proposed_at_utc":"2026-06-07T11:48:09Z","api_call_log_ref":"session-ph6-desktop-doctrine-v1.2","ratified_by":null}
```

---

## 1. Core Doctrine

The PH6 Desktop Interface is a **Class 3 Prototype Cockpit**.

It is not the primary development authority.
It is not the primary operational authority.
It is not a sovereign PH6 node.
It does not generate evidence authority.
It does not issue PASS or DROP.
It does not modify CRAM, PSEUDO, SoSo, or canonical evidence structures.

The governing sentence is:

**Desktop consumes evidence. Desktop does not generate authority. Desktop is a Class 3 prototype cockpit.**

```text
=============================================================================
         PH6-DESKTOP-CLASS3-PROTOTYPE-DOCTRINE-v1.2 ── CORNERSTONE
=============================================================================
 [LANE 1: CORE AUTHORITY]  ─── Contains: CRAM, PSEUDO, PASS/DROP Gating
            │
            ▼ (Read-Only Consumption Layer)
 [CLASS 3 DESKTOP INTERFACE] ─── Prototype Cockpit [Authority: ZERO]
=============================================================================
```

---

## 2. Workstation Hierarchy

```text
CLASS 1
Cloud / Claude Terminal
PRIMARY — Development Authority

CLASS 2
SSH Terminal
PRIMARY OPERATIONAL — Device Authority

CLASS 3
PH6 Desktop Controlled Terminal
PROTOTYPE — Prototype Operator Cockpit
Authority ZERO
```

|   Class | Interface                   | Role                                   | Authority             |
| ------: | --------------------------- | -------------------------------------- | --------------------- |
| Class 1 | Claude / Cloud Terminal     | Primary development workstation        | Development authority |
| Class 2 | SSH Terminal                | Primary operational device workstation | Operational authority |
| Class 3 | Desktop Controlled Terminal | Prototype operator cockpit             | Authority ZERO        |

The Desktop Interface may grow in capability over time, but it remains third in the workstation hierarchy until formally promoted by PH6 certification (see Section 11 / Phase 7+ gate).

---

## 3. PH6 Prototype Notice (required on every screen)

```text
PH6 Prototype Notice

This workstation is a prototype development cockpit.

Primary development authority:
Class 1 Cloud Terminal

Primary operational authority:
Class 2 SSH Terminal

Desktop functions are limited to approved prototype capabilities.
```

---

## 4. Evidence Chain Position & Boundary Isolation

The Desktop Interface sits **after** the evidence chain.

Canonical flow:

```text
Reality → Sensors → CRAM-0 → PSEUDO-M → PSEUDO-A → CRAM-A / CRAM-R → SoSo → Tokens → Reports → Desktop → Human Review
```

Desktop consumes outputs from: CRAM-derived reports, governance scans, topology files, test results, audit artifacts, visualization outputs, advisory MRAM-S products.

Desktop may not write into: CRAM-0, CRAM-A, CRAM-R, PSEUDO verdict files, EvidencePacket authority fields, Lane-1 threshold profiles, authority-chain hash records.

```text
                    ┌──────────────────────────────┐
                    │ CLASS 3 DESKTOP ARCHITECTURE │
                    └──────────────┬───────────────┘
                                   │
         ┌─────────────────────────┴─────────────────────────┐
         ▼                                                   ▼
 ┌───────────────┐                                   ┌───────────────┐
 │   CONSUMES    │                                   │ DOES NOT      │
 │  READ-ONLY    │                                   │ GENERATE      │
 └───────┬───────┘                                   └───────┬───────┘
         ├── Evidence packet views                          ├── System authority
         ├── Local integration test metrics                 ├── PASS / DROP signals
         ├── Telemetry topology maps                        ├── CRAM core mutations
         ├── Verification reports                           ├── PSEUDO threshold changes
         ├── Governance reports                             ├── EvidencePacket mutations
         └── Operator dashboards                            └── Authority-chain writes
```

### 4.1 Preserved Architecture Axioms

1. **Lane 1 Authority Invariance** — System authority remains bound inside Lane 1. No Desktop interface action may update, bypass, or reinterpret Lane-1 validation sequences.
2. **Gating Exclusivity** — System-level PASS/DROP verdicts belong entirely to PSEUDO-A. Desktop cannot produce, replicate, intercept, override, or transform these verdicts.
3. **Contamination Mitigation** — Advisory processing layers and client monitors operate without write access to state-preservation paths. Desktop must not mutate CRAM-0, CRAM-A, CRAM-R, EvidencePacket records, authority hashes, or PSEUDO threshold profiles.
4. **Read-Only Evidence Consumption** — Desktop may display evidence-derived outputs. Display is not authority. Visualization is not adjudication.

---

## 5. Desktop CAN / CANNOT (operator-facing summary)

**Desktop CAN:**
```text
Launch approved tests
Monitor tests
View results
Browse evidence
View topology
View governance
Review replay
Export reports
```

**Desktop CANNOT:**
```text
Commit
Push
Pull
Modify governance
Modify authority
Modify canon
Modify CRAM
Modify PSEUDO
Modify replay doctrine
```

### 5.1 Detailed authority-boundary enforcement (carried forward from v1.1)

**Desktop CAN (detail):** display PH6 state · launch approved tests · monitor running tests · preview evidence artifacts · display governance/topology status · display replay and report summaries · provide operator controls for approved workflows · store UI preferences and local non-authoritative state

**Desktop CANNOT (detail):** issue PASS or DROP · override PSEUDO-A · modify PSEUDO thresholds · mutate EvidencePacket records · promote advisory output into authority · write to CRAM-A or CRAM-R · bypass Claude/SSH locks · act as a hidden controller · become an autonomous authority node

**Violation condition:** If Desktop writes authority data or influences Lane-1 adjudication, declare DRIFT_FAIL.

---

## 6. Test Control Split

Each test declares a Desktop state: `TEST_CONTROL` (launch+monitor), `TEST_MONITOR` (observe only), `BLOCKED` (log review only).

| Test / System                      | Desktop State                                            |
| ---------------------------------- | -------------------------------------------------------- |
| USB camera characterization        | TEST_CONTROL                                             |
| Governance scan                    | TEST_CONTROL                                             |
| ESP_S1 topology viewer             | TEST_MONITOR or TEST_CONTROL depending on implementation |
| Long-running production monitor    | TEST_MONITOR                                             |
| HRG9 certification closure         | BLOCKED unless explicitly authorized                     |
| CRAM-A mutation / authority repair | BLOCKED                                                  |

Rule: **Some tests may be visible without being launchable.**

---

## 7. Session Lock Doctrine — "One Controller. Many Observers."

* If Claude/Cloud Terminal holds the active control lock → Desktop transitions CONTROL → MONITOR_ONLY
* If SSH Terminal holds the active control lock → Desktop transitions CONTROL → MONITOR_ONLY
* If Desktop holds a limited approved test lock → Claude and SSH remain superior and may override, review, or terminate the session

Desktop lock scope must be narrow, logged, and revocable.

---

## 8. Maturity Panel (revised in v1.2 — current-state assessment)

| Module                  | Status      |
| ----------------------- | ----------- |
| UI Framework            | ACTIVE      |
| Evidence Browser        | ACTIVE      |
| Test Control            | ACTIVE      |
| Authority Monitor       | ACTIVE      |
| Characterization Center | DEVELOPMENT |
| Runtime Evidence Flow   | PLANNED     |
| Courtroom Readiness     | PLANNED     |
| Tricorder Mode          | PLANNED     |
| Fleet Support           | PLANNED     |

> **v1.2 correction note:** v1.1 rated UI Framework / Evidence Browser / Governance Viewer as DEVELOPMENT and Realtime Dashboard / Characterization Center / Tricorder Mode as EXPERIMENTAL. The operator has confirmed the table above as the more accurate current-state assessment; it supersedes v1.1 Section 7 in full. No module becomes production-primary merely by reaching ACTIVE.

---

## 9. Evidence Browser Classification (carried forward from v1.1)

| Label      | Meaning                                           |
| ---------- | ------------------------------------------------- |
| REPORT     | Human-readable output or summary                  |
| ARTIFACT   | Generated runtime/test artifact                   |
| TOPOLOGY   | Node, sensor, or graph topology data              |
| GOVERNANCE | Drift scan, policy scan, authority report         |
| TOKEN      | SoSo / token / advisory continuity artifact       |
| CRAM       | CRAM-related evidence or manifest                 |
| TEST       | Test run output or test manifest                  |
| LOG        | Runtime or diagnostic log                         |
| CONFIG     | Non-authoritative configuration view              |
| UNKNOWN    | Unclassified file; preview allowed, edits blocked |

Rules: preview allowed · editing blocked by default · writes blocked by default · authority files read-only · unknown files treated conservatively · any attempted authority mutation triggers an audit warning.

---

## 10. Permanent Footer (required on every screen)

```text
Desktop Status:
Experimental Development Platform

Authority:
ZERO

Lane Impact:
None

Current Maturity:
Early Operational Prototype
```

---

## 11. Pre-Ratification Verification Gate Matrix (carried forward from v1.1)

```text
[ ] GATE 01: Dashboard Stability Verification Run
[ ] GATE 02: Session Lock Validation and Timeout Test
[ ] GATE 03: Evidence Browser Read-Only Strict Flag Enforcement
[ ] GATE 04: Local Test Control Execution Boundaries Check
[ ] GATE 05: ESP_S1 Physical Topology Mapping Validation
[ ] GATE 06: Automated Governance Scanner Clean Pass
[ ] GATE 07: Cryptographic Proof of No Authority Writeback
[ ] GATE 08: Directory Protection Check — Zero CRAM Mutations Allowed
[ ] GATE 09: Logic Boundary Audit — Zero PSEUDO Threshold Interference
[ ] GATE 10: State Integrity Verification — Zero PASS/DROP Generation Paths
```

Until all ten gates pass code analysis, runtime validation, and governance scan review, Desktop remains:

```text
Class: CLASS 3
Status: PROPOSED / RATIFY NEXT
Authority: ZERO
Production Role: NOT PRIMARY
```

Desktop may be developed, tested, and improved. Desktop may not become primary. Desktop may not gain authority by convenience, interface completeness, or operator preference.

---

## 12. Prototype Capability Roadmap (carried forward from v1.1)

**Phase 6A — Prototype Cockpit Foundation:** shell, dashboard, evidence browser, governance viewer, realtime status, basic approved-test launcher, read-only topology viewer, session lock awareness

**Phase 6B — Scientific Operator Tools:** Characterization Center, camera test workflow, sensor condition viewer, Tricorder Mode prototype, Artifact Explorer, report comparison, operator notes

**Phase 6C — Multi-Node Awareness:** Fleet View, Pi5/Pi Zero/ESP_S1 panels, multi-node replay viewer, cross-node topology comparison, environmental modeling, long-run monitor

**Phase 7+ — Candidate Primary Interface (gated):** requires governance scan PASS, lane boundary tests PASS, session lock tests PASS, evidence browser mutation tests PASS, CRAM write-protection tests PASS, test launcher safety tests PASS, multi-hour stability PASS, operator ratification, certification review. Until all pass: **Desktop remains Class 3.**

---

## 13. PH6 Architectural Result

```text
Cloud Terminal  = Primary Development Platform
SSH Terminal    = Primary Operational Platform
Desktop         = Prototype Development Cockpit

Future Goal:     Unified Operator Control Panel
Current Status:  Development Prototype
```

---

## 14. Source Tree Ingestion (unchanged from v1.1 — corrected placement)

**Doctrine path (this file):** `PH6_SOURCE/DESKTOP_CONTROLLED_TERMINAL/PH6_DESKTOP_CLASS3_PROTOTYPE_DOCTRINE_v1.2.md`
**Validation blueprint:** `PH6_SOURCE/DESKTOP_CONTROLLED_TERMINAL/schemas/ph6_desktop_class3_validation_blueprint_v1.1.schema.json`
**Boundary tests:** `PH6_SOURCE/DESKTOP_CONTROLLED_TERMINAL/tests/`

This doctrine is **Class 3 interface doctrine**, not swarm/token/advisory research, and is therefore placed under `DESKTOP_CONTROLLED_TERMINAL/` — *not* under Book V, which remains quarantined for advisory swarm and token science material only.

Governance acceptance for this placement requires:
```text
0 CRITICAL · 0 HIGH · 0 WARN
No authority widening · No PASS/DROP leakage · No Lane 2 → Lane 1 path
No CRAM mutation path · No PSEUDO threshold mutation path
```

---

## 15. Ratification Statement

This doctrine may be ratified as: **PH6-DESKTOP-CLASS3-PROTOTYPE-DOCTRINE-v1.2**, superseding the staged (not yet ratified) v1.1 draft.

Ratification effect:
* Desktop hierarchy is locked as Class 3 / Prototype Operator Cockpit / Authority ZERO.
* The v1.2 Maturity Panel (Section 8) becomes the operative current-state assessment.
* The Prototype Notice (Section 3) and Permanent Footer (Section 10) become required on every Desktop screen.
* The operator-facing CAN/CANNOT summary (Section 5) and detailed authority-boundary rules (Section 5.1) both apply — the summary for display, the detail for enforcement.
* Desktop remains subordinate to Claude/Cloud Terminal and SSH Terminal, and Authority remains ZERO until the Section 11 gate matrix passes in full.

**Final lock sentence:**
**Desktop consumes evidence. Desktop does not generate authority. Desktop is a Class 3 prototype cockpit.**

```text
[ STATUS: PROPOSED / RATIFY NEXT | CLASS 3 PROTOTYPE | AUTHORITY ZERO | SUPERSEDES v1.1 (UNRATIFIED) ]
```
