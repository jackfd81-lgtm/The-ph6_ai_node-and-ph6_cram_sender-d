================================================================================
PH6 CLUSTER DEPLOYMENT CHECKLIST
================================================================================
Version  : DCL-1.0
Date     : 2026-05-19
Status   : ACTIVE
================================================================================

Update this file as deployment progresses.
Each item: [ ] = pending, [x] = complete, [!] = blocked/issue.

================================================================================
PHASE 0 -- GOVERNANCE (COMPLETE)
================================================================================

[x] Fleet constitution committed
[x] Node assignment documents committed
[x] jackjack L2 advisory integration (JAI-1.0) committed
[x] Constitutional engineering principles (CEP-1.0) committed
[x] DGD-1.1 Principle 7 committed
[x] Claude Terminal preload v1.0 committed
[x] All canon pushed to GitHub (ee71bec100)

================================================================================
PHASE 1 -- PH6-FASTPI (Healthy Pi 5)
================================================================================

Node: ph6-fastpi | Tier 1 FAST CRAM Worker

[ ] OS installed (Raspberry Pi OS Lite 64-bit or Debian 13)
[ ] Hostname set to ph6-fastpi
[ ] SSH enabled and reachable from main_pi
[ ] System updated (apt upgrade)
[ ] Dependencies installed (python3, git, rsync, stress-ng, can-utils)
[ ] PH6 directory structure created (/var/ph6/fast-cram, hotstore, export, replay)
[ ] /etc/ph6/node.conf written (PH6-FC-WORKER)
[ ] NVMe detected and mountable (lsblk | grep nvme)
[ ] Thermal validation passed (stress-ng 300s + vcgencmd measure_temp)
[ ] Node reachable via SSH key from main_pi

Script: ph6_fastpi_setup.sh (run as root on ph6-fastpi)

================================================================================
PHASE 2 -- SSH CLUSTER CONNECTIVITY
================================================================================

[ ] ed25519 key generated on main_pi (or operator node)
[ ] Key distributed to ph6-fastpi
[ ] Key distributed to jackjack
[ ] Key distributed to ph6-zero-sentinel
[ ] ssh pi@ph6-fastpi hostname -- PASS
[ ] ssh pi@jackjack hostname -- PASS
[ ] ssh pi@ph6-zero-sentinel hostname -- PASS

Script: ph6_cluster_ssh_setup.sh (run from main_pi)

================================================================================
PHASE 3 -- JACKJACK CAN HAT VALIDATION
================================================================================

Node: jackjack | PH6-L2-CAN-ADVISORY-01

[ ] CAN HAT physically installed (GPIO/SPI)
[ ] SPI enabled in /boot/config.txt (or raspi-config)
[ ] dtoverlay for CAN HAT in /boot/config.txt
[ ] can0 interface present (ip link show can0)
[ ] can0 brought up at 500000 bps
[ ] candump can0 runs without error
[ ] /var/ph6/can_advisory/ write path exists
[ ] PCIe failure confirmed in dmesg (constitutional -- expected)
[ ] USB peripherals functional (lsusb)
[ ] Thermal validation passed (stress-ng 300s)
[ ] Claude Terminal preload verified on jackjack

Script: jackjack_can_validation.sh (run as root on jackjack)

================================================================================
PHASE 4 -- PI ZERO 2W SENTINEL
================================================================================

Node: ph6-zero-sentinel | Tier 0.5 Sentinel/Witness

[ ] OS installed
[ ] Hostname set to ph6-zero-sentinel
[ ] SSH enabled
[ ] Sentinel bootstrap script run
[ ] ph6-heartbeat-watch.service running
[ ] ph6-rsync-sentinel.service running
[ ] ph6-witness-timestamp.service running
[ ] ping ph6-fastpi from ph6-zero-sentinel -- PASS
[ ] ping jackjack from ph6-zero-sentinel -- PASS
[ ] RSYNC shadow pull from ph6-fastpi audit/ -- PASS
[ ] Heartbeat log populating (/var/ph6/heartbeat/heartbeat.log)
[ ] Witness timestamps populating (/var/ph6/witness/timestamps.log)

Script: ph6_zero_sentinel_bootstrap.sh (run as root on ph6-zero-sentinel)

================================================================================
PHASE 5 -- FIRST DISTRIBUTED CLUSTER TEST
================================================================================

This is the operational milestone. All nodes must be up for this phase.

[ ] ph6-fastpi captures test frames
[ ] FAST CRAM staging confirmed on ph6-fastpi
[ ] Advisory copy RSYNC from ph6-fastpi to jackjack -- PASS
[ ] jackjack receives advisory ingest without error
[ ] ph6-zero-sentinel witnesses RSYNC event
[ ] Heartbeat shows all nodes ALIVE
[ ] No authority boundary violations in logs
[ ] Claude Terminal on jackjack reads advisory report correctly

================================================================================
PHASE 6 -- JACKJACK FULL VALIDATION (pending from governance)
================================================================================

[ ] PCIe failure scope confirmed (lspci + dmesg output recorded)
[ ] USB stability under load (USB SSD + camera + Ethernet simultaneous)
[ ] Thermal stability (stress-ng 300s) -- temp recorded
[ ] Validation results committed to governance record

================================================================================
OPEN ISSUES
================================================================================

(record any blockers here)

================================================================================
END -- DEPLOYMENT CHECKLIST DCL-1.0
================================================================================
