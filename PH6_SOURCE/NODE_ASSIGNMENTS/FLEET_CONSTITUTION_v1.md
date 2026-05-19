================================================================================
PH6 FLEET CONSTITUTION v1
================================================================================
Classification : CANON -- Constitutional Infrastructure
Authority      : FULL
Version        : FC-1.0
Date           : 2026-05-19
================================================================================

================================================================================
PREAMBLE
================================================================================

PH6 is a deterministic scientific instrument distributed across physical nodes.

Each node has a constitutional role.
Each role has defined authority boundaries.
Authority boundaries are enforced at the hardware, software, and governance layers
simultaneously.

This document is the constitutional foundation for all fleet governance.
Node assignment documents derive from this constitution.
Implementation derives from node assignments.
Nothing in implementation may override fleet constitution.

================================================================================
NODE CLASSES
================================================================================

CLASS 1 -- AUTHORITY NODE
  Lane 1 operations: PSEUDO-A adjudication, SLOW CRAM sealing,
  audit chain issuance, sequence authority.
  Single node per production scope.
  Simpler hardware preferred for auditability and thermal stability.

CLASS 2 -- FAST CRAM WORKER
  FAST CRAM staging, HOTSTORE buffering, replay operations.
  No adjudication authority. No sealing authority.
  High-throughput storage path required (NVMe via PCIe preferred).

CLASS 3 -- ADVISORY NODE
  Lane 2 operations only. Authority ZERO.
  May be degraded hardware, AI accelerators, sensor fusion nodes.
  Hardware Constitutional Segregation may enforce ZERO authority physically.

CLASS 4 -- FUTURE / PLACEHOLDER
  Defined before integration.
  Governance recorded before hardware is connected.
  Prevents authority creep at integration time.

================================================================================
AUTHORITY TIERS
================================================================================

  TIER 0  FULL     CLASS 1 only
  TIER 1  LIMITED  CLASS 2 only
  TIER 2  ZERO     CLASS 3 and CLASS 4

Authority tiers are not a hierarchy of trust.
They are explicit capability boundaries.
ZERO authority is not inferior -- it is correct for its class.

================================================================================
HARDWARE TRUST MODEL
================================================================================

Hardware trust is NOT assumed.

Trust is established through:
  - capability review
  - storage integrity validation
  - thermal stability validation
  - explicit governance assignment

Hardware trust does NOT transfer:
  - replacement hardware is not trusted by default
  - repaired hardware requires recertification
  - borrowed or temporary hardware requires explicit temporary assignment

Hardware Constitutional Segregation:
  When hardware is physically incapable of supporting authority operations,
  that hardware incapability is a governance feature, not a deficit.
  Damaged PCIe, missing NVMe, absent accelerators -- these may enforce
  constitutional boundaries more reliably than software controls alone.

================================================================================
PROMOTION AND DEMOTION RULES
================================================================================

PROMOTION (lower tier -> higher tier):
  - Requires explicit governance decision
  - Requires capability review for target tier
  - Requires commit to NODE_ASSIGNMENTS/
  - Requires NODE_ROLE_MATRIX update
  - Requires production clearance review if scope changes
  - No implicit promotion ever

DEMOTION (higher tier -> lower tier):
  - May occur immediately on capability failure detection
  - Must be documented within the same operational session
  - Must not silently continue authority operations during transition
  - Graceful handoff of in-progress authority operations required
  - NODE_ROLE_MATRIX update required before next session

LATERAL TRANSFER (same tier, different role):
  - Requires explicit governance document update
  - Requires NODE_ROLE_MATRIX update
  - No capability review required if tier is unchanged

================================================================================
DEGRADED STATE GOVERNANCE
================================================================================

A degraded node is constitutionally valid.

Degraded state classification:
  - node reaches operational state (boots, logins functional)
  - one or more hardware subsystems non-functional
  - remaining subsystems operational

Degraded state handling:
  - capability assessment determines appropriate tier
  - if remaining capabilities support current tier: tier retained
  - if remaining capabilities cannot support current tier: demotion required
  - degraded state documented in node assignment file

Degraded nodes at TIER 2 (ZERO):
  - are constitutionally fully valid
  - contribute advisory, sensor fusion, telemetry, replay analysis
  - do not require repair to remain operationally useful
  - must not be silently re-promoted after self-repair

================================================================================
REPLACEMENT PROCEDURE
================================================================================

Step 1: Decommission old node
  - Update old node assignment document: STATUS = DECOMMISSIONED
  - Record decommission date and reason
  - Commit

Step 2: Register new node
  - Create new node assignment document
  - Record hardware identity (model, serial/MAC, first registration date)
  - Assign designation and tier explicitly
  - Commit

Step 3: Validate new node
  - Capability review appropriate to target tier
  - Storage validation if TIER 1 or TIER 0
  - Thermal validation
  - Commit validation results

Step 4: Activate
  - Update NODE_ROLE_MATRIX
  - Commit

Authority is never inherited. A replacement node starts without tier.

================================================================================
REPAIR RECERTIFICATION
================================================================================

Hardware repair does not restore authority automatically.

Required for any repaired node seeking tier restoration:

  [ ] Document what was repaired and when
  [ ] Hardware capability review for target tier
  [ ] Storage integrity validation (if storage path involved)
  [ ] Thermal stability test (stress-ng 300s + temp monitoring)
  [ ] Subsystem validation (lspci + dmesg for PCIe repairs)
  [ ] Update node assignment document
  [ ] Update NODE_ROLE_MATRIX
  [ ] Commit before operating at restored tier

================================================================================
MULTI-NODE AUTHORITY SAFETY
================================================================================

At no time may two nodes simultaneously hold TIER 0 authority.

If a replacement TIER 0 node is being commissioned:
  - old TIER 0 node must be demoted before new node is promoted
  - transition must be explicit and committed
  - no authority gap is permitted -- sequence authority must be continuous

Split-brain authority (two TIER 0 nodes) is a constitutional violation.

================================================================================
FLEET CONSTITUTION AMENDMENT
================================================================================

This constitution may be amended.

Amendment requirements:
  - version increment (FC-1.0 -> FC-1.1 -> FC-2.0 etc.)
  - explicit rationale documented in this file
  - governance commit
  - NODE_ASSIGNMENTS/README.md reviewed for consistency

Amendments may not reduce existing authority protections retroactively.
Amendments may not grant TIER 0 to CLASS 3 or CLASS 4 nodes.

================================================================================
CANONICAL STATEMENT
================================================================================

  Hardware determines capability.
  Governance determines authority.
  Constitution determines the boundary between them.
  No node may self-promote across that boundary.

================================================================================
END -- FLEET CONSTITUTION FC-1.0
================================================================================
