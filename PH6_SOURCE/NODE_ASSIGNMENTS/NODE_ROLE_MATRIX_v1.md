================================================================================
PH6 NODE ROLE MATRIX v1
================================================================================
Classification : CANON -- Constitutional Infrastructure
Authority      : FULL
Version        : NRM-1.0
Last updated   : 2026-05-19
================================================================================

================================================================================
CANONICAL FLEET ASSIGNMENT
================================================================================

  Node                     Designation               Role                          Authority
  -----------------------  ------------------------  ----------------------------  ---------
  Pi 3B+                   PH6-L1-AUTHORITY          Lane 1 Authority Node         FULL
  Pi 5 (healthy NVMe)      PH6-FC-WORKER             FAST CRAM / HOTSTORE          LIMITED
  Pi 5 jackjack (PCIe fail) PH6-L2-ADVISORY-01       Lane 2 Advisory / Sensor      ZERO
  Jetson Nano              PH6-L2-AI-ACCEL (future)  Advisory AI Acceleration      ZERO

================================================================================
AUTHORITY TIER DEFINITIONS
================================================================================

  FULL     Lane 1 operations: PASS/DROP adjudication, audit chain,
           authoritative CRAM-A/CRAM-R sealing, sequence issuance

  LIMITED  FAST CRAM staging, HOTSTORE buffering, replay worker operations.
           No final adjudication. No audit chain authority.

  ZERO     Advisory operations only: Lane 2, SoSo, TOK, sensor fusion,
           telemetry, observability. No authority operations ever.

================================================================================
CONSTITUTIONAL LANE ASSIGNMENT
================================================================================

  Node              Lane F   Lane FC   Lane P   Lane SC   Lane 2   Lane 5
  ----------------  ------   -------   ------   -------   ------   ------
  Pi 3B+            YES      YES       YES      YES       NO*      YES
  Pi 5 (healthy)    YES      YES       NO       NO        NO*      YES
  jackjack          NO       NO        NO       NO        YES      NO**
  Jetson Nano       NO       NO        NO       NO        YES      NO**

  * Lane 2 output may be consumed but not issued with authority
  ** RSYNC authority excluded from ZERO-authority nodes

================================================================================
HARDWARE CONSTITUTIONAL SEGREGATION STATUS
================================================================================

  jackjack PCIe failure:
    - physically prevents NVMe attachment
    - physically prevents Hailo / Coral PCIe attachment
    - hardware enforces Lane 2 containment
    - this is a constitutional advantage, not merely a limitation

================================================================================
MATRIX GOVERNANCE RULES
================================================================================

1. This matrix is updated only by explicit reassignment commits.
2. No implicit authority changes -- every change requires a document update.
3. Node addition requires a corresponding assignment document before matrix entry.
4. Degraded state changes require documentation before matrix update.
5. Matrix version increments on any structural change.

================================================================================
OPEN ITEMS
================================================================================

  VALIDATION PENDING -- jackjack:
    [ ] PCIe failure scope confirmed (lspci + dmesg)
    [ ] USB stability validated under load
    [ ] Thermal stability validated (stress-ng 300s)

  FUTURE -- Jetson Nano:
    [ ] Node not yet integrated
    [ ] Assignment document is PLACEHOLDER -- not operational

================================================================================
END -- NODE ROLE MATRIX NRM-1.0
================================================================================
