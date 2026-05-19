================================================================================
PH6 NODE ASSIGNMENTS -- FLEET GOVERNANCE RULES
================================================================================
Classification : CANON -- Constitutional Infrastructure
Authority      : FULL
Version        : FGR-1.0
================================================================================

================================================================================
PURPOSE
================================================================================

Node identity, authority scope, hardware degradation state, and reassignment
policy are constitutional infrastructure -- not temporary operational notes.

This directory is the canonical registry for all PH6 fleet node assignments.

Every node in the PH6 fleet must have a corresponding assignment document here.
No node may operate in an authority role without a registered assignment.

================================================================================
NODE IDENTITY PERMANENCE
================================================================================

A node's identity is its hardware -- not its hostname, IP address, or role.

Identity is established at first registration and survives:
  - hostname changes
  - IP reassignment
  - OS reinstallation
  - role changes
  - degradation events

Identity must be recorded as:
  - hardware model
  - serial number or MAC address (where available)
  - first registration date
  - canonical node designation

Hostnames are advisory labels. Hardware identity is canonical.

================================================================================
AUTHORITY TIERS
================================================================================

  TIER 0  FULL          Lane 1 authority -- PASS/DROP -- audit chain issuance
  TIER 1  LIMITED       FAST CRAM worker -- no final adjudication
  TIER 2  ZERO          Advisory only -- Lane 2 -- no authority operations

Authority tier is assigned at registration.
Authority tier change requires EXPLICIT REASSIGNMENT (see below).
No implicit promotion ever occurs.

================================================================================
AUTHORITY REASSIGNMENT RULES
================================================================================

Promotion (ZERO -> LIMITED -> FULL):
  - requires explicit governance document update
  - requires hardware capability review
  - requires storage integrity validation
  - requires thermal stability validation
  - requires PCIe / storage path verification (if applicable)
  - requires commit to NODE_ASSIGNMENTS/ with updated role document
  - requires update to NODE_ROLE_MATRIX

Demotion (FULL -> LIMITED -> ZERO):
  - may occur immediately on hardware failure detection
  - must be documented in node assignment file
  - must be reflected in NODE_ROLE_MATRIX
  - must not suppress ongoing operations -- graceful handoff required

================================================================================
DEGRADED NODE HANDLING
================================================================================

A degraded node is NOT a dead node.

Degraded state is formally defined as:
  - node boots and reaches operational state
  - one or more hardware subsystems are non-functional
  - remaining subsystems are operational

Degraded nodes:
  - retain their authority tier if remaining capabilities support it
  - may be reassigned to a lower tier based on capability review
  - must have degradation state documented in their assignment file
  - must not silently re-acquire authority responsibilities after repair

Degraded state is CONSTITUTIONAL -- not a failure of governance.
PH6 explicitly permits degraded nodes at TIER 2 (ZERO authority).

================================================================================
HARDWARE CONSTITUTIONAL SEGREGATION
================================================================================

Hardware limitations may enforce governance boundaries.

This is architecturally desirable.

When a node's hardware is incapable of supporting authority operations:
  - advisory hardware physically cannot become authority accidentally
  - hardware failure cages the node within its constitutional tier
  - authority isolation is enforced at the physical layer

Hardware Constitutional Segregation is a valid and preferred isolation model.
It is stronger than software-only isolation in degraded conditions.

================================================================================
REPAIR RECERTIFICATION REQUIREMENTS
================================================================================

If a degraded node is repaired:

  1. Hardware repair must be documented
  2. Full capability review required -- do not assume pre-failure capability
  3. Storage integrity validation required (if storage path affected)
  4. Thermal stability test required (stress-ng + temp monitoring)
  5. PCIe / subsystem validation required (lspci + dmesg review)
  6. Node assignment document must be updated
  7. NODE_ROLE_MATRIX must be updated
  8. Commit required before node may resume previous role

No implicit promotion after repair.
Recertification is explicit and committed.

================================================================================
HOSTNAME GOVERNANCE
================================================================================

Hostnames must not imply authority the node does not possess.

PROHIBITED hostname patterns for TIER 2 nodes:
  - authority
  - cram-a
  - primary
  - master
  - producer
  - sealer

ACCEPTABLE hostname patterns:
  - l2 suffix (e.g. jackjack-l2)
  - advisory prefix/suffix (e.g. ph6-advisory-01)
  - functional label (e.g. ph6-soso-01, ph6-tok-01)

Hostname changes do not alter constitutional assignment.
Constitutional assignment lives in this directory -- not in DNS or /etc/hostname.

================================================================================
REPLACEMENT PROCEDURE
================================================================================

When a node is replaced (new hardware):

  1. Old node document updated: status = DECOMMISSIONED
  2. New node document created with new hardware identity
  3. Authority tier explicitly re-assigned -- not inherited
  4. If replacing an authority node: full recertification required
  5. NODE_ROLE_MATRIX updated

No authority inheritance between hardware units.
A replacement Pi 5 is not automatically a FAST CRAM worker.
Authority is granted -- never transferred.

================================================================================
FLEET DOCUMENT INDEX
================================================================================

  NODE_ROLE_MATRIX_v1.md                  Fleet role overview
  FLEET_CONSTITUTION_v1.md                Constitutional node governance
  PI3B_PLUS_AUTHORITY_NODE.md             Lane 1 authority node
  PI5_FAST_CRAM_WORKER.md                 FAST CRAM / HOTSTORE / replay worker
  JACKJACK_L2_ADVISORY_NODE.md            Lane 2 advisory (broken PCIe Pi 5)
  JETSON_NANO_ADVISORY_ACCELERATOR.md     Future advisory AI acceleration

================================================================================
END -- FLEET GOVERNANCE RULES FGR-1.0
================================================================================
