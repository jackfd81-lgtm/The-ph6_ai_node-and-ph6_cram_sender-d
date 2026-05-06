#!/usr/bin/env bash
# CRAM-PU OI-03 — Two-Pi loopback transfer test
# Expected final line: TWO_PI_TRANSFER_PASS=True
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec python3 "$SCRIPT_DIR/../run_two_pi_transfer_test.py" "$@"
