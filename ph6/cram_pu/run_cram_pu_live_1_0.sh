#!/usr/bin/env bash
# CRAM-PU-LIVE-1.0 acceptance runner
# Expected final line: CRAM_PU_LIVE_1_0_PASS=True
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec python3 "$SCRIPT_DIR/cram_pu_live.py" "$@"
