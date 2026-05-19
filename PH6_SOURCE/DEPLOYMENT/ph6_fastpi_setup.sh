#!/bin/bash
# PH6 ph6-fastpi node setup — Tier 1 FAST CRAM Worker
# Run once after fresh OS install. Idempotent.
# Node: ph6-fastpi (Healthy Pi 5)
# Version: 1.0 / 2026-05-19

set -euo pipefail

HOSTNAME_TARGET="ph6-fastpi"
PH6_USER="${SUDO_USER:-pi}"
PH6_HOME="/home/${PH6_USER}"
PH6_ROOT="/var/ph6"

log() { echo "[ph6-fastpi-setup] $*"; }
warn() { echo "[ph6-fastpi-setup] WARN: $*" >&2; }

# ── 1. HOSTNAME ───────────────────────────────────────────────────────────────
log "Setting hostname to ${HOSTNAME_TARGET}"
current_hostname=$(hostname)
if [ "$current_hostname" != "$HOSTNAME_TARGET" ]; then
    hostnamectl set-hostname "$HOSTNAME_TARGET"
    sed -i "s/${current_hostname}/${HOSTNAME_TARGET}/g" /etc/hosts 2>/dev/null || true
    log "Hostname set to ${HOSTNAME_TARGET}"
else
    log "Hostname already ${HOSTNAME_TARGET} -- skipping"
fi

# ── 2. SSH ────────────────────────────────────────────────────────────────────
log "Enabling SSH"
systemctl enable ssh
systemctl start ssh
log "SSH enabled and started"

# ── 3. SYSTEM UPDATE ──────────────────────────────────────────────────────────
log "Updating system packages"
apt-get update -q
apt-get upgrade -y -q
log "System update complete"

# ── 4. DEPENDENCIES ──────────────────────────────────────────────────────────
log "Installing PH6 runtime dependencies"
apt-get install -y -q \
    python3 \
    python3-pip \
    python3-venv \
    git \
    rsync \
    stress-ng \
    can-utils \
    htop \
    iotop \
    vim \
    jq \
    blake2 \
    lsof \
    net-tools
log "Dependencies installed"

# ── 5. PH6 DIRECTORY STRUCTURE ────────────────────────────────────────────────
log "Creating PH6 directory structure"
dirs=(
    "${PH6_ROOT}/fast-cram"
    "${PH6_ROOT}/hotstore"
    "${PH6_ROOT}/export"
    "${PH6_ROOT}/replay"
    "${PH6_ROOT}/audit"
    "${PH6_ROOT}/staging"
    "${PH6_ROOT}/logs"
)
for d in "${dirs[@]}"; do
    mkdir -p "$d"
    chown "${PH6_USER}:${PH6_USER}" "$d"
    log "  created $d"
done

# ── 6. NVMe MOUNT VERIFICATION ────────────────────────────────────────────────
log "Checking NVMe / storage"
if lsblk | grep -q nvme; then
    log "NVMe device detected -- verify mount point manually if needed"
    lsblk | grep nvme
else
    warn "No NVMe device found -- verify PCIe + NVMe attachment before HOTSTORE use"
fi

# ── 7. NODE ROLE MARKER ───────────────────────────────────────────────────────
log "Writing node role marker"
mkdir -p /etc/ph6
cat > /etc/ph6/node.conf << 'EOF'
# PH6 Node Configuration
# DO NOT EDIT without governance update
PH6_NODE_DESIGNATION=PH6-FC-WORKER
PH6_NODE_HOSTNAME=ph6-fastpi
PH6_NODE_AUTHORITY_TIER=1
PH6_NODE_AUTHORITY_LEVEL=LIMITED
PH6_PASS_AUTHORITY=false
PH6_CRAM_A_AUTHORITY=false
PH6_AUDIT_CHAIN_AUTHORITY=false
EOF
log "Node role marker written to /etc/ph6/node.conf"

# ── 8. VALIDATION ─────────────────────────────────────────────────────────────
log ""
log "=== SETUP COMPLETE ==="
log "Hostname:   $(hostname)"
log "Node role:  Tier 1 FAST CRAM Worker"
log "Authority:  LIMITED (no PASS/DROP, no CRAM-A)"
log ""
log "Next steps:"
log "  1. Verify NVMe mount if storage path needs it"
log "  2. Run ssh-copy-id from main node"
log "  3. Run cluster connectivity test"
log "  4. Run: stress-ng --cpu 4 --timeout 300s (thermal validation)"
log "  5. Check: vcgencmd measure_temp"
log ""
log "PASS: ph6-fastpi setup complete"
