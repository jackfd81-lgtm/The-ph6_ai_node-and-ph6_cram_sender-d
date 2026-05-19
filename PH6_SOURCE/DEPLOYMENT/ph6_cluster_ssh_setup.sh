#!/bin/bash
# PH6 cluster SSH key distribution and connectivity test
# Run from the operator node (main_pi or any connected node)
# Version: 1.0 / 2026-05-19

set -uo pipefail

NODES=(
    "ph6-fastpi"
    "jackjack"
    "ph6-zero-sentinel"
)
SSH_USER="${PH6_SSH_USER:-pi}"
KEY_FILE="${HOME}/.ssh/ph6_ed25519"

log()  { echo "[ph6-ssh-setup] $*"; }
pass() { echo "[ph6-ssh-setup] PASS: $*"; }
fail() { echo "[ph6-ssh-setup] FAIL: $*" >&2; }

# ── 1. GENERATE KEY IF NEEDED ─────────────────────────────────────────────────
if [ ! -f "${KEY_FILE}" ]; then
    log "Generating ed25519 SSH key at ${KEY_FILE}"
    ssh-keygen -t ed25519 -C "ph6-node-link-$(date +%Y%m%d)" -f "${KEY_FILE}" -N ""
    log "Key generated"
else
    log "Key ${KEY_FILE} already exists -- skipping generation"
fi

# ── 2. DISTRIBUTE KEYS ────────────────────────────────────────────────────────
log ""
log "=== DISTRIBUTING SSH KEYS ==="
failed_copy=()
for node in "${NODES[@]}"; do
    log "Copying key to ${SSH_USER}@${node}"
    if ssh-copy-id -i "${KEY_FILE}.pub" -o ConnectTimeout=10 "${SSH_USER}@${node}" 2>/dev/null; then
        pass "Key copied to ${node}"
    else
        fail "Could not copy key to ${node} -- node may be offline"
        failed_copy+=("$node")
    fi
done

# ── 3. CONNECTIVITY TEST ──────────────────────────────────────────────────────
log ""
log "=== CONNECTIVITY TEST ==="
failed_connect=()
for node in "${NODES[@]}"; do
    result=$(ssh -i "${KEY_FILE}" \
                 -o ConnectTimeout=10 \
                 -o BatchMode=yes \
                 -o StrictHostKeyChecking=accept-new \
                 "${SSH_USER}@${node}" \
                 "hostname && uname -m && cat /etc/ph6/node.conf 2>/dev/null | grep PH6_NODE_DESIGNATION || echo 'no node.conf yet'" \
                 2>/dev/null)
    if [ $? -eq 0 ]; then
        pass "${node} connected:"
        echo "$result" | sed 's/^/    /'
    else
        fail "${node} connection FAILED"
        failed_connect+=("$node")
    fi
done

# ── 4. SUMMARY ────────────────────────────────────────────────────────────────
log ""
log "=== SUMMARY ==="
log "Nodes tested: ${#NODES[@]}"
if [ ${#failed_copy[@]} -eq 0 ] && [ ${#failed_connect[@]} -eq 0 ]; then
    pass "All nodes reachable"
else
    [ ${#failed_copy[@]} -gt 0 ]    && fail "Key copy failed:    ${failed_copy[*]}"
    [ ${#failed_connect[@]} -gt 0 ] && fail "Connect failed:     ${failed_connect[*]}"
    echo ""
    echo "Offline nodes are expected if hardware is not yet connected."
    echo "Re-run this script after all nodes are powered and on the network."
fi
