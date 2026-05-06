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
from ph6.cram_pu.crash_replay import (
    CRAMPaths,
    CrashReplayValidator,
    CRAMWriter,
    SheddingLogger,
)
from ph6.cram_pu.tools.cram_pu_schema_validate import validate_run_dir


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
            payload = bytes([8] * 300)          # brightness_low  → DROP
        elif i % 7 == 0:
            payload = bytes([238] * 300)        # brightness_high → DROP
        else:
            payload = bytes([(i * 37 + j * 13) % 180 + 25 for j in range(300)])
        packets.append((i, payload))
    return packets


def run(n_packets: int = 10, base_dir: Path | None = None) -> bool:
    ts     = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_id = str(uuid.uuid4())

    if base_dir is None:
        base_dir = HERE / "runtime" / f"run_{ts}"

    cram_store = base_dir / "cram_store"
    mram_s_dir = base_dir / "mram_s" / "swarms"
    cram_store.mkdir(parents=True, exist_ok=True)
    mram_s_dir.mkdir(parents=True, exist_ok=True)

    paths = CRAMPaths(cram_store=cram_store, mram_s=mram_s_dir)

    departure_logger = DepartureLogger(paths.departure_log)
    arrival_logger   = ArrivalLogger(paths.arrival_log)
    verdict_logger   = VerdictLogger(paths.verdict_log)
    shedding_logger  = SheddingLogger(paths)
    cram_writer      = CRAMWriter(cram_store)

    packets = _generate_packets(n_packets)

    counts = {"pass": 0, "drop": 0}

    for frame_id, payload in packets:
        # 1. Departure
        dep = departure_logger.log(frame_id, payload)

        # 2. Arrival — verify hash
        arr = arrival_logger.log(frame_id, payload, dep["payload_hash"])
        if arr["transfer_status"] != "OK":
            print(f"  WARNING: frame {frame_id} HASH_MISMATCH on arrival",
                  file=sys.stderr)

        # 3. Verdict (PSEUDO deterministic, SoSo advisory only)
        verd = verdict_logger.log(frame_id, payload, dep["payload_hash"])

        # 4+5. Route by verdict
        if verd["verdict"] == "PASS":
            # CRAMWriter.commit() writes both the CRAM JSON and the .blake2b
            # marker atomically (write→fsync→rename→fsync dir).
            cram_writer.commit(frame_id, dep["payload_hash"], verd)
            counts["pass"] += 1
        else:
            shedding_logger.log(
                frame_id=frame_id,
                policy_ref="PH6-DROP-POLICY-v1",
                reason=("; ".join(verd["reasons"])
                        if verd["reasons"] else "drop_no_reason"),
            )
            counts["drop"] += 1

        # 6. MRAM-S advisory sidecar — Authority NONE, zero Lane-1 path refs
        advisory = {
            "schema":    "ph6.mram_s.advisory.v1",
            "frame_id":  frame_id,
            "soso":      verd["soso_advisory"],
            "authority": "NONE",
            "timestamp": time.time(),
        }
        _atomic_write_json(mram_s_dir / f"S{frame_id:010d}.json", advisory)

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

    # 8. Schema validation
    schema_errors = validate_run_dir(paths)
    if schema_errors:
        print("SCHEMA VIOLATIONS:")
        for err in schema_errors:
            print(f"  {err}")
    else:
        print("  Schema validation: PASS")

    # 9. Crash/replay validation (seven invariants)
    print()
    validator = CrashReplayValidator(paths)
    report    = validator.run()
    print(report.summary())
    print()

    # 10. Manifest
    manifest = {
        "schema":    "ph6.cram_pu.live_manifest.v1",
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
        "cram_store": str(cram_store),
        "mram_s":     str(mram_s_dir),
        "counts":     counts,
        "schema_ok":  len(schema_errors) == 0,
        "replay_verdict": report.verdict,
        "acceptance": {
            "continuity_required":         True,
            "replay_required":             True,
            "authority_leakage_forbidden": True,
            "pass_shedding_forbidden":     True,
        },
    }
    _atomic_write_json(base_dir / "manifest.json", manifest)

    return report.verdict == "PASS" and len(schema_errors) == 0


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--packets",  type=int,  default=10)
    ap.add_argument("--run-dir",  type=Path, default=None)
    args = ap.parse_args()

    ok = run(n_packets=args.packets, base_dir=args.run_dir)
    if ok:
        print("CRAM_PU_LIVE_1_0_PASS=True")
        sys.exit(0)
    else:
        print("CRAM_PU_LIVE_1_0_PASS=False", file=sys.stderr)
        sys.exit(1)
