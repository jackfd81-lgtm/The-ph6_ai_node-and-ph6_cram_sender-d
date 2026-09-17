#!/usr/bin/env bash
# PH6 EVC-04-LIVE — Live Payload Replay Verdict and Metric Comparison
# Closes GAP-16: live ingest replay unproven.
#
# Usage:
#   ./run_evc04_live_replay.sh <cram_store_dir> [--out-dir PATH]
#
# <cram_store_dir> must contain:
#   verdict_log.jsonl   (required)
#   payloads/           (required — written by cram_pu_live.py v2+)
#
# For a fresh live run:
#   python3 -m ph6.cram_pu.cram_pu_live [--packets N]
#   RUN_DIR=$(ls -td ph6/cram_pu/runtime/run_* | head -1)
#   ./run_evc04_live_replay.sh "$RUN_DIR/cram_store"

set -euo pipefail

if [ $# -eq 0 ]; then
    echo "[EVC-04-LIVE] Usage: $0 <cram_store_dir> [--out-dir PATH]"
    echo "  <cram_store_dir> must contain verdict_log.jsonl and payloads/"
    exit 1
fi

SOURCE_DIR="$1"
shift

# Preflight: required
if [ ! -f "${SOURCE_DIR}/verdict_log.jsonl" ]; then
    echo "[EVC-04-LIVE] FATAL: required artifact missing: ${SOURCE_DIR}/verdict_log.jsonl"
    exit 1
fi

if [ ! -d "${SOURCE_DIR}/payloads" ]; then
    echo "[EVC-04-LIVE] FATAL: payloads/ directory missing: ${SOURCE_DIR}/payloads"
    echo "  Re-run the live capture with the current cram_pu_live.py (which writes payloads/)."
    exit 1
fi

PAYLOAD_COUNT=$(ls "${SOURCE_DIR}/payloads/"frame_*.bin 2>/dev/null | wc -l)
echo "[EVC-04-LIVE] Source:        ${SOURCE_DIR}"
echo "[EVC-04-LIVE] Payload files: ${PAYLOAD_COUNT}"

python3 -m ph6.cram_pu.evc04_live_payload_replay --source-dir "${SOURCE_DIR}" "$@"
