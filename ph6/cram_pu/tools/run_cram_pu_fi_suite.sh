#!/usr/bin/env bash
# CRAM-PU failure injection suite runner
# Expected final line: CRAM_PU_FI_SUITE_PASS=True
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec python3 "$SCRIPT_DIR/cram_pu_fi_suite.py" "$@"
