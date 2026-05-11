#!/usr/bin/env python3
"""
FI-04: Lane 2 contamination attempt.
Simulates advisory (SoSo/TOK) output attempting to enter CRAM-A.
Proves: CRAM writer rejects packets with Lane 2 authority fields.
PASS: contaminated records are rejected, clean records committed normally.
"""
import hashlib, json, os, tempfile
from pathlib import Path

CRAM_A = Path(tempfile.mkdtemp(prefix="fi04_cram_a_"))

FORBIDDEN_FIELDS = {"authority_override", "soso_verdict", "tok_verdict",
                    "ai_decision", "lane2_pass", "advisory_authority",
                    "may_influence_verdict", "motion_score", "motion_decay_score"}

def validate_record(record: dict) -> tuple[bool, list[str]]:
    bad = FORBIDDEN_FIELDS.intersection(record.keys())
    if bad:
        return False, sorted(bad)
    if record.get("authority") not in (None, "PSEUDO_A", "LANE_1"):
        return False, [f"authority={record['authority']}"]
    if record.get("lane") == "LANE_2":
        return False, ["lane=LANE_2"]
    return True, []

def commit_if_clean(path: Path, record: dict) -> tuple[bool, list[str]]:
    ok, violations = validate_record(record)
    if not ok:
        return False, violations
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
    return True, []

results = []

# Clean Lane 1 record — should commit
clean = {"frame_id": 1, "verdict": "PASS", "authority": "PSEUDO_A", "motion_fraction": 250}
ok, v = commit_if_clean(CRAM_A / "frame_000001.json", clean)
results.append(("CLEAN_RECORD_COMMITTED",       ok))

# SoSo contamination — has soso_verdict field
soso = {"frame_id": 2, "verdict": "PASS", "soso_verdict": "ADVISORY_PASS", "authority": "PSEUDO_A"}
ok, v = commit_if_clean(CRAM_A / "frame_000002.json", soso)
results.append(("SOSO_CONTAMINATION_REJECTED",  not ok))

# Lane 2 authority claim
lane2 = {"frame_id": 3, "verdict": "PASS", "authority": "SOSO", "lane": "LANE_2"}
ok, v = commit_if_clean(CRAM_A / "frame_000003.json", lane2)
results.append(("LANE2_AUTHORITY_REJECTED",     not ok))

# Forbidden motion field
drift = {"frame_id": 4, "verdict": "PASS", "motion_score": 0.5, "authority": "PSEUDO_A"}
ok, v = commit_if_clean(CRAM_A / "frame_000004.json", drift)
results.append(("MOTION_DRIFT_FIELD_REJECTED",  not ok))

# CRAM-A has exactly 1 committed record
committed = [f for f in CRAM_A.iterdir() if f.suffix == ".json" and ".tmp" not in f.name]
results.append(("CRAM_A_HAS_ONLY_CLEAN_RECORD", len(committed) == 1))

failures = sum(1 for _, ok in results if not ok)
for name, ok in results:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}")

print()
if failures == 0:
    print("FI-04 LANE2_CONTAMINATION: PASS")
else:
    print(f"FI-04 LANE2_CONTAMINATION: FAIL ({failures} assertions)")
    raise SystemExit(1)
