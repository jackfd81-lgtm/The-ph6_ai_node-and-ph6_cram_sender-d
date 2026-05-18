# PH6 / CRAM — Production Clearance Declaration

**Declaration ID:** `PH6-PROD-CLEAR-2026-05-18-001`
**Declared by:** Jack Disla
**Declared at:** `2026-05-18T08:50:40Z`
**Generated:** `2026-05-18T09:37:43.008772Z`

---

## Production Clearance

**STATUS: DECLARED**
**Type: HUMAN OPERATOR DECLARATION**

---

## Scope

Single-node PH6/CRAM evidence instrument — Lane 1 deterministic ingest, measurement, PASS/DROP authority, preservation, replay certification, and export/hash-continuity verification. Cross-node rsync transfer to jackjack (192.168.254.189) is included only as export/hash-continuity verification. It does not grant distributed authority, remote PASS/DROP authority, or multi-writer CRAM authority.

---

## Cleared For

- CRAM-0 raw intake
- PSEUDO-M deterministic measurement
- PSEUDO-A PASS/DROP authority
- CRAM-A authoritative evidence store
- CRAM-R deterministic reject vault
- VRC-1.0 replay certification
- Cross-node rsync transfer with hash continuity verification


## Not Cleared For

- Hailo hardware integration (OI-01 — DESCOPED, future revision)
- Multi-writer CRAM
- Distributed authority
- Remote PASS/DROP authority
- Remote CRAM-A write authority
- Kubernetes CRAM-A storage
- Lane 2 authority of any kind


---

## Evidence Basis

| Campaign | State    | Commit       | Notes |
|----------|----------|--------------|-------|
| C07      | CLOSED   | a26c111c25   | Governance drift validation |
| OI-03A   | CLOSED   | 1c1a430e47   | 300 frames, 0 mismatches |
| OI-03B   | CLOSED   | e445e7a3be   | 1200 frames, 0 mismatches |
| OI-03C   | CLOSED   | 2e42ce3705   | 3600 frames, 0 mismatches |
| EVC-05   | CLOSED   | 9deda5b1ab   | 1800 frames, 3 phases PASS |
| OI-01    | DESCOPED | —            | Hailo deferred |

---

## Doctrine Guardrails

- Lane 1 remains authority.
- Lane 2 remains Authority ZERO.
- PSEUDO-A remains sole PASS/DROP authority.
- RSYNC export remains Priority Zero.
- Cross-node rsync is export/hash-continuity verification only.
- Distributed authority is not cleared.
- Remote PASS/DROP authority is not cleared.

---

## Operator Statement

I, Jack Disla, have reviewed the evidence campaigns and governance records listed above. The single-node PH6/CRAM instrument on main_pi is cleared for production operation within the defined scope. OI-01 is descoped. Cross-node rsync transfer to jackjack is cleared only for export/hash-continuity verification. Distributed authority, remote PASS/DROP authority, remote CRAM-A write authority, multi-writer CRAM, Kubernetes CRAM-A storage, Hailo integration, and Lane 2 authority are not proven and are not claimed.
