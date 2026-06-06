#!/usr/bin/env bash
# create_desktop_restore_point.sh
# Lane: 2 / Authority: ZERO
# Snapshots current known-good desktop/status files into restore_points/LAST_KNOWN_GOOD/.
# Does NOT commit, push, or touch CRAM/canon/governance.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESTORE_DIR="${SCRIPT_DIR}/restore_points/LAST_KNOWN_GOOD"
MANIFEST="${SCRIPT_DIR}/restore_points/LAST_KNOWN_GOOD_MANIFEST.json"
DESKTOP="${SCRIPT_DIR}/ph6_windows_terminal_display.py"
REGISTRY="${SCRIPT_DIR}/test_registry.json"
GUARDS="${SCRIPT_DIR}/test_desktop_status_guards.py"
STATUS_CMD="/home/jack/.claude/commands/ph6-status.md"
SCANNER="/home/jack/PH6_SOURCE/TOOLS/governance_drift_scan.py"

echo "=== PH6 Desktop Restore Point Creator ==="
echo "  destination: ${RESTORE_DIR}"
echo ""

mkdir -p "${RESTORE_DIR}"

files_copied=()

copy_if_exists() {
    local src="$1" dst_name="$2"
    if [[ -f "${src}" ]]; then
        cp "${src}" "${RESTORE_DIR}/${dst_name}"
        echo "  COPIED: ${src##*/home/jack/} → restore_points/LAST_KNOWN_GOOD/${dst_name}"
        files_copied+=("${dst_name}")
    else
        echo "  SKIP  : ${src##*/home/jack/} (not found)"
    fi
}

copy_if_exists "${DESKTOP}"    "ph6_windows_terminal_display.py"
copy_if_exists "${REGISTRY}"   "test_registry.json"
copy_if_exists "${GUARDS}"     "test_desktop_status_guards.py"
copy_if_exists "${STATUS_CMD}" "ph6-status.md"
copy_if_exists "${SCANNER}"    "governance_drift_scan.py"

# Get git HEAD if available
GIT_HEAD="UNKNOWN"
if git -C /home/jack log --oneline -1 2>/dev/null; then
    GIT_HEAD="$(git -C /home/jack log --oneline -1 2>/dev/null || echo UNKNOWN)"
fi

HOSTNAME_VAL="$(hostname 2>/dev/null || echo unknown)"
TIMESTAMP="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

# Build manifest
FILES_JSON="["
for i in "${!files_copied[@]}"; do
    [[ $i -gt 0 ]] && FILES_JSON+=","
    FILES_JSON+="\"${files_copied[$i]}\""
done
FILES_JSON+="]"

cat > "${MANIFEST}" <<EOF
{
  "schema": "ph6.desktop.restore_manifest.v1",
  "label": "LAST_KNOWN_GOOD",
  "timestamp_utc": "${TIMESTAMP}",
  "hostname": "${HOSTNAME_VAL}",
  "git_head": "${GIT_HEAD}",
  "restore_dir": "${RESTORE_DIR}",
  "files_snapshotted": ${FILES_JSON},
  "authority": "ZERO",
  "note": "Desktop/status interface snapshot only. CRAM, canon, evidence, replay, production data NOT included.",
  "forbidden_restore_targets": [
    "CRAM authority files",
    "canon files",
    "evidence chain files",
    "replay authority files",
    "production data",
    "git history"
  ],
  "proposed_by": "create_desktop_restore_point.sh",
  "ratified_by": null
}
EOF

echo ""
echo "  MANIFEST: ${MANIFEST}"
echo ""
echo "=== Restore point created at ${TIMESTAMP} ==="
echo "    Files: ${#files_copied[@]} snapshotted"
echo "    To restore: bash ${SCRIPT_DIR}/restore_desktop_last_good.sh"
