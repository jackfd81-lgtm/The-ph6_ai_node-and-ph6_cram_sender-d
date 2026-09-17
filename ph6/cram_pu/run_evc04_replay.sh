#!/usr/bin/env bash
# PH6 EVC-04 — Payload Replay Verdict and Metric Comparison
#
# Usage:
#   ./run_evc04_replay.sh <source-dir> [--out-dir PATH]
#
#   <source-dir>  Directory containing verdict_log.jsonl.
#                 For EVC-02 synthetic runs:   validation_runs/evc02_<ts>/
#                 For cram_pu_live runs:        runtime/<run>/cram_store/
#                 Default (no args):            uses hardcoded EVC-02 baseline
#
# Required artifact in <source-dir>:
#   verdict_log.jsonl
#
# Optional artifacts (reported if present):
#   ingest_receipt_log.jsonl
#   ph6.vrc_receipt.v1.json

set -euo pipefail

if [ $# -eq 0 ]; then
    echo "[EVC-04] No source-dir given — using default EVC-02 baseline"
    python3 -m ph6.cram_pu.evc04_payload_replay
    exit $?
fi

SOURCE_DIR="$1"
shift

# Preflight: required
if [ ! -f "${SOURCE_DIR}/verdict_log.jsonl" ]; then
    echo "[EVC-04] FATAL: required artifact missing: ${SOURCE_DIR}/verdict_log.jsonl"
    exit 1
fi

# Preflight: optional, warn only
for opt in ingest_receipt_log.jsonl ph6.vrc_receipt.v1.json; do
    if [ ! -f "${SOURCE_DIR}/${opt}" ]; then
        echo "[EVC-04] NOTE: optional artifact not found: ${SOURCE_DIR}/${opt}"
    fi
done

python3 -m ph6.cram_pu.evc04_payload_replay --source-dir "${SOURCE_DIR}" "$@"
