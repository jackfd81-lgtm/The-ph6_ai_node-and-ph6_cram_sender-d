================================================================================
PH6 NODE ASSIGNMENT -- PI 5 FAST CRAM WORKER
================================================================================
Classification : CANON -- Constitutional Infrastructure
Node           : Pi 5 (healthy NVMe)
Designation    : PH6-FC-WORKER
Authority      : LIMITED
Status         : OPERATIONAL
Version        : PI5-1.0
Date           : 2026-05-19
================================================================================

================================================================================
NODE IDENTITY
================================================================================

Hardware:      Raspberry Pi 5 (PCIe subsystem intact)
Designation:   PH6-FC-WORKER
Role:          FAST CRAM / HOTSTORE / Replay Worker

Note: This document covers the HEALTHY Pi 5 (NVMe operational).
For the degraded Pi 5 (broken PCIe), see JACKJACK_L2_ADVISORY_NODE.md.

================================================================================
AUTHORITY TIER
================================================================================

  TIER 1 -- LIMITED

  This node supports FAST CRAM staging and HOTSTORE operations.
  It does NOT issue PASS/DROP verdicts.
  It does NOT seal CRAM-A / CRAM-R with authority.
  It does NOT issue audit chain sequences.

================================================================================
CONSTITUTIONAL ROLE
================================================================================

This node is the FAST CRAM acceleration layer and replay worker.

It supports:
  - high-speed FAST CRAM staging (Lane FC)
  - HOTSTORE buffering
  - replay worker operations
  - RSYNC export (Lane 5, as worker -- not authority origin)

It does NOT support:
  - PSEUDO-A adjudication
  - SLOW CRAM authority sealing
  - audit chain issuance
  - sequence authority

================================================================================
ALLOWED RESPONSIBILITIES
================================================================================

  - Lane F: FAST Capture (sensor ingestion)
  - Lane FC: FAST CRAM staging (PRE-AUTHORITY -- PENDING_SEAL)
  - HOTSTORE: high-speed durable buffer
  - Replay: reconstruction from sealed evidence
  - Lane 5: RSYNC export relay

================================================================================
FORBIDDEN RESPONSIBILITIES
================================================================================

  - PASS/DROP adjudication
  - SLOW CRAM authority sealing
  - audit chain issuance
  - event_seq authority
  - authority_hash issuance
  - schema authority
  - lane promotion authority

================================================================================
HARDWARE STATE
================================================================================

  CPU/RAM:  OPERATIONAL
  PCIe:     OPERATIONAL
  NVMe:     OPERATIONAL (attached via PCIe)
  Storage:  NVMe (HOTSTORE / staging)
  Network:  OPERATIONAL

================================================================================
HARDWARE ADVANTAGE NOTE
================================================================================

The healthy Pi 5 PCIe + NVMe combination provides:
  - high-throughput staging capacity
  - low-latency FAST CRAM buffering
  - replay-capable durable storage
  - HOTSTORE performance above SD-card nodes

These capabilities make it the correct FAST CRAM acceleration node.

================================================================================
REASSIGNMENT GOVERNANCE RULE
================================================================================

If PCIe or NVMe degrades on this node:
  - node must be demoted to ZERO authority immediately
  - see JACKJACK_L2_ADVISORY_NODE.md as the reference degradation case
  - demotion must be documented and committed
  - NODE_ROLE_MATRIX must be updated before operations continue

No silent degraded operation at LIMITED tier with failed storage path.

================================================================================
END -- PI 5 FAST CRAM WORKER ASSIGNMENT PI5-1.0
================================================================================
