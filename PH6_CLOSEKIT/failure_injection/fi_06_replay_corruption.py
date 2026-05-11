#!/usr/bin/env python3
"""
FI-06: Replay corruption attempt.
Simulates replay engine attempting to mutate evidence during verification.
Proves: replay is read-only; it verifies but never modifies CRAM-A.
PASS: CRAM-A files are identical before and after replay; any mutation is detected.
"""
import hashlib, json, os, tempfile
from pathlib import Path

CRAM_A = Path(tempfile.mkdtemp(prefix="fi06_cram_a_"))

def blake2b_file(path: Path) -> str:
    h = hashlib.blake2b(digest_size=32)
    h.update(path.read_bytes())
    return h.hexdigest()

def commit_frame(seq: int, verdict: str) -> Path:
    path = CRAM_A / f"frame_{seq:06d}.json"
    record = {"frame_id": seq, "verdict": verdict, "authority": "PSEUDO_A"}
    data = json.dumps(record, sort_keys=True, separators=(",", ":")).encode()
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
    marker = path.with_suffix(path.suffix + ".blake2b")
    marker.write_bytes(hashlib.blake2b(data, digest_size=32).hexdigest().encode())
    return path

def replay_read_only(cram_dir: Path) -> dict:
    """Correct replay: read and verify only, never write."""
    results = {}
    for path in sorted(cram_dir.glob("frame_*.json")):
        data = path.read_bytes()
        actual  = hashlib.blake2b(data, digest_size=32).hexdigest()
        marker  = path.with_suffix(path.suffix + ".blake2b")
        expected = marker.read_text().strip() if marker.exists() else None
        results[path.name] = {"match": actual == expected, "hash": actual}
    return results

def replay_corrupt_attempt(cram_dir: Path) -> None:
    """Malicious replay that tries to rewrite a record."""
    for path in sorted(cram_dir.glob("frame_*.json")):
        record = json.loads(path.read_bytes())
        record["verdict"] = "PASS_INJECTED_BY_REPLAY"  # mutation attempt
        try:
            path.write_text(json.dumps(record))  # direct overwrite — forbidden
        except Exception:
            pass
        break  # only attempt on first record

# Commit 5 clean frames
paths = [commit_frame(i, "PASS" if i % 2 == 0 else "DROP") for i in range(1, 6)]

# Snapshot hashes before replay
before = {p.name: blake2b_file(p) for p in paths}

# Run correct (read-only) replay
replay_results = replay_read_only(CRAM_A)
after_clean = {p.name: blake2b_file(p) for p in paths}

results = []
results.append(("REPLAY_ALL_HASHES_MATCH",     all(v["match"] for v in replay_results.values())))
results.append(("READ_ONLY_REPLAY_NO_MUTATION", before == after_clean))

# Now simulate a corrupt replay attempt
before_corrupt = {p.name: blake2b_file(p) for p in paths}
replay_corrupt_attempt(CRAM_A)
after_corrupt = {p.name: blake2b_file(p) for p in paths}

# Detect mutation
mutations = {k for k in before_corrupt if before_corrupt[k] != after_corrupt.get(k)}
results.append(("CORRUPTION_DETECTED",         len(mutations) > 0))

# Verify verifier now flags the mutated record
post_corrupt_replay = replay_read_only(CRAM_A)
flagged = [k for k, v in post_corrupt_replay.items() if not v["match"]]
results.append(("VERIFIER_FLAGS_MUTATED_RECORD", len(flagged) > 0))

failures = sum(1 for _, ok in results if not ok)
for name, ok in results:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}")

print()
if failures == 0:
    print("FI-06 REPLAY_CORRUPTION: PASS")
else:
    print(f"FI-06 REPLAY_CORRUPTION: FAIL ({failures} assertions)")
    raise SystemExit(1)
