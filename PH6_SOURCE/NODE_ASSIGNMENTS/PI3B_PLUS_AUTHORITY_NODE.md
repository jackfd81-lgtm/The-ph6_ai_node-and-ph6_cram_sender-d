================================================================================
PH6 NODE ASSIGNMENT -- PI 3B+ AUTHORITY NODE
================================================================================
Classification : CANON -- Constitutional Infrastructure
Node           : Pi 3B+ (main_pi)
Designation    : PH6-L1-AUTHORITY
Authority      : FULL
Status         : OPERATIONAL
Version        : PI3-1.0
Date           : 2026-05-19
================================================================================

================================================================================
NODE IDENTITY
================================================================================

Hardware:      Raspberry Pi 3B+
Designation:   PH6-L1-AUTHORITY
Role:          Lane 1 Authority Node

================================================================================
AUTHORITY TIER
================================================================================

  TIER 0 -- FULL

  This node is the sole Lane 1 authority node in the current single-node
  production clearance scope (PH6-PROD-CLEAR-2026-05-18-001).

================================================================================
CONSTITUTIONAL ROLE
================================================================================

This node is the authoritative source for:
  - PSEUDO-A adjudication (PASS/DROP)
  - SLOW CRAM sealing (CRAM-A / CRAM-R)
  - audit chain issuance (event_seq + authority_hash)
  - authoritative BLAKE2b-256 markers
  - RSYNC export sovereignty

================================================================================
ALLOWED RESPONSIBILITIES
================================================================================

  - Lane F: FAST Capture
  - Lane FC: FAST CRAM staging
  - Lane P: PSEUDO-M measurement + PSEUDO-A adjudication
  - Lane SC: SLOW CRAM atomic sealing
  - Lane 5: RSYNC export
  - audit chain maintenance
  - sequence issuance (event_seq, monotonic)

================================================================================
FORBIDDEN RESPONSIBILITIES
================================================================================

  - Hailo / PCIe AI acceleration (not cleared -- see production clearance seal)
  - distributed authority operations (not cleared for current scope)
  - Lane 2 authority (Lane 2 is ZERO authority on all nodes)

================================================================================
PRODUCTION CLEARANCE SCOPE
================================================================================

Single-node production clearance declared 2026-05-18.
Seal: 1be60d06b4

Scope:
  - main_pi single-node operation
  - RSYNC export to USB3 NVMe (pending GAP resolution)
  - Lane 1 authority operations only

Not cleared:
  - Hailo acceleration
  - distributed multi-node authority
  - Lane 2 authority operations

See: PH6_SOURCE/GOVERNANCE/PH6_PRODUCTION_CLEARANCE_SEAL_2026-05-18.md

================================================================================
HARDWARE STATE
================================================================================

  CPU/RAM:  OPERATIONAL
  Storage:  SD card (authoritative -- single-node scope)
  Network:  OPERATIONAL
  USB:      OPERATIONAL
  PCIe:     N/A (Pi 3B+ does not have PCIe)

================================================================================
REASSIGNMENT GOVERNANCE RULE
================================================================================

If this node is replaced or upgraded:
  - full recertification required
  - authority is NOT transferred to replacement hardware
  - replacement node must be registered and recertified explicitly
  - production clearance scope must be reviewed and re-declared

See README.md -- Replacement Procedure.

================================================================================
END -- PI 3B+ AUTHORITY NODE ASSIGNMENT PI3-1.0
================================================================================
