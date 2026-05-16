"""
OI-03 Phase 1 — RSYNC Priority Zero Verification

Proves RSYNC export is not blocked, starved, or subordinated while
the CRAM-PU Lane-1 pipeline is under operational load.

Doctrine:
  A transferred hash only has evidentiary weight after the export path
  proves it cannot be starved.  Phase 1 proves export sovereignty first.

Load profile during verification:
  - Lane-1 ingest (N synthetic packets, CRAM atomic writes)
  - PSEUDO evaluation (entropy / laplacian_var / motion_fraction)
  - TOK advisory sidecar (Lane-2, MRAM-S only)
  - Disk I/O pressure (JSONL appends + fsync per record)

Test procedure:
  1. Populate source CRAM store (pipeline run, N packets)
  2. Baseline: time rsync(source → dest_baseline), no load
  3. Under load: start rsync(source → dest_loaded) concurrently with a
     new N-packet pipeline run in a separate load directory
  4. Verify: rsync completed, load_ratio < LOAD_RATIO_MAX

Pass conditions (ALL must hold):
  - rsync exit code 0 (not killed, not timed out)
  - rsync ran concurrently with pipeline (overlap_s > 0)
  - load_ratio = loaded_s / baseline_s < LOAD_RATIO_MAX

Failure conditions:
  - rsync timeout or non-zero exit → BLOCKED (governance failure)
  - load_ratio >= LOAD_RATIO_MAX    → SUBORDINATED (governance failure)
  - overlap_s == 0                  → NO_CONCURRENT_LOAD (test invalid)

Evidence schema: ph6.oi03.rsync_priority.v1
"""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJ = HERE.parent.parent.parent
sys.path.insert(0, str(PROJ))

from ph6.cram_pu.cram_pu_live import run as pipeline_run
from ph6.cram_pu.schemas.canonical import blake2b_256, canonical_json

# ---------------------------------------------------------------------------
# Policy constants
# ---------------------------------------------------------------------------

RSYNC_TIMEOUT_S  = 120    # rsync must complete within 2 minutes
LOAD_RATIO_MAX   = 10.0   # loaded_s / baseline_s must be < this
PIPELINE_PACKETS = 300    # packets for both source population and load run

RECEIPTS_DIR = Path("/home/jack/PH6_SOURCE/EVIDENCE_CAMPAIGNS/RECEIPTS")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _atomic_write_json(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(str(path) + ".tmp")
    data = (json.dumps(record, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False, allow_nan=False) + "\n").encode()
    fd = os.open(str(tmp), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)
    try:
        os.write(fd, data)
        os.fsync(fd)
    finally:
        os.close(fd)
    os.replace(str(tmp), str(path))
    dir_fd = os.open(str(path.parent), os.O_RDONLY)
    try:
        os.fsync(dir_fd)
    finally:
        os.close(dir_fd)


def _run_rsync(src: Path, dst: Path,
               timeout_s: float = RSYNC_TIMEOUT_S) -> dict:
    """
    Run rsync -a --checksum src/ dst/ and return timing + exit info.
    Returns dict with: exit_code, elapsed_s, stdout, stderr, timed_out.
    """
    dst.mkdir(parents=True, exist_ok=True)
    cmd = ["rsync", "-a", "--checksum",
           str(src) + "/", str(dst) + "/"]
    t0 = time.monotonic()
    timed_out = False
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=timeout_s,
        )
        exit_code = result.returncode
        stdout = result.stdout.decode(errors="replace")
        stderr = result.stderr.decode(errors="replace")
    except subprocess.TimeoutExpired as e:
        timed_out = True
        exit_code = -1
        stdout = ""
        stderr = f"rsync timed out after {timeout_s}s"
    elapsed_s = time.monotonic() - t0
    return {
        "exit_code":  exit_code,
        "elapsed_s":  round(elapsed_s, 4),
        "timed_out":  timed_out,
        "stdout":     stdout[:500],
        "stderr":     stderr[:500],
        "ok":         (exit_code == 0 and not timed_out),
    }


def _run_pipeline_in_thread(n_packets: int,
                             base_dir: Path) -> dict:
    """Run pipeline_run() and return result + elapsed."""
    t0 = time.monotonic()
    result = pipeline_run(n_packets=n_packets, base_dir=base_dir,
                          tok_enabled=True)
    result["elapsed_s"] = round(time.monotonic() - t0, 4)
    return result


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run(n_packets: int = PIPELINE_PACKETS,
        work_dir: Path | None = None) -> dict:

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_id = str(uuid.uuid4())
    node = socket.gethostname()

    if work_dir is None:
        work_dir = (PROJ / "ph6" / "cram_pu" / "runtime"
                    / f"oi03_phase1_{stamp}")
    work_dir.mkdir(parents=True, exist_ok=True)

    print(f"\nOI-03 Phase 1 — RSYNC Priority Zero Verification")
    print(f"  stamp     : {stamp}")
    print(f"  node      : {node}")
    print(f"  packets   : {n_packets}")
    print(f"  work_dir  : {work_dir}")
    print()

    failure_reasons: list[str] = []

    # ------------------------------------------------------------------
    # Step 1: Populate source CRAM store
    # ------------------------------------------------------------------
    print("Step 1: Populating source CRAM store ...")
    source_dir = work_dir / "source_run"
    t0 = time.monotonic()
    source_result = pipeline_run(n_packets=n_packets, base_dir=source_dir,
                                 tok_enabled=True)
    source_elapsed = round(time.monotonic() - t0, 4)
    print(f"  source pipeline: PASS={source_result['ok']} "
          f"elapsed={source_elapsed}s "
          f"result_set_hash={source_result['result_set_hash'][:16]}…")

    # ------------------------------------------------------------------
    # Step 2: Baseline rsync — no load
    # ------------------------------------------------------------------
    print("\nStep 2: Baseline rsync (no load) ...")
    dest_baseline = work_dir / "dest_baseline"
    baseline = _run_rsync(source_dir, dest_baseline)
    print(f"  rsync exit={baseline['exit_code']} "
          f"elapsed={baseline['elapsed_s']}s "
          f"ok={baseline['ok']}")
    if not baseline["ok"]:
        failure_reasons.append(
            f"baseline_rsync_failed: exit={baseline['exit_code']} "
            f"timed_out={baseline['timed_out']}"
        )

    # ------------------------------------------------------------------
    # Step 3: Populate a second source store (will be rsync'd under load)
    # ------------------------------------------------------------------
    print("\nStep 3: Populating second CRAM store for load test ...")
    source2_dir = work_dir / "source2_run"
    source2_result = pipeline_run(n_packets=n_packets, base_dir=source2_dir,
                                  tok_enabled=True)
    print(f"  source2 pipeline: PASS={source2_result['ok']} "
          f"result_set_hash={source2_result['result_set_hash'][:16]}…")

    # ------------------------------------------------------------------
    # Step 4: Concurrent — rsync + pipeline load simultaneously
    # ------------------------------------------------------------------
    print("\nStep 4: Concurrent rsync + Lane-1 pipeline load ...")
    dest_loaded  = work_dir / "dest_loaded"
    load_dir     = work_dir / "load_run"

    rsync_result: dict = {}
    pipeline_result: dict = {}
    rsync_start = rsync_end = pipeline_start = pipeline_end = 0.0

    rsync_thread_exc: list = []
    pipeline_thread_exc: list = []

    def rsync_worker():
        nonlocal rsync_start, rsync_end, rsync_result
        rsync_start = time.monotonic()
        try:
            rsync_result = _run_rsync(source2_dir, dest_loaded)
        except Exception as e:
            rsync_thread_exc.append(e)
            rsync_result = {"ok": False, "exit_code": -1,
                            "elapsed_s": 0, "timed_out": False,
                            "stderr": str(e), "stdout": ""}
        finally:
            rsync_end = time.monotonic()

    def pipeline_worker():
        nonlocal pipeline_start, pipeline_end, pipeline_result
        pipeline_start = time.monotonic()
        try:
            pipeline_result = _run_pipeline_in_thread(n_packets, load_dir)
        except Exception as e:
            pipeline_thread_exc.append(e)
            pipeline_result = {"ok": False, "elapsed_s": 0}
        finally:
            pipeline_end = time.monotonic()

    t_rsync    = threading.Thread(target=rsync_worker,    daemon=False)
    t_pipeline = threading.Thread(target=pipeline_worker, daemon=False)

    # Start rsync first — it is Priority Zero
    t_rsync.start()
    time.sleep(0.05)          # brief yield, then start load
    t_pipeline.start()

    t_rsync.join(timeout=RSYNC_TIMEOUT_S + 10)
    t_pipeline.join(timeout=RSYNC_TIMEOUT_S + 10)

    rsync_elapsed    = round(rsync_end    - rsync_start, 4) if rsync_end    else 0.0
    pipeline_elapsed = round(pipeline_end - pipeline_start, 4) if pipeline_end else 0.0

    # Compute overlap: how long rsync and pipeline ran concurrently
    overlap_start = max(rsync_start, pipeline_start)
    overlap_end   = min(rsync_end, pipeline_end)
    overlap_s     = round(max(0.0, overlap_end - overlap_start), 4)

    print(f"  rsync   : exit={rsync_result.get('exit_code', '?')} "
          f"elapsed={rsync_elapsed}s ok={rsync_result.get('ok')}")
    print(f"  pipeline: elapsed={pipeline_elapsed}s "
          f"ok={pipeline_result.get('ok')}")
    print(f"  overlap : {overlap_s}s")

    # ------------------------------------------------------------------
    # Step 5: Evaluate
    # ------------------------------------------------------------------
    baseline_s = baseline["elapsed_s"]
    loaded_s   = rsync_elapsed

    load_ratio = round(loaded_s / baseline_s, 4) if baseline_s > 0 else 0.0

    if not rsync_result.get("ok"):
        failure_reasons.append(
            f"loaded_rsync_failed: exit={rsync_result.get('exit_code')} "
            f"timed_out={rsync_result.get('timed_out')}"
        )
    if overlap_s == 0:
        failure_reasons.append("no_concurrent_overlap: test invalid")
    if load_ratio >= LOAD_RATIO_MAX:
        failure_reasons.append(
            f"load_ratio_exceeded: {load_ratio:.2f} >= {LOAD_RATIO_MAX}"
        )

    status = "PASS" if not failure_reasons else "FAIL"

    print(f"\n  baseline_rsync_s : {baseline_s}")
    print(f"  loaded_rsync_s   : {loaded_s}")
    print(f"  load_ratio       : {load_ratio:.2f}  (max {LOAD_RATIO_MAX})")
    print(f"  rsync_blocked    : {not rsync_result.get('ok', False)}")
    print(f"  OI03_PHASE1      : {status}")

    # ------------------------------------------------------------------
    # Evidence packet
    # ------------------------------------------------------------------
    receipt = {
        "schema":                 "ph6.oi03.rsync_priority.v1",
        "phase":                  "PHASE_1_RSYNC_PRIORITY",
        "run_id":                 run_id,
        "generated_at_utc":       stamp,
        "node":                   node,
        "status":                 status,
        "failure_reasons":        failure_reasons,

        "pipeline_packets":       n_packets,
        "rsync_timeout_policy_s": RSYNC_TIMEOUT_S,
        "load_ratio_max_policy":  LOAD_RATIO_MAX,

        "rsync_baseline_s":       baseline_s,
        "rsync_loaded_s":         loaded_s,
        "load_ratio":             load_ratio,
        "overlap_s":              overlap_s,

        "rsync_exit_code":        rsync_result.get("exit_code", -1),
        "rsync_timed_out":        rsync_result.get("timed_out", False),
        "rsync_blocked":          not rsync_result.get("ok", False),
        "rsync_ok":               rsync_result.get("ok", False),

        "lane1_load_active":      True,
        "tok_load_active":        True,
        "pipeline_ok":            pipeline_result.get("ok", False),
        "pipeline_elapsed_s":     pipeline_elapsed,

        "source_result_set_hash": source_result.get("result_set_hash", ""),
        "source2_result_set_hash": source2_result.get("result_set_hash", ""),
        "work_dir":               str(work_dir),

        "authority":              "NONE",
        "doctrine":               (
            "A transferred hash only has evidentiary weight after the export "
            "path proves it cannot be starved."
        ),
    }

    # Write local evidence
    local_receipt = work_dir / "phase1_receipt.json"
    _atomic_write_json(local_receipt, receipt)

    # Write to canonical receipts dir
    RECEIPTS_DIR.mkdir(parents=True, exist_ok=True)
    receipt_name = f"OI03_PHASE1_RSYNC_PRIORITY_{stamp}.json"
    canonical_receipt = RECEIPTS_DIR / receipt_name
    _atomic_write_json(canonical_receipt, receipt)

    receipt_hash = blake2b_256(canonical_json(receipt))

    print(f"\n  Receipt  : {canonical_receipt}")
    print(f"  Hash     : {receipt_hash}")
    print(f"\nOI03_PHASE1_RSYNC_PRIORITY_{status}=True")

    return receipt


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--packets",  type=int,  default=PIPELINE_PACKETS,
                    help="Packets for source population and load run")
    ap.add_argument("--work-dir", type=Path, default=None)
    args = ap.parse_args()
    result = run(n_packets=args.packets, work_dir=args.work_dir)
    sys.exit(0 if result["status"] == "PASS" else 1)
