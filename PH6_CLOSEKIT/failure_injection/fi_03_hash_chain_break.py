#!/usr/bin/env python3
"""
FI-03: Hash chain break.
Mutates one event in a manifest chain and proves the verifier detects it.
PASS: chain verifier reports CHAIN_BREAK at the mutated record.
"""
import hashlib, json, tempfile
from pathlib import Path

WORK = Path(tempfile.mkdtemp(prefix="fi03_"))

def blake2b(data: bytes) -> str:
    return hashlib.blake2b(data, digest_size=32).hexdigest()

def build_chain(n: int) -> list[dict]:
    events, prev = [], "GENESIS"
    for i in range(1, n + 1):
        ev = {
            "schema":          "ph6.audit_event.v1",
            "event_seq":       i,
            "event_type":      "FRAME_COMMIT",
            "verdict":         "PASS" if i % 3 != 0 else "DROP",
            "prev_event_hash": prev,
        }
        canon = json.dumps(ev, sort_keys=True, separators=(",", ":"))
        ev["event_hash"] = blake2b(canon.encode())
        prev = ev["event_hash"]
        events.append(ev)
    return events

def verify_chain(events: list[dict]) -> list[int]:
    """Check both link integrity and event_hash self-consistency."""
    broken, prev = [], "GENESIS"
    for ev in events:
        # Link check: prev pointer must match last committed hash
        if ev.get("prev_event_hash") != prev:
            broken.append(ev["event_seq"])
            prev = ev.get("event_hash", "")
            continue
        # Content check: recompute hash over all fields except event_hash itself
        ev_body = {k: v for k, v in ev.items() if k != "event_hash"}
        canon = json.dumps(ev_body, sort_keys=True, separators=(",", ":"))
        expected_hash = blake2b(canon.encode())
        if ev.get("event_hash") != expected_hash:
            broken.append(ev["event_seq"])
        prev = ev.get("event_hash", "")
    return broken

# Build clean chain
events = build_chain(10)
clean_breaks = verify_chain(events)

# Mutate event 5 — simulates tampered record
events[4]["verdict"] = "PASS_INJECTED"  # tamper without recomputing hash
dirty_breaks = verify_chain(events)

results = [
    ("CLEAN_CHAIN_NO_BREAKS",    len(clean_breaks) == 0),
    ("TAMPERED_CHAIN_DETECTED",  len(dirty_breaks) > 0),
    ("BREAK_AT_SEQ_5",           5 in dirty_breaks),  # content hash mismatch on tampered record
]

failures = sum(1 for _, ok in results if not ok)
for name, ok in results:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}")
if dirty_breaks:
    print(f"  Chain breaks detected at seqs: {dirty_breaks}")

print()
if failures == 0:
    print("FI-03 HASH_CHAIN_BREAK: PASS")
else:
    print(f"FI-03 HASH_CHAIN_BREAK: FAIL ({failures} assertions)")
    raise SystemExit(1)
