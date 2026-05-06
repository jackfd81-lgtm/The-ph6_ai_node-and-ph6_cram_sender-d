"""
CRAM-PU departure logger.
Writes ph6.raw_departure.v1 records keyed by frame_id.
Authority: NONE — source node observes only.
"""

import hashlib
import json
import os
import time
from pathlib import Path


def _blake2b256_bytes(data: bytes) -> str:
    return hashlib.blake2b(data, digest_size=32).hexdigest()


def _append_jsonl(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, sort_keys=True, separators=(",", ":"),
                           ensure_ascii=False, allow_nan=False))
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())


class DepartureLogger:
    def __init__(self, log_path: Path):
        self.log_path = log_path

    def log(self, frame_id: int, payload: bytes,
            media_type: str = "FRAME") -> dict:
        record = {
            "schema":              "ph6.raw_departure.v1",
            "frame_id":            frame_id,
            "payload_hash":        _blake2b256_bytes(payload),
            "hash_algorithm":      "BLAKE2b-256",
            "media_type":          media_type,
            "size_bytes":          len(payload),
            "departure_timestamp": time.time(),
            "authority":           "NONE",
        }
        _append_jsonl(self.log_path, record)
        return record
