#!/usr/bin/env bash
# =============================================================================
# PH6_MULTI_NODE_HEALTH_AND_BOUNDARY_VERIFICATION.sh
# (formerly PH6_PI5_TEST_SUITE.sh — rewritten per operator review 2026-06-13)
#
# Authority: ZERO (Claude-generated, PROPOSED — operator ratification required)
# Mode:      READ_ONLY_RECON
#
# This script makes NO certification or governance conclusions. It does not
# emit PASS/FAIL. It records OBSERVATIONS only, classified as:
#
#   OBSERVED           — the checked condition/artifact was found as described
#   NOT_OBSERVED       — the checked condition/artifact was not found
#   OPEN               — known open item; this script cannot close it
#   UNKNOWN            — could not be determined (tool/access missing)
#   CONFLICTING        — multiple/contradictory signals found
#   VIOLATION_DETECTED — an actual doctrine boundary violation pattern was found
#
# Presence of a file/value is NOT proof of correctness — it is reported as
# OBSERVED only, with no PASS implication. Operator interprets all results.
#
# Hard constraints (enforced by intent of this script, not just hooks):
#   - Do not modify files. Do not commit. Do not stage.
#   - Do not reboot. Do not flash firmware. Do not alter GPIO.
#   - Do not change network configuration.
#   - No write access to USB / camera / video / CAN / HAT devices.
#
# Usage:  bash ph6_pi5_test_suite.sh [--verbose]
# Output: One classification line per observation. Exit code is always 0 —
#         this script never decides PASS/FAIL; it reports for operator review.
# =============================================================================

set -uo pipefail

VERBOSE=0
[[ "${1:-}" == "--verbose" ]] && VERBOSE=1

declare -A COUNTS=( [OBSERVED]=0 [NOT_OBSERVED]=0 [OPEN]=0 [UNKNOWN]=0 [CONFLICTING]=0 [VIOLATION_DETECTED]=0 )
RESULTS=()

_log() { [[ $VERBOSE -eq 1 ]] && echo "  [detail] $*" || true; }

_obs() {
  local class="$1" name="$2" msg="$3"
  local color=""
  case "$class" in
    OBSERVED)           color="\033[0;32m" ;;
    NOT_OBSERVED)       color="\033[0;36m" ;;
    OPEN)               color="\033[0;33m" ;;
    UNKNOWN)            color="\033[0;90m" ;;
    CONFLICTING)        color="\033[0;35m" ;;
    VIOLATION_DETECTED) color="\033[0;31m" ;;
  esac
  COUNTS[$class]=$(( ${COUNTS[$class]} + 1 ))
  printf "${color}[%-18s]\033[0m %s — %s\n" "$class" "$name" "$msg"
  RESULTS+=("${class}|${name}|${msg}")
}

echo "============================================================"
echo " PH6 Multi-Node Health and Boundary Verification (RECON)"
echo " Host    : $(hostname)"
echo " Date    : $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo " Kernel  : $(uname -r)"
echo " Branch  : $(git -C "$(dirname "$0")" branch --show-current 2>/dev/null || echo 'N/A')"
echo "============================================================"
echo ""

# ─────────────────────────────────────────────────────────────────
# SECTION A — HOST HEALTH
# ─────────────────────────────────────────────────────────────────
echo "── A. Host Health ────────────────────────────────────────"

_obs OBSERVED "A-01:hostname" "$(hostname)"

_obs OBSERVED "A-02:kernel" "$(uname -a)"

MEM=$(free -h 2>/dev/null | awk '/^Mem:/{print "total="$2", used="$3", free="$4", avail="$7}')
if [[ -n "$MEM" ]]; then
  _obs OBSERVED "A-03:memory" "$MEM"
else
  _obs UNKNOWN "A-03:memory" "free command unavailable or produced no output"
fi

DISK=$(df -h / 2>/dev/null | awk 'NR==2{print "root_fs size="$2", used="$3", avail="$4", use%="$5}')
if [[ -n "$DISK" ]]; then
  _obs OBSERVED "A-04:storage_root" "$DISK"
else
  _obs UNKNOWN "A-04:storage_root" "df command unavailable or produced no output"
fi

if command -v vcgencmd &>/dev/null; then
  TEMP=$(vcgencmd measure_temp 2>/dev/null || true)
  if [[ -n "$TEMP" ]]; then
    _obs OBSERVED "A-05:temperature" "$TEMP"
  else
    _obs UNKNOWN "A-05:temperature" "vcgencmd present but measure_temp returned nothing"
  fi
elif [[ -r /sys/class/thermal/thermal_zone0/temp ]]; then
  RAW=$(cat /sys/class/thermal/thermal_zone0/temp 2>/dev/null)
  _obs OBSERVED "A-05:temperature" "thermal_zone0=$((RAW/1000)).$((RAW%1000/100))'C"
else
  _obs UNKNOWN "A-05:temperature" "no vcgencmd and no readable thermal_zone0"
fi

if command -v vcgencmd &>/dev/null; then
  THR=$(vcgencmd get_throttled 2>/dev/null || true)
  if [[ -n "$THR" ]]; then
    if [[ "$THR" == "throttled=0x0" ]]; then
      _obs NOT_OBSERVED "A-06:throttling" "$THR — no throttling/undervoltage flags set"
    else
      _obs OBSERVED "A-06:throttling" "$THR — non-zero throttling flags present (decode bitmask before interpreting)"
    fi
  else
    _obs UNKNOWN "A-06:throttling" "vcgencmd present but get_throttled returned nothing"
  fi
else
  _obs UNKNOWN "A-06:throttling" "vcgencmd not available on this host"
fi

echo ""

# ─────────────────────────────────────────────────────────────────
# SECTION B — NETWORK NODE DISCOVERY
# ─────────────────────────────────────────────────────────────────
echo "── B. Network Node Discovery ────────────────────────────"

declare -A KNOWN_NODES=(
  [192.168.254.188]="jackjack (Pi 5 primary, CRAM-0)"
  [192.168.254.189]="jackjack2 (Pi Zero 2W sentinel)"
  [192.168.254.194]="ESP_S1 (ESP_HTTP_SENSOR_NODE)"
)

for ip in "${!KNOWN_NODES[@]}"; do
  label="${KNOWN_NODES[$ip]}"
  if ping -c 2 -W 2 "$ip" &>/dev/null; then
    RTT=$(ping -c 1 -W 2 "$ip" 2>/dev/null | grep -oP 'time=\K[0-9.]+' || true)
    _obs OBSERVED "B-node:$ip" "$label — reachable (rtt=${RTT:-?}ms)"
  else
    _obs NOT_OBSERVED "B-node:$ip" "$label — no response to ping (2 probes)"
  fi
done

if command -v arp &>/dev/null; then
  ARP=$(arp -a 2>/dev/null | head -20)
  if [[ -n "$ARP" ]]; then
    _obs OBSERVED "B-04:arp_table" "$(echo "$ARP" | wc -l) entries (see --verbose for detail)"
    _log "$ARP"
  else
    _obs NOT_OBSERVED "B-04:arp_table" "arp -a returned no entries"
  fi
else
  _obs UNKNOWN "B-04:arp_table" "arp command not available"
fi

if command -v ip &>/dev/null; then
  ROUTE=$(ip route 2>/dev/null | head -5)
  if [[ -n "$ROUTE" ]]; then
    _obs OBSERVED "B-05:ip_route" "$(echo "$ROUTE" | tr '\n' ';')"
  else
    _obs NOT_OBSERVED "B-05:ip_route" "ip route returned no entries"
  fi
else
  _obs UNKNOWN "B-05:ip_route" "ip command not available"
fi

echo ""

# ─────────────────────────────────────────────────────────────────
# SECTION C — USB / SERIAL DEVICE DISCOVERY
# Read-only enumeration only. No flashing, no opening of devices.
# ─────────────────────────────────────────────────────────────────
echo "── C. USB / Serial Device Discovery ─────────────────────"

if command -v lsusb &>/dev/null; then
  LSUSB=$(lsusb 2>/dev/null)
  if [[ -n "$LSUSB" ]]; then
    COUNT=$(echo "$LSUSB" | wc -l)
    _obs OBSERVED "C-01:lsusb" "$COUNT device(s) enumerated (see --verbose for detail)"
    _log "$LSUSB"

    # Known vendor:product IDs for PH6-relevant boards (read-only classification)
    declare -A VIDPID_MAP=(
      ["2e8a:0003"]="PICO_DETECTED (RP2040 bootloader/BOOTSEL)"
      ["2e8a:000a"]="PICO_DETECTED (RP2040 CDC/UART)"
      ["2e8a:0009"]="PICO_DETECTED (RP2040 CDC, alt)"
      ["2e8a:000c"]="PICO2_DETECTED (RP2350)"
      ["10c4:ea60"]="ESP32_DETECTED (CP210x UART bridge)"
      ["1a86:7523"]="ESP32_OR_ESP8266_DETECTED (CH340 UART bridge)"
      ["0403:6001"]="UNKNOWN_FTDI_DEVICE (FT232 — common on ESP dev boards, not conclusive)"
    )
    for vidpid in "${!VIDPID_MAP[@]}"; do
      if echo "$LSUSB" | grep -qi "$vidpid"; then
        _obs OBSERVED "C-classify:$vidpid" "${VIDPID_MAP[$vidpid]}"
      fi
    done
  else
    _obs NOT_OBSERVED "C-01:lsusb" "no USB devices enumerated"
  fi
else
  _obs UNKNOWN "C-01:lsusb" "lsusb not available"
fi

TTYUSB=$(ls /dev/ttyUSB* 2>/dev/null || true)
if [[ -n "$TTYUSB" ]]; then
  _obs OBSERVED "C-02:ttyUSB" "$(echo "$TTYUSB" | tr '\n' ' ')"
else
  _obs NOT_OBSERVED "C-02:ttyUSB" "no /dev/ttyUSB* nodes present"
fi

TTYACM=$(ls /dev/ttyACM* 2>/dev/null || true)
if [[ -n "$TTYACM" ]]; then
  _obs OBSERVED "C-03:ttyACM" "$(echo "$TTYACM" | tr '\n' ' ')"
else
  _obs NOT_OBSERVED "C-03:ttyACM" "no /dev/ttyACM* nodes present"
fi

echo ""

# ─────────────────────────────────────────────────────────────────
# SECTION D — LANE BOUNDARY VERIFICATION
# Looks for textual patterns suggestive of Lane-2 code issuing
# Lane-1-only artifacts. Pattern matches are NOT proof — they are
# reported as OBSERVED/VIOLATION_DETECTED candidates for operator
# review, since static grep cannot establish call-path/authority.
# ─────────────────────────────────────────────────────────────────
echo "── D. Lane Boundary Verification ────────────────────────"

LANE2_DIRS=()
for d in ph6/ssmt ph6/tok ph6/research_agent; do
  [[ -d "$d" ]] && LANE2_DIRS+=("$d")
done

if [[ ${#LANE2_DIRS[@]} -eq 0 ]]; then
  _obs UNKNOWN "D-00:lane2_dirs" "none of ph6/ssmt, ph6/tok, ph6/research_agent found from cwd $(pwd)"
else
  _obs OBSERVED "D-00:lane2_dirs" "scanning: ${LANE2_DIRS[*]}"

  # D-01 PASS/DROP verdict issuance in Lane-2 code
  HITS=$(grep -rnE '"\s*(verdict|status)\s*"\s*:\s*"(PASS|DROP)"|=\s*"(PASS|DROP)"' "${LANE2_DIRS[@]}" --include="*.py" 2>/dev/null | head -5 || true)
  if [[ -z "$HITS" ]]; then
    _obs NOT_OBSERVED "D-01:lane2_pass_drop_issuance" "no PASS/DROP literal verdict assignment found in Lane-2 dirs"
  else
    _obs VIOLATION_DETECTED "D-01:lane2_pass_drop_issuance" "$HITS"
  fi

  # D-02 EvidencePacket mutation by Lane-2
  HITS=$(grep -rln "EvidencePacket" "${LANE2_DIRS[@]}" --include="*.py" 2>/dev/null | head -5 || true)
  if [[ -z "$HITS" ]]; then
    _obs NOT_OBSERVED "D-02:lane2_evidencepacket_ref" "no EvidencePacket references in Lane-2 dirs"
  else
    MUT=$(grep -nE "EvidencePacket.*(\.|\[).*=" "${LANE2_DIRS[@]}" --include="*.py" 2>/dev/null | head -5 || true)
    if [[ -n "$MUT" ]]; then
      _obs VIOLATION_DETECTED "D-02:lane2_evidencepacket_mutation" "$MUT"
    else
      _obs OBSERVED "D-02:lane2_evidencepacket_ref" "EvidencePacket referenced (read-only?) in: $HITS — review manually"
    fi
  fi

  # D-03 authority_hash mutation by Lane-2
  HITS=$(grep -rnE "authority_hash\s*=" "${LANE2_DIRS[@]}" --include="*.py" 2>/dev/null | head -5 || true)
  if [[ -z "$HITS" ]]; then
    _obs NOT_OBSERVED "D-03:lane2_authority_hash_mutation" "no authority_hash assignment found in Lane-2 dirs"
  else
    _obs VIOLATION_DETECTED "D-03:lane2_authority_hash_mutation" "$HITS"
  fi

  # D-04 CRAM-A write path / .blake2b marker writes from Lane-2
  HITS=$(grep -rniE "CRAM-A|\.blake2b" "${LANE2_DIRS[@]}" --include="*.py" 2>/dev/null | head -5 || true)
  if [[ -z "$HITS" ]]; then
    _obs NOT_OBSERVED "D-04:lane2_cram_a_writepath" "no CRAM-A / .blake2b references found in Lane-2 dirs"
  else
    _obs OBSERVED "D-04:lane2_cram_a_reference" "$HITS — references found; manual review required to confirm write-path vs. read-only/advisory mention"
  fi
fi

# D-05 ARC-DG / drift_gate status (known open item, not resolvable here)
DG=$(find . -name "drift_gate.py" 2>/dev/null | head -1)
if [[ -n "$DG" ]]; then
  TRACKED="UNKNOWN"
  git ls-files --error-unmatch "$DG" &>/dev/null && TRACKED="tracked" || TRACKED="untracked"
  _obs OBSERVED "D-05:drift_gate_arc_dg" "drift_gate.py found at $DG ($TRACKED) — ARC-DG closure status remains OPEN regardless of presence"
else
  _obs NOT_OBSERVED "D-05:drift_gate_arc_dg" "drift_gate.py not found — ARC-DG remains OPEN"
fi
_obs OPEN "D-05b:arc_dg_closure" "ARC-DG closure is an operator decision; this script cannot close it"

# D-06 HRG9 status — per CLAUDE.md, HRG9 is CLOSED at commit 2ef5fd6 and must
# never be re-listed as open. This is a fixed governance fact, not a recon item.
_obs OBSERVED "D-06:hrg9_status" "HRG9 recorded CLOSED at commit 2ef5fd6 per CLAUDE.md — not re-evaluated by this script"

echo ""

# ─────────────────────────────────────────────────────────────────
# SECTION E — PRIVILEGE BOUNDARY VERIFICATION
# ─────────────────────────────────────────────────────────────────
echo "── E. Privilege Boundary Verification ───────────────────"

if [[ "$(id -u)" -ne 0 ]]; then
  _obs OBSERVED "E-01:not_root" "running as $(whoami) (uid=$(id -u))"
else
  _obs OBSERVED "E-01:running_as_root" "running as root — unexpected for this script"
fi

GIT_OWNER=$(stat -c "%U" .git 2>/dev/null || echo "unknown")
if [[ "$GIT_OWNER" == "root" ]]; then
  _obs VIOLATION_DETECTED "E-02:git_repo_root_owned" ".git owned by root — normal-user git operations will fail"
elif [[ "$GIT_OWNER" == "unknown" ]]; then
  _obs UNKNOWN "E-02:git_repo_owner" ".git ownership could not be determined (not in a git repo from cwd?)"
else
  _obs OBSERVED "E-02:git_repo_owner" ".git owned by $GIT_OWNER"
fi

if sudo -n true 2>/dev/null; then
  NOPASSWD_ALL=$(sudo -l 2>/dev/null | grep "NOPASSWD.*ALL" | head -3 || true)
  if [[ -n "$NOPASSWD_ALL" ]]; then
    _obs OBSERVED "E-03:sudo_nopasswd_all" "$NOPASSWD_ALL"
  else
    _obs OBSERVED "E-03:sudo_passwordless_scoped" "sudo -n true succeeded but no blanket NOPASSWD ALL line found"
  fi
else
  _obs NOT_OBSERVED "E-03:sudo_passwordless" "sudo -n true failed — password required or no sudo rights"
fi

WW_PH6_SOURCE=$(find PH6_SOURCE -perm -o+w -type f 2>/dev/null | head -10 || true)
WW_PH6=$(find ph6 -perm -o+w -type f 2>/dev/null | head -10 || true)
if [[ -z "$WW_PH6_SOURCE" && -z "$WW_PH6" ]]; then
  _obs NOT_OBSERVED "E-04:world_writable_files" "none found under PH6_SOURCE/ or ph6/"
else
  _obs OBSERVED "E-04:world_writable_files" "PH6_SOURCE: ${WW_PH6_SOURCE:-none}; ph6: ${WW_PH6:-none}"
fi

BAD=$(grep -rn "shell=True" . --include="*.py" 2>/dev/null | xargs -r grep -l "sudo\|chmod 777\|chown root" 2>/dev/null | head -3 || true)
if [[ -z "$BAD" ]]; then
  _obs NOT_OBSERVED "E-05:shell_true_privilege_escalation" "no shell=True combined with privilege commands found"
else
  _obs VIOLATION_DETECTED "E-05:shell_true_privilege_escalation" "$BAD"
fi

BAD_SETUID=$(grep -rn "os\.setuid\|os\.setgid\|os\.seteuid\|ctypes.*setuid" . --include="*.py" 2>/dev/null | head -5 || true)
if [[ -z "$BAD_SETUID" ]]; then
  _obs NOT_OBSERVED "E-06:setuid_setgid_calls" "no setuid/setgid calls found in Python sources"
else
  _obs OBSERVED "E-06:setuid_setgid_calls" "$BAD_SETUID — review necessity"
fi

BAD_KEYS=$(find ~/.ssh -name "id_*" -not -name "*.pub" -perm /077 2>/dev/null | head -5 || true)
if [[ -z "$BAD_KEYS" ]]; then
  _obs NOT_OBSERVED "E-07:ssh_key_overly_permissive" "no overly-permissive private keys found"
else
  _obs OBSERVED "E-07:ssh_key_overly_permissive" "$BAD_KEYS — consider chmod 600"
fi

echo ""
echo "============================================================"
echo " OBSERVATION SUMMARY (no PASS/FAIL — operator interprets)"
echo "============================================================"
for class in OBSERVED NOT_OBSERVED OPEN UNKNOWN CONFLICTING VIOLATION_DETECTED; do
  printf " %-19s: %d\n" "$class" "${COUNTS[$class]}"
done
echo ""

if [[ ${COUNTS[VIOLATION_DETECTED]} -gt 0 ]]; then
  echo " NOTE: ${COUNTS[VIOLATION_DETECTED]} VIOLATION_DETECTED item(s) — these are pattern"
  echo "       matches requiring operator review, not confirmed certifications."
  for r in "${RESULTS[@]}"; do
    IFS='|' read -r c n m <<< "$r"
    [[ "$c" == "VIOLATION_DETECTED" ]] && printf "   [VIOLATION_DETECTED] %s — %s\n" "$n" "$m"
  done
fi

if [[ ${COUNTS[OPEN]} -gt 0 ]]; then
  echo " NOTE: ${COUNTS[OPEN]} OPEN item(s) carried forward — not closeable by this script."
fi

exit 0

# {"proposed_by":"claude-code-lane2","proposed_at_utc":"2026-06-13T13:30:00Z","api_call_log_ref":"session-20260613","ratified_by":null}
