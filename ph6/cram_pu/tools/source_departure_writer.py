"""
Phase 2 — SOURCE NODE departure writer.
Writes ph6.raw_departure.v1 records to departure_log.jsonl.
Called on the RAW Pi before any packet is transferred.
"""

import hashlib
import json
import os
import sys
import time
import uuid
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


class DepartureWriter:
    def __init__(self, log_path: Path):
        self.log_path = log_path
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self._seq = 0

    def write(self, packet_id: str, payload: bytes, media_type: str = "FRAME",
              source_node_id: str = "RAW_PI5") -> dict:
        self._seq += 1
        record = {
            "schema":              "ph6.raw_departure.v1",
            "packet_id":           packet_id,
            "source_node_id":      source_node_id,
            "departure_seq":       self._seq,
            "departure_timestamp": time.time(),
            "payload_hash":        _blake2b256_bytes(payload),
            "media_type":          media_type,
            "size_bytes":          len(payload),
            "authority":           "NONE",
        }
        _append_jsonl(self.log_path, record)
        return record


def write_departures(packets: list, log_path: Path) -> list:
    """Write departures for a list of (packet_id, payload_bytes, media_type) tuples."""
    writer = DepartureWriter(log_path)
    return [writer.write(pid, payload, mtype) for pid, payload, mtype in packets]


if __name__ == "__main__":
    import argparse, base64
    ap = argparse.ArgumentParser()
    ap.add_argument("--log",  required=True)
    ap.add_argument("--data", required=True, help="base64-encoded payload")
    ap.add_argument("--media-type", default="FRAME")
    ap.add_argument("--source", default="RAW_PI5")
    args = ap.parse_args()
    payload = base64.b64decode(args.data)
    pid = str(uuid.uuid4())
    rec = DepartureWriter(Path(args.log)).write(pid, payload, args.media_type, args.source)
    print(json.dumps(rec, indent=2))
