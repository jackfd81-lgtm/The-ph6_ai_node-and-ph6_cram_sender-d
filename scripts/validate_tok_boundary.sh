#!/usr/bin/env bash
set -euo pipefail

echo "[TOK] Running lifecycle smoke test..."
python3 ph6/tok/lifecycle.py

echo "[TOK] Checking forbidden authority terms in source (*.py, excluding tests/)..."
if grep -RInE "issue_pass|issue_drop|set_pass|set_drop|modify_pseudo|write_cram|block_rsync|replay_authority" \
    --include="*.py" --exclude-dir=tests ph6/tok; then
  echo "[FAIL] Forbidden authority term found in TOK source."
  exit 1
fi

echo "[TOK] Checking forbidden PH6 write paths in source (*.py, excluding tests/)..."
if grep -RInE "/var/ph6/cram-0|/var/ph6/cram-a|/var/ph6/cram-r|/var/ph6/export|/var/ph6/audit" \
    --include="*.py" --exclude-dir=tests ph6/tok; then
  echo "[FAIL] Forbidden PH6 path found in TOK source."
  exit 1
fi

echo "[TOK] Checking required Authority ZERO markers..."
grep -RIn '"authority": "ZERO"\|authority: str = "ZERO"' ph6/tok >/dev/null

echo "[PASS] TOK boundary validation passed."
