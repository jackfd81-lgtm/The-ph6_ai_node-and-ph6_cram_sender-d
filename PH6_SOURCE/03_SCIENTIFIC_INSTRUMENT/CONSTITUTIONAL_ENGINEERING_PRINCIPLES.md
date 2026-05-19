================================================================================
PH6 CONSTITUTIONAL ENGINEERING PRINCIPLES
================================================================================
Classification : CANON -- Book II / Book III
Authority      : FULL
Version        : CEP-1.0
Date           : 2026-05-19
================================================================================

================================================================================
PREAMBLE
================================================================================

These principles govern how PH6 guarantees are implemented.

They are engineering principles, not documentation principles.
They apply to runtime design, hardware selection, schema design,
fleet topology, audit architecture, and governance decisions.

The distinction these principles encode:

  STRUCTURAL GUARANTEE   capability is architecturally impossible
  POLICY GUARANTEE       capability exists but rules forbid it

PH6 prefers structural guarantees wherever achievable.

================================================================================
PRINCIPLE 1 -- STRUCTURAL BEFORE POLICY
================================================================================

When a new guarantee is required, first ask:
  can this be structural?

If yes:
  make it structural.

Policy prohibition is used only when structural enforcement is
genuinely impossible.

Reason:
  Structural guarantees survive:
    - operator turnover
    - configuration drift
    - system upgrades
    - documentation decay
    - adversarial conditions
    - partial system knowledge

  Policy guarantees depend on:
    - correct operator behavior
    - accurate documentation
    - continuous enforcement
    - awareness of the rule

  Structural guarantees are stronger under degradation.
  That is the correct direction for forensic instrumentation.

================================================================================
STRUCTURAL GUARANTEE TABLE
================================================================================

Current PH6 guarantees and their structural mechanisms:

  Guarantee                      Structural Mechanism
  -----------------------------  ------------------------------------------
  Lane 1 authority isolation     Dedicated authority node (Pi 3B+)
  AI non-authority               Tier 2 constitutional lock -- no cert path
  Jetson non-authority           No recertification path exists -- permanent
  Pi Zero no PASS                Missing code path -- structurally absent
  jackjack no authority storage  Broken PCIe / no NVMe path
  RSYNC continuity               Independent sentinel witness node
  Advisory isolation             Separate hardware class
  Replay segregation             Tiered nodes -- no cross-tier authority path
  CAN telemetry non-authority    GPIO/SPI path only -- no authority storage
  Claude/Klaw non-authority      Write paths physically restricted to advisory dirs

================================================================================
PRINCIPLE 2 -- HARDWARE CLASS PARTICIPATES IN GOVERNANCE
================================================================================

Hardware limitations are governance features, not deficits.

When hardware cannot physically support an authority operation:
  - that incapability is constitutionally beneficial
  - it enforces governance at the physical layer
  - it is stronger than software-only isolation

Hardware Constitutional Segregation examples in PH6:

  jackjack (broken PCIe):
    - physically cannot attach NVMe
    - physically cannot host Hailo / Coral PCIe
    - naturally caged away from authority storage
    - CAN HAT (GPIO/SPI) is unaffected -- correct subset survives

  Pi Zero 2 W:
    - no PCIe, no NVMe
    - hardware class prevents any path to authority storage
    - DROP-only spigot is the maximum bounded authority function

  Jetson Nano (GPU class):
    - GPU compute is probabilistic / non-deterministic by nature
    - non-determinism disqualifies it from deterministic authority
    - hardware nature enforces advisory-only classification

Rule: when selecting hardware for a PH6 role, prefer hardware whose
physical capabilities match exactly the authority tier required.
Over-capable hardware at advisory tier is a governance risk.

================================================================================
PRINCIPLE 3 -- AUTHORITY IS CENTRALIZED, FUNCTION IS DISTRIBUTED
================================================================================

PH6 distributes function across nodes.
PH6 does NOT distribute authority.

Authority remains:
  - on a single Lane 1 node
  - inside PSEUDO-A
  - inside SLOW CRAM seal path
  - inside the audit chain

Distribution of advisory function does not dilute authority.
Distribution of sensing and ingest does not dilute authority.
Distribution of telemetry and analysis does not dilute authority.

The cluster is distributed in function.
The cluster is centralized in authority.

Rule: any design that requires authority to move across nodes requires
a new constitutional analysis and explicit production clearance update.
No implicit authority distribution.

================================================================================
PRINCIPLE 4 -- ADVISORY AI IS DOWNSTREAM OF DETERMINISTIC AUTHORITY
================================================================================

AI advisory systems are interpreters of authority outputs.
They are never sources of authority.

Correct placement:
  PSEUDO -> SoSo -> TOK -> Claude/Klaw Advisory

Forbidden placement:
  Claude/Klaw -> PSEUDO
  Claude/Klaw -> PASS/DROP
  Claude/Klaw -> CRAM-A

Advisory AI receives:
  - sealed evidence summaries
  - SoSo advisory products
  - TOK topology products
  - operator queries

Advisory AI produces:
  - advisory reports (ZERO_HASH sentinel in any audit record)
  - operator recommendations
  - drift-risk analysis
  - replay interpretation

Advisory AI does NOT produce:
  - PASS/DROP verdicts
  - authority markers
  - audit chain entries with Lane 1 authority_hash
  - schema changes

Rule: any proposed use of AI output that would affect Lane P or Lane SC
is a constitutional violation. AI outputs are advisory artifacts only.

================================================================================
PRINCIPLE 5 -- TEMPORARY DEPLOYMENTS MUST CARRY MIGRATION PATHS
================================================================================

A constitutionally bounded temporary deployment is legitimate.

Requirements for temporary deployments:
  - explicit TEMPORARY designation in governance document
  - defined migration trigger condition
  - defined successor node or architecture
  - migration procedure recorded before deployment begins
  - no implicit promotion at migration time

Jackjack advisory AI is the reference implementation of this principle:
  - designated temporary until Jetson Nano integration
  - migration trigger: Jetson Nano PLACEHOLDER -> ACTIVE
  - migration procedure documented in JAI-1.0
  - jackjack retains CAN telemetry role after migration

Rule: "temporary" without a migration path is a governance debt.
Temporary deployments must have documented exit conditions.

================================================================================
PRINCIPLE 6 -- PROMOTION REQUIRES EXPLICIT COMMITS
================================================================================

No node may change constitutional role without:
  - explicit human approval
  - committed node-assignment update
  - NODE_ROLE_MATRIX update
  - governance PASS from pre-commit scan

Hardware repair does not implicitly restore authority.
Capability improvement does not implicitly raise tier.
Operator intention does not substitute for committed governance update.

Rule: if a tier change is not in a commit, it did not happen constitutionally.

================================================================================
SUMMARY TABLE
================================================================================

  Principle   Rule
  ---------   -----------------------------------------------------------------
  P1          Structural before policy -- make it impossible, not just forbidden
  P2          Hardware class participates in governance -- use limitations
  P3          Centralized authority, distributed function -- never split authority
  P4          AI is downstream of deterministic authority -- never upstream
  P5          Temporary deployments need documented migration paths
  P6          Promotion requires explicit commits -- no implicit tier change

================================================================================
CANONICAL STATEMENT
================================================================================

  Hardware enforces where code cannot.
  Structure enforces where policy cannot.
  Authority is centralized where function is distributed.
  AI interprets truth. AI does not produce truth.

================================================================================
END -- CONSTITUTIONAL ENGINEERING PRINCIPLES CEP-1.0
================================================================================
