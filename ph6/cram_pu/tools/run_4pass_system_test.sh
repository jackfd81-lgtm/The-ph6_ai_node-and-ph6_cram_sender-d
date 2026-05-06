#!/usr/bin/env bash
# PH6 / CRAM — 4-Pass System Test
# Expected final lines:
#   PH6_4_PASS_SYSTEM_TEST_VERDICT=PASS
#   PH6_DETERMINISM_CONFIRMED=True
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec python3 "$SCRIPT_DIR/../run_4pass_system_test.py" "$@"
