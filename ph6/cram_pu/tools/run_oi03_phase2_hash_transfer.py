"""
OI-03 Phase 2 — Result-Set-Hash Transfer Verification

After Phase 1 proves export sovereignty, Phase 2 proves deterministic
evidence identity survives transfer unchanged.

Prerequisite: Phase 1 PASS (RSYNC Priority Zero Verification).

Verification set:
  - manifest.json           (result_set_hash, run_id, counts)
  - verdict_log.jsonl       (Lane-1 verdict sequence)
  - .blake2b markers        (per-CRAM-file integrity markers)
  - CRAM commit files       (*.json in cram_store)
  - cram_store/rsync_queue  (export health record)

Required equality checks:
  - source result_set_hash == destination result_set_hash
  - source .blake2b file count == destination .blake2b file count
  - per-file .blake2b content matches (source vs dest)
  - CRAM file count matches
  - manifest run_id matches

Failure condition:
  Any mismatch keeps OI-03 OPEN.

Evidence schema: ph6.oi03.hash_transfer.v1
"""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJ = HERE.parent.parent.parent
sys.path.insert(0, str(PROJ))

from ph6.cram_pu.cram_pu_live import run as pipeline_run
from ph6.cram_pu.schemas.canonical import blake2b_256, canonical_json

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


def _file_hash(path: Path) -> str:
    """BLAKE2b-256 of a file's bytes."""
    import hashlib
    h = hashlib.blake2b(digest_size=32)
    h.update(path.read_bytes())
    return h.hexdigest()


def _rsync_dir(src: Path, dst: Path, timeout_s: float = 120) -> dict:
    """Rsync src/ to dst/ with checksum verification."""
    dst.mkdir(parents=True, exist_ok=True)
    cmd = ["rsync", "-a", "--checksum",
           str(src) + "/", str(dst) + "/"]
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=timeout_s)
        return {
            "exit_code": result.returncode,
            "ok": result.returncode == 0,
            "stderr": result.stderr.decode(errors="replace")[:300],
        }
    except subprocess.TimeoutExpired:
        return {"exit_code": -1, "ok": False,
                "stderr": f"timeout after {timeout_s}s"}


def _collect_evidence_snapshot(run_dir: Path,
                                cram_store: Path) -> dict:
    """
    Collect the full evidence snapshot from a CRAM-PU run directory.
    Returns a dict suitable for comparison between source and destination.
    """
    snapshot: dict = {
        "run_dir":            str(run_dir),
        "result_set_hash":    None,
        "manifest_run_id":    None,
        "cram_file_count":    0,
        "blake2b_marker_count": 0,
        "blake2b_markers":    {},    # filename → hash-of-file-content
        "cram_file_hashes":   {},    # filename → hash-of-file-content
        "verdict_log_hash":   None,
        "manifest_hash":      None,
        "errors":             [],
    }

    # manifest.json — contains result_set_hash
    manifest_path = run_dir / "manifest.json"
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            snapshot["result_set_hash"] = manifest.get("result_set_hash")
            snapshot["manifest_run_id"] = manifest.get("run_id")
            snapshot["manifest_hash"]   = _file_hash(manifest_path)
        except Exception as e:
            snapshot["errors"].append(f"manifest read error: {e}")
    else:
        snapshot["errors"].append("manifest.json missing")

    # .blake2b markers
    if cram_store.exists():
        markers = sorted(cram_store.glob("*.blake2b"))
        snapshot["blake2b_marker_count"] = len(markers)
        for m in markers:
            snapshot["blake2b_markers"][m.name] = m.read_text().strip()

        # CRAM JSON files
        cram_files = sorted(cram_store.glob("cram_*.json"))
        snapshot["cram_file_count"] = len(cram_files)
        for cf in cram_files:
            snapshot["cram_file_hashes"][cf.name] = _file_hash(cf)
    else:
        snapshot["errors"].append(f"cram_store missing: {cram_store}")

    # verdict_log
    verdict_log = cram_store / "verdict_log.jsonl"
    if verdict_log.exists():
        snapshot["verdict_log_hash"] = _file_hash(verdict_log)
    else:
        snapshot["errors"].append("verdict_log.jsonl missing")

    return snapshot


def _compare_snapshots(src: dict, dst: dict) -> list[str]:
    """
    Compare source and destination snapshots.
    Returns list of mismatch descriptions (empty = match).
    """
    mismatches: list[str] = []

    # result_set_hash
    if src["result_set_hash"] != dst["result_set_hash"]:
        mismatches.append(
            f"result_set_hash mismatch: "
            f"src={src['result_set_hash']!r} "
            f"dst={dst['result_set_hash']!r}"
        )

    # manifest run_id
    if src["manifest_run_id"] != dst["manifest_run_id"]:
        mismatches.append(
            f"manifest run_id mismatch: "
            f"src={src['manifest_run_id']!r} "
            f"dst={dst['manifest_run_id']!r}"
        )

    # .blake2b marker count
    if src["blake2b_marker_count"] != dst["blake2b_marker_count"]:
        mismatches.append(
            f"blake2b_marker_count mismatch: "
            f"src={src['blake2b_marker_count']} "
            f"dst={dst['blake2b_marker_count']}"
        )

    # Per-marker content
    for name, src_content in src["blake2b_markers"].items():
        dst_content = dst["blake2b_markers"].get(name)
        if dst_content is None:
            mismatches.append(f"blake2b marker missing in dst: {name}")
        elif src_content != dst_content:
            mismatches.append(
                f"blake2b marker content mismatch: {name} "
                f"src={src_content[:16]}… dst={dst_content[:16]}…"
            )

    # CRAM file count
    if src["cram_file_count"] != dst["cram_file_count"]:
        mismatches.append(
            f"cram_file_count mismatch: "
            f"src={src['cram_file_count']} dst={dst['cram_file_count']}"
        )

    # Per-CRAM-file hash
    for name, src_hash in src["cram_file_hashes"].items():
        dst_hash = dst["cram_file_hashes"].get(name)
        if dst_hash is None:
            mismatches.append(f"CRAM file missing in dst: {name}")
        elif src_hash != dst_hash:
            mismatches.append(f"CRAM file hash mismatch: {name}")

    # verdict_log
    if src["verdict_log_hash"] != dst["verdict_log_hash"]:
        mismatches.append(
            f"verdict_log_hash mismatch: "
            f"src={src['verdict_log_hash']!r} "
            f"dst={dst['verdict_log_hash']!r}"
        )

    return mismatches


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run(n_packets: int = 300,
        work_dir: Path | None = None) -> dict:

    stamp  = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_id = str(uuid.uuid4())
    node   = socket.gethostname()

    if work_dir is None:
        work_dir = (PROJ / "ph6" / "cram_pu" / "runtime"
                    / f"oi03_phase2_{stamp}")
    work_dir.mkdir(parents=True, exist_ok=True)

    print(f"\nOI-03 Phase 2 — Result-Set-Hash Transfer Verification")
    print(f"  stamp    : {stamp}")
    print(f"  node     : {node}")
    print(f"  packets  : {n_packets}")
    print()

    failure_reasons: list[str] = []

    # ------------------------------------------------------------------
    # Step 1: Generate source CRAM store
    # ------------------------------------------------------------------
    print("Step 1: Generating source CRAM store ...")
    source_run_dir = work_dir / "source_run"
    source_cram    = source_run_dir / "cram_store"
    pipeline_result = pipeline_run(n_packets=n_packets,
                                   base_dir=source_run_dir,
                                   tok_enabled=True)
    src_result_set_hash = pipeline_result.get("result_set_hash", "")
    print(f"  pipeline PASS={pipeline_result['ok']} "
          f"result_set_hash={src_result_set_hash[:16]}…")

    # ------------------------------------------------------------------
    # Step 2: Collect source snapshot
    # ------------------------------------------------------------------
    print("\nStep 2: Collecting source evidence snapshot ...")
    src_snapshot = _collect_evidence_snapshot(source_run_dir, source_cram)
    print(f"  cram_files      : {src_snapshot['cram_file_count']}")
    print(f"  blake2b_markers : {src_snapshot['blake2b_marker_count']}")
    print(f"  result_set_hash : {str(src_snapshot['result_set_hash'])[:16]}…")
    if src_snapshot["errors"]:
        failure_reasons.append(f"source_snapshot_errors: {src_snapshot['errors']}")

    # ------------------------------------------------------------------
    # Step 3: Transfer via rsync to destination
    # ------------------------------------------------------------------
    print("\nStep 3: Transferring via rsync (source → destination) ...")
    dest_run_dir = work_dir / "dest_run"
    rsync_result = _rsync_dir(source_run_dir, dest_run_dir)
    print(f"  rsync exit={rsync_result['exit_code']} ok={rsync_result['ok']}")
    if not rsync_result["ok"]:
        failure_reasons.append(
            f"rsync_failed: {rsync_result.get('stderr', '')}"
        )

    # ------------------------------------------------------------------
    # Step 4: Collect destination snapshot
    # ------------------------------------------------------------------
    print("\nStep 4: Collecting destination evidence snapshot ...")
    dest_cram    = dest_run_dir / "cram_store"
    dst_snapshot = _collect_evidence_snapshot(dest_run_dir, dest_cram)
    print(f"  cram_files      : {dst_snapshot['cram_file_count']}")
    print(f"  blake2b_markers : {dst_snapshot['blake2b_marker_count']}")
    print(f"  result_set_hash : {str(dst_snapshot['result_set_hash'])[:16]}…")
    if dst_snapshot["errors"]:
        failure_reasons.append(f"dest_snapshot_errors: {dst_snapshot['errors']}")

    # ------------------------------------------------------------------
    # Step 5: Compare
    # ------------------------------------------------------------------
    print("\nStep 5: Comparing source vs destination ...")
    mismatches = _compare_snapshots(src_snapshot, dst_snapshot)
    if mismatches:
        for m in mismatches:
            print(f"  MISMATCH: {m}")
        failure_reasons.extend(mismatches)
    else:
        print("  All evidence fields match — identity preserved.")

    # Specific checks summary
    rsh_match     = src_snapshot["result_set_hash"] == dst_snapshot["result_set_hash"]
    b2b_count_match = (src_snapshot["blake2b_marker_count"]
                       == dst_snapshot["blake2b_marker_count"])
    b2b_content_ok = not any("blake2b" in m for m in mismatches)
    cram_count_match = (src_snapshot["cram_file_count"]
                        == dst_snapshot["cram_file_count"])
    verdict_match  = (src_snapshot["verdict_log_hash"]
                      == dst_snapshot["verdict_log_hash"])

    print(f"\n  result_set_hash match  : {rsh_match}")
    print(f"  blake2b count match    : {b2b_count_match}")
    print(f"  blake2b content match  : {b2b_content_ok}")
    print(f"  CRAM file count match  : {cram_count_match}")
    print(f"  verdict_log hash match : {verdict_match}")

    status = "PASS" if not failure_reasons else "FAIL"
    print(f"\n  OI03_PHASE2 : {status}")

    # ------------------------------------------------------------------
    # Evidence packet
    # ------------------------------------------------------------------
    receipt = {
        "schema":                   "ph6.oi03.hash_transfer.v1",
        "phase":                    "PHASE_2_HASH_TRANSFER",
        "run_id":                   run_id,
        "generated_at_utc":         stamp,
        "node":                     node,
        "status":                   status,
        "failure_reasons":          failure_reasons,
        "mismatch_count":           len(mismatches),

        "pipeline_packets":         n_packets,
        "rsync_exit_code":          rsync_result.get("exit_code", -1),
        "rsync_ok":                 rsync_result.get("ok", False),

        "source_result_set_hash":   src_snapshot["result_set_hash"],
        "dest_result_set_hash":     dst_snapshot["result_set_hash"],
        "result_set_hash_match":    rsh_match,

        "source_blake2b_count":     src_snapshot["blake2b_marker_count"],
        "dest_blake2b_count":       dst_snapshot["blake2b_marker_count"],
        "blake2b_count_match":      b2b_count_match,
        "blake2b_content_match":    b2b_content_ok,

        "source_cram_file_count":   src_snapshot["cram_file_count"],
        "dest_cram_file_count":     dst_snapshot["cram_file_count"],
        "cram_file_count_match":    cram_count_match,

        "verdict_log_hash_match":   verdict_match,
        "source_verdict_log_hash":  src_snapshot["verdict_log_hash"],
        "dest_verdict_log_hash":    dst_snapshot["verdict_log_hash"],

        # Audit chain: not yet wired in this pipeline — noted as PENDING
        "audit_chain_verified":     False,
        "audit_chain_note":         "PENDING — audit.py not yet promoted to canonical path",

        "work_dir":                 str(work_dir),
        "authority":                "NONE",
        "doctrine": (
            "A transferred hash only has evidentiary weight after the export "
            "path proves it cannot be starved. Phase 1 precedes Phase 2."
        ),
    }

    _atomic_write_json(work_dir / "phase2_receipt.json", receipt)
    RECEIPTS_DIR.mkdir(parents=True, exist_ok=True)
    receipt_name     = f"OI03_PHASE2_HASH_TRANSFER_{stamp}.json"
    canonical_receipt = RECEIPTS_DIR / receipt_name
    _atomic_write_json(canonical_receipt, receipt)

    receipt_hash = blake2b_256(canonical_json(receipt))
    print(f"\n  Receipt  : {canonical_receipt}")
    print(f"  Hash     : {receipt_hash}")
    print(f"\nOI03_PHASE2_HASH_TRANSFER_{status}=True")

    return receipt


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--packets",  type=int,  default=300)
    ap.add_argument("--work-dir", type=Path, default=None)
    args = ap.parse_args()
    result = run(n_packets=args.packets, work_dir=args.work_dir)
    sys.exit(0 if result["status"] == "PASS" else 1)
