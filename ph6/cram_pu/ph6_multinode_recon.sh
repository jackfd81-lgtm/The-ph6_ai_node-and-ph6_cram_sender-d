#!/usr/bin/env bash
# =============================================================================
# ph6_multinode_recon.sh
# Authority : ZERO  (Claude-generated, PROPOSED — operator ratification required)
# Mode      : READ_ONLY_RECON
# Version   : 2.0
#
# DO NOT modify files.  DO NOT commit.  DO NOT stage.  DO NOT reboot.
# DO NOT flash firmware.  DO NOT alter GPIO.  DO NOT change network config.
#
# Output classifications:
#   OBSERVED        — artifact/state confirmed present and inspectable
#   NOT_OBSERVED    — artifact/state not found; no conclusion drawn
#   OPEN            — known open item, status unresolved by design
#   UNKNOWN         — insufficient data to classify
#   CONFLICTING     — two or more observations are inconsistent
#   VIOLATION_DETECTED — a doctrine boundary was crossed
#
# No PASS. No FAIL. No certification conclusions. No governance closure.
# Returns observations only.
# =============================================================================

set -uo pipefail

VERBOSE=0
[[ "${1:-}" == "--verbose" ]] && VERBOSE=1

# ── Output helpers ────────────────────────────────────────────────
TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)
LOG_LINES=()

_obs() {
  local code="$1" id="$2" msg="$3"
  local pad="          "
  printf "[%-18s] %-35s %s\n" "$code" "$id" "$msg"
  LOG_LINES+=("${TS}|${code}|${id}|${msg}")
}

_detail() { [[ $VERBOSE -eq 1 ]] && echo "               detail: $*" || true; }

_section() {
  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "  $*"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

# ── Preamble ──────────────────────────────────────────────────────
echo "============================================================"
echo " PH6 Multi-Node Health & Boundary Recon"
echo " Authority : ZERO"
echo " Mode      : READ_ONLY_RECON"
echo " Generated : $TS"
echo " Host      : $(hostname) / kernel $(uname -r)"
echo "============================================================"
echo ""
echo " Classification key:"
echo "   OBSERVED          confirmed present / measurable"
echo "   NOT_OBSERVED      not found; no conclusion drawn"
echo "   OPEN              known open item; unresolved by design"
echo "   UNKNOWN           insufficient data to classify"
echo "   CONFLICTING       two observations are inconsistent"
echo "   VIOLATION_DETECTED doctrine boundary crossed"
echo ""
echo " No PASS. No FAIL. No certification conclusions."
echo "============================================================"

# ─────────────────────────────────────────────────────────────────
# SECTION A — HOST HEALTH
# ─────────────────────────────────────────────────────────────────
_section "A. Host Health"

# A-01  hostname / kernel
HNAME=$(hostname 2>/dev/null || echo "UNKNOWN")
KERN=$(uname -r 2>/dev/null || echo "UNKNOWN")
_obs OBSERVED      "A-01:hostname"        "$HNAME"
_obs OBSERVED      "A-01:kernel"          "$KERN"

# A-02  Architecture
ARCH=$(uname -m 2>/dev/null || echo "UNKNOWN")
_obs OBSERVED      "A-02:architecture"    "$ARCH"

# A-03  Memory
if [[ -f /proc/meminfo ]]; then
  MEM_TOTAL=$(grep MemTotal /proc/meminfo | awk '{print $2,$3}')
  MEM_AVAIL=$(grep MemAvailable /proc/meminfo | awk '{print $2,$3}')
  _obs OBSERVED    "A-03:mem_total"       "$MEM_TOTAL"
  _obs OBSERVED    "A-03:mem_available"   "$MEM_AVAIL"
else
  _obs UNKNOWN     "A-03:memory"          "/proc/meminfo not accessible"
fi

# A-04  Storage — df on key paths
for MOUNT in / /home /tmp; do
  if mountpoint -q "$MOUNT" 2>/dev/null || [[ "$MOUNT" == "/" ]]; then
    DF=$(df -h "$MOUNT" 2>/dev/null | tail -1 | awk '{print "size="$2" used="$3" avail="$4" use%="$5}')
    _obs OBSERVED  "A-04:storage:$MOUNT"  "$DF"
  fi
done

# Check for NVMe devices (Pi 5 dual-NVMe config)
NVME_LIST=$(ls /dev/nvme* 2>/dev/null | tr '\n' ' ' || true)
if [[ -n "$NVME_LIST" ]]; then
  _obs OBSERVED    "A-04:nvme_devices"    "$NVME_LIST"
else
  _obs NOT_OBSERVED "A-04:nvme_devices"   "no /dev/nvme* found"
fi

# A-05  Temperature
if command -v vcgencmd &>/dev/null; then
  TEMP=$(vcgencmd measure_temp 2>/dev/null || echo "unavailable")
  _obs OBSERVED    "A-05:soc_temp"        "$TEMP"
else
  # Fallback: thermal zone
  TZ=$(cat /sys/class/thermal/thermal_zone0/temp 2>/dev/null || echo "")
  if [[ -n "$TZ" ]]; then
    TEMP_C=$(echo "scale=1; $TZ/1000" | bc 2>/dev/null || echo "$TZ milli°C")
    _obs OBSERVED  "A-05:thermal_zone0"   "${TEMP_C}°C"
  else
    _obs UNKNOWN   "A-05:temperature"     "vcgencmd and thermal_zone both unavailable"
  fi
fi

# A-06  Throttling
if command -v vcgencmd &>/dev/null; then
  THROT=$(vcgencmd get_throttled 2>/dev/null || echo "unavailable")
  if [[ "$THROT" == "throttled=0x0" ]]; then
    _obs OBSERVED  "A-06:throttle_state"  "no throttling ($THROT)"
  else
    _obs OBSERVED  "A-06:throttle_state"  "THROTTLE FLAG SET: $THROT — review power supply"
  fi
else
  _obs UNKNOWN     "A-06:throttle_state"  "vcgencmd not available"
fi

# A-07  Uptime
UPTIME=$(uptime -p 2>/dev/null || uptime 2>/dev/null || echo "unknown")
_obs OBSERVED      "A-07:uptime"          "$UPTIME"

# A-08  Git repo state (read-only)
if git rev-parse --git-dir &>/dev/null 2>&1; then
  GIT_BRANCH=$(git branch --show-current 2>/dev/null || echo "UNKNOWN")
  GIT_HEAD=$(git rev-parse --short HEAD 2>/dev/null || echo "UNKNOWN")
  GIT_DIRTY=$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')
  _obs OBSERVED    "A-08:git_branch"      "$GIT_BRANCH"
  _obs OBSERVED    "A-08:git_head"        "$GIT_HEAD"
  if [[ "$GIT_DIRTY" -gt 0 ]]; then
    _obs OBSERVED  "A-08:git_state"       "DIRTY ($GIT_DIRTY modified/untracked)"
  else
    _obs OBSERVED  "A-08:git_state"       "CLEAN"
  fi
else
  _obs NOT_OBSERVED "A-08:git_repo"       "not inside a git repository"
fi

# ─────────────────────────────────────────────────────────────────
# SECTION B — NETWORK NODE DISCOVERY
# ─────────────────────────────────────────────────────────────────
_section "B. Network Node Discovery"

# B-01  Local interfaces
echo ""
echo "  Interface snapshot:"
ip -br addr 2>/dev/null | while IFS= read -r line; do echo "    $line"; done

echo ""

# Known PH6 node map
declare -A NODES=(
  ["pi5_ingest"]="192.168.254.188"
  ["pi_zero_2w"]="192.168.254.189"
  ["esp32_cam_mb"]="192.168.254.191"
  ["esp_s1"]="192.168.254.194"
)

declare -A NODE_ROLES=(
  ["pi5_ingest"]="Pi5 / Ingest / CRAM-0"
  ["pi_zero_2w"]="Zero 2W / Node-6 / Smart Spigot / drop-only"
  ["esp32_cam_mb"]="ESP32-CAM-MB / Lane-2 advisory candidate"
  ["esp_s1"]="ESP32 S1 / Lane-2 advisory candidate"
)

for NODE_ID in "${!NODES[@]}"; do
  IP="${NODES[$NODE_ID]}"
  ROLE="${NODE_ROLES[$NODE_ID]}"
  if ping -c 3 -W 1 "$IP" &>/dev/null 2>&1; then
    LATENCY=$(ping -c 3 -W 1 "$IP" 2>/dev/null | grep "avg" | awk -F'/' '{print $5"ms"}' || echo "?")
    _obs OBSERVED    "B-01:node:$NODE_ID"   "ip=$IP role=$ROLE latency=$LATENCY"
  else
    _obs NOT_OBSERVED "B-01:node:$NODE_ID"  "ip=$IP role=$ROLE NOT reachable"
  fi
done

# B-02  ARP table — passive recon
echo ""
echo "  ARP table (passive, read-only):"
arp -a 2>/dev/null | while IFS= read -r line; do echo "    $line"; done || \
  ip neigh 2>/dev/null | while IFS= read -r line; do echo "    $line"; done
echo ""

# B-03  Route inspection
DEFAULT_GW=$(ip route show default 2>/dev/null | awk '{print $3}' | head -1 || echo "UNKNOWN")
_obs OBSERVED      "B-03:default_gateway" "$DEFAULT_GW"

# ─────────────────────────────────────────────────────────────────
# SECTION C — USB / SERIAL DEVICE DISCOVERY
# ─────────────────────────────────────────────────────────────────
_section "C. USB / Serial Device Discovery"

# C-01  lsusb full dump
echo ""
echo "  USB device list (lsusb):"
lsusb 2>/dev/null | while IFS= read -r line; do echo "    $line"; done || \
  _obs UNKNOWN "C-01:lsusb" "lsusb not available"
echo ""

# C-02  Classify known serial chipsets
declare -A SERIAL_CHIPS=(
  ["CP210x"]="Silicon Labs CP210x (common ESP32/ESP8266 programmer)"
  ["CH340"]="CH340/CH341 (common ESP32/Arduino programmer)"
  ["CH341"]="CH340/CH341 (common ESP32/Arduino programmer)"
  ["FTDI"]="FTDI FT232 (common serial programmer)"
  ["FT232"]="FTDI FT232 (common serial programmer)"
  ["RP2040"]="Raspberry Pi RP2040 / Pico"
  ["RP2350"]="Raspberry Pi RP2350 / Pico 2"
  ["2e8a"]="Raspberry Pi RP-series (USB VID 2e8a)"
  ["10c4"]="Silicon Labs VID (CP210x family)"
  ["1a86"]="WCH VID (CH340/CH341 family)"
  ["0403"]="FTDI VID"
)

USB_RAW=$(lsusb 2>/dev/null || echo "")
for CHIP in "${!SERIAL_CHIPS[@]}"; do
  DESC="${SERIAL_CHIPS[$CHIP]}"
  if echo "$USB_RAW" | grep -qi "$CHIP"; then
    _obs OBSERVED    "C-02:serial_chip"    "$CHIP — $DESC"
  fi
done

# If nothing matched, report
if [[ -n "$USB_RAW" ]]; then
  HAS_SERIAL=0
  for CHIP in "${!SERIAL_CHIPS[@]}"; do
    echo "$USB_RAW" | grep -qi "$CHIP" && HAS_SERIAL=1 && break
  done
  [[ $HAS_SERIAL -eq 0 ]] && _obs NOT_OBSERVED "C-02:serial_chips" "no known serial programmer chipset detected"
else
  _obs UNKNOWN "C-02:serial_chips" "lsusb output unavailable"
fi

# C-03  ttyUSB / ttyACM device nodes
for PREFIX in ttyUSB ttyACM; do
  DEVS=$(ls /dev/${PREFIX}* 2>/dev/null | tr '\n' ' ' || true)
  if [[ -n "$DEVS" ]]; then
    _obs OBSERVED    "C-03:dev_nodes"      "$DEVS"
  else
    _obs NOT_OBSERVED "C-03:dev_nodes"     "/dev/${PREFIX}* — none present"
  fi
done

# C-04  Board classification from dev nodes + lsusb
PICO_DETECTED=0
ESP32_DETECTED=0
ESP8266_DETECTED=0

# RP2040/RP2350 via VID
echo "$USB_RAW" | grep -qi "2e8a" && PICO_DETECTED=1
# CP210x → likely ESP
echo "$USB_RAW" | grep -qi "10c4\|CP210" && ESP32_DETECTED=1
# CH340 → could be ESP8266 or ESP32
echo "$USB_RAW" | grep -qi "1a86\|CH34" && ESP32_DETECTED=1

[[ $PICO_DETECTED -eq 1 ]]   && _obs OBSERVED "C-04:board_class" "PICO_DETECTED (RP2040/RP2350 VID)"
[[ $ESP32_DETECTED -eq 1 ]]  && _obs OBSERVED "C-04:board_class" "ESP32_OR_ESP8266_DETECTED (serial chipset)"
[[ $PICO_DETECTED -eq 0 && $ESP32_DETECTED -eq 0 ]] && \
  _obs NOT_OBSERVED "C-04:board_class" "PICO / ESP32 / ESP8266 — none detected via USB"

# ─────────────────────────────────────────────────────────────────
# SECTION D — LANE BOUNDARY VERIFICATION
# Observations only. No certification conclusions.
# Looking for: PASS/DROP issuance outside PSEUDO-A,
#              EvidencePacket mutation by Lane-2,
#              authority_hash mutation by Lane-2,
#              CRAM-A write path from Lane-2 code.
# ─────────────────────────────────────────────────────────────────
_section "D. Lane Boundary Verification"

# D-01  PASS/DROP issuance: locate all call sites, classify source lane
#       Any PASS/DROP outside PSEUDO-A code path is a doctrine observation
echo ""
echo "  Scanning for PASS/DROP issuance sites..."
PD_SITES=$(grep -rn '"PASS"\|"DROP"\|verdict.*PASS\|verdict.*DROP' \
  . --include="*.py" 2>/dev/null | grep -v "^Binary\|\.git" || true)

if [[ -z "$PD_SITES" ]]; then
  _obs NOT_OBSERVED "D-01:pass_drop_sites" "no PASS/DROP issuance found in Python sources"
else
  while IFS= read -r line; do
    FILE=$(echo "$line" | cut -d: -f1)
    # Check if this file is inside an advisory/lane-2 path
    if echo "$FILE" | grep -qi "advisory\|lane.2\|soso\|grok\|claude\|jetson"; then
      _obs VIOLATION_DETECTED "D-01:pass_drop_in_lane2" "Lane-2 file issues PASS/DROP: $line"
    else
      _obs OBSERVED           "D-01:pass_drop_site"     "$line"
    fi
  done <<< "$PD_SITES"
fi

# D-02  EvidencePacket mutation by Lane-2 code
echo ""
echo "  Scanning for EvidencePacket mutation in advisory code paths..."
EP_MUTATIONS=$(grep -rn "EvidencePacket\|evidence_packet" \
  . --include="*.py" 2>/dev/null | \
  grep -i "advisory\|lane.2\|soso\|grok\|claude\|jetson" | \
  grep -v "^Binary\|\.git\|#.*EvidencePacket" || true)

if [[ -z "$EP_MUTATIONS" ]]; then
  _obs NOT_OBSERVED "D-02:evidence_packet_mutation" "no EvidencePacket mutation in advisory paths"
else
  while IFS= read -r line; do
    _obs VIOLATION_DETECTED "D-02:evidence_packet_mutation" "$line"
  done <<< "$EP_MUTATIONS"
fi

# D-03  authority_hash mutation by Lane-2
echo ""
echo "  Scanning for authority_hash mutation in advisory code paths..."
AH_MUT=$(grep -rn "authority_hash" \
  . --include="*.py" 2>/dev/null | \
  grep -i "advisory\|lane.2\|soso\|grok\|claude\|jetson" | \
  grep -iv "#.*authority_hash\|^Binary\|\.git" || true)

if [[ -z "$AH_MUT" ]]; then
  _obs NOT_OBSERVED "D-03:authority_hash_mutation" "no authority_hash mutation in advisory paths"
else
  while IFS= read -r line; do
    _obs VIOLATION_DETECTED "D-03:authority_hash_mutation" "$line"
  done <<< "$AH_MUT"
fi

# D-04  CRAM-A write path accessible from Lane-2 code
echo ""
echo "  Scanning for CRAM-A write access in advisory code paths..."
CRAM_A=$(grep -rn "CRAM.A\|cram_a\|CRAM_A" \
  . --include="*.py" 2>/dev/null | \
  grep -i "advisory\|lane.2\|soso\|grok\|claude\|jetson" | \
  grep -iv "#\|^Binary\|\.git" || true)

if [[ -z "$CRAM_A" ]]; then
  _obs NOT_OBSERVED "D-04:cram_a_lane2_write" "no CRAM-A write path in advisory code"
else
  while IFS= read -r line; do
    _obs VIOLATION_DETECTED "D-04:cram_a_lane2_write" "$line"
  done <<< "$CRAM_A"
fi

# D-05  ADVISORY_PROVENANCE_RECEIPT co-location with verdict packets
echo ""
RECEIPT_COLOCATED=$(grep -rl "ADVISORY_PROVENANCE_RECEIPT" . \
  --include="*.py" --include="*.json" 2>/dev/null | \
  xargs grep -l "lane1_verdict\|PSEUDO.A" 2>/dev/null | head -3 || true)

if [[ -z "$RECEIPT_COLOCATED" ]]; then
  _obs NOT_OBSERVED "D-05:receipt_verdict_colocation" \
    "ADVISORY_PROVENANCE_RECEIPT not co-located with lane1_verdict/PSEUDO-A"
else
  _obs VIOLATION_DETECTED "D-05:receipt_verdict_colocation" \
    "MRAM-S receipt embedded in verdict context: $RECEIPT_COLOCATED"
fi

# D-06  Open governance items — state as OPEN, no conclusions
_obs OPEN "D-06:ARC-DG"            "drift_gate.py install status unresolved"
_obs OPEN "D-06:OI-01_OI-03"       "SCOPE_LAYERING_CONFLICT — full cert STOP-SHIP"
_obs OPEN "D-06:OI-C1"             "ROUND_HALF_EVEN ADR pending operator decision"
_obs OPEN "D-06:canon_ratification" "canon_combined_manifest.json ratified_by=null"
_obs OPEN "D-06:HRG9"              "CONFLICTING_CERTIFICATION_TEXT — operator reconciliation pending"
_obs OPEN "D-06:blur_drop_low"     "_BLUR_DROP_LOW=0.3 provenance unverified"

# D-07  Known authority hash — reference observation only
KNOWN_HASH="014652358db408cf7977c3e99ab3cceb57ee01d7bf7c265daaaead625485a2d7"
HASH_REF=$(grep -rl "$KNOWN_HASH" . \
  --include="*.json" --include="*.md" --include="*.py" --include="*.sh" \
  2>/dev/null | head -3 || true)

if [[ -n "$HASH_REF" ]]; then
  _obs OBSERVED    "D-07:authority_hash_ref" \
    "known-good hash referenced in: $(echo $HASH_REF | tr '\n' ' ')"
else
  _obs NOT_OBSERVED "D-07:authority_hash_ref" \
    "known-good hash $KNOWN_HASH not found in any tracked file"
fi
# Explicit: presence/absence is observation only, not integrity verdict
echo "               note: hash reference ≠ integrity conclusion"

# ─────────────────────────────────────────────────────────────────
# SECTION E — PRIVILEGE BOUNDARY VERIFICATION
# ─────────────────────────────────────────────────────────────────
_section "E. Privilege Boundary Verification"

# E-01  Running user
UID_NOW=$(id -u)
USER_NOW=$(whoami)
if [[ "$UID_NOW" -eq 0 ]]; then
  _obs OBSERVED    "E-01:run_user"       "root (uid=0) — recon should run as normal user"
else
  _obs OBSERVED    "E-01:run_user"       "$USER_NOW (uid=$UID_NOW)"
fi

# E-02  sudo exposure
if sudo -n true 2>/dev/null; then
  SUDO_L=$(sudo -l 2>/dev/null || true)
  if echo "$SUDO_L" | grep -q "NOPASSWD.*ALL"; then
    _obs OBSERVED  "E-02:sudo_scope"     "NOPASSWD ALL — passwordless full sudo active"
  else
    _obs OBSERVED  "E-02:sudo_scope"     "passwordless sudo present but scoped (not NOPASSWD ALL)"
  fi
else
  _obs OBSERVED    "E-02:sudo_scope"     "sudo requires password"
fi

# E-03  setuid calls in Python sources
SETUID=$(grep -rn "os\.setuid\|os\.setgid\|os\.seteuid\|os\.setegid" \
  . --include="*.py" 2>/dev/null | grep -v "^Binary\|\.git" || true)
if [[ -z "$SETUID" ]]; then
  _obs NOT_OBSERVED "E-03:setuid_calls"  "no setuid/setgid calls in Python sources"
else
  while IFS= read -r line; do
    _obs OBSERVED  "E-03:setuid_calls"   "$line"
  done <<< "$SETUID"
fi

# E-04  shell=True with privilege commands
SH_PRIV=$(grep -rn "shell=True" . --include="*.py" 2>/dev/null | \
  xargs grep -l "sudo\|chmod 777\|chown root" 2>/dev/null | head -5 || true)
if [[ -z "$SH_PRIV" ]]; then
  _obs NOT_OBSERVED "E-04:shell_true_priv" "no shell=True + privilege command pairing"
else
  while IFS= read -r line; do
    _obs OBSERVED  "E-04:shell_true_priv" "$line"
  done <<< "$SH_PRIV"
fi

# E-05  World-writable files in PH6_SOURCE
WW=$(find PH6_SOURCE -perm -o+w -type f 2>/dev/null | head -10 || true)
if [[ -z "$WW" ]]; then
  _obs NOT_OBSERVED "E-05:world_writable"  "no world-writable files under PH6_SOURCE/"
else
  while IFS= read -r f; do
    _obs OBSERVED  "E-05:world_writable"   "$f"
  done <<< "$WW"
fi

# E-06  .git ownership
GIT_OWNER=$(stat -c "%U" .git 2>/dev/null || echo "UNKNOWN")
_obs OBSERVED      "E-06:git_ownership"   ".git owned by $GIT_OWNER"

# E-07  SSH private key permissions
BAD_KEYS=$(find ~/.ssh -name "id_*" ! -name "*.pub" -perm /077 2>/dev/null | head -5 || true)
if [[ -z "$BAD_KEYS" ]]; then
  _obs NOT_OBSERVED "E-07:ssh_key_perms"  "no overly-permissive SSH private keys found"
else
  while IFS= read -r k; do
    _obs OBSERVED  "E-07:ssh_key_perms"   "permissive key: $k (chmod 600 recommended)"
  done <<< "$BAD_KEYS"
fi

# E-08  apply_*.py execute bit
EXEC_APPLY=$(find . -name "apply_*.py" -perm /111 2>/dev/null | head -5 || true)
if [[ -z "$EXEC_APPLY" ]]; then
  _obs NOT_OBSERVED "E-08:apply_exec_bit" "apply_*.py files not executable (expected)"
else
  while IFS= read -r f; do
    _obs OBSERVED  "E-08:apply_exec_bit"  "execute bit set on historical artifact: $f"
  done <<< "$EXEC_APPLY"
fi

# ─────────────────────────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────────────────────────
echo ""
echo "============================================================"
echo " RECON SUMMARY"
echo " Generated : $TS"
echo "============================================================"

declare -A COUNTS=(
  [OBSERVED]=0 [NOT_OBSERVED]=0 [OPEN]=0
  [UNKNOWN]=0  [CONFLICTING]=0  [VIOLATION_DETECTED]=0
)

for entry in "${LOG_LINES[@]}"; do
  CODE=$(echo "$entry" | cut -d'|' -f2)
  [[ -n "${COUNTS[$CODE]+x}" ]] && ((COUNTS[$CODE]++)) || true
done

for CODE in OBSERVED NOT_OBSERVED OPEN UNKNOWN CONFLICTING VIOLATION_DETECTED; do
  printf "  %-20s : %d\n" "$CODE" "${COUNTS[$CODE]}"
done

echo ""

VD="${COUNTS[VIOLATION_DETECTED]}"
if [[ "$VD" -gt 0 ]]; then
  echo " ⚠  $VD VIOLATION(S) DETECTED — operator review required before next session"
  echo ""
  echo " Violations:"
  for entry in "${LOG_LINES[@]}"; do
    CODE=$(echo "$entry" | cut -d'|' -f2)
    if [[ "$CODE" == "VIOLATION_DETECTED" ]]; then
      ID=$(echo "$entry" | cut -d'|' -f3)
      MSG=$(echo "$entry" | cut -d'|' -f4)
      printf "   [%s] %s\n" "$ID" "$MSG"
    fi
  done
else
  echo " No VIOLATION_DETECTED entries."
fi

echo ""
echo " Open items: ${COUNTS[OPEN]} (carry forward — operator decision required)"
echo " Conflicting: ${COUNTS[CONFLICTING]}"
echo ""
echo " Authority: ZERO. No certification conclusions. No governance closure."
echo " All output is PROPOSED until operator ratification."
echo "============================================================"

# {"proposed_by":"claude-code-lane2","proposed_at_utc":"2026-06-13T13:40:00Z","api_call_log_ref":"session-20260613","ratified_by":null}
