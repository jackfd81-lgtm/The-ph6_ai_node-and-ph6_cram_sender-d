#!/usr/bin/env bash
# PH6 EVC-02 — Long-Run Receipt Chain Behavior
# Runs the deterministic EVC-02 synthetic pipeline.
#
# Usage:
#   ./run_evc02.sh [--frames N] [--run-dir PATH]
#
# Defaults:
#   --frames 300
#   --run-dir  auto-generated under validation_runs/evc02_<timestamp>/
#
# Output:
#   <run-dir>/ph6.evc02_receipt.v1.json
#   <run-dir>/verdict_log.jsonl          (usable as --source-dir for run_evc04_replay.sh)
#   <run-dir>/ingest_receipt_log.jsonl
#   <run-dir>/ph6.vrc_receipt.v1.json

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

python3 -m ph6.cram_pu.evc02_long_run "$@"
