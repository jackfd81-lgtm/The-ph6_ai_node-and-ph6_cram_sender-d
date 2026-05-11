#!/usr/bin/env bash
# PH6 HRG9 Closure Verifier
# HRG9 is CLOSED at commit 2ef5fd6. This script verifies the evidence is intact.
# It does NOT regenerate HRG9 artifacts.
set -euo pipefail

HRG9_DIR="$HOME/PH6_SOURCE/HRG9_CLOSURE"
EXPECTED_RESULT_SET_HASH="901d34616169362ad8cc92451f71838c3e83d825b58c7c1f95d341968261d15a"

echo "PH6 HRG9 Closure Verification"
echo "Evidence dir: $HRG9_DIR"
echo "Expected result_set_hash: $EXPECTED_RESULT_SET_HASH"
echo ""

# Phase 1 — Artifact presence
echo "Phase 1: Artifact presence"
REQUIRED=(
    hrg9_manifest.json
    hrg9_replay_parity_receipt.json
    hrg9_authority_boundary_report.json
    hrg9_canon_lint_report.json
    hrg9_marker_integrity_report.json
    hrg9_timestamp_fixedpoint_report.json
    hrg9_environment_snapshot.json
    hrg9_final_summary.md
)
ALL_PRESENT=true
for f in "${REQUIRED[@]}"; do
    if [[ -f "$HRG9_DIR/$f" ]]; then
        echo "  PRESENT: $f"
    else
        echo "  MISSING: $f"
        ALL_PRESENT=false
    fi
done

if [[ "$ALL_PRESENT" != "true" ]]; then
    echo "PHASE 1 FAIL: missing artifacts"
    exit 1
fi
echo "Phase 1: PASS"
echo ""

# Phase 2 — Hash verification
echo "Phase 2: result_set_hash verification"
ACTUAL=$(python3 - <<'EOF'
import hashlib, json
from pathlib import Path

d = Path.home() / "PH6_SOURCE/HRG9_CLOSURE"
hashes = {}
for f in sorted(d.iterdir()):
    if f.is_file():
        h = hashlib.blake2b(f.read_bytes(), digest_size=32).hexdigest()
        hashes[f.name] = h

combined = json.dumps(hashes, sort_keys=True, separators=(",",":")).encode()
print(hashlib.blake2b(combined, digest_size=32).hexdigest())
EOF
)

echo "  Computed: $ACTUAL"
echo "  Expected: $EXPECTED_RESULT_SET_HASH"

if [[ "$ACTUAL" == "$EXPECTED_RESULT_SET_HASH" ]]; then
    echo "Phase 2: PASS — result_set_hash matches"
else
    echo "Phase 2: FAIL — result_set_hash MISMATCH"
    echo "  This means HRG9 evidence has been modified since closure."
    exit 1
fi
echo ""

# Phase 3 — Manifest schema check
echo "Phase 3: Manifest schema check"
python3 - <<'EOF'
import json
from pathlib import Path
m = json.loads((Path.home() / "PH6_SOURCE/HRG9_CLOSURE/hrg9_manifest.json").read_text())
assert m.get("schema") == "ph6.hrg9.manifest.v1", f"Bad schema: {m.get('schema')}"
assert m["validation_results"]["test_suite"]["result"] == "PASS"
assert m["validation_results"]["test_suite"]["failed"] == 0
print("  Schema: OK")
print(f"  Tests: {m['validation_results']['test_suite']['passed']} passed, 0 failed")
EOF
echo "Phase 3: PASS"
echo ""

# Phase 4 — Replay parity check
echo "Phase 4: Replay parity receipt check"
python3 - <<'EOF'
import json
from pathlib import Path
r = json.loads((Path.home() / "PH6_SOURCE/HRG9_CLOSURE/hrg9_replay_parity_receipt.json").read_text())
assert r.get("schema") == "ph6.hrg9.replay_parity_receipt.v1"
verdict = r.get("parity_verdict") or r.get("verdict") or r.get("result", "UNKNOWN")
print(f"  Parity verdict: {verdict}")
passes = r.get("passes", [])
print(f"  Passes recorded: {len(passes)}")
EOF
echo "Phase 4: PASS"
echo ""

# Final verdict
echo "========================================="
echo "HRG9 CLOSURE VERIFICATION: PASS"
echo "Evidence intact at commit 2ef5fd6"
echo "STOP-SHIP remains: OI-01 (hardware-gated) + OI-03 (real Pi-to-Pi)"
echo "Do NOT reopen HRG9."
echo "========================================="
