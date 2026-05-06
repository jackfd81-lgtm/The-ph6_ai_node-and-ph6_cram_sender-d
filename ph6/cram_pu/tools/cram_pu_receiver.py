"""
Phase 3 — CRAM-PU arrival receiver.
Reads departure_log.jsonl, verifies payload hashes on arrival,
writes ph6.raw_arrival.v1 records to arrival_log.jsonl.
"""

import hashlib
import json
import os
import time
from pathlib import Path


def _blake2b256_bytes(data: bytes) -> str:
    return "blake2b256:" + hashlib.blake2b(data, digest_size=32).hexdigest()


def _append_jsonl(path: Path, record: dict) -> None:
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, sort_keys=True, separators=(",", ":"),
                           ensure_ascii=False, allow_nan=False))
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())


def _read_departures(departure_log: Path) -> list:
    if not departure_log.exists():
        return []
    records = []
    with departure_log.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


class ArrivalReceiver:
    def __init__(self, arrival_log: Path):
        self.arrival_log = arrival_log
        self.arrival_log.parent.mkdir(parents=True, exist_ok=True)
        self._seq = 0

    def receive(self, packet_id: str, payload: bytes, expected_hash: str) -> dict:
        self._seq += 1
        received_hash = _blake2b256_bytes(payload)
        if received_hash == expected_hash:
            status = "OK"
        else:
            status = "HASH_MISMATCH"
        record = {
            "schema":            "ph6.raw_arrival.v1",
            "packet_id":         packet_id,
            "arrival_seq":       self._seq,
            "arrival_timestamp": time.time(),
            "received_hash":     received_hash,
            "transfer_status":   status,
            "authority":         "LANE_1_RECEIVER",
        }
        _append_jsonl(self.arrival_log, record)
        return record


def receive_from_departures(departures: list, payloads: dict, arrival_log: Path) -> list:
    """
    Given a list of departure records and a {packet_id: bytes} payload map,
    write arrival records. Simulates in-process transfer (no network hop needed
    for single-Pi or test mode).
    """
    receiver = ArrivalReceiver(arrival_log)
    results = []
    for dep in departures:
        pid = dep["packet_id"]
        payload = payloads.get(pid, b"")
        results.append(receiver.receive(pid, payload, dep["payload_hash"]))
    return results


if __name__ == "__main__":
    import argparse, base64
    ap = argparse.ArgumentParser()
    ap.add_argument("--departure-log", required=True)
    ap.add_argument("--arrival-log",   required=True)
    ap.add_argument("--payloads-json", required=True,
                    help='JSON map of {packet_id: base64_payload}')
    args = ap.parse_args()
    deps = _read_departures(Path(args.departure_log))
    raw = json.loads(Path(args.payloads_json).read_text())
    payloads = {k: __import__("base64").b64decode(v) for k, v in raw.items()}
    results = receive_from_departures(deps, payloads, Path(args.arrival_log))
    print(json.dumps(results, indent=2))
