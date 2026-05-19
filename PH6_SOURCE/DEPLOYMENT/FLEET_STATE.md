# PH6 Fleet State

## Locked Node Map

| Node | Role | Status |
|---|---|---|
| 192.168.254.189 | Raspberry Pi Zero 2 W sentinel | Active SSH target |
| jackjack2 | Intended hostname for Zero 2 W | Rename pending until confirmed |
| Pi 5 / NVMe node | Fast CRAM / storage / Claude Code host | Primary compute/storage node |
| Second Pi 5 | Secondary/advisory/transfer node | Active fleet member |
| Waveshare RS485/CAN HAT | Optional CAN/RS485 module | Deferred / non-blocking |

## Zero 2 W Rule

The Raspberry Pi Zero 2 W is armv7l / 32-bit ARM and is not a Claude Code host.

Do not install Claude Code on the Zero 2 W.

Use the Zero 2 W only for:
- sentinel heartbeat
- lightweight monitoring
- uptime/status reporting
- simple SSH-controlled checks

## CAN HAT Rule

CAN HAT debugging is deferred.

Do not reopen MCP2515, SPI, dtoverlay, interrupt, or CAN debugging unless explicitly requested.
