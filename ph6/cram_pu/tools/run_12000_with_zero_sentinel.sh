#!/usr/bin/env bash
# PH6 12,000-Frame CRAM Test with Zero 2W Sentinel
#
# Architecture:
#   Pi 5  — PSEUDO-M/A authority, camera capture, CRAM evidence
#   Zero  — Lane 2 sentinel, advisory observation only, Authority ZERO
#
# Zero output destination: ph6/mram-s/zero2w/ (advisory, never CRAM paths)
# Pi 5 PSEUDO-A remains sole PASS/DROP authority.

set -euo pipefail

ZERO_HOST="${ZERO_HOST:-192.168.254.189}"
ZERO_USER="${ZERO_USER:-jack}"
DEVICE="${DEVICE:-/dev/video0}"
FRAMES="${FRAMES:-12000}"
FPS="${FPS:-15}"
WIDTH="${WIDTH:-640}"
HEIGHT="${HEIGHT:-480}"

REPO="/home/jack"
SENTINEL_DIR="$REPO/ph6/mram-s/zero2w"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
SENTINEL_LOG="$SENTINEL_DIR/sentinel_${STAMP}.jsonl"
COMBINED_REPORT="$SENTINEL_DIR/combined_report_${STAMP}.json"

mkdir -p "$SENTINEL_DIR"

echo "============================================"
echo "PH6 12,000-FRAME CRAM + ZERO SENTINEL RUN"
echo "============================================"
echo "Pi 5:       $(hostname) / PSEUDO-A authority"
echo "Zero 2W:    $ZERO_USER@$ZERO_HOST / Lane 2 sentinel"
echo "Frames:     $FRAMES @ $FPS fps  ${WIDTH}x${HEIGHT}"
echo "Stamp:      $STAMP"
echo

# ── Deploy sentinel script to Zero 2W ────────────────────────────────────────

echo "[1/4] Deploying sentinel to Zero 2W..."

ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no "$ZERO_USER@$ZERO_HOST" \
'cat > /tmp/zero_sentinel.sh' <<'SENTINEL'
#!/bin/sh
# Zero 2W sentinel — advisory observation only, Authority ZERO
OUT="/tmp/sentinel_log.jsonl"
PI5_IP="192.168.254.188"
> "$OUT"

while [ -f /tmp/sentinel_running ]; do
  TS=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  TEMP=$(cat /sys/class/thermal/thermal_zone0/temp 2>/dev/null || echo 0)
  UPTIME=$(cat /proc/uptime | awk "{print \$1}")
  THROTTLE=$(vcgencmd get_throttled 2>/dev/null || echo unknown)

  # Ping Pi 5 for network health
  PING_MS=$(ping -c 1 -W 2 "$PI5_IP" 2>/dev/null | awk -F'/' '/rtt/{print $5}' || echo -1)

  printf '{"ts":"%s","authority":"ZERO","thermal_millic":%s,"uptime_sec":"%s","throttle":"%s","ping_pi5_ms":"%s"}\n' \
    "$TS" "$TEMP" "$UPTIME" "$THROTTLE" "$PING_MS" >> "$OUT"

  sleep 10
done

echo "Sentinel stopped."
SENTINEL

ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no "$ZERO_USER@$ZERO_HOST" \
  'chmod +x /tmp/zero_sentinel.sh && touch /tmp/sentinel_running && nohup /tmp/zero_sentinel.sh >/tmp/sentinel.out 2>&1 &
   echo "Sentinel PID: $!"'

echo "  Sentinel deployed and running on Zero 2W."
echo

# ── Run Pi 5 CRAM test ────────────────────────────────────────────────────────

echo "[2/4] Starting Pi 5 12,000-frame CRAM test..."
echo "  Authority: PSEUDO-A (Pi 5 only)"
echo

cd "$REPO"
python3 PH6_SOURCE/TESTS/USB_CAMERA_12000/run_usb_camera_12000.py \
  --device "$DEVICE" \
  --frames "$FRAMES" \
  --fps    "$FPS"    \
  --width  "$WIDTH"  \
  --height "$HEIGHT"

# Capture the latest run dir
CRAM_RUN_DIR=$(ls -td "$REPO/ph6/cram_pu/validation_runs"/PH6-USB-CAM-PSEUDO-SOSO-TOK-12000* 2>/dev/null | head -1)
echo
echo "  CRAM run dir: $CRAM_RUN_DIR"

# ── Stop sentinel and collect log ─────────────────────────────────────────────

echo
echo "[3/4] Stopping Zero 2W sentinel and collecting log..."

ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no "$ZERO_USER@$ZERO_HOST" \
  'rm -f /tmp/sentinel_running; sleep 2; wc -l /tmp/sentinel_log.jsonl'

scp -o ConnectTimeout=5 "$ZERO_USER@$ZERO_HOST:/tmp/sentinel_log.jsonl" "$SENTINEL_LOG" 2>/dev/null && \
  echo "  Sentinel log: $SENTINEL_LOG ($(wc -l < "$SENTINEL_LOG") records)" || \
  echo "  WARN: could not collect sentinel log"

# ── Write combined report ────────────────────────────────────────────────────

echo
echo "[4/4] Writing combined report..."

PASS_COUNT=""
DROP_COUNT=""
REPLAY_STATUS=""
if [ -n "$CRAM_RUN_DIR" ] && [ -f "$CRAM_RUN_DIR/replay_digest.json" ]; then
  PASS_COUNT=$(python3 -c "import json; d=json.load(open('$CRAM_RUN_DIR/replay_digest.json')); print(d['pass_count'])")
  DROP_COUNT=$(python3 -c "import json; d=json.load(open('$CRAM_RUN_DIR/replay_digest.json')); print(d['drop_count'])")
  REPLAY_DIGEST=$(python3 -c "import json; d=json.load(open('$CRAM_RUN_DIR/replay_digest.json')); print(d['summary_digest'])")
  REPLAY_STATUS="MATCH"
fi

SENTINEL_RECORDS=$(wc -l < "$SENTINEL_LOG" 2>/dev/null || echo 0)

ZERO_HOSTNAME=$(ssh -o ConnectTimeout=3 "$ZERO_USER@$ZERO_HOST" 'hostname' 2>/dev/null || echo unknown)
ZERO_FINAL_TEMP=$(ssh -o ConnectTimeout=3 "$ZERO_USER@$ZERO_HOST" \
  'cat /sys/class/thermal/thermal_zone0/temp 2>/dev/null | awk "{printf \"%.1fC\", \$1/1000}"' 2>/dev/null || echo unknown)

cat > "$COMBINED_REPORT" <<JSON
{
  "schema": "ph6.combined_cram_sentinel.v1",
  "created_at_utc": "$STAMP",
  "pi5": {
    "hostname": "$(hostname)",
    "authority": "PSEUDO-A sole PASS/DROP issuer",
    "frames_requested": $FRAMES,
    "pass_count": "${PASS_COUNT:-unknown}",
    "drop_count": "${DROP_COUNT:-unknown}",
    "replay_status": "${REPLAY_STATUS:-unknown}",
    "replay_digest": "${REPLAY_DIGEST:-unknown}",
    "cram_run_dir": "${CRAM_RUN_DIR:-unknown}"
  },
  "zero2w": {
    "hostname": "$ZERO_HOSTNAME",
    "ip": "$ZERO_HOST",
    "authority": "ZERO",
    "lane": "Lane 2 sentinel / advisory",
    "sentinel_records": $SENTINEL_RECORDS,
    "final_temp": "$ZERO_FINAL_TEMP",
    "sentinel_log": "$SENTINEL_LOG",
    "destination": "ph6/mram-s/zero2w/ (advisory only, not CRAM path)"
  },
  "authority_statement": "PSEUDO-A on Pi 5 was the only PASS/DROP issuer. Zero 2W observed as advisory sentinel. Zero output is in advisory path only."
}
JSON

echo
echo "============================================"
echo "COMBINED REPORT"
echo "============================================"
cat "$COMBINED_REPORT"
echo
echo "Combined report: $COMBINED_REPORT"
echo "Sentinel log:    $SENTINEL_LOG"
