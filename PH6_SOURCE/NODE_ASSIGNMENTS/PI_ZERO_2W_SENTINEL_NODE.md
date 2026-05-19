================================================================================
PH6 NODE ASSIGNMENT -- PI ZERO 2W SENTINEL / WITNESS NODE
================================================================================
Classification : CANON -- Constitutional Infrastructure
Node           : Raspberry Pi Zero 2 W
Designation    : PH6-L0.5-SENTINEL-WITNESS
Hostname       : ph6-zero-sentinel
Authority      : ZERO (DROP-only prefilter if explicitly configured)
Status         : ACTIVE BUILD PLAN
Version        : PIZ-1.0
Date           : 2026-05-19
================================================================================

================================================================================
NODE IDENTITY
================================================================================

Hardware:      Raspberry Pi Zero 2 W
Designation:   PH6-L0.5-SENTINEL-WITNESS
Hostname:      ph6-zero-sentinel
Role:          RSYNC Sentinel / Watchdog / Distributed Witness

================================================================================
AUTHORITY TIER
================================================================================

  TIER 2 -- ZERO

  With one bounded exception: DROP-only Smart Spigot prefilter.

  DROP-only prefilter:
    - may issue DROP on clearly invalid frames before PSEUDO
    - may NEVER issue PASS
    - may NEVER promote a frame toward CRAM-A
    - explicit configuration required -- not active by default
    - prefilter decisions must be logged and auditable
    - prefilter must not suppress loss

  PASS authority: NEVER
  CRAM-A authority: NEVER
  Audit chain authority: NEVER

================================================================================
PRIMARY DUTIES
================================================================================

  - RSYNC Sentinel: monitor export process, detect stalls
  - Watchdog: monitor node liveness for ph6-fastpi and jackjack
  - Heartbeat monitor: receive and log heartbeat signals from both nodes
  - Export backlog monitor: alert when export queue exceeds thresholds
  - Telemetry collector: basic system telemetry from cluster nodes
  - Distributed timestamp witness: independent timestamp record
  - Node liveness monitor: detect node failure or network partition
  - Emergency alert node: notify operator on failure conditions
  - Optional DROP-only Smart Spigot: bounded prefilter (explicit config only)

================================================================================
ALLOWED RESPONSIBILITIES
================================================================================

  - receive heartbeat signals
  - monitor RSYNC export progress
  - log witness timestamps (independent clock source)
  - alert on stall or failure conditions
  - collect and relay basic telemetry
  - maintain node liveness state
  - issue DROP-only prefilter verdicts (if explicitly configured)
  - write to: /var/ph6/witness/
  - write to: /var/ph6/sentinel/
  - write to: /var/ph6/alerts/

================================================================================
FORBIDDEN RESPONSIBILITIES
================================================================================

  - PASS authority (absolute -- no exception)
  - CRAM-A writes
  - audit-chain authority
  - schema authority
  - final adjudication authority
  - AI inference authority
  - advisory authority (not an advisory node -- it is a witness)
  - blocking RSYNC
  - writing to: /var/ph6/cram-a/
  - writing to: /var/ph6/cram-r/
  - writing to: /var/ph6/audit/
  - writing to: /var/ph6/export/ (read-only monitoring only)
  - altering evidence in transit

================================================================================
SERVICES
================================================================================

  ph6-heartbeat-watch.service       monitor heartbeat from ph6-fastpi + jackjack
  ph6-rsync-sentinel.service        monitor RSYNC export progress + stall detection
  ph6-witness-timestamp.service     log independent timestamps
  ph6-node-liveness.service         detect node failure / network partition

================================================================================
NETWORK ROLE
================================================================================

Receives from:
  ph6-fastpi:/var/ph6/audit/ -> /var/ph6/witness/audit_shadow/ (shadow copy)

Monitors (read-only):
  ph6-fastpi: RSYNC export queue + heartbeat
  jackjack: heartbeat + advisory health

Does NOT write back to ph6-fastpi or jackjack.
Does NOT alter any data it receives.
Witness copies are forensic shadow -- not authoritative.

================================================================================
HARDWARE PROFILE
================================================================================

Hardware:      Raspberry Pi Zero 2 W
CPU:           ARM Cortex-A53 quad-core 1GHz
RAM:           512MB
Storage:       SD card (witness + sentinel logs only)
Network:       WiFi or USB-OTG Ethernet
PCIe:          N/A
NVMe:          N/A (not required for sentinel role)

Hardware limitations are appropriate for sentinel role:
  - low power consumption suits always-on watchdog function
  - no PCIe / NVMe removes any possibility of authority storage
  - Hardware Constitutional Segregation enforced by hardware class

================================================================================
CANONICAL AUTHORITY RULE
================================================================================

Pi Zero 2 W may:
  - monitor
  - witness
  - alert
  - DROP-only prefilter (if explicitly configured)

Pi Zero 2 W may NEVER:
  - issue PASS
  - promote a frame toward CRAM-A
  - seal evidence
  - issue sequence numbers
  - alter thresholds
  - write CRAM-A
  - write audit chain entries

PASS authority is structurally absent -- not merely forbidden by policy.
There is no code path on this node that issues PASS.

================================================================================
DROP-ONLY SMART SPIGOT -- GOVERNANCE
================================================================================

The DROP-only prefilter is an OPTIONAL bounded authority function.

Activation requirements:
  [ ] explicit configuration in /etc/ph6/node.conf
  [ ] ph6-gates.conf entry confirming spigot enabled
  [ ] drop criteria defined as deterministic rules (no probabilistic gates)
  [ ] drop log path configured and writable
  [ ] operator review of drop criteria before activation

Spigot invariants:
  - DROP verdicts are logged with frame_id + reason + timestamp
  - DROP log is auditable (human-readable)
  - PASS is structurally impossible -- spigot has no PASS code path
  - Spigot criteria may not be changed at runtime
  - Spigot may not suppress loss -- every DROP is recorded

Failure behavior:
  - If spigot service fails: frames pass through unfiltered (fail-open)
  - Fail-open is constitutional -- false-safe is better than silent DROP
  - Spigot failure is logged and alerted

================================================================================
INITIAL VALIDATION COMMANDS
================================================================================

Run on ph6-zero-sentinel:
  hostname
  uname -a
  ip addr
  df -h
  free -h
  vcgencmd measure_temp

Run network connectivity:
  ping -c 3 ph6-fastpi
  ping -c 3 jackjack

================================================================================
REASSIGNMENT GOVERNANCE RULE
================================================================================

This node may not be promoted to authority tier without:
  - explicit governance decision and commit
  - capability review for target tier
  - NODE_ROLE_MATRIX update

The DROP-only Smart Spigot does not constitute authority promotion.
It is a bounded DROP-only prefilter with ZERO PASS authority.

See README.md -- Authority Reassignment Rules.

================================================================================
END -- PI ZERO 2W SENTINEL NODE ASSIGNMENT PIZ-1.0
================================================================================
