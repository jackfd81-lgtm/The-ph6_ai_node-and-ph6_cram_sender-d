# PH6 Cockpit Authority Boundary Audit

**File:** PH6_SOURCE/DESKTOP_CONTROLLED_TERMINAL/PH6_COCKPIT_AUTHORITY_AUDIT_20260608.md
**Date:** 2026-06-08
**Auditor:** Perplexity Computer
**Audit class:** Class 3 advisory audit
**Authority:** ZERO — not Lane-1 ratification
**Subject:** PH6 Class 3 Desktop Cockpit — preview build deployed 2026-06-08
**Audit scope:** Server routes · React pages · Interactive controls · simulated data · seed records
**Audit method:** Static source review of server/routes.ts, server/storage.ts, shared/schema.ts, and cockpit React pages
**Files modified:** None

---

## Audit Mandate

The cockpit is Class 3: display, advisory, and operator-note only.

Class 3 may display Lane-1 data if that data originates from a real Lane-1 source and is clearly represented as read-only. Class 3 may not create, simulate, alter, ratify, overwrite, or delete Lane-1 evidence.

Governing rules:

1. Class 3 may not create, modify, ratify, overwrite, or delete Lane-1 evidence.
2. Class 3 may not generate PASS/DROP as real measurement or governance output.
3. Class 3 may display PASS/DROP only when clearly sourced from real Lane-1 records.
4. All simulated, seeded, demo, or cockpit-generated data must be visibly labeled SIMULATED, DEMO, or AUTHORITY ZERO.
5. Any operational-looking button must either call a real bounded route or be clearly marked as simulation.
6. No route may allow Class 3 to fabricate authority-tagged packets that could be mistaken for Pi-5-generated Lane-1 records.

---

## Section 1 — Page-Level Summary

| Page | Role | Verdict | Notes |
|---|---|---|---|
| Overview | Read-only display | CONDITIONAL PASS | Evidence stream and KPI cards display seed/demo PASS counts without clear DEMO/SIMULATED labeling. |
| Camera Monitor | Read-only + checklist | CONDITIONAL PASS | Header says LANE 1 PSEUDO, which implies authority rather than read-only display. Seed session lacks SIMULATED marker. |
| Evidence Log | Read-only display | FAIL | Seed packets display PSEUDO-L1, EVIDENCE, and L1 authority markers without disambiguation. |
| Governance Scan | Interactive simulation | FAIL | Route hardcodes PASS, fabricates git status, persists result, and powers sidebar status. |
| Node Topology | Interactive simulation | CONDITIONAL PASS | Discovery is simulated but labeled like a live Pi-5 operation. Node health seed data has no SIMULATED marker. |
| Issue Register | Operator notes | PASS | Mutations are cockpit-local issue-status notes only. No Lane-1 impact. |
| Doctrine Reference | Static reference | PASS | No interactive authority behavior. |

---

## Section 2 — Route Audit

### 2.1 Read-Only Routes

| Route | Verdict | Notes |
|---|---|---|
| GET /api/evidence/packets | PASS | Read-only. |
| GET /api/evidence/stats | PASS | Aggregate of cockpit-local DB only. |
| GET /api/camera/sessions | PASS | Read-only. |
| GET /api/camera/active | PASS | Read-only. |
| GET /api/governance/scans | PASS | Read-only history. |
| GET /api/governance/latest | PASS | Read-only, but unsafe if backing records are fabricated. |
| GET /api/nodes/health | PASS | Read-only health snapshot. |
| GET /api/issues | PASS | Read-only issue list. |

---

### V-1 — POST /api/evidence/packets

**Severity:** HIGH
**Type:** Authority-fabrication route

The route accepts arbitrary JSON and writes it to evidence_packets with no Class-3 boundary constraint.

A caller can submit:

```
authorityTag: "PSEUDO-L1"
verdict: "PASS"
tempClass: "EVIDENCE"
laneSource: 1
```

This can make the cockpit database contain records visually and structurally indistinguishable from Pi-5 Lane-1 output.

**Violation:** Class 3 may display evidence but may not create Lane-1 evidence or Lane-1-looking evidence.

**Required fix:** Remove the route for Class-3 preview, or force all inserted records to COCKPIT-SIM, laneSource: 0, tempClass: DEMO/SIMULATED, and authority: ZERO.

---

### V-2 — POST /api/governance/scan

**Severity:** HIGH
**Type:** Fabricated governance verdict

The route hardcodes:

```
verdict: "PASS"
gitHead: crypto.randomBytes(4).toString("hex")
gitStatus: "clean"
repoClean: 1
```

No real governance scan is executed. The resulting record is persisted and can power cockpit-wide PASS indicators.

**Violation:** Class 3 may display a real governance PASS, but may not generate one.

**Required fix:** Replace with SIMULATED-PASS, gitHead: "UNVERIFIED", gitStatus: "UNVERIFIED", repoClean: 0, and simulated: true.

---

### V-3 — POST /api/camera/sessions

**Severity:** MEDIUM
**Type:** Unconstrained session fabrication

The route allows arbitrary camera session creation, including fields such as:

```
replayStatus: "MATCH"
passCount
dropCount
lane2Leakage
storagePath
```

This can fabricate a session that appears replay-verified.

**Required fix:** Either remove the route from Class-3 preview or force created sessions to DEMO/SIMULATED status and prohibit MATCH, real-looking storage paths, and fabricated PASS/DROP counts.

---

### V-4 — PATCH /api/camera/sessions/:sessionId

**Severity:** MEDIUM
**Type:** Unbounded field mutation

The route passes req.body directly into updateCameraSession.

This allows Class 3 to overwrite replay status, leakage fields, counts, and other evidence-adjacent state.

**Required fix:** Add a strict allowlist such as:

```
const ALLOWED_SESSION_PATCH_FIELDS = ["notes", "status"];
```

Reject all other fields.

---

### B-1 — POST /api/nodes/health

**Severity:** LOW
**Type:** Misleading telemetry risk

Node health is not Lane-1 evidence, but the route permits cockpit-generated health records with arbitrary authorityClass.

**Required fix:** Mark records as simulated: true unless pushed from a verified external source.

---

## Section 3 — Seed Data Audit

### Evidence Packet Seeds

**Severity:** HIGH

Seed packets currently use authority-looking values:

| Field | Current Problem |
|---|---|
| authorityTag: "PSEUDO-L1" | Claims Lane-1 authority origin. |
| tempClass: "EVIDENCE" | Claims evidence classification. |
| laneSource: 1 | Claims Lane-1 source. |
| verdict: "PASS" / "DROP" | Acceptable only if visibly DEMO/SIMULATED; currently not labeled. |
| payloadHash: sha256:${Math.random()...} | Fake non-deterministic value presented as SHA-256. |
| canonHash: blake2b:${Math.random()...} | Fake non-deterministic value presented as BLAKE2b. |

**Required fix:**

```
authorityTag: "COCKPIT-SEED-DEMO"
tempClass: "DEMO"
laneSource: 0
payloadHash: `demo:${i.toString().padStart(64, "0")}`
canonHash: `demo:${i.toString().padStart(64, "0")}`
simulated: true
authorityLevel: "ZERO"
```

---

### Camera Session Seed

**Severity:** HIGH

Problem fields:

```
replayStatus: "MATCH"
replayHash: "blake2b:..."
storagePath: "/mnt/nvme/ph6/sessions/cam-baseline-001"
```

These imply real replay verification and real Pi-5 storage.

**Required fix:**

```
replayStatus: "DEMO-MATCH"
replayHash: "demo:..."
storagePath: "cockpit-demo://sessions/cam-baseline-001"
simulated: true
authorityLevel: "ZERO"
```

---

### Governance Scan Seed

**Severity:** HIGH

Problem fields:

```
verdict: "PASS"
gitHead: "a3f7c12"
gitStatus: "clean"
```

These imply real governance state.

**Required fix:**

```
verdict: "DEMO-PASS"
gitHead: "UNVERIFIED-SEED"
gitStatus: "UNVERIFIED"
repoClean: 0
simulated: true
authorityLevel: "ZERO"
```

---

### Node Health Seed

**Severity:** LOW/MEDIUM

Static temperatures and authority classes are displayed as if live.

**Required fix:**

```
simulated: true
telemetryFreshness: "SEED_DEMO"
authorityLevel: "ZERO"
```

UI must show DEMO TELEMETRY.

---

## Section 4 — UI Control Audit

### Governance Scan UI

**Severity:** HIGH

The scan log displays hardcoded terminal-like output that mimics a real Pi-5 scan.

Required UI correction:

```jsx
<span className="lane-badge lane-zero">
  COCKPIT SIMULATION — command not executed
</span>
```

Prefix all fabricated log lines:

```
[SIM] $ python3 ...
[SIM] command not executed
[SIM] output is scripted preview text
```

Never display bare:

```
VERDICT: PASS
```

for cockpit-generated scans. Use:

```
SIMULATED VERDICT: DEMO-PASS
```

---

### Node Discovery UI

**Severity:** MEDIUM

Current UI implies discovery is run from Pi-5.

Required correction:

```jsx
{discovering ? "SIMULATING…" : "SIM DISCOVERY"}
```

Use log lines:

```
[SIM] Cockpit cannot run discovery from Pi-5.
[SIM] Execute discovery from Pi-5 SSH terminal for real results.
[SIM] $ lsusb — command not executed
[SIM] $ dmesg | tail -100 — command not executed
```

---

### Camera Monitor Header

**Severity:** MEDIUM

Replace:

```jsx
<span className="lane-badge lane-1">LANE 1 PSEUDO</span>
```

With:

```jsx
<span className="lane-badge lane-zero">
  DISPLAYS LANE-1 DATA · CLASS 3 READ-ONLY
</span>
```

Replace subheading:

```
Lane 1 deterministic measurement — PASS/DROP authority
```

With:

```
Read-only cockpit display of Lane-1 data. This page has no PASS/DROP authority.
```

---

### Evidence Log

**Severity:** HIGH

Seed/demo evidence rows must not use Lane-1 visual styling unless the row is backed by verified Lane-1 provenance.

Required banner:

```jsx
{packetsArr.some((p: any) => p.authorityTag === "COCKPIT-SEED-DEMO") && (
  <div className="authority-banner">
    DEMO DATA LOADED — not Pi-5 Lane-1 measurement output
  </div>
)}
```

---

### Overview KPI Cards

**Severity:** MEDIUM

KPI values derived from seed/demo records must be labeled:

```
DEMO · not live
AUTHORITY ZERO
```

PASS counts are acceptable only when the source is explicit.

---

## Section 5 — Consolidated Violation Register

| ID | Severity | Location | Description |
|---|---|---|---|
| V-1 | HIGH | POST /api/evidence/packets | Allows cockpit to create Lane-1-looking evidence packets. |
| V-2 | HIGH | POST /api/governance/scan | Fabricates and persists governance PASS. |
| V-3 | MEDIUM | POST /api/camera/sessions | Allows replay/session fabrication. |
| V-4 | MEDIUM | PATCH /api/camera/sessions/:sessionId | Allows unbounded session mutation. |
| V-5 | HIGH | Seed evidence packets | Use PSEUDO-L1, EVIDENCE, and laneSource: 1. |
| V-6 | HIGH | Seed hashes | Math.random() values are mislabeled as SHA-256/BLAKE2b. |
| V-7 | HIGH | Seed camera session | Fabricated replay MATCH. |
| V-8 | HIGH | Seed governance scan | Fabricated governance PASS, git SHA, and clean status. |
| V-9 | HIGH | Governance scan UI | Fake Pi-5 terminal output without simulation label. |
| V-10 | MEDIUM | Node topology UI | Simulated discovery presented as Pi-5 action. |
| V-11 | MEDIUM | Camera monitor UI | Header suggests Lane-1 authority. |
| V-12 | HIGH | Evidence log UI | Seed records displayed with Lane-1 authority styling. |
| V-13 | MEDIUM | Overview KPI cards | Demo PASS/evidence counts lack source labeling. |
| B-1 | LOW | POST /api/nodes/health | Allows misleading cockpit-generated health records. |

---

## Section 6 — Patch Set Required

### P-1 — Disable or constrain POST /api/evidence/packets

Preferred Class-3 preview behavior:

```ts
app.post("/api/evidence/packets", (_req, res) => {
  return res.status(403).json({
    error: "CLASS 3 BOUNDARY: cockpit may not create evidence packets",
    authority: "ZERO",
  });
});
```

Alternate demo-only behavior must forcibly override authority fields.

---

### P-2 — Convert governance scan route to simulation-only

```ts
app.post("/api/governance/scan", (_req, res) => {
  const scan = storage.createGovernanceScan({
    scanId: `cockpit-sim-${Date.now()}`,
    critical: 0,
    high: 0,
    warn: 0,
    verdict: "SIMULATED-PASS",
    gitHead: "UNVERIFIED",
    gitStatus: "UNVERIFIED",
    repoClean: 0,
    scannedAt: new Date().toISOString(),
    simulated: 1,
    authorityLevel: "ZERO",
    notes: "[COCKPIT SIMULATION — not a real ph6_governor.py scan. Run from Pi 5 SSH terminal for authoritative results.]",
  });
  res.json({
    ...scan,
    _cockpit_notice: "SIMULATED — Class 3 cockpit cannot execute authoritative governance scans",
  });
});
```

---

### P-3 — Constrain camera session creation

```ts
app.post("/api/camera/sessions", (req, res) => {
  const data = insertCameraSessionSchema.parse(req.body);
  if (data.replayStatus === "MATCH") {
    return res.status(403).json({
      error: "CLASS 3 BOUNDARY: cockpit may not assert replayStatus MATCH",
      authority: "ZERO",
    });
  }
  const safeData = {
    ...data,
    replayStatus: data.replayStatus ?? "PENDING",
    lane2Leakage: null,
    simulated: 1,
    authorityLevel: "ZERO",
  };
  res.status(201).json(storage.createCameraSession(safeData));
});
```

---

### P-4 — Allowlist session patch fields

```ts
const ALLOWED_SESSION_PATCH_FIELDS = ["notes", "status"];
app.patch("/api/camera/sessions/:sessionId", (req, res) => {
  const { sessionId } = req.params;
  const patch: Record<string, unknown> = {};
  for (const field of ALLOWED_SESSION_PATCH_FIELDS) {
    if (field in req.body) patch[field] = req.body[field];
  }
  if (Object.keys(patch).length === 0) {
    return res.status(400).json({
      error: "No Class-3 patchable fields provided",
    });
  }
  const updated = storage.updateCameraSession(sessionId, patch);
  if (!updated) {
    return res.status(404).json({ error: "Session not found" });
  }
  res.json(updated);
});
```

---

### P-5 — Fix seed data

All seed data must be explicitly non-authoritative:

```
simulated: 1
authorityLevel: "ZERO"
source: "COCKPIT_SEED_DEMO"
```

Evidence packet seed replacements:

```
authorityTag: "COCKPIT-SEED-DEMO"
tempClass: "DEMO"
laneSource: 0
payloadHash: `demo:${i.toString().padStart(64, "0")}`
canonHash: `demo:${i.toString().padStart(64, "0")}`
```

Governance seed replacements:

```
verdict: "DEMO-PASS"
gitHead: "UNVERIFIED-SEED"
gitStatus: "UNVERIFIED"
repoClean: 0
```

Camera seed replacements:

```
replayStatus: "DEMO-MATCH"
replayHash: "demo:seed-camera-session"
storagePath: "cockpit-demo://sessions/cam-baseline-001"
```

---

### P-6 — Add simulation labels to UI

Every cockpit-generated value must render one of:

```
SIMULATED
DEMO
AUTHORITY ZERO
COMMAND NOT EXECUTED
NOT PI-5 LANE-1 OUTPUT
```

---

### P-7 — Add schema support

Add explicit fields where absent:

```
simulated: integer("simulated").notNull().default(1)
authorityLevel: text("authority_level").notNull().default("ZERO")
sourceClass: text("source_class").notNull().default("COCKPIT")
```

---

## Section 7 — Final Verdict

**FINAL VERDICT: UNSAFE FOR CLASS-3 PREVIEW IN CURRENT FORM**

Confirmed high-severity authority-boundary failures:
- V-1: cockpit can write Lane-1-looking evidence packets
- V-2: cockpit fabricates governance PASS
- V-5: seed packets carry Lane-1 authority markers
- V-6: fake hashes are presented as cryptographic hashes
- V-7: seed camera session fabricates replay MATCH
- V-8: seed governance scan fabricates PASS / git clean state
- V-9: governance UI fabricates Pi-5 terminal scan output
- V-12: Evidence Log displays seed records with Lane-1 authority styling

These are not cosmetic issues. They create a provenance-contamination risk where cockpit-local data can become visually and structurally indistinguishable from real Lane-1 output.

Required path to safe Class-3 preview:

1. Apply P-1 through P-7.
2. Re-run static authority-boundary audit.
3. Confirm cockpit-generated records cannot use Lane-1 authority markers.
4. Confirm all demo/simulated records are labeled.
5. Do not connect cockpit to any real PH6 evidence pipeline until the boundary patch passes.

---

## Appendix A — Files Audited

| File | Status |
|---|---|
| server/routes.ts | Full read |
| server/storage.ts | Full read |
| shared/schema.ts | Full read |
| client/src/App.tsx | Full read |
| client/src/components/Layout.tsx | Full read |
| client/src/pages/Overview.tsx | Full read |
| client/src/pages/CameraMonitor.tsx | Full read |
| client/src/pages/EvidenceLog.tsx | Full read |
| client/src/pages/GovernanceScan.tsx | Full read |
| client/src/pages/NodeTopology.tsx | Full read |
| client/src/pages/IssueRegister.tsx | Full read |
| client/src/pages/DoctrineReference.tsx | Full read |

---

## Appendix B — Not Audited

- Runtime traffic
- SQLite migration safety
- Network exposure
- Authentication / authorization
- CSS rendering details
- client/src/lib/queryClient.ts

---

## Closing Classification

This document is Class-3 advisory output.

It may guide remediation.

It does not ratify doctrine.

It does not certify the cockpit.

It does not close any PH6 authority gate.

**Authority: ZERO.**
