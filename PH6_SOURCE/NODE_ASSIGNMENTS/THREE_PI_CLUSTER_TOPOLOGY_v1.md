================================================================================
PH6 THREE-PI CLUSTER TOPOLOGY v1
================================================================================
Classification : CANON -- Constitutional Infrastructure
Authority      : FULL
Version        : TPT-1.0
Date           : 2026-05-19
================================================================================

================================================================================
CLUSTER OBJECTIVE
================================================================================

Configure three Raspberry Pi nodes as a distributed PH6 instrument cluster.

Constitutional constraints preserved:
  - Lane 1 decides
  - Lane 2 advises only
  - Pi Zero 2 W watches, relays, and witnesses
  - RSYNC must never be blocked
  - No advisory node may issue PASS/DROP
  - No damaged or experimental node may become authority by accident

================================================================================
NODE ASSIGNMENTS
================================================================================

  Node                  Hostname           Designation               Authority
  --------------------  -----------------  ------------------------  ---------
  Healthy Pi 5          ph6-fastpi         PH6-FC-WORKER             LIMITED
  Broken-PCIe Pi 5      jackjack           PH6-L2-ADVISORY-01        ZERO
  Pi Zero 2 W           ph6-zero-sentinel  PH6-L0.5-SENTINEL-WITNESS ZERO

Note: Pi 3B+ (PH6-L1-AUTHORITY, FULL) is the authority node for this cluster.
It is governed separately in PI3B_PLUS_AUTHORITY_NODE.md.

================================================================================
CANONICAL EXECUTION ORDER
================================================================================

  1. Capture / FAST CRAM           (ph6-fastpi)
  2. PSEUDO-M measurement          (ph6-fastpi or main_pi)
  3. PSEUDO PASS/DROP authority    (main_pi -- Lane 1 only)
  4. CRAM-A / CRAM-R sealing       (main_pi -- Lane 1 only)
  5. SoSo advisory mapping         (jackjack -- Lane 2)
  6. TOK advisory topology         (jackjack -- Lane 2)
  7. Claude/Klaw advisory          (jackjack -- Lane 2)
  8. RSYNC export                  (ph6-fastpi -> storage)
  9. Witness verification          (ph6-zero-sentinel)

Claude/Klaw Terminal is AFTER PSEUDO and after SoSo/TOK advisory products exist.
Claude/Klaw Terminal is NOT in the authority path.

CORRECT:  PSEUDO -> SoSo -> TOK -> Claude/Klaw Advisory
WRONG:    Claude/Klaw -> PSEUDO
WRONG:    Claude/Klaw -> PASS/DROP
WRONG:    Claude/Klaw -> CRAM-A

================================================================================
NETWORK TOPOLOGY
================================================================================

  ph6-fastpi:
    - emits ingest events
    - writes FAST CRAM staging
    - exports evidence and replay artifacts via RSYNC
    - source of authoritative data flows

  jackjack:
    - receives advisory copies from ph6-fastpi (read-only ingest)
    - runs SoSo / TOK / Claude advisory workflows
    - produces advisory-only reports
    - writes only to advisory paths

  ph6-zero-sentinel:
    - monitors heartbeat from both nodes
    - monitors RSYNC export backlog
    - logs witness timestamps
    - alerts on stall or failure
    - receives audit shadow copy from ph6-fastpi (read-only)

RSYNC flows:

  ph6-fastpi:/var/ph6/export/
      -> jackjack:/var/ph6/advisory_ingest/        (advisory copy)

  ph6-fastpi:/var/ph6/audit/
      -> ph6-zero-sentinel:/var/ph6/witness/audit_shadow/  (witness copy)

================================================================================
WRITE PATH GOVERNANCE
================================================================================

ph6-fastpi WRITES:
  /var/ph6/fast-cram/           FAST CRAM staging
  /var/ph6/hotstore/            durable staging buffer
  /var/ph6/export/              RSYNC export source
  /var/ph6/replay/              replay preparation

ph6-fastpi MUST NOT WRITE:
  /var/ph6/cram-a/              authority sealing (main_pi only)
  /var/ph6/audit/               audit chain (main_pi only)

jackjack WRITES:
  /var/ph6/advisory_ingest/     received advisory copies
  /var/ph6/mram-s/advisory/     Claude/Klaw advisory outputs
  /var/ph6/advisory_reports/    advisory reports

jackjack MUST NOT WRITE:
  /var/ph6/cram-a/
  /var/ph6/cram-r/
  /var/ph6/cram-0/
  /var/ph6/audit/
  /etc/ph6/gates.conf
  /etc/ph6/node.conf

ph6-zero-sentinel WRITES:
  /var/ph6/witness/             witness logs and audit shadow
  /var/ph6/sentinel/            sentinel state
  /var/ph6/alerts/              alert log

ph6-zero-sentinel MUST NOT WRITE:
  /var/ph6/cram-a/
  /var/ph6/cram-r/
  /var/ph6/audit/
  /var/ph6/export/              sentinel monitors but never alters

================================================================================
CLAUDE/KLAW TERMINAL PLACEMENT
================================================================================

Install on: jackjack only
Role:       PH6-L2-ADVISORY-CONSOLE

Permitted operations:
  - read PH6 reports
  - summarize validation runs
  - detect drift risks
  - explain SoSo/TOK outputs
  - generate operator recommendations
  - prepare non-authoritative reports

Output paths (advisory only):
  /var/ph6/mram-s/advisory/
  /var/ph6/advisory_reports/

Hard forbidden write paths:
  /var/ph6/cram-a/
  /var/ph6/cram-r/
  /var/ph6/cram-0/
  /var/ph6/audit/
  /etc/ph6/gates.conf
  /etc/ph6/node.conf

Claude/Klaw output is advisory artifact only.
Claude/Klaw output carries ZERO_HASH sentinel in any audit record.
Claude/Klaw may never gate PASS/DROP.
Claude/Klaw may never influence PSEUDO-A verdicts.

================================================================================
SERVICE MODEL
================================================================================

ph6-fastpi services:
  ph6-fast-cram.service
  ph6-ingest.service
  ph6-replay-prep.service
  ph6-rsync-export.service

jackjack services:
  ph6-soso-advisory.service
  ph6-tok-advisory.service
  ph6-claude-advisory.service
  ph6-dashboard.service

ph6-zero-sentinel services:
  ph6-heartbeat-watch.service
  ph6-rsync-sentinel.service
  ph6-witness-timestamp.service
  ph6-node-liveness.service

================================================================================
SSH SETUP
================================================================================

From operator machine or primary node:

  ssh-keygen -t ed25519 -C "ph6-node-link"

Copy keys:
  ssh-copy-id pi@ph6-fastpi
  ssh-copy-id pi@jackjack
  ssh-copy-id pi@ph6-zero-sentinel

Verify:
  ssh pi@ph6-fastpi hostname
  ssh pi@jackjack hostname
  ssh pi@ph6-zero-sentinel hostname

================================================================================
INITIAL VALIDATION COMMANDS
================================================================================

Run on each node:
  hostname
  uname -a
  ip addr
  df -h
  free -h
  vcgencmd measure_temp

Run on jackjack only:
  lspci || true
  dmesg | grep -i pcie || true
  lsusb

Run on ph6-zero-sentinel:
  ping -c 3 ph6-fastpi
  ping -c 3 jackjack

Run from ph6-fastpi (dry-run RSYNC validation):
  rsync -av --dry-run /var/ph6/export/ pi@jackjack:/var/ph6/advisory_ingest/
  rsync -av --dry-run /var/ph6/audit/ pi@ph6-zero-sentinel:/var/ph6/witness/audit_shadow/

================================================================================
FAILURE BEHAVIOR
================================================================================

ph6-fastpi failure:
  - ingest and FAST CRAM stop
  - jackjack advisory continues from last received data
  - ph6-zero-sentinel alerts on heartbeat loss
  - RSYNC export stalls -- sentinel detects and alerts
  - no authority operations on advisory nodes during recovery

jackjack failure:
  - advisory layer goes dark
  - Lane 1 operations unaffected
  - ph6-fastpi continues ingest and export
  - ph6-zero-sentinel alerts on heartbeat loss
  - operator reconnects advisory when node recovers

ph6-zero-sentinel failure:
  - witness logging stops
  - heartbeat monitoring stops
  - sentinel alerts cease
  - Lane 1 and Lane 2 operations continue
  - operator restores sentinel independently

Network partition (ph6-fastpi <-> jackjack):
  - jackjack operates on stale advisory data -- acceptable at ZERO authority
  - ph6-fastpi continues ingest and export -- unaffected
  - partition detected via heartbeat loss

================================================================================
PROMOTION RULES
================================================================================

ph6-fastpi: may be considered for Lane 1 authority promotion only after:
  [ ] explicit governance decision
  [ ] production clearance scope update
  [ ] capability review and certification
  [ ] Pi 3B+ demoted or decommissioned first
  [ ] commit to NODE_ASSIGNMENTS/ and NODE_ROLE_MATRIX update

jackjack: may not be promoted while PCIe is failed.
  If repaired: see README.md Repair Recertification Requirements.
  Even after repair: promotion requires full recertification.

ph6-zero-sentinel: DROP-only Smart Spigot is NOT authority promotion.
  Authority promotion from ZERO to any tier requires full recertification.

================================================================================
GOVERNING DOCTRINE
================================================================================

  The cluster is distributed.
  Authority is not distributed.

  Lane 1 remains protected on main_pi (Pi 3B+).
  Lane 2 remains advisory on jackjack.
  Pi Zero 2 W protects continuity and witnesses export.
  RSYNC remains Priority Zero.

  Hardware Constitutional Segregation:
    jackjack PCIe failure physically enforces Lane 2 containment.
    Pi Zero 2 W hardware class prevents NVMe/authority storage.
    Hardware limitations are constitutional features, not deficits.

================================================================================
END -- THREE-PI CLUSTER TOPOLOGY TPT-1.0
================================================================================
