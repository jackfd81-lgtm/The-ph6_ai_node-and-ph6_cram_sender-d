#!/bin/bash
# PH6 Pi Zero 2W sentinel bootstrap
# Run on ph6-zero-sentinel after OS install
# Node: ph6-zero-sentinel (Tier 0.5 Sentinel/Witness)
# Version: 1.0 / 2026-05-19

set -euo pipefail

PH6_USER="${SUDO_USER:-pi}"
PH6_FASTPI="${PH6_FASTPI_HOST:-ph6-fastpi}"
PH6_JACKJACK="${PH6_JACKJACK_HOST:-jackjack}"
SENTINEL_ROOT="/var/ph6"
SERVICE_DIR="/etc/systemd/system"

log()  { echo "[ph6-zero-sentinel] $*"; }
pass() { echo "[ph6-zero-sentinel] PASS: $*"; }
warn() { echo "[ph6-zero-sentinel] WARN: $*" >&2; }

log "PH6 Pi Zero 2W sentinel bootstrap"
log "Node role: Tier 0.5 Sentinel/Witness (ZERO authority, DROP-only spigot optional)"
log ""

# ── 1. SYSTEM UPDATE ──────────────────────────────────────────────────────────
log "Installing sentinel dependencies"
apt-get update -q
apt-get install -y -q rsync openssh-client iputils-ping curl jq
log "Dependencies installed"

# ── 2. HOSTNAME ───────────────────────────────────────────────────────────────
current_hostname=$(hostname)
if [ "$current_hostname" != "ph6-zero-sentinel" ]; then
    log "Setting hostname to ph6-zero-sentinel"
    hostnamectl set-hostname "ph6-zero-sentinel"
    sed -i "s/${current_hostname}/ph6-zero-sentinel/g" /etc/hosts 2>/dev/null || true
fi

# ── 3. DIRECTORY STRUCTURE ────────────────────────────────────────────────────
log "Creating sentinel directory structure"
dirs=(
    "${SENTINEL_ROOT}/witness"
    "${SENTINEL_ROOT}/witness/audit_shadow"
    "${SENTINEL_ROOT}/sentinel"
    "${SENTINEL_ROOT}/alerts"
    "${SENTINEL_ROOT}/heartbeat"
)
for d in "${dirs[@]}"; do
    mkdir -p "$d"
    chown "${PH6_USER}:${PH6_USER}" "$d"
done
pass "Sentinel directories created"

# ── 4. NODE ROLE MARKER ───────────────────────────────────────────────────────
mkdir -p /etc/ph6
cat > /etc/ph6/node.conf << 'EOF'
# PH6 Node Configuration
# DO NOT EDIT without governance update
PH6_NODE_DESIGNATION=PH6-L0.5-SENTINEL-WITNESS
PH6_NODE_HOSTNAME=ph6-zero-sentinel
PH6_NODE_AUTHORITY_TIER=0.5
PH6_NODE_AUTHORITY_LEVEL=ZERO
PH6_PASS_AUTHORITY=false
PH6_CRAM_A_AUTHORITY=false
PH6_AUDIT_CHAIN_AUTHORITY=false
PH6_DROP_SPIGOT_ENABLED=false
EOF

# ── 5. HEARTBEAT WATCH SERVICE ────────────────────────────────────────────────
log "Installing heartbeat watch service"
cat > "${SERVICE_DIR}/ph6-heartbeat-watch.service" << EOF
[Unit]
Description=PH6 Heartbeat Watch (Sentinel)
After=network.target

[Service]
Type=simple
User=${PH6_USER}
ExecStart=/bin/bash /usr/local/bin/ph6-heartbeat-watch.sh
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
EOF

cat > /usr/local/bin/ph6-heartbeat-watch.sh << EOF
#!/bin/bash
# PH6 heartbeat monitor -- runs continuously
LOG="${SENTINEL_ROOT}/heartbeat/heartbeat.log"
ALERT_DIR="${SENTINEL_ROOT}/alerts"
while true; do
    ts=\$(date -u +%Y-%m-%dT%H:%M:%SZ)
    for node in "${PH6_FASTPI}" "${PH6_JACKJACK}"; do
        if ping -c 1 -W 5 "\$node" &>/dev/null; then
            echo "\$ts ALIVE \$node" >> "\$LOG"
        else
            echo "\$ts UNREACHABLE \$node" >> "\$LOG"
            echo "\$ts ALERT: \$node unreachable" >> "\${ALERT_DIR}/node_down.log"
        fi
    done
    sleep 60
done
EOF
chmod +x /usr/local/bin/ph6-heartbeat-watch.sh

# ── 6. RSYNC SENTINEL SERVICE ─────────────────────────────────────────────────
log "Installing RSYNC sentinel service"
cat > "${SERVICE_DIR}/ph6-rsync-sentinel.service" << EOF
[Unit]
Description=PH6 RSYNC Export Sentinel
After=network.target ph6-heartbeat-watch.service

[Service]
Type=simple
User=${PH6_USER}
ExecStart=/bin/bash /usr/local/bin/ph6-rsync-sentinel.sh
Restart=always
RestartSec=60

[Install]
WantedBy=multi-user.target
EOF

cat > /usr/local/bin/ph6-rsync-sentinel.sh << EOF
#!/bin/bash
# PH6 RSYNC sentinel -- monitors export continuity
SENTINEL_LOG="${SENTINEL_ROOT}/sentinel/rsync.log"
ALERT_DIR="${SENTINEL_ROOT}/alerts"
SHADOW_DIR="${SENTINEL_ROOT}/witness/audit_shadow"
FASTPI_AUDIT="${PH6_USER}@${PH6_FASTPI}:/var/ph6/audit/"
while true; do
    ts=\$(date -u +%Y-%m-%dT%H:%M:%SZ)
    # Pull audit shadow copy (witness -- does not alter source)
    if rsync -aq --timeout=30 "\${FASTPI_AUDIT}" "\${SHADOW_DIR}/" 2>/dev/null; then
        echo "\$ts RSYNC_OK shadow_pull from ${PH6_FASTPI}" >> "\$SENTINEL_LOG"
    else
        echo "\$ts RSYNC_FAIL shadow_pull from ${PH6_FASTPI}" >> "\$SENTINEL_LOG"
        echo "\$ts ALERT: RSYNC shadow pull failed" >> "\${ALERT_DIR}/rsync_fail.log"
    fi
    sleep 300
done
EOF
chmod +x /usr/local/bin/ph6-rsync-sentinel.sh

# ── 7. WITNESS TIMESTAMP SERVICE ─────────────────────────────────────────────
log "Installing witness timestamp service"
cat > "${SERVICE_DIR}/ph6-witness-timestamp.service" << EOF
[Unit]
Description=PH6 Witness Timestamp Log
After=network.target

[Service]
Type=simple
User=${PH6_USER}
ExecStart=/bin/bash /usr/local/bin/ph6-witness-timestamp.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

cat > /usr/local/bin/ph6-witness-timestamp.sh << EOF
#!/bin/bash
# PH6 independent witness timestamp -- runs every 30s
LOG="${SENTINEL_ROOT}/witness/timestamps.log"
while true; do
    echo "\$(date -u +%Y-%m-%dT%H:%M:%SZ) WITNESS_TICK sentinel_alive" >> "\$LOG"
    sleep 30
done
EOF
chmod +x /usr/local/bin/ph6-witness-timestamp.sh

# ── 8. ENABLE AND START SERVICES ─────────────────────────────────────────────
log "Enabling sentinel services"
systemctl daemon-reload
for svc in ph6-heartbeat-watch ph6-rsync-sentinel ph6-witness-timestamp; do
    systemctl enable "${svc}.service"
    systemctl start "${svc}.service" 2>/dev/null && pass "${svc} started" || warn "${svc} failed to start -- check: journalctl -u ${svc}"
done

# ── 9. INITIAL CONNECTIVITY TEST ─────────────────────────────────────────────
log ""
log "=== INITIAL CONNECTIVITY ==="
for node in "${PH6_FASTPI}" "${PH6_JACKJACK}"; do
    if ping -c 2 -W 5 "$node" &>/dev/null; then
        pass "Reachable: ${node}"
    else
        warn "Unreachable: ${node} (expected if not yet connected)"
    fi
done

log ""
log "=== SENTINEL BOOTSTRAP COMPLETE ==="
pass "ph6-zero-sentinel configured"
log "Services: heartbeat-watch | rsync-sentinel | witness-timestamp"
log "Logs at:  ${SENTINEL_ROOT}/heartbeat/ | ${SENTINEL_ROOT}/sentinel/ | ${SENTINEL_ROOT}/witness/"
log "Alerts:   ${SENTINEL_ROOT}/alerts/"
