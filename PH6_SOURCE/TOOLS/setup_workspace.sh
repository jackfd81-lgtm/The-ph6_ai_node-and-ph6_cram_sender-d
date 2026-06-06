#!/usr/bin/env bash
# ==============================================================================
# PH6CRAM WORKSPACE DEPLOYMENT ENGINE
# Integrated under PH6_SOURCE/ — run from repo root (/home/jack) or PH6_SOURCE/.
# All paths provisioned relative to PH6_SOURCE/.
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PH6_SOURCE_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=============================================================="
echo "PH6CRAM REPOSITORY PROVISIONING: INITIALIZING IMMUTABLE CORE"
echo "  PH6_SOURCE root: ${PH6_SOURCE_ROOT}"
echo "=============================================================="

TARGET_PATHS=(
    "CANON"
    "CRAM/cram0"
    "CRAM/crama"
    "CRAM/cramr"
    "CRAM/mrams"
    "SCHEMAS"
    "SENSORS/optical"
    "SENSORS/environmental"
    "AI/derivatives"
    "AI/topology"
    "TOOLS"
    "TESTS"
    "CERTIFICATION"
    "EXPORT"
)

for rel_path in "${TARGET_PATHS[@]}"; do
    abs_path="${PH6_SOURCE_ROOT}/${rel_path}"
    if [ ! -d "${abs_path}" ]; then
        mkdir -p "${abs_path}"
        echo "[PROVISIONED] ${abs_path}"
    else
        echo "[EXISTING]    ${rel_path}"
    fi
done

# Preserve directory tree with gitkeep markers inside CRAM lanes
for lane in cram0 crama cramr mrams; do
    keeper="${PH6_SOURCE_ROOT}/CRAM/${lane}/.gitkeep"
    [ -f "${keeper}" ] || touch "${keeper}"
done

# PH6_SOURCE-scoped .gitignore — does NOT overwrite repo root .gitignore
PH6_GITIGNORE="${PH6_SOURCE_ROOT}/.gitignore"
if [ ! -f "${PH6_GITIGNORE}" ]; then
    cat << 'GITEOF' > "${PH6_GITIGNORE}"
# CRAM data lanes — keep structure, exclude live data
CRAM/cram0/*
CRAM/crama/*
CRAM/cramr/*
CRAM/mrams/*
!CRAM/**/.gitkeep

# Runtime environment
.venv/
__pycache__/
*.pyc
.ruff_cache/
GITEOF
    echo "[PROVISIONED] ${PH6_GITIGNORE}"
else
    echo "[EXISTING]    PH6_SOURCE/.gitignore"
fi

# Isolated venv for PH6_SOURCE toolchain (separate from repo root)
VENV_PATH="${PH6_SOURCE_ROOT}/.venv"
if [ ! -d "${VENV_PATH}" ]; then
    echo "[ENVIRONMENT] Building isolated runtime container..."
    python3 -m venv "${VENV_PATH}"
    echo "[PROVISIONED] ${VENV_PATH}"
else
    echo "[EXISTING]    .venv"
fi

echo "=============================================================="
echo "PH6CRAM INITIALIZATION COMPLETE: ALL BOUNDARIES DRIFT PROTECTED"
echo "=============================================================="
