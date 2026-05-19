================================================================================
PH6 JACKJACK ADVISORY AI INTEGRATION
================================================================================
Classification : CANON -- Node Role Extension
Node           : jackjack
Designation    : PH6-L2-CAN-ADVISORY-01
Version        : JAI-1.0
Status         : ACTIVE
Date           : 2026-05-19
================================================================================

================================================================================
PURPOSE
================================================================================

The broken-PCIe Raspberry Pi 5 node jackjack is designated as the temporary
PH6 advisory AI node until Jetson Nano integration is operational.

This node provides:
  - advisory reasoning
  - telemetry interpretation
  - CAN bus analysis
  - SoSo/TOK augmentation
  - operator assistance
  - validation interpretation
  - replay review
  - drift-risk analysis

This node does NOT participate in authority issuance.

This deployment is temporary but constitutionally bounded.

Migration path:
  When Jetson Nano (PH6-L2-AI-ACCEL) is integrated, advisory AI workloads
  migrate there. jackjack retains CAN telemetry and sentinel relay roles.
  Migration requires explicit governance update -- not automatic.

================================================================================
CORE PRINCIPLE
================================================================================

jackjack acts as an advisory intelligence layer.
It is not an authority layer.

PH6 authority remains exclusively inside:
  - PSEUDO-A
  - Lane 1 deterministic measurement
  - CRAM-A authority path
  - explicit constitutional authority nodes

Claude/Klaw is treated as an interpreter of authority.
It is never the source of authority.

================================================================================
HARDWARE JUSTIFICATION
================================================================================

The broken PCIe subsystem is architecturally beneficial for this role.

Because PCIe/NVMe authority storage is unavailable:
  - authoritative storage is naturally isolated
  - replay authority is naturally isolated
  - AI experimentation is naturally caged
  - advisory compute is separated from deterministic authority

This is Hardware Constitutional Segregation.
The hardware itself reinforces governance boundaries.

CAN HAT operates over GPIO/SPI -- PCIe-independent.
PCIe failure does not materially affect CAN functionality.
jackjack is therefore constitutionally fit for CAN advisory work.

================================================================================
CLAUDE/KLAW TERMINAL ROLE
================================================================================

Canonical designation:  PH6-L2-ADVISORY-CONSOLE

Primary functions:
  - read PH6 reports
  - summarize validation campaigns
  - explain SoSo outputs
  - explain TOK topology
  - correlate CAN telemetry
  - identify drift-risk patterns
  - generate advisory-only recommendations
  - provide operator interaction layer
  - perform replay interpretation
  - perform telemetry synthesis

Optional future functions:
  - CAN anomaly clustering
  - multi-node telemetry correlation
  - replay annotation
  - environmental pattern summaries

================================================================================
CAN BUS RESPONSIBILITIES
================================================================================

jackjack canonical CAN designation:  PH6-L2-CAN-ADVISORY-01

Allowed:
  - CAN frame ingestion
  - CAN frame decoding
  - vehicle telemetry observation
  - sensor-bus advisory analysis
  - CAN correlation against PH6 ingest timelines
  - advisory-only event interpretation

Forbidden:
  - vehicle control authority
  - PASS issuance from CAN data
  - threshold mutation from CAN telemetry
  - autonomous control actions

CAN telemetry is observational only.

================================================================================
EXECUTION ORDER
================================================================================

  1. Capture / FAST CRAM
  2. PSEUDO deterministic measurement
  3. PSEUDO PASS/DROP authority
  4. CRAM-A / CRAM-R handling
  5. SoSo advisory mapping
  6. TOK advisory topology
  7. Claude/Klaw advisory reasoning
  8. RSYNC export / witness verification

Claude/Klaw Terminal exists AFTER deterministic authority.
It is downstream of authority.
It may interpret authority outputs.
It may never generate authority outputs.

CORRECT:  PSEUDO -> SoSo -> TOK -> Claude/Klaw Advisory
WRONG:    Claude/Klaw -> PSEUDO
WRONG:    Claude/Klaw -> PASS/DROP
WRONG:    Claude/Klaw -> CRAM-A

================================================================================
STRUCTURAL AUTHORITY ABSENCE
================================================================================

The following capabilities are structurally absent from jackjack:
  - PASS issuance
  - CRAM-A authority writes
  - sequence issuance
  - audit-chain authority
  - deterministic adjudication
  - threshold governance
  - replay authority sealing

These are not merely forbidden by policy.
There is no lawful architectural path for jackjack to perform them.

================================================================================
ALLOWED WRITE LOCATIONS
================================================================================

Claude/Klaw Terminal output may ONLY be written to:
  /var/ph6/mram-s/advisory/
  /var/ph6/advisory_reports/
  /var/ph6/can_advisory/

Forbidden write destinations:
  /var/ph6/cram-a/
  /var/ph6/cram-r/
  /var/ph6/cram-0/
  /var/ph6/audit/
  /etc/ph6/
  /var/ph6/sequence/

================================================================================
SERVICE MODEL
================================================================================

Active services:
  ph6-soso-advisory.service
  ph6-tok-advisory.service
  ph6-can-telemetry.service
  ph6-claude-advisory.service
  ph6-dashboard.service

Optional future services:
  ph6-can-correlation.service
  ph6-replay-annotation.service

================================================================================
TEMPORARY DEPLOYMENT NOTE
================================================================================

This document governs jackjack as the advisory AI node until Jetson Nano
integration. At that point:

  1. Advisory AI workloads migrate to Jetson Nano
  2. This document is updated: Status = SUPERSEDED
  3. JACKJACK_L2_ADVISORY_NODE.md updated to reflect residual CAN role
  4. JETSON_NANO_ADVISORY_ACCELERATOR.md updated from PLACEHOLDER to ACTIVE
  5. NODE_ROLE_MATRIX updated

Migration requires explicit governance commits.
No advisory AI migration occurs implicitly.

================================================================================
FINAL STATUS
================================================================================

  jackjack:
    operational
    advisory
    CAN-capable
    constitutionally bounded
    structurally non-authoritative

  The cluster remains:
    distributed in function
    centralized in authority

================================================================================
END -- JACKJACK AI ADVISORY INTEGRATION JAI-1.0
================================================================================
