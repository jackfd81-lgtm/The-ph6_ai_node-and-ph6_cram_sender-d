import json
import hashlib
from dataclasses import asdict, is_dataclass
from typing import Any


HASH_LABEL = "BLAKE2b-256"


def canonical_dumps(obj: Any) -> str:
    if is_dataclass(obj):
        obj = asdict(obj)
    return json.dumps(
        obj,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def canonical_bytes(obj: Any) -> bytes:
    return canonical_dumps(obj).encode("utf-8")


def blake2b256_bytes(data: bytes) -> str:
    return hashlib.blake2b(data, digest_size=32).hexdigest()


def canon_hash(obj: Any) -> str:
    return blake2b256_bytes(canonical_bytes(obj))


def chain_event(event: dict, prev_event_hash: str) -> dict:
    event = dict(event)
    event["prev_event_hash"] = prev_event_hash
    event["event_hash"] = canon_hash({
        k: v for k, v in event.items()
        if k != "event_hash"
    })
    return event
