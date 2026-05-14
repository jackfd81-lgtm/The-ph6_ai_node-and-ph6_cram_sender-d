#!/usr/bin/env python3
"""
TOK-1.0 Token Lifecycle + Deterministic Pruning
PH6 / CRAM Advisory Layer

Lane: 2
Authority: ZERO
Write domain: MRAM-S only
Hash: BLAKE2b-256
Audit: append-only JSONL hash chain

Doctrine: PH6_SOURCE/DRAFT/PH6-TOK-LIFECYCLE-PRUNE-1.0.md
"""

from __future__ import annotations

import os
import json
import time
import tempfile
import hashlib
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional, Any, Literal


# =============================================================================
# Canonical Helpers
# =============================================================================

def now_ms() -> int:
    return int(time.time() * 1000)


def canonical_json(obj: Any) -> bytes:
    """
    PH6-style canonical JSON:
    - sorted keys
    - UTF-8
    - no NaN / Infinity
    - compact separators
    """
    return json.dumps(
        obj,
        sort_keys=True,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")


def blake2b256_hex(obj: Any) -> str:
    return hashlib.blake2b(canonical_json(obj), digest_size=32).hexdigest()


def atomic_write_json(path: Path, payload: Any) -> None:
    """
    Advisory MRAM-S atomic write:
    write(tmp) -> fsync(fd) -> rename -> fsync(dir)

    This is not CRAM authority, but it follows crash-safe discipline.
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    data = canonical_json(payload)

    fd, tmp_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=str(path.parent),
    )

    tmp_path = Path(tmp_name)

    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())

        os.replace(tmp_path, path)

        dir_fd = os.open(str(path.parent), os.O_DIRECTORY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)

    finally:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)


def append_jsonl(path: Path, payload: dict) -> None:
    """Append-only JSONL advisory audit."""
    path.parent.mkdir(parents=True, exist_ok=True)
    line = canonical_json(payload) + b"\n"

    with open(path, "ab") as f:
        f.write(line)
        f.flush()
        os.fsync(f.fileno())


# =============================================================================
# Token Models
# =============================================================================

TokenType = Literal["RT", "VDT", "VLT"]


@dataclass(frozen=True)
class TokenBase:
    token_id: str
    cram_ref_hash: str
    timestamp_ms: int
    token_type: TokenType
    authority: str = "ZERO"
    advisory_only: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)

    def state_hash(self) -> str:
        return blake2b256_hex(self.to_dict())

    def is_invalid(self) -> bool:
        return (
            not self.token_id
            or not self.cram_ref_hash
            or self.authority != "ZERO"
            or self.advisory_only is not True
        )


@dataclass(frozen=True)
class RT(TokenBase):
    object_class: str = ""
    bbox: List[float] = field(default_factory=list)
    confidence: float = 0.0
    token_type: TokenType = "RT"


@dataclass(frozen=True)
class VDT(TokenBase):
    object_class: str = ""
    bbox: List[float] = field(default_factory=list)
    confidence: float = 0.0
    support_count: int = 1
    last_updated_ms: int = 0
    token_type: TokenType = "VDT"


@dataclass(frozen=True)
class VLT(TokenBase):
    object_class: str = ""
    bbox: List[float] = field(default_factory=list)
    confidence: float = 0.0
    first_seen_ms: int = 0
    last_seen_ms: int = 0
    support_count: int = 0
    mean_confidence: float = 0.0
    centroid: List[float] = field(default_factory=list)
    protected: bool = False
    token_type: TokenType = "VLT"


# =============================================================================
# Advisory Audit Chain
# =============================================================================

_TOK_EVENT_ADVISORY_RESULT = {
    "RT_GENESIS": "OBSERVATION",
    "VDT_GENESIS": "OBSERVATION",
    "VLT_GENESIS": "OBSERVATION",
    "VDT_PROMOTED_TO_VLT": "ANALYSIS_COMPLETE",
    "VDT_PRUNED": "ANALYSIS_COMPLETE",
    "VLT_PRUNED": "ANALYSIS_COMPLETE",
    "VLT_PROTECTION_REQUEST": "OBSERVATION",
    "LIVE_STORE_LOAD_WARNING": "DRIFT_WARNING",
}


class AdvisoryAudit:
    """
    Append-only advisory audit chain.
    Lane-2 only. Never affects CRAM authority.
    """

    def __init__(self, audit_path: Path):
        self.audit_path = audit_path
        self.prev_event_hash = self._load_last_hash()

    def _load_last_hash(self) -> str:
        if not self.audit_path.exists():
            return "GENESIS"

        last = None
        with open(self.audit_path, "rb") as f:
            for line in f:
                if line.strip():
                    last = line

        if not last:
            return "GENESIS"

        try:
            obj = json.loads(last.decode("utf-8"))
            return obj.get("event_hash", "GENESIS")
        except Exception:
            return "GENESIS"

    def emit(self, event_type: str, payload: dict, event_time_ms: Optional[int] = None) -> dict:
        event = {
            "schema": "ph6.tok.advisory_event.v1",
            "authority": "ZERO",
            "advisory_only": True,
            "advisory_result": _TOK_EVENT_ADVISORY_RESULT.get(event_type, "OBSERVATION"),
            "replay_dependency": False,
            "affects_pass_drop": False,
            "affects_thresholds": False,
            "affects_cram_commit": False,
            "affects_rsync": False,
            "event_type": event_type,
            "timestamp_ms": event_time_ms if event_time_ms is not None else now_ms(),
            "prev_event_hash": self.prev_event_hash,
            "payload": payload,
        }

        event["event_hash"] = blake2b256_hex(event)
        append_jsonl(self.audit_path, event)
        self.prev_event_hash = event["event_hash"]
        return event


# =============================================================================
# Token Store
# =============================================================================

class TokenStore:
    """
    TOK-1.0 live materialization store.

    This store is rebuildable from the advisory audit chain.
    This store is not authoritative truth.
    """

    def __init__(self, base_dir: str = "/var/ph6/mram-s/tokens"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

        self.audit = AdvisoryAudit(self.base_dir / "tok_advisory_audit.jsonl")

        self.rt_store: Dict[str, RT] = {}
        self.vdt_store: Dict[str, VDT] = {}
        self.vlt_store: Dict[str, VLT] = {}

        self.load_live_materialization()

    def _path(self, name: str) -> Path:
        return self.base_dir / name

    def _save_all(self) -> None:
        payload = {
            "schema": "ph6.tok.live_store.v1",
            "authority": "ZERO",
            "advisory_only": True,
            "rt_store": {k: v.to_dict() for k, v in sorted(self.rt_store.items())},
            "vdt_store": {k: v.to_dict() for k, v in sorted(self.vdt_store.items())},
            "vlt_store": {k: v.to_dict() for k, v in sorted(self.vlt_store.items())},
        }

        atomic_write_json(self._path("live_tokens.json"), payload)

    def load_live_materialization(self) -> None:
        path = self._path("live_tokens.json")
        if not path.exists():
            return

        try:
            raw = json.loads(path.read_text(encoding="utf-8"))

            for k, v in raw.get("rt_store", {}).items():
                self.rt_store[k] = RT(**v)

            for k, v in raw.get("vdt_store", {}).items():
                self.vdt_store[k] = VDT(**v)

            for k, v in raw.get("vlt_store", {}).items():
                self.vlt_store[k] = VLT(**v)

        except Exception as e:
            self.audit.emit(
                "LIVE_STORE_LOAD_WARNING",
                {"reason": str(e), "path": str(path)},
            )

    # -------------------------------------------------------------------------
    # Add / Update Operations
    # -------------------------------------------------------------------------

    def add_rt(self, rt: RT) -> None:
        if rt.is_invalid():
            raise ValueError("Invalid RT")

        self.rt_store[rt.cram_ref_hash] = rt

        self.audit.emit("RT_GENESIS", {
            "token_id": rt.token_id,
            "token_type": "RT",
            "cram_ref_hash": rt.cram_ref_hash,
            "token_state_hash": rt.state_hash(),
        })

        self._save_all()

    def add_vdt(self, vdt: VDT) -> None:
        if vdt.is_invalid():
            raise ValueError("Invalid VDT")

        if vdt.last_updated_ms <= 0:
            vdt = VDT(**{**vdt.to_dict(), "last_updated_ms": vdt.timestamp_ms})

        self.vdt_store[vdt.token_id] = vdt

        self.audit.emit("VDT_GENESIS", {
            "token_id": vdt.token_id,
            "token_type": "VDT",
            "cram_ref_hash": vdt.cram_ref_hash,
            "token_state_hash": vdt.state_hash(),
        })

        self._save_all()

    def protect_vlt(self, token_id: str, reason: str, event_time_ms: Optional[int] = None) -> bool:
        """
        Audited protection request. Not an override. Authority ZERO.
        """
        vlt = self.vlt_store.get(token_id)
        if not vlt:
            return False

        new_vlt = VLT(**{**vlt.to_dict(), "protected": True})
        self.vlt_store[token_id] = new_vlt

        self.audit.emit("VLT_PROTECTION_REQUEST", {
            "token_id": token_id,
            "reason": reason,
            "token_state_hash": new_vlt.state_hash(),
        }, event_time_ms)

        self._save_all()
        return True

    # -------------------------------------------------------------------------
    # Promotion
    # -------------------------------------------------------------------------

    def promote_to_vlt(
        self,
        candidate_vdt_ids: List[str],
        config: dict,
        event_time_ms: Optional[int] = None,
    ) -> Optional[VLT]:
        vdts = [self.vdt_store[x] for x in candidate_vdt_ids if x in self.vdt_store]
        vlt = attempt_vdt_promotion(vdts, config, event_time_ms or now_ms())

        if not vlt:
            return None

        self.vlt_store[vlt.token_id] = vlt

        for vdt in vdts:
            self.vdt_store.pop(vdt.token_id, None)

        self.audit.emit("VDT_PROMOTED_TO_VLT", {
            "vlt_token_id": vlt.token_id,
            "source_vdt_ids": [v.token_id for v in vdts],
            "cram_ref_hash": vlt.cram_ref_hash,
            "token_state_hash": vlt.state_hash(),
            "config_hash": blake2b256_hex(config),
        }, event_time_ms)

        self._save_all()
        return vlt

    # -------------------------------------------------------------------------
    # Pruning
    # -------------------------------------------------------------------------

    def prune(self, config: dict, current_time_ms: Optional[int] = None) -> int:
        """
        Deterministic pruning pass.

        Deletes live materializations only.
        Emits advisory audit events before deletion.
        Audit history is never deleted.
        """
        now = current_time_ms if current_time_ms is not None else now_ms()
        config_hash = blake2b256_hex(config)

        pruned_count = 0

        for token_id in sorted(list(self.vdt_store.keys())):
            vdt = self.vdt_store[token_id]
            reason = should_prune_vdt(vdt, now, config)

            if reason:
                self.audit.emit("VDT_PRUNED", {
                    "token_id": token_id,
                    "token_type": "VDT",
                    "reason": reason,
                    "cram_ref_hash": vdt.cram_ref_hash,
                    "token_state_hash": vdt.state_hash(),
                    "config_hash": config_hash,
                }, now)

                self.vdt_store.pop(token_id, None)
                pruned_count += 1

        for token_id in sorted(list(self.vlt_store.keys())):
            vlt = self.vlt_store[token_id]

            if vlt.protected:
                continue

            reason = should_prune_vlt(vlt, now, config)

            if reason:
                if config.get("archive_pruned", True):
                    self._archive_vlt(vlt, config_hash, now)

                self.audit.emit("VLT_PRUNED", {
                    "token_id": token_id,
                    "token_type": "VLT",
                    "reason": reason,
                    "cram_ref_hash": vlt.cram_ref_hash,
                    "token_state_hash": vlt.state_hash(),
                    "config_hash": config_hash,
                }, now)

                self.vlt_store.pop(token_id, None)
                pruned_count += 1

        if pruned_count:
            self._save_all()

        return pruned_count

    def _archive_vlt(self, vlt: VLT, config_hash: str, timestamp_ms: int) -> None:
        archive_dir = self.base_dir / "archive"
        archive_dir.mkdir(parents=True, exist_ok=True)

        archive_payload = {
            "schema": "ph6.tok.vlt_archive.v1",
            "authority": "ZERO",
            "advisory_only": True,
            "replay_dependency": False,
            "timestamp_ms": timestamp_ms,
            "config_hash": config_hash,
            "token": vlt.to_dict(),
            "token_state_hash": vlt.state_hash(),
        }

        archive_payload["archive_hash"] = blake2b256_hex(archive_payload)

        path = archive_dir / f"{vlt.token_id}.{timestamp_ms}.json"
        atomic_write_json(path, archive_payload)


# =============================================================================
# Prune Rules
# =============================================================================

def should_prune_vdt(vdt: VDT, now: int, config: dict) -> Optional[str]:
    age = now - vdt.timestamp_ms
    inactivity = now - vdt.last_updated_ms

    if age > config.get("VDT_TTL_ms", 8000):
        return "ttl_expired"

    if age > config.get("promotion_window_ms", 10000) and vdt.support_count < config.get("N", 5):
        return "promotion_window_expired_weak_support"

    if inactivity > config.get("VDT_inactive_prune_ms", 5000) and vdt.support_count < config.get("N", 5):
        return "inactive_weak_support"

    if vdt.confidence < config.get("vdt_min_confidence", 0.25):
        return "confidence_collapse"

    return None


def should_prune_vlt(vlt: VLT, now: int, config: dict) -> Optional[str]:
    age = now - vlt.first_seen_ms
    inactivity = now - vlt.last_seen_ms

    if age > config.get("VLT_max_lifetime_ms", 86400000):
        return "max_lifetime_expired"

    if inactivity > config.get("VLT_inactive_prune_ms", 1800000):
        return "inactive"

    if vlt.mean_confidence < config.get("vlt_min_confidence", 0.65):
        return "confidence_decay"

    return None


# =============================================================================
# Promotion Logic
# =============================================================================

def attempt_vdt_promotion(
    candidate_vdts: List[VDT],
    config: dict,
    current_time_ms: int,
) -> Optional[VLT]:
    """Fail-closed VDT -> VLT promotion."""

    if not candidate_vdts:
        return None

    vdts = sorted(candidate_vdts, key=lambda v: (v.timestamp_ms, v.token_id))

    for vdt in vdts:
        if vdt.is_invalid():
            return None

        if current_time_ms - vdt.timestamp_ms > config.get("promotion_window_ms", 10000):
            return None

    if len(vdts) < config.get("N", 5):
        return None

    min_ts = min(v.timestamp_ms for v in vdts)
    max_ts = max(v.timestamp_ms for v in vdts)

    if max_ts - min_ts > config.get("W_ms", 1500):
        return None

    cram_ref_hash = vdts[0].cram_ref_hash
    if any(v.cram_ref_hash != cram_ref_hash for v in vdts):
        return None

    object_class = vdts[0].object_class
    if any(v.object_class != object_class for v in vdts):
        return None

    if not meets_spatial_consistency(vdts, config.get("iou_min", 0.6)):
        return None

    mean_conf = sum(v.confidence for v in vdts) / len(vdts)
    if mean_conf < config.get("C_min", 0.55):
        return None

    centroid = compute_centroid([v.bbox for v in vdts])

    source_ids = [v.token_id for v in vdts]
    vlt_seed = {
        "cram_ref_hash": cram_ref_hash,
        "source_vdt_ids": source_ids,
        "first_seen_ms": min_ts,
        "last_seen_ms": max_ts,
        "object_class": object_class,
    }

    vlt_id = "vlt_" + blake2b256_hex(vlt_seed)[:24]

    return VLT(
        token_id=vlt_id,
        cram_ref_hash=cram_ref_hash,
        timestamp_ms=min_ts,
        first_seen_ms=min_ts,
        last_seen_ms=max_ts,
        object_class=object_class,
        bbox=vdts[0].bbox,
        confidence=mean_conf,
        support_count=len(vdts),
        mean_confidence=mean_conf,
        centroid=centroid,
        protected=False,
        metadata={
            "promoted_from": source_ids,
            "promotion_seed_hash": blake2b256_hex(vlt_seed),
        },
    )


# =============================================================================
# Geometry Helpers
# =============================================================================

def bbox_iou(a: List[float], b: List[float]) -> float:
    """Intersection over Union. bbox format: [x, y, w, h]"""
    if len(a) != 4 or len(b) != 4:
        return 0.0

    ax1, ay1, aw, ah = a
    bx1, by1, bw, bh = b

    ax2, ay2 = ax1 + aw, ay1 + ah
    bx2, by2 = bx1 + bw, by1 + bh

    inter_w = max(0.0, min(ax2, bx2) - max(ax1, bx1))
    inter_h = max(0.0, min(ay2, by2) - max(ay1, by1))
    inter_area = inter_w * inter_h

    area_a = max(0.0, aw) * max(0.0, ah)
    area_b = max(0.0, bw) * max(0.0, bh)
    denom = area_a + area_b - inter_area

    if denom <= 0:
        return 0.0

    return inter_area / denom


def meets_spatial_consistency(vdts: List[VDT], iou_min: float) -> bool:
    if len(vdts) < 2:
        return True

    base = vdts[0].bbox
    return all(bbox_iou(base, v.bbox) >= iou_min for v in vdts[1:])


def compute_centroid(bboxes: List[List[float]]) -> List[float]:
    centers = [
        [x + w / 2.0, y + h / 2.0]
        for b in bboxes
        if len(b) == 4
        for x, y, w, h in [b]
    ]

    if not centers:
        return [0.0, 0.0]

    cx = sum(c[0] for c in centers) / len(centers)
    cy = sum(c[1] for c in centers) / len(centers)
    return [round(cx, 6), round(cy, 6)]


# =============================================================================
# Default Config
# =============================================================================

DEFAULT_TOK_CONFIG = {
    "schema": "ph6.tok.config.v1",
    "authority": "ZERO",
    "advisory_only": True,

    "N": 5,
    "W_ms": 1500,
    "iou_min": 0.6,
    "C_min": 0.55,

    "VDT_TTL_ms": 8000,
    "VDT_inactive_prune_ms": 5000,
    "vdt_min_confidence": 0.25,
    "promotion_window_ms": 10000,

    "VLT_max_lifetime_ms": 86400000,
    "VLT_inactive_prune_ms": 1800000,
    "vlt_min_confidence": 0.65,

    "max_tokens_per_store": 50000,
    "minimum_working_set": 500,
    "archive_pruned": True,
    "prune_interval_seconds": 60,
}


# =============================================================================
# Smoke Test
# =============================================================================

if __name__ == "__main__":
    store = TokenStore("./mram-s-test/tokens")

    t0 = now_ms()

    for i in range(5):
        vdt = VDT(
            token_id=f"vdt_test_{i}",
            cram_ref_hash="cram_ref_abc123",
            timestamp_ms=t0 + i * 100,
            last_updated_ms=t0 + i * 100,
            object_class="vehicle",
            bbox=[10.0 + i, 20.0, 100.0, 60.0],
            confidence=0.75,
            support_count=1,
        )
        store.add_vdt(vdt)

    vlt = store.promote_to_vlt(
        [f"vdt_test_{i}" for i in range(5)],
        DEFAULT_TOK_CONFIG,
        event_time_ms=t0 + 600,
    )

    print("PROMOTED:", vlt.token_id if vlt else None)

    pruned = store.prune(DEFAULT_TOK_CONFIG, current_time_ms=t0 + 9000)
    print("PRUNED:", pruned)
