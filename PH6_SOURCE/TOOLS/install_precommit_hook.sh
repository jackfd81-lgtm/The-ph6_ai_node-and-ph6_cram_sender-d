#!/usr/bin/env bash
# PH6 Governance Pre-Commit Hook Installer
# Lane:      2 (Advisory tooling — no authority path writes)
# Authority: ZERO
#
# Run from the repository root:
#   bash PH6_SOURCE/TOOLS/install_precommit_hook.sh
#
# Effect:
#   Copies PH6_SOURCE/TOOLS/pre-commit.ph6-governance.example to .git/hooks/pre-commit.
#   Backs up any existing hook before replacing it.
#   Sets executable bit on the installed hook.
#
# To uninstall:
#   rm .git/hooks/pre-commit

set -euo pipefail

HOOK_TEMPLATE="PH6_SOURCE/TOOLS/pre-commit.ph6-governance.example"
HOOK_TARGET=".git/hooks/pre-commit"

if [[ ! -d ".git" ]]; then
    echo "ERROR: .git directory not found." >&2
    echo "       Run this script from the repository root." >&2
    exit 1
fi

if [[ ! -f "$HOOK_TEMPLATE" ]]; then
    echo "ERROR: Hook template not found: $HOOK_TEMPLATE" >&2
    echo "       Ensure PH6_SOURCE/TOOLS/pre-commit.ph6-governance.example is present." >&2
    exit 1
fi

if [[ -f "$HOOK_TARGET" ]]; then
    BACKUP="${HOOK_TARGET}.backup.$(date -u +%Y%m%dT%H%M%SZ)"
    echo "Existing hook found — backing up to: $BACKUP"
    cp "$HOOK_TARGET" "$BACKUP"
fi

cp "$HOOK_TEMPLATE" "$HOOK_TARGET"
chmod +x "$HOOK_TARGET"

echo "Installed: $HOOK_TARGET"
echo "PH6 governance pre-commit hook is now active."
