"""
CRAM-PU crash/replay validation harness.

Proves six Lane-1 invariants after any crash or restart:
  1. No torn authoritative final files (.tmp artifacts)
  2. No silent PASS loss (every PASS verdict has a CRAM commit)
  3. DROP shedding is policy-bound and logged
  4. Advisory shedding never affects Lane-1
  5. CRAM history is replay-consistent (hash chain intact)
  6. RSYNC export path is never blocked

Reference: PH6-ARCH-CRAM-PU-v1.1
Authority: LANE_1
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from ph6.cfc import make_failure, make_replay_failure


# ---------------------------------------------------------------------------
# Canonical hashing (matches ph6/ssmt/hash_chain.py)
# ---------------------------------------------------------------------------

def _canonical_bytes(obj) -> bytes:
    return json.dumps(
        obj,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def blake2b256(obj) -> str:
    return hashlib.blake2b(_canonical_bytes(obj), digest_size=32).hexdigest()


def blake2b256_file(path: Path) -> str:
    h = hashlib.blake2b(digest_size=32)
    with path.open("rb") as f:
        while chunk := f.read(1 << 20):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

CRAM_STORE_DEFAULT = Path("/var/ph6/cram-0")
MRAM_S_DEFAULT = Path("/var/ph6/mram-s/swarms")


@dataclass
class CRAMPaths:
    cram_store: Path = field(default_factory=lambda: CRAM_STORE_DEFAULT)
    mram_s: Path = field(default_factory=lambda: MRAM_S_DEFAULT)

    @property
    def departure_log(self) -> Path:
        return self.cram_store / "departure_log.jsonl"

    @property
    def arrival_log(self) -> Path:
        return self.cram_store / "arrival_log.jsonl"

    @property
    def verdict_log(self) -> Path:
        return self.cram_store / "verdict_log.jsonl"

    @property
    def shedding_log(self) -> Path:
        return self.cram_store / "shedding_log.jsonl"

    @property
    def rsync_queue(self) -> Path:
        return self.cram_store / "rsync_queue.jsonl"


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

@dataclass
class TornFileResult:
    torn: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return len(self.torn) == 0


@dataclass
class ContinuityResult:
    matched: int = 0
    orphan_departures: List[dict] = field(default_factory=list)
    orphan_arrivals: List[dict] = field(default_factory=list)
    hash_mismatches: List[dict] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return (
            len(self.orphan_departures) == 0
            and len(self.orphan_arrivals) == 0
            and len(self.hash_mismatches) == 0
        )


@dataclass
class PassLossResult:
    pass_verdicts: int = 0
    cram_commits: int = 0
    silent_losses: List[int] = field(default_factory=list)  # frame_ids

    @property
    def ok(self) -> bool:
        return len(self.silent_losses) == 0


@dataclass
class DropSheddingResult:
    total_drops: int = 0
    logged_drops: int = 0
    unlogged_drops: List[int] = field(default_factory=list)  # frame_ids

    @property
    def ok(self) -> bool:
        return len(self.unlogged_drops) == 0


@dataclass
class AdvisoryIsolationResult:
    lane1_paths_touched_by_advisory: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return len(self.lane1_paths_touched_by_advisory) == 0


@dataclass
class CRAMIntegrityResult:
    total_files: int = 0
    hash_failures: List[str] = field(default_factory=list)
    chain_broken_at: Optional[int] = None  # frame_id where chain breaks
    prev_hash_mismatches: List[int] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return (
            len(self.hash_failures) == 0
            and self.chain_broken_at is None
            and len(self.prev_hash_mismatches) == 0
        )


@dataclass
class RSYNCHealthResult:
    queue_depth: int = 0
    blocked: bool = False
    reason: str = ""

    @property
    def ok(self) -> bool:
        return not self.blocked


@dataclass
class CrashReplayReport:
    timestamp: float = field(default_factory=time.time)
    torn_files: TornFileResult = field(default_factory=TornFileResult)
    continuity: ContinuityResult = field(default_factory=ContinuityResult)
    pass_loss: PassLossResult = field(default_factory=PassLossResult)
    drop_shedding: DropSheddingResult = field(default_factory=DropSheddingResult)
    advisory_isolation: AdvisoryIsolationResult = field(default_factory=AdvisoryIsolationResult)
    cram_integrity: CRAMIntegrityResult = field(default_factory=CRAMIntegrityResult)
    rsync_health: RSYNCHealthResult = field(default_factory=RSYNCHealthResult)

    @property
    def verdict(self) -> str:
        checks = [
            self.torn_files.ok,
            self.continuity.ok,
            self.pass_loss.ok,
            self.drop_shedding.ok,
            self.advisory_isolation.ok,
            self.cram_integrity.ok,
            self.rsync_health.ok,
        ]
        if all(checks):
            return "PASS"
        return "FAIL"

    def failures(self) -> list[dict]:
        """
        Produce CFC-1.0 failure records for every detected condition.
        Maps check results to R/C/A/G/O failure classes for traceability.
        """
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        result: list[dict] = []

        # Torn .tmp files → C1 (atomic write contract violated)
        for path in self.torn_files.torn:
            result.append(make_failure(
                "C1", "HIGH", "torn .tmp file found — atomic write contract violated",
                path=path, timestamp_utc=now,
            ))

        # Continuity: departure hash ≠ arrival hash → R3 (authority hash mismatch)
        for mm in self.continuity.hash_mismatches:
            result.append(make_replay_failure(
                "R3", "HIGH", "authority_hash mismatch — departure/arrival payload divergence",
                object_id=str(mm.get("frame_id")),
                expected_hash=mm.get("dep_hash"),
                observed_hash=mm.get("arr_hash"),
                timestamp_utc=now,
            ))

        # Continuity: departure with no arrival → R2 (sequence break)
        for od in self.continuity.orphan_departures:
            result.append(make_failure(
                "R2", "HIGH", "departure without matching arrival — replay sequence break",
                frame_id=od.get("frame_id"), timestamp_utc=now,
            ))

        # Continuity: arrival with no departure → R2
        for oa in self.continuity.orphan_arrivals:
            result.append(make_failure(
                "R2", "HIGH", "arrival without matching departure — replay sequence break",
                frame_id=oa.get("frame_id"), timestamp_utc=now,
            ))

        # Silent PASS loss → R5 (PASS/DROP verdict mismatch with CRAM state)
        for fid in self.pass_loss.silent_losses:
            result.append(make_replay_failure(
                "R5", "CRITICAL", "PASS verdict without CRAM commit — silent loss forbidden",
                object_id=str(fid), timestamp_utc=now,
            ))

        # Unlogged DROPs → A1 (audit continuity broken)
        for fid in self.drop_shedding.unlogged_drops:
            result.append(make_failure(
                "A1", "HIGH", "DROP verdict without shedding log entry — audit continuity broken",
                frame_id=fid, timestamp_utc=now,
            ))

        # Advisory isolation violations → G5 (authority boundary violated)
        for path in self.advisory_isolation.lane1_paths_touched_by_advisory:
            result.append(make_failure(
                "G5", "CRITICAL", "advisory packet references Lane-1 path — authority boundary violated",
                path=path, timestamp_utc=now,
            ))

        # CRAM file hash failures → R3
        for path in self.cram_integrity.hash_failures:
            result.append(make_replay_failure(
                "R3", "HIGH", "CRAM file authority_hash mismatch — content corrupted",
                object_id=path, timestamp_utc=now,
            ))

        # CRAM chain breaks → R4 (chain integrity failure)
        for fid in self.cram_integrity.prev_hash_mismatches:
            result.append(make_failure(
                "R4", "HIGH", "CRAM prev_cram_hash chain break — chain integrity failure",
                frame_id=fid, timestamp_utc=now,
            ))

        # RSYNC blocked → O1
        if self.rsync_health.blocked:
            result.append(make_failure(
                "O1", "CRITICAL", "RSYNC is blocked — Priority Zero violated",
                blocked_by=self.rsync_health.reason, timestamp_utc=now,
            ))

        return result

    def to_report(self) -> dict:
        """Machine-readable report including CFC-1.0 failure records."""
        f = self.failures()
        return {
            "schema":          "ph6.crash_replay_report.v2",
            "verdict":         self.verdict,
            "timestamp_utc":   datetime.fromtimestamp(self.timestamp, timezone.utc)
                               .strftime("%Y-%m-%dT%H:%M:%SZ"),
            "failure_count":   len(f),
            "failures":        f,
            "checks": {
                "torn_files":        self.torn_files.ok,
                "continuity":        self.continuity.ok,
                "pass_loss":         self.pass_loss.ok,
                "drop_shedding":     self.drop_shedding.ok,
                "advisory_isolation": self.advisory_isolation.ok,
                "cram_integrity":    self.cram_integrity.ok,
                "rsync_health":      self.rsync_health.ok,
            },
        }

    def summary(self) -> str:
        failures = self.failures()
        by_check: dict[str, list[str]] = {}
        for f in failures:
            cls = f["failure_class"]
            by_check.setdefault(cls, []).append(cls)

        def _tag(ok: bool, codes: list[str]) -> str:
            s = "PASS" if ok else "FAIL"
            if not ok and codes:
                s += f" [{','.join(sorted(set(codes)))}]"
            return s

        lines = [
            f"CRAM-PU Crash/Replay Validation",
            f"Timestamp : {self.timestamp:.3f}",
            f"Verdict   : {self.verdict}",
            f"Failures  : {len(failures)}",
            f"",
            f"[1] Torn files       : {_tag(self.torn_files.ok, ['C1'])} "
            f"({len(self.torn_files.torn)} torn)",
            f"[2] PASS loss        : {_tag(self.pass_loss.ok, ['R5'])} "
            f"({len(self.pass_loss.silent_losses)} silent losses)",
            f"[3] DROP shedding    : {_tag(self.drop_shedding.ok, ['A1'])} "
            f"({len(self.drop_shedding.unlogged_drops)} unlogged drops)",
            f"[4] Advisory iso     : {_tag(self.advisory_isolation.ok, ['G5'])} "
            f"({len(self.advisory_isolation.lane1_paths_touched_by_advisory)} violations)",
            f"[5] CRAM integrity   : {_tag(self.cram_integrity.ok, ['R3','R4'])} "
            f"({len(self.cram_integrity.hash_failures)} hash failures, "
            f"{len(self.cram_integrity.prev_hash_mismatches)} chain breaks)",
            f"[6] RSYNC health     : {_tag(self.rsync_health.ok, ['O1'])} "
            f"(blocked={self.rsync_health.blocked})",
            f"    Continuity       : {_tag(self.continuity.ok, ['R2','R3'])} "
            f"({self.continuity.matched} matched, "
            f"{len(self.continuity.orphan_departures)} orphan_dep, "
            f"{len(self.continuity.orphan_arrivals)} orphan_arr, "
            f"{len(self.continuity.hash_mismatches)} hash_mismatch)",
        ]
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Log helpers
# ---------------------------------------------------------------------------

def _read_jsonl(path: Path) -> List[dict]:
    if not path.exists():
        return []
    records = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def _read_cram_files(store: Path) -> List[dict]:
    """Read all cram_*.json files in sorted frame_id order."""
    files = sorted(store.glob("cram_*.json"), key=lambda p: p.name)
    records = []
    for p in files:
        with p.open("r", encoding="utf-8") as f:
            records.append((p, json.load(f)))
    return records


# ---------------------------------------------------------------------------
# Check 1: Torn files
# ---------------------------------------------------------------------------

def check_torn_files(paths: CRAMPaths) -> TornFileResult:
    """Scan cram_store for .tmp files left by a crashed atomic write."""
    result = TornFileResult()
    if not paths.cram_store.exists():
        return result
    for p in paths.cram_store.rglob("*.tmp"):
        result.torn.append(str(p))
    return result


# ---------------------------------------------------------------------------
# Check 2+3: Transfer continuity (departure → arrival pairing + hash match)
# ---------------------------------------------------------------------------

def check_continuity(paths: CRAMPaths) -> ContinuityResult:
    """
    Every departure must have a matching arrival (frame_id + payload_hash).
    Missing or mismatched pairs are anomalies.
    """
    result = ContinuityResult()
    departures = _read_jsonl(paths.departure_log)
    arrivals = _read_jsonl(paths.arrival_log)

    dep_index: dict[int, dict] = {}
    for d in departures:
        fid = d.get("frame_id")
        if fid is not None:
            dep_index[fid] = d

    arr_index: dict[int, dict] = {}
    for a in arrivals:
        fid = a.get("frame_id")
        if fid is not None:
            arr_index[fid] = a

    all_frame_ids = set(dep_index) | set(arr_index)

    for fid in sorted(all_frame_ids):
        dep = dep_index.get(fid)
        arr = arr_index.get(fid)

        if dep and not arr:
            result.orphan_departures.append({"frame_id": fid, "dep": dep})
        elif arr and not dep:
            result.orphan_arrivals.append({"frame_id": fid, "arr": arr})
        else:
            dep_hash = dep.get("payload_hash", "")
            arr_hash = arr.get("payload_hash", "")
            if dep_hash != arr_hash:
                result.hash_mismatches.append({
                    "frame_id": fid,
                    "dep_hash": dep_hash,
                    "arr_hash": arr_hash,
                })
            else:
                result.matched += 1

    return result


# ---------------------------------------------------------------------------
# Check 4: Silent PASS loss
# ---------------------------------------------------------------------------

def check_pass_loss(paths: CRAMPaths) -> PassLossResult:
    """
    Every frame with verdict=PASS must have a corresponding CRAM commit file.
    A PASS verdict with no CRAM file is a silent loss — forbidden.
    """
    result = PassLossResult()
    verdicts = _read_jsonl(paths.verdict_log)
    cram_records = _read_cram_files(paths.cram_store)

    cram_frame_ids = {rec.get("frame_id") for _, rec in cram_records}

    for v in verdicts:
        if v.get("verdict") == "PASS":
            result.pass_verdicts += 1
            fid = v.get("frame_id")
            if fid in cram_frame_ids:
                result.cram_commits += 1
            else:
                result.silent_losses.append(fid)

    return result


# ---------------------------------------------------------------------------
# Check 5: DROP shedding audit
# ---------------------------------------------------------------------------

def check_drop_shedding(paths: CRAMPaths) -> DropSheddingResult:
    """
    Every DROP verdict must have a corresponding shedding_log entry with
    a policy reference. Unlogged drops are forbidden.
    """
    result = DropSheddingResult()
    verdicts = _read_jsonl(paths.verdict_log)
    shedding = _read_jsonl(paths.shedding_log)

    shed_frame_ids = {s.get("frame_id") for s in shedding if s.get("policy_ref")}

    for v in verdicts:
        if v.get("verdict") == "DROP":
            result.total_drops += 1
            fid = v.get("frame_id")
            if fid in shed_frame_ids:
                result.logged_drops += 1
            else:
                result.unlogged_drops.append(fid)

    return result


# ---------------------------------------------------------------------------
# Check 6: Advisory isolation (Lane-2 never touches Lane-1 paths)
# ---------------------------------------------------------------------------

def check_advisory_isolation(paths: CRAMPaths) -> AdvisoryIsolationResult:
    """
    Scan MRAM-S advisory packets for any field that names a Lane-1 path
    (cram_store, departure_log, verdict_log, etc.).
    If any advisory packet contains a Lane-1 path reference, flag it.
    """
    result = AdvisoryIsolationResult()
    lane1_paths = {
        str(paths.cram_store),
        str(paths.departure_log),
        str(paths.arrival_log),
        str(paths.verdict_log),
    }

    if not paths.mram_s.exists():
        return result

    for p in paths.mram_s.glob("S*.json"):
        try:
            with p.open("r", encoding="utf-8") as f:
                raw = f.read()
            for l1path in lane1_paths:
                if l1path in raw:
                    result.lane1_paths_touched_by_advisory.append(str(p))
                    break
        except Exception:
            pass

    return result


# ---------------------------------------------------------------------------
# Check 7: CRAM integrity (file hashes + prev_cram_hash chain)
# ---------------------------------------------------------------------------

def check_cram_integrity(paths: CRAMPaths) -> CRAMIntegrityResult:
    """
    Walk every cram_*.json file in frame_id order.
    Verify:
      - stored cram_hash matches recomputed hash of file content
      - prev_cram_hash links match the hash of the previous file
    """
    result = CRAMIntegrityResult()
    cram_records = _read_cram_files(paths.cram_store)
    result.total_files = len(cram_records)

    GENESIS = "0" * 64
    prev_hash = GENESIS

    for p, rec in cram_records:
        stored_hash = rec.get("cram_hash", "")
        stored_prev = rec.get("prev_cram_hash", "")
        frame_id = rec.get("frame_id")

        # Recompute hash of the record minus cram_hash field
        body = {k: v for k, v in rec.items() if k != "cram_hash"}
        recomputed = blake2b256(body)

        if recomputed != stored_hash:
            result.hash_failures.append(str(p))

        if stored_prev != prev_hash:
            result.prev_hash_mismatches.append(frame_id)
            if result.chain_broken_at is None:
                result.chain_broken_at = frame_id

        prev_hash = stored_hash

    return result


# ---------------------------------------------------------------------------
# Check 8: RSYNC health
# ---------------------------------------------------------------------------

def check_rsync_health(paths: CRAMPaths) -> RSYNCHealthResult:
    """
    RSYNC must never be blocked.
    Check the rsync_queue log for a 'blocked' sentinel entry.
    If the queue file has a 'blocked_by' field in the latest entry, flag it.
    """
    result = RSYNCHealthResult()
    entries = _read_jsonl(paths.rsync_queue)
    if not entries:
        return result

    result.queue_depth = len(entries)
    latest = entries[-1]
    blocked_by = latest.get("blocked_by")
    if blocked_by:
        result.blocked = True
        result.reason = str(blocked_by)

    return result


# ---------------------------------------------------------------------------
# Main validator
# ---------------------------------------------------------------------------

class CrashReplayValidator:
    def __init__(self, paths: Optional[CRAMPaths] = None):
        self.paths = paths or CRAMPaths()

    def run(self) -> CrashReplayReport:
        report = CrashReplayReport()
        report.torn_files = check_torn_files(self.paths)
        report.continuity = check_continuity(self.paths)
        report.pass_loss = check_pass_loss(self.paths)
        report.drop_shedding = check_drop_shedding(self.paths)
        report.advisory_isolation = check_advisory_isolation(self.paths)
        report.cram_integrity = check_cram_integrity(self.paths)
        report.rsync_health = check_rsync_health(self.paths)
        return report


# ---------------------------------------------------------------------------
# CRAM writer (atomic commit contract)
# Used by CRAM-PU ingest to write Lane-1 authoritative records.
# ---------------------------------------------------------------------------

class CRAMWriter:
    """
    Atomic CRAM commit: write(tmp) → fsync(tmp) → rename → fsync(dir)
    Never call this with verdict != PASS.
    """

    def __init__(self, store: Path):
        self.store = store
        self.store.mkdir(parents=True, exist_ok=True)
        self._prev_hash = self._load_last_hash()

    def _load_last_hash(self) -> str:
        files = sorted(self.store.glob("cram_*.json"), key=lambda p: p.name)
        if not files:
            return "0" * 64
        with files[-1].open("r", encoding="utf-8") as f:
            rec = json.load(f)
        return rec.get("cram_hash", "0" * 64)

    def commit(self, frame_id: int, payload_hash: str, verdict_record: dict) -> dict:
        if verdict_record.get("verdict") != "PASS":
            raise ValueError(
                f"CRAMWriter.commit called with verdict={verdict_record.get('verdict')}. "
                "Only PASS frames may be committed to CRAM."
            )

        record = {
            "schema":         "ph6.cram_commit.v1",
            "frame_id":       frame_id,
            "payload_hash":   payload_hash,
            "hash_algorithm": "BLAKE2b-256",
            "verdict":        "PASS",
            "authority":      "LANE_1",
            "prev_cram_hash": self._prev_hash,
            "timestamp_utc":  datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        record["cram_hash"] = blake2b256(
            {k: v for k, v in record.items() if k != "cram_hash"}
        )

        filename = f"cram_{frame_id:010d}.json"
        final    = self.store / filename
        tmp      = self.store / (filename + ".tmp")
        marker   = self.store / (filename + ".blake2b")
        tmp_marker = self.store / (filename + ".blake2b.tmp")

        # Atomic write: CRAM commit JSON
        with tmp.open("w", encoding="utf-8") as f:
            json.dump(record, f, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())

        os.replace(str(tmp), str(final))

        # Atomic write: .blake2b commit marker
        marker_data = record["cram_hash"].encode("utf-8") + b"\n"
        fd = os.open(str(tmp_marker), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)
        try:
            os.write(fd, marker_data)
            os.fsync(fd)
        finally:
            os.close(fd)
        os.replace(str(tmp_marker), str(marker))

        # Single fsync of parent dir covers both final files
        dir_fd = os.open(str(self.store), os.O_RDONLY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)

        self._prev_hash = record["cram_hash"]
        return record


# ---------------------------------------------------------------------------
# Shedding logger (required for any DROP that is shed from RAM staging)
# ---------------------------------------------------------------------------

class SheddingLogger:
    """Log explicit DROP shedding events. Required before any DROP is discarded."""

    def __init__(self, paths: CRAMPaths):
        self.paths = paths

    def log(self, frame_id: int, policy_ref: str, reason: str) -> dict:
        entry = {
            "schema": "ph6.drop_shedding.v1",
            "frame_id": frame_id,
            "policy_ref": policy_ref,
            "reason": reason,
            "authority": "LANE_1",
            "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        with self.paths.shedding_log.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, sort_keys=True, separators=(",", ":"),
                               allow_nan=False, ensure_ascii=False))
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        return entry
