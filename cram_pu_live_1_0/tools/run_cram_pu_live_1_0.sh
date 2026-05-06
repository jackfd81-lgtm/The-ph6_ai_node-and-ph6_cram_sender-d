#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="${PYTHON:-python3}"
RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)"
RUNTIME="$ROOT/runtime/run_$RUN_ID"
SOURCE_DIR="$RUNTIME/source"
OUTBOX="$RUNTIME/outbox"
ARRIVAL_DIR="$RUNTIME/arrival"
COMMIT_DIR="$RUNTIME/cram_commits"
LOG_DIR="$RUNTIME/logs"
RECEIPT_DIR="$RUNTIME/receipts"
mkdir -p "$SOURCE_DIR" "$OUTBOX" "$ARRIVAL_DIR" "$COMMIT_DIR" "$LOG_DIR" "$RECEIPT_DIR"
DEPARTURE_LOG="$LOG_DIR/departure_log.jsonl"
ARRIVAL_LOG="$LOG_DIR/arrival_log.jsonl"
CONTINUITY_REPORT="$LOG_DIR/continuity_report.json"
VERDICT_LOG="$LOG_DIR/verdicts.jsonl"
COMMIT_LOG="$LOG_DIR/commit_log.jsonl"
SHEDDING_LOG="$LOG_DIR/shedding_log.jsonl"
SHEDDING_REPORT="$LOG_DIR/shedding_report.json"
REPLAY_REPORT="$LOG_DIR/replay_report.json"
POSTRUN_RECEIPT="$RECEIPT_DIR/postrun_receipt.json"
DROP_POLICY="$RUNTIME/drop_shedding_policy.json"

printf 'CRAM-PU-LIVE-1.0 active moving payload sample A\n' > "$SOURCE_DIR/payload_001.bin"
printf 'CRAM-PU-LIVE-1.0 quiet\n' > "$SOURCE_DIR/payload_002.bin"
dd if=/dev/urandom of="$SOURCE_DIR/payload_003.bin" bs=1024 count=4 status=none

cat > "$DROP_POLICY" <<'JSON'
{"schema":"ph6.cram_pu.drop_shedding_policy.v1","policy_id":"DROP_SHED_POLICY_TEST_1","allowed_verdict":"DROP","pass_shedding_allowed":false,"audit_required":true}
JSON

for seq in 1 2 3; do
  "$PYTHON" "$ROOT/tools/source_departure_writer.py" \
    --payload "$SOURCE_DIR/payload_00${seq}.bin" \
    --source-node-id source-pi --seq $seq --media-type test \
    --outbox "$OUTBOX" --departure-log "$DEPARTURE_LOG"
done

"$PYTHON" "$ROOT/tools/cram_pu_receiver.py" --departure-log "$DEPARTURE_LOG" --arrival-dir "$ARRIVAL_DIR" --arrival-log "$ARRIVAL_LOG"
"$PYTHON" "$ROOT/tools/cram_pu_continuity_check.py" --departure-log "$DEPARTURE_LOG" --arrival-log "$ARRIVAL_LOG" --out "$CONTINUITY_REPORT"
"$PYTHON" "$ROOT/tools/cram_pu_verdict_runner.py" --arrival-log "$ARRIVAL_LOG" --verdict-log "$VERDICT_LOG"
"$PYTHON" "$ROOT/tools/cram_pu_atomic_commit.py" --verdict-log "$VERDICT_LOG" --commit-dir "$COMMIT_DIR" --commit-log "$COMMIT_LOG"
"$PYTHON" "$ROOT/tools/cram_pu_shedding.py" --verdict-log "$VERDICT_LOG" --policy "$DROP_POLICY" --shedding-log "$SHEDDING_LOG" --out "$SHEDDING_REPORT"
"$PYTHON" "$ROOT/tools/cram_pu_replay_verify.py" --arrival-log "$ARRIVAL_LOG" --verdict-log "$VERDICT_LOG" --commit-log "$COMMIT_LOG" --out "$REPLAY_REPORT"
"$PYTHON" "$ROOT/tools/cram_pu_postrun_receipt.py" \
  --departure-log "$DEPARTURE_LOG" --arrival-log "$ARRIVAL_LOG" \
  --continuity-report "$CONTINUITY_REPORT" --verdict-log "$VERDICT_LOG" \
  --commit-log "$COMMIT_LOG" --shedding-report "$SHEDDING_REPORT" \
  --replay-report "$REPLAY_REPORT" --out "$POSTRUN_RECEIPT"

python3 - "$POSTRUN_RECEIPT" <<'PY'
import json, sys
receipt = json.load(open(sys.argv[1]))
print("")
print("=== CRAM-PU-LIVE-1.0 ACCEPTANCE ===")
print(f"CRAM_PU_LIVE_1_0_PASS={receipt['cram_pu_live_1_0_pass']}")
if not receipt["cram_pu_live_1_0_pass"]:
    raise SystemExit(1)
PY
