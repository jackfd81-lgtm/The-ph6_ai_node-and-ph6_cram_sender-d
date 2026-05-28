"""
ph6_cram_sim.py — PH6/CRAM Internal Simulation Core
Standalone and importable.  No camera, USB, CAN, or HAT.

CANON RULES ENFORCED:
  - BLAKE2b-256 (digest_size=32) is the sole authority hash
  - SHA-256 retained as compat sidecar only
  - motion_fraction is the only permitted motion metric
  - .blake2b marker written LAST on PASS path; NEVER on DROP path
  - Atomic write = 4-step contract: write-tmp -> fsync-file -> rename -> fsync-dir
  - PASS/DROP are the only permitted verdicts
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final, Literal

# ---------------------------------------------------------------------------
# Gate thresholds — named constants, single source of truth
# ---------------------------------------------------------------------------

GATE_ENTROPY_MIN:     Final[float] = 6.0
GATE_LAPLACIAN_MIN:   Final[float] = 100.0
GATE_MOTION_FRAC_MIN: Final[float] = 0.01
GATE_MOTION_FRAC_MAX: Final[float] = 0.75

FIELD_ENTROPY:         Final[str] = "entropy"
FIELD_LAPLACIAN:       Final[str] = "laplacian_var"
FIELD_MOTION_FRACTION: Final[str] = "motion_fraction"

FORBIDDEN_MOTION_FIELDS: Final[frozenset[str]] = frozenset({
    "motion_score",
    "motion_decay_score",
})

Verdict = Literal["PASS", "DROP"]


# ---------------------------------------------------------------------------
# Hashing
# ---------------------------------------------------------------------------

def blake2b256(data: bytes) -> str:
    return hashlib.blake2b(data, digest_size=32).hexdigest()


def sha256hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(obj: object) -> bytes:
    """Deterministic JSON bytes — sort_keys, no spaces."""
    return json.dumps(
        obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode()


# ---------------------------------------------------------------------------
# Atomic write — 4-step contract
# ---------------------------------------------------------------------------

def atomic_write(path: Path, data: bytes) -> None:
    """
    4-step atomic write:
      1. Write to a temp file in the same directory
      2. fsync the file descriptor
      3. os.replace (atomic on POSIX)
      4. fsync the parent directory

    Tracks whether os.replace succeeded so the finally block never unlinks
    a file that was already renamed into place (TOCTOU fix).
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_str = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=str(path.parent),
    )
    tmp = Path(tmp_str)
    replaced = False
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
        replaced = True
        dfd = os.open(str(path.parent), os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(dfd)
        finally:
            os.close(dfd)
    finally:
        if not replaced and tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass  # best-effort; do not mask the original exception


# ---------------------------------------------------------------------------
# Gate
# ---------------------------------------------------------------------------

def check_forbidden_fields(metrics: dict) -> None:
    """Raise ValueError if any forbidden motion field is present."""
    bad = FORBIDDEN_MOTION_FIELDS & metrics.keys()
    if bad:
        raise ValueError(f"Forbidden metric fields present: {sorted(bad)}")


def gate(metrics: dict) -> Verdict:
    """
    Deterministic PASS/DROP gate.  Returns identical result on replay.
    Caller must call check_forbidden_fields() first.
    """
    entropy_ok = float(metrics[FIELD_ENTROPY]) >= GATE_ENTROPY_MIN
    blur_ok    = float(metrics[FIELD_LAPLACIAN]) >= GATE_LAPLACIAN_MIN
    motion_ok  = (
        GATE_MOTION_FRAC_MIN
        <= float(metrics[FIELD_MOTION_FRACTION])
        <= GATE_MOTION_FRAC_MAX
    )
    return "PASS" if (entropy_ok and blur_ok and motion_ok) else "DROP"


# ---------------------------------------------------------------------------
# Audit chain
# ---------------------------------------------------------------------------

@dataclass
class AuditChain:
    events: list[dict] = field(default_factory=list)
    _prev_hash: str = field(default="GENESIS", init=False, repr=False)

    def emit(
        self,
        event_type: str,
        object_id: str,
        status: Verdict,
        authority_hash: str,
        stage: str,
        node_id: str = "pi5-internal-test",
    ) -> dict:
        event: dict = {
            "schema_version": "ph6.audit.event.v1",
            "event_id": f"event_{len(self.events) + 1:06d}",
            "event_seq": len(self.events) + 1,
            "event_type": event_type,
            "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "node_id": node_id,
            "object_id": object_id,
            "stage": stage,
            "status": status,
            "authority_hash": authority_hash,
            "prev_event_hash": self._prev_hash,
        }
        # Hash computed before adding event_hash field — no pop needed on verify
        event_hash = blake2b256(canonical_json(event))
        event["event_hash"] = event_hash
        self._prev_hash = event_hash
        self.events.append(event)
        return event

    def write(self, path: Path) -> None:
        lines = b"".join(
            (json.dumps(e, sort_keys=True) + "\n").encode()
            for e in self.events
        )
        atomic_write(path, lines)

    @staticmethod
    def verify(path: Path) -> tuple[bool, str]:
        """
        Verify the hash chain at path.  Returns (ok, message).

        Builds a copy of each event dict without event_hash for canonical
        hashing — the loaded data is never mutated (fixes the dict-pop bug).
        """
        prev = "GENESIS"
        for lineno, line in enumerate(path.read_text().splitlines(), 1):
            ev = json.loads(line)
            stored_hash = ev.get("event_hash")
            if stored_hash is None:
                return False, f"line {lineno}: missing event_hash"
            ev_for_hash = {k: v for k, v in ev.items() if k != "event_hash"}
            if ev_for_hash.get("prev_event_hash") != prev:
                return False, (
                    f"line {lineno}: prev_event_hash mismatch "
                    f"(expected {prev!r}, got {ev_for_hash['prev_event_hash']!r})"
                )
            calc = blake2b256(canonical_json(ev_for_hash))
            if calc != stored_hash:
                return False, f"line {lineno}: event_hash mismatch (calc={calc})"
            prev = stored_hash
        return True, "OK"


# ---------------------------------------------------------------------------
# CRAM simulation
# ---------------------------------------------------------------------------

@dataclass
class FrameInput:
    object_id: str
    raw: bytes
    metrics: dict
    node_id: str = "pi5-internal-test"
    sensor_id: str = "simulated-internal-no-camera"


@dataclass
class FrameResult:
    object_id: str
    verdict: Verdict
    authority_hash: str
    metrics: dict


class CRAMSimulation:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.audit = AuditChain()
        self.results: list[FrameResult] = []
        for sub in ("cram-0", "cram-a", "cram-r", "audit", "export", "mram-s", "replay"):
            (root / sub).mkdir(parents=True, exist_ok=True)

    def process(self, frame: FrameInput) -> FrameResult:
        check_forbidden_fields(frame.metrics)
        verdict        = gate(frame.metrics)
        authority_hash = blake2b256(frame.raw + canonical_json(frame.metrics))

        meta = {
            "schema_version": "ph6.cram.meta.v1",
            "object_id": frame.object_id,
            "lane": 1,
            "tier": "cram-a" if verdict == "PASS" else "cram-r",
            "capture_timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "node_id": frame.node_id,
            "sensor_id": frame.sensor_id,
            "metrics": frame.metrics,
            "verdict": verdict,
            "authority_hash": authority_hash,
            "sha256_compat": sha256hex(frame.raw),
        }

        if verdict == "PASS":
            self._write_pass(frame, meta, authority_hash)
        else:
            self._write_drop(frame, meta, authority_hash)

        result = FrameResult(
            object_id=frame.object_id,
            verdict=verdict,
            authority_hash=authority_hash,
            metrics=frame.metrics,
        )
        self.results.append(result)
        return result

    def _write_pass(self, frame: FrameInput, meta: dict, authority_hash: str) -> None:
        tier = self.root / "cram-a"
        oid  = frame.object_id
        atomic_write(tier / f"{oid}_raw.bin",   frame.raw)
        atomic_write(tier / f"{oid}_meta.json", json.dumps(meta, sort_keys=True, indent=2).encode())
        atomic_write(tier / f"{oid}.sha256",    (meta["sha256_compat"] + "\n").encode())
        self.audit.emit("CRAM_INTERNAL_PASS_PROMOTION", frame.object_id, "PASS", authority_hash, "cram-a")
        atomic_write(tier / f"{oid}.blake2b",   (authority_hash + "\n").encode())  # LAST

    def _write_drop(self, frame: FrameInput, meta: dict, authority_hash: str) -> None:
        tier = self.root / "cram-r"
        oid  = frame.object_id
        atomic_write(tier / f"{oid}_raw.bin",   frame.raw)
        atomic_write(tier / f"{oid}_meta.json", json.dumps(meta, sort_keys=True, indent=2).encode())
        self.audit.emit("CRAM_INTERNAL_REJECT", frame.object_id, "DROP", authority_hash, "cram-r")
        if (tier / f"{oid}.blake2b").exists():
            raise RuntimeError(f"INVARIANT VIOLATION: CRAM-R has forbidden .blake2b marker for {oid}")

    def finalize_audit(self) -> Path:
        audit_path = self.root / "audit" / "audit.jsonl"
        self.audit.write(audit_path)
        return audit_path

    def export_copy(self, src_tier: str = "cram-a") -> Path:
        """Local shutil copy — no rsync, no USB, no external device."""
        dst = self.root / "export" / f"{src_tier}-copy"
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(self.root / src_tier, dst)
        return dst

    def verify_pass_files(self, object_id: str) -> list[str]:
        """Returns list of missing paths (empty = all present)."""
        tier = self.root / "cram-a"
        required = [
            tier / f"{object_id}_raw.bin",
            tier / f"{object_id}_meta.json",
            tier / f"{object_id}.sha256",
            tier / f"{object_id}.blake2b",
        ]
        return [str(p) for p in required if not p.exists()]

    def verify_drop_files(self, object_id: str) -> list[str]:
        """Returns missing required files + flags forbidden marker if present."""
        tier = self.root / "cram-r"
        required = [
            tier / f"{object_id}_raw.bin",
            tier / f"{object_id}_meta.json",
        ]
        issues = [str(p) for p in required if not p.exists()]
        marker = tier / f"{object_id}.blake2b"
        if marker.exists():
            issues.append(f"FORBIDDEN_MARKER_EXISTS:{marker}")
        return issues

    def replay_check(self, frames: list[FrameInput]) -> tuple[bool, str]:
        """Re-run gate on original frames; compare verdicts and authority hashes."""
        for frame, original in zip(frames, self.results):
            check_forbidden_fields(frame.metrics)
            v  = gate(frame.metrics)
            ah = blake2b256(frame.raw + canonical_json(frame.metrics))
            if v != original.verdict:
                return False, f"{frame.object_id}: verdict mismatch ({v} vs {original.verdict})"
            if ah != original.authority_hash:
                return False, f"{frame.object_id}: authority_hash mismatch"
        return True, "OK"

    def export_verify(self, src_tier: str = "cram-a") -> tuple[bool, str]:
        """Byte-exact comparison of export copy vs source tier."""
        src = self.root / src_tier
        dst = self.root / "export" / f"{src_tier}-copy"
        for src_file in sorted(src.iterdir()):
            dst_file = dst / src_file.name
            if not dst_file.exists():
                return False, f"Missing in export: {dst_file.name}"
            if src_file.read_bytes() != dst_file.read_bytes():
                return False, f"Mismatch: {src_file.name}"
        return True, "OK"
