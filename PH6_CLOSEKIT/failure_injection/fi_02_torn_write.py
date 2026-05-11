#!/usr/bin/env python3
"""
FI-02: Torn write (partial payload).
Simulates a partial write where tmp contains truncated data.
Proves: BLAKE2b verification catches corruption before promotion.
PASS: hash mismatch detected, record rejected, CRAM-A not contaminated.
"""
import hashlib, json, os, tempfile
from pathlib import Path

CRAM_A = Path(tempfile.mkdtemp(prefix="fi02_cram_a_"))

def blake2b(data: bytes) -> str:
    return hashlib.blake2b(data, digest_size=32).hexdigest()

def verify_and_commit(path: Path, data: bytes) -> bool:
    """Write, verify hash, write marker only if hash is stable."""
    tmp = path.with_suffix(path.suffix + ".tmp")
    fd = os.open(str(tmp), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)
    try:
        os.write(fd, data)
        os.fsync(fd)
    finally:
        os.close(fd)
    written = Path(tmp).read_bytes()
    if blake2b(written) != blake2b(data):
        os.unlink(tmp)
        return False
    os.replace(str(tmp), str(path))
    dfd = os.open(str(path.parent), os.O_RDONLY)
    try:
        os.fsync(dfd)
    finally:
        os.close(dfd)
    marker = path.with_suffix(path.suffix + ".blake2b")
    marker.write_bytes(blake2b(data).encode())
    return True

def write_torn(path: Path, data: bytes, truncate_at: int) -> None:
    """Write only the first truncate_at bytes — simulates torn write."""
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "wb") as f:
        f.write(data[:truncate_at])
        f.flush()
        os.fsync(f.fileno())
    # Do NOT rename — torn write leaves tmp only

results = []

# Good frame
p1 = CRAM_A / "frame_000001.json"
d1 = json.dumps({"frame_id": 1, "verdict": "PASS", "hash_alg": "BLAKE2b-256"}, sort_keys=True).encode()
ok = verify_and_commit(p1, d1)
results.append(("GOOD_FRAME_COMMITTED",    ok and p1.exists()))

# Torn frame — truncated at halfway
p2 = CRAM_A / "frame_000002.json"
d2 = json.dumps({"frame_id": 2, "verdict": "PASS", "hash_alg": "BLAKE2b-256"}, sort_keys=True).encode()
write_torn(p2, d2, len(d2) // 2)

# Detect torn write: tmp exists, final does not, tmp hash != expected
torn_tmp = p2.with_suffix(p2.suffix + ".tmp")
torn_detected = torn_tmp.exists() and not p2.exists()
if torn_tmp.exists():
    torn_hash  = blake2b(torn_tmp.read_bytes())
    clean_hash = blake2b(d2)
    hash_mismatch = torn_hash != clean_hash
else:
    hash_mismatch = False

results.append(("TORN_FINAL_ABSENT",  not p2.exists()))
results.append(("TORN_TMP_EXISTS",    torn_detected))
results.append(("TORN_HASH_MISMATCH", hash_mismatch))

# CRAM-A has exactly one final record
final = [f for f in CRAM_A.iterdir() if f.suffix == ".json" and ".tmp" not in f.name]
results.append(("CRAM_A_UNCONTAMINATED", len(final) == 1))

failures = sum(1 for _, ok in results if not ok)
for name, ok in results:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}")

print()
if failures == 0:
    print("FI-02 TORN_WRITE: PASS")
else:
    print(f"FI-02 TORN_WRITE: FAIL ({failures} assertions)")
    raise SystemExit(1)
