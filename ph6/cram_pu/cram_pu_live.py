#!/usr/bin/env python3
"""
CRAM-PU-LIVE-1.0 runtime orchestrator.
departure → arrival → verdict → commit → shedding → MRAM-S → replay proof

Usage:
    python3 cram_pu_live.py [--packets N] [--run-dir PATH]

Final line on success:
    CRAM_PU_LIVE_1_0_PASS=True
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent))  # /home/jack

from ph6.cram_pu.departure_logger import DepartureLogger
from ph6.cram_pu.arrival_logger import ArrivalLogger
from ph6.cram_pu.verdict_logger import VerdictLogger
from ph6.cram_pu._lane1_auth import mint_commit_authorization
from ph6.cram_pu.crash_replay import (
    CRAMPaths,
    CrashReplayValidator,
    CRAMWriter,
    SheddingLogger,
)
from ph6.cram_pu.tools.cram_pu_schema_validate import validate_run_dir
from ph6.cram_pu.schemas.canonical import canonical_json, blake2b_256
from ph6.tok.handoff import TokenHandoff


class _TokSidecar(TokenHandoff):
    """Compatibility name for the memory-only, nonblocking notification client."""

    def __init__(self, mram_s_dir: Path, enabled: bool, **kwargs) -> None:
        super().__init__(mram_s_dir.parent.parent / "cram_store", enabled, **kwargs)


def _write_payload_bin(payloads_dir: Path, frame_id: int, payload: bytes) -> None:
    """Persist live payload bytes for replay verification (GAP-16)."""
    payloads_dir.mkdir(parents=True, exist_ok=True)
    path = payloads_dir / f"frame_{frame_id:010d}.bin"
    fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)
    try:
        os.write(fd, payload)
        os.fsync(fd)
    finally:
        os.close(fd)


def _atomic_write_json(path: Path, record: dict) -> None:
    """write(tmp) → fsync(fd) → rename → fsync(dir)"""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(str(path) + ".tmp")
    data = (json.dumps(record, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")
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


def _generate_packets(n: int) -> list[tuple[int, bytes]]:
    """Generate n packets with varied content — some PASS, some DROP."""
    packets = []
    for i in range(1, n + 1):
        if i % 5 == 0:
            payload = bytes([8] * 300)          # entropy_low  → DROP (constant byte)
        elif i % 7 == 0:
            payload = bytes([238] * 300)        # entropy_low  → DROP (constant byte)
        else:
            payload = bytes([(i * 37 + j * 13) % 180 + 25 for j in range(300)])
        packets.append((i, payload))
    return packets


def run(n_packets: int = 10, base_dir: Path | None = None,
        tok_enabled: bool = True) -> dict:
    ts     = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_id = str(uuid.uuid4())

    if base_dir is None:
        base_dir = HERE / "runtime" / f"run_{ts}"

    cram_store   = base_dir / "cram_store"
    payloads_dir = cram_store / "payloads"
    mram_s_dir   = base_dir / "mram_s" / "swarms"
    cram_store.mkdir(parents=True, exist_ok=True)

    paths = CRAMPaths(cram_store=cram_store, mram_s=mram_s_dir)

    tok = _TokSidecar(mram_s_dir, enabled=tok_enabled)

    departure_logger = DepartureLogger(paths.departure_log)
    arrival_logger   = ArrivalLogger(paths.arrival_log)
    verdict_logger   = VerdictLogger(paths.verdict_log, include_advisory=False)
    shedding_logger  = SheddingLogger(paths)
    cram_writer      = CRAMWriter(cram_store)

    packets = _generate_packets(n_packets)

    counts = {"pass": 0, "drop": 0}

    for frame_id, payload in packets:
        # 1. Departure
        dep = departure_logger.log(frame_id, payload)

        # 2. Arrival — verify hash; persist payload for replay (GAP-16)
        arr = arrival_logger.log(frame_id, payload, dep["payload_hash"])
        _write_payload_bin(payloads_dir, frame_id, payload)
        if arr["transfer_status"] != "OK":
            print(f"  WARNING: frame {frame_id} HASH_MISMATCH on arrival",
                  file=sys.stderr)

        # 3. Verdict (PSEUDO deterministic, SoSo advisory only)
        verd = verdict_logger.log(frame_id, payload, dep["payload_hash"])

        # 4+5. Route by verdict
        if verd["verdict"] == "PASS":
            # CRAMWriter.commit() writes both the CRAM JSON and the .blake2b
            # marker atomically (write→fsync→rename→fsync dir).
            auth = mint_commit_authorization(
                frame_id=frame_id, payload_hash=dep["payload_hash"], verdict=verd["verdict"]
            )
            cram_writer.commit(frame_id, dep["payload_hash"], verd, auth)
            tok.on_pass(frame_id, dep["payload_hash"])  # Lane-2 advisory, authority ZERO
            counts["pass"] += 1
        else:
            shedding_logger.log(
                frame_id=frame_id,
                policy_ref="PH6-DROP-POLICY-v1",
                reason=("; ".join(verd["reasons"])
                        if verd["reasons"] else "drop_no_reason"),
            )
            counts["drop"] += 1

        # SoSo context is already preserved in the verdict record. Its separate
        # advisory snapshot is reconstructed by the worker, outside acquisition.

    print(f"  Processed {len(packets)} packets: "
          f"PASS={counts['pass']}  DROP={counts['drop']}")

    # 7. Write RSYNC queue — healthy, not blocked
    rsync_entry = {
        "schema":     "ph6.rsync_queue.v1",
        "depth":      0,
        "blocked_by": None,
        "timestamp":  time.time(),
    }
    with paths.rsync_queue.open("w", encoding="utf-8") as f:
        f.write(json.dumps(rsync_entry, sort_keys=True, separators=(",", ":"),
                           ensure_ascii=False, allow_nan=False) + "\n")

    # 8. result_set_hash — hash of the verdict sequence only (TOK must not affect this)
    verdict_records = [
        json.loads(line)
        for line in paths.verdict_log.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    verdict_sequence = [
        {"frame_id": r["frame_id"], "verdict": r["verdict"]}
        for r in verdict_records
    ]
    result_set_hash = blake2b_256(canonical_json(verdict_sequence))

    # 9. Schema validation
    schema_errors = validate_run_dir(paths)
    if schema_errors:
        print("SCHEMA VIOLATIONS:")
        for err in schema_errors:
            print(f"  {err}")
    else:
        print("  Schema validation: PASS")

    # 10. Crash/replay validation (seven invariants)
    print()
    validator = CrashReplayValidator(paths)
    report    = validator.run()
    print(report.summary())
    print()

    # 11. Manifest
    manifest = {
        "schema":    "ph6.cram_pu.live_manifest.v2",
        "milestone": "CRAM-PU-LIVE-1.0",
        "run_id":    run_id,
        "created_utc": ts,
        "root":      str(base_dir),
        "logs": {
            "departure_log": str(paths.departure_log),
            "arrival_log":   str(paths.arrival_log),
            "verdict_log":   str(paths.verdict_log),
            "shedding_log":  str(paths.shedding_log),
            "rsync_queue":   str(paths.rsync_queue),
        },
        "cram_store":   str(cram_store),
        "payloads_dir": str(payloads_dir),
        "mram_s":       str(mram_s_dir),
        "counts":           counts,
        "schema_ok":        len(schema_errors) == 0,
        "replay_verdict":   report.verdict,
        "result_set_hash":  result_set_hash,
        "tok_enabled":      tok_enabled,
        "tok_rt_count":     tok.rt_count(),
        "tok_handoff":      tok.accounting(),
        "acceptance": {
            "continuity_required":         True,
            "replay_required":             True,
            "authority_leakage_forbidden": True,
            "pass_shedding_forbidden":     True,
        },
    }
    _atomic_write_json(base_dir / "manifest.json", manifest)

    ok = report.verdict == "PASS" and len(schema_errors) == 0
    return {
        "ok":              ok,
        "result_set_hash": result_set_hash,
        "tok_enabled":     tok_enabled,
        "tok_rt_count":    tok.rt_count(),
        "tok_handoff":     tok.accounting(),
        "run_dir":         str(base_dir),
    }


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--packets",      type=int,            default=10)
    ap.add_argument("--run-dir",      type=Path,           default=None)
    ap.add_argument("--tok-disabled", action="store_true", default=False)
    args = ap.parse_args()

    result = run(
        n_packets=args.packets,
        base_dir=args.run_dir,
        tok_enabled=not args.tok_disabled,
    )
    print(f"  result_set_hash : {result['result_set_hash']}")
    print(f"  tok_enabled     : {result['tok_enabled']}")
    print(f"  tok_rt_count    : {result['tok_rt_count']}")
    if result["ok"]:
        print("CRAM_PU_LIVE_1_0_PASS=True")
        sys.exit(0)
    else:
        print("CRAM_PU_LIVE_1_0_PASS=False", file=sys.stderr)
        sys.exit(1)
