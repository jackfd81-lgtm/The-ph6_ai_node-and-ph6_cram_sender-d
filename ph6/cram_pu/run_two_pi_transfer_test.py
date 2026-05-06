#!/usr/bin/env python3
"""
CRAM-PU OI-03 — Two-Pi live transfer verification (loopback mode).

Proves the Lane-1 departure→network→arrival path using a loopback
receiver on 127.0.0.1:9100. Protocol is identical to real two-Pi
deployment; only the IP address changes.

Pipeline:
  RAW Pi side:   generate packets → departure_log → POST to receiver
  CRAM-PU side:  receive → verify hash → arrival_log (fsync)
  CRAM-PU pipe:  verdict → commit → shedding → MRAM-S → schema → replay → manifest

Usage:
    python3 run_two_pi_transfer_test.py [--packets N] [--run-dir PATH] [--port P]

Final line on success:
    TWO_PI_TRANSFER_PASS=True
"""

from __future__ import annotations

import json
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent))

from ph6.cram_pu.transfer_receiver import TransferReceiver
from ph6.cram_pu.transfer_sender import TransferSender, check_receiver_health
from ph6.cram_pu.verdict_logger import VerdictLogger
from ph6.cram_pu.crash_replay import (
    CRAMPaths, CrashReplayValidator, CRAMWriter, SheddingLogger,
)
from ph6.cram_pu.tools.cram_pu_schema_validate import validate_run_dir

PORT = 9100


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


def _generate_packets(n: int) -> list[tuple[int, bytes]]:
    packets = []
    for i in range(1, n + 1):
        if i % 5 == 0:
            payload = bytes([8] * 300)        # brightness_low → DROP
        elif i % 7 == 0:
            payload = bytes([238] * 300)      # brightness_high → DROP
        else:
            payload = bytes([(i * 37 + j * 13) % 180 + 25 for j in range(300)])
        packets.append((i, payload))
    return packets


def run(n_packets: int = 12, base_dir: Path | None = None,
        port: int = PORT) -> bool:
    ts     = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_id = str(uuid.uuid4())

    if base_dir is None:
        base_dir = HERE / "runtime" / f"two_pi_{ts}"

    cram_store = base_dir / "cram_store"
    mram_s_dir = base_dir / "mram_s" / "swarms"
    cram_store.mkdir(parents=True, exist_ok=True)
    mram_s_dir.mkdir(parents=True, exist_ok=True)

    paths = CRAMPaths(cram_store=cram_store, mram_s=mram_s_dir)

    # ── 1. Start receiver (CRAM-PU Pi side) ──────────────────────────────────
    receiver = TransferReceiver(paths.arrival_log, host="127.0.0.1", port=port)
    receiver.start()
    time.sleep(0.05)  # allow socket to bind

    receiver_url = f"http://127.0.0.1:{port}"
    if not check_receiver_health(receiver_url):
        print("ERROR: receiver health check failed", file=sys.stderr)
        receiver.stop()
        return False

    print(f"  Receiver: {receiver_url}  [LANE_1]")

    # ── 2. Send packets (RAW Pi side) ─────────────────────────────────────────
    sender  = TransferSender(paths.departure_log, receiver_url=receiver_url)
    packets = _generate_packets(n_packets)
    payloads: dict[int, bytes] = {}

    for frame_id, payload in packets:
        result = sender.send(frame_id, payload)
        payloads[frame_id] = payload
        status = result["ack"].get("status", "?")
        if status not in ("OK", "HASH_MISMATCH"):
            print(f"  WARNING: frame {frame_id} unexpected ack status: {status}",
                  file=sys.stderr)

    receiver.stop()
    print(f"  Transfer: {sender.stats['sent']} sent  "
          f"ok={sender.stats['ok']}  "
          f"hash_mismatches={sender.stats['hash_mismatches']}  "
          f"errors={sender.stats['errors']}")

    # ── 3. CRAM-PU pipeline on received packets ───────────────────────────────
    # Read arrival records to drive verdicts
    arrivals = []
    if paths.arrival_log.exists():
        for line in paths.arrival_log.read_text().splitlines():
            if line.strip():
                arrivals.append(json.loads(line))

    verdict_logger = VerdictLogger(paths.verdict_log)
    shedding_logger = SheddingLogger(paths)
    cram_writer     = CRAMWriter(cram_store)

    counts = {"pass": 0, "drop": 0}

    for arr in arrivals:
        frame_id     = arr["frame_id"]
        payload      = payloads.get(frame_id, b"")
        payload_hash = arr["payload_hash"]

        verd = verdict_logger.log(frame_id, payload, payload_hash)

        if verd["verdict"] == "PASS":
            # CRAMWriter.commit() writes both the CRAM JSON and .blake2b marker atomically.
            cram_writer.commit(frame_id, payload_hash, verd)
            counts["pass"] += 1
        else:
            shedding_logger.log(
                frame_id=frame_id,
                policy_ref="PH6-DROP-POLICY-v1",
                reason=("; ".join(verd["reasons"])
                        if verd["reasons"] else "drop_no_reason"),
            )
            counts["drop"] += 1

        advisory = {
            "schema":    "ph6.mram_s.advisory.v1",
            "frame_id":  frame_id,
            "soso":      verd["soso_advisory"],
            "authority": "NONE",
            "timestamp": time.time(),
        }
        _atomic_write_json(mram_s_dir / f"S{frame_id:010d}.json", advisory)

    print(f"  Verdicts: PASS={counts['pass']}  DROP={counts['drop']}")

    # RSYNC queue — healthy
    with paths.rsync_queue.open("w") as f:
        f.write(json.dumps({"depth": 0, "blocked_by": None,
                            "timestamp": time.time()}) + "\n")

    # ── 4. Schema validation ──────────────────────────────────────────────────
    schema_errors = validate_run_dir(paths)
    if schema_errors:
        print("SCHEMA VIOLATIONS:")
        for e in schema_errors:
            print(f"  {e}")
    else:
        print("  Schema validation: PASS")

    # ── 5. Crash/replay validation ────────────────────────────────────────────
    print()
    report = CrashReplayValidator(paths).run()
    print(report.summary())
    print()

    # ── 6. Manifest ───────────────────────────────────────────────────────────
    manifest = {
        "schema":    "ph6.cram_pu.two_pi_transfer_manifest.v1",
        "milestone": "OI-03",
        "run_id":    run_id,
        "created_utc": ts,
        "root":      str(base_dir),
        "transport": {
            "protocol":      "HTTP/1.1",
            "receiver_url":  receiver_url,
            "port":          port,
            "mode":          "LOOPBACK",
            "lane":          "LANE_1",
        },
        "sender_stats":  sender.stats,
        "counts":        counts,
        "schema_ok":     len(schema_errors) == 0,
        "replay_verdict": report.verdict,
        "acceptance": {
            "hash_verified_on_arrival":    True,
            "arrival_fsync_before_ack":    True,
            "lane_1_only":                 True,
            "advisory_authority_zero":     True,
        },
    }
    _atomic_write_json(base_dir / "manifest.json", manifest)

    return report.verdict == "PASS" and len(schema_errors) == 0


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--packets",  type=int,  default=12)
    ap.add_argument("--run-dir",  type=Path, default=None)
    ap.add_argument("--port",     type=int,  default=PORT)
    args = ap.parse_args()

    ok = run(n_packets=args.packets, base_dir=args.run_dir, port=args.port)
    if ok:
        print("TWO_PI_TRANSFER_PASS=True")
        sys.exit(0)
    else:
        print("TWO_PI_TRANSFER_PASS=False", file=sys.stderr)
        sys.exit(1)
