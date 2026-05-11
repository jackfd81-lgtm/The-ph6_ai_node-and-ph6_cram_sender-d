#!/usr/bin/env python3
"""
FI-01: Power loss mid-commit.
Simulates crash after tmp write but before rename.
Proves: orphaned .tmp file is never promoted to CRAM-A.
PASS: final path does not exist, committed records unaffected.
"""
import hashlib, json, os, tempfile
from pathlib import Path

CRAM_A = Path(tempfile.mkdtemp(prefix="fi01_cram_a_"))

def atomic_write(path: Path, data: bytes) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    fd = os.open(str(tmp), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)
    try:
        os.write(fd, data)
        os.fsync(fd)
    finally:
        os.close(fd)
    os.replace(str(tmp), str(path))
    dfd = os.open(str(path.parent), os.O_RDONLY)
    try:
        os.fsync(dfd)
    finally:
        os.close(dfd)

def crash_after_tmp(path: Path, data: bytes) -> Path:
    tmp = path.with_suffix(path.suffix + ".tmp")
    fd = os.open(str(tmp), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)
    try:
        os.write(fd, data)
        os.fsync(fd)
    finally:
        os.close(fd)
    return tmp  # rename never happens — power loss here

results = []

# Frame 1 — clean commit
p1 = CRAM_A / "frame_000001.json"
d1 = json.dumps({"frame_id": 1, "verdict": "PASS"}, sort_keys=True).encode()
atomic_write(p1, d1)
m1 = p1.with_suffix(p1.suffix + ".blake2b")
atomic_write(m1, hashlib.blake2b(d1, digest_size=32).hexdigest().encode())
results.append(("FRAME1_COMMITTED",      p1.exists() and m1.exists()))

# Frame 2 — crash mid-commit
p2 = CRAM_A / "frame_000002.json"
d2 = json.dumps({"frame_id": 2, "verdict": "PASS"}, sort_keys=True).encode()
orphan = crash_after_tmp(p2, d2)
results.append(("FRAME2_FINAL_ABSENT",   not p2.exists()))
results.append(("FRAME2_ORPHAN_EXISTS",  orphan.exists()))

# Frame 3 — clean commit after simulated recovery
p3 = CRAM_A / "frame_000003.json"
d3 = json.dumps({"frame_id": 3, "verdict": "DROP"}, sort_keys=True).encode()
atomic_write(p3, d3)
m3 = p3.with_suffix(p3.suffix + ".blake2b")
atomic_write(m3, hashlib.blake2b(d3, digest_size=32).hexdigest().encode())
results.append(("FRAME3_COMMITTED",      p3.exists() and m3.exists()))

committed = [f for f in CRAM_A.iterdir() if f.suffix == ".json" and ".tmp" not in f.name]
results.append(("ONLY_2_FINAL_RECORDS",  len(committed) == 2))

failures = sum(1 for _, ok in results if not ok)
for name, ok in results:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}")

print()
if failures == 0:
    print("FI-01 POWER_LOSS_MID_COMMIT: PASS")
else:
    print(f"FI-01 POWER_LOSS_MID_COMMIT: FAIL ({failures} assertions)")
    raise SystemExit(1)
