#!/usr/bin/env bash
# CRAM-PU-LIVE-1.0 acceptance test
# Runs the full pipeline: departure → arrival → continuity →
# verdict → commit → shedding → replay → receipt
# Pass condition: CRAM_PU_RUNTIME_WIRED = true

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
TOOLS="$SCRIPT_DIR"
RUN_DIR="/tmp/cram_pu_live_test_$$"

echo "=== CRAM-PU-LIVE-1.0 Runtime Test ==="
echo "Run dir: $RUN_DIR"
mkdir -p "$RUN_DIR/cram_commits"

# Make ph6 importable
export PYTHONPATH="$REPO_ROOT:${PYTHONPATH:-}"

# ── generate test packets ─────────────────────────────────────────────────────
python3 - <<PYEOF
import base64, hashlib, json, sys, uuid
import numpy as np
import cv2
from pathlib import Path

rng    = np.random.default_rng(42)
run_dir = Path("$RUN_DIR")

packets = []
# 5 PASS frames: normal brightness, sharp
for i in range(5):
    frame = np.full((64, 64, 3), 128, dtype=np.uint8)
    frame[20:44, 20:44] = rng.integers(60, 200, (24, 24, 3), dtype=np.uint8)
    ok, buf = cv2.imencode(".jpg", frame)
    payload = buf.tobytes()
    packets.append(("PASS", str(uuid.uuid4()), payload))

# 2 DROP frames: dark (brightness_low)
for i in range(2):
    frame = np.full((64, 64, 3), 10, dtype=np.uint8)
    ok, buf = cv2.imencode(".jpg", frame)
    payload = buf.tobytes()
    packets.append(("DROP", str(uuid.uuid4()), payload))

# Save payloads map for later tools
payloads_map = {pid: base64.b64encode(data).decode() for _, pid, data in packets}
(run_dir / "payloads.json").write_text(json.dumps(payloads_map))

# Save packet list
packet_list = [{"expected": exp, "packet_id": pid} for exp, pid, _ in packets]
(run_dir / "packet_list.json").write_text(json.dumps(packet_list))

print(f"Generated {len(packets)} packets ({sum(1 for e,_,_ in packets if e=='PASS')} PASS, {sum(1 for e,_,_ in packets if e=='DROP')} DROP)")
PYEOF

# ── phase 2: departure writer ─────────────────────────────────────────────────
echo ""
echo "--- Phase 2: Departure ---"
python3 - <<PYEOF
import base64, json, sys, time, os
from pathlib import Path
sys.path.insert(0, "$REPO_ROOT")
from ph6.cram_pu.tools.source_departure_writer import DepartureWriter

run_dir = Path("$RUN_DIR")
payloads = {k: base64.b64decode(v) for k, v in json.loads((run_dir/"payloads.json").read_text()).items()}
plist    = json.loads((run_dir/"packet_list.json").read_text())

writer = DepartureWriter(run_dir / "departure_log.jsonl")
for p in plist:
    writer.write(p["packet_id"], payloads[p["packet_id"]])
print(f"Departures written: {len(plist)}")
PYEOF

# ── phase 3: arrival receiver ─────────────────────────────────────────────────
echo "--- Phase 3: Arrival ---"
python3 - <<PYEOF
import base64, json, sys
from pathlib import Path
sys.path.insert(0, "$REPO_ROOT")
from ph6.cram_pu.tools.cram_pu_receiver import receive_from_departures

run_dir  = Path("$RUN_DIR")
payloads = {k: base64.b64decode(v) for k, v in json.loads((run_dir/"payloads.json").read_text()).items()}
with (run_dir/"departure_log.jsonl").open() as f:
    deps = [json.loads(l) for l in f if l.strip()]
arrivals = receive_from_departures(deps, payloads, run_dir/"arrival_log.jsonl")
ok_count = sum(1 for a in arrivals if a["transfer_status"] == "OK")
print(f"Arrivals written: {len(arrivals)}  OK={ok_count}")
PYEOF

# ── phase 4: continuity check ─────────────────────────────────────────────────
echo "--- Phase 4: Continuity ---"
python3 "$TOOLS/cram_pu_continuity_check.py" \
  --departure-log "$RUN_DIR/departure_log.jsonl" \
  --arrival-log   "$RUN_DIR/arrival_log.jsonl" \
  --report        "$RUN_DIR/continuity_report.json"

# ── phase 5: verdict runner ───────────────────────────────────────────────────
echo "--- Phase 5: Verdicts ---"
python3 - <<PYEOF
import base64, json, sys
from pathlib import Path
sys.path.insert(0, "$REPO_ROOT")
from ph6.cram_pu.tools.cram_pu_verdict_runner import run_verdicts

run_dir  = Path("$RUN_DIR")
payloads = {k: base64.b64decode(v) for k, v in json.loads((run_dir/"payloads.json").read_text()).items()}
with (run_dir/"arrival_log.jsonl").open() as f:
    arrivals = [json.loads(l) for l in f if l.strip()]
results = run_verdicts(arrivals, payloads, run_dir/"verdicts.jsonl")
passes = sum(1 for r in results if r["verdict"]=="PASS")
drops  = sum(1 for r in results if r["verdict"]=="DROP")
print(f"Verdicts: {len(results)}  PASS={passes}  DROP={drops}")
PYEOF

# ── phase 6: atomic commit ────────────────────────────────────────────────────
echo "--- Phase 6: Commit ---"
python3 "$TOOLS/cram_pu_atomic_commit.py" \
  --verdict-log "$RUN_DIR/verdicts.jsonl" \
  --cram-dir    "$RUN_DIR/cram_commits"

# ── phase 7: shedding ─────────────────────────────────────────────────────────
echo "--- Phase 7: Shedding ---"
python3 "$TOOLS/cram_pu_shedding.py" \
  --verdict-log  "$RUN_DIR/verdicts.jsonl" \
  --shedding-log "$RUN_DIR/shedding_log.jsonl"

# ── phase 8: replay verify ────────────────────────────────────────────────────
echo "--- Phase 8: Replay ---"
python3 - <<PYEOF
import base64, json, sys
from pathlib import Path
sys.path.insert(0, "$REPO_ROOT")
from ph6.cram_pu.tools.cram_pu_replay_verify import verify_replay

run_dir  = Path("$RUN_DIR")
payloads = {k: base64.b64decode(v) for k, v in json.loads((run_dir/"payloads.json").read_text()).items()}
with (run_dir/"verdicts.jsonl").open() as f:
    verdicts = [json.loads(l) for l in f if l.strip()]
report = verify_replay(verdicts, payloads, run_dir/"cram_commits", run_dir/"replay_report.json")
status = "PASS" if report["ok"] else "FAIL"
print(f"REPLAY: {status}  replayed={report['replayed']}  mismatches={len(report['mismatches'])}  chain_valid={report['chain_valid']}")
PYEOF

# ── phase 9: postrun receipt ──────────────────────────────────────────────────
echo "--- Phase 9: Receipt ---"
python3 "$TOOLS/cram_pu_postrun_receipt.py" \
  --run-dir "$RUN_DIR" \
  --receipt "$RUN_DIR/postrun_receipt.json"

# ── output manifest ───────────────────────────────────────────────────────────
echo ""
echo "=== Output Files ==="
for f in departure_log.jsonl arrival_log.jsonl continuity_report.json \
          verdicts.jsonl shedding_log.jsonl replay_report.json postrun_receipt.json; do
  if [ -f "$RUN_DIR/$f" ]; then
    echo "  OK  $f"
  else
    echo "  MISSING  $f"
  fi
done
cram_count=$(ls "$RUN_DIR/cram_commits"/cram_*.json 2>/dev/null | wc -l)
echo "  OK  cram_commits/ ($cram_count files)"
