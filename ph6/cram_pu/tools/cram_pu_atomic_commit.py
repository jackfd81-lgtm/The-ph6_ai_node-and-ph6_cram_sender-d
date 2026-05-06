"""
Phase 6 — CRAM-PU atomic commit writer.
Commits PASS verdicts to NVMe CRAM using the contract:
  write(tmp) → fsync(fd) → rename(tmp, final) → fsync(parent_dir)
DROP packets are never committed here. PASS packets are never skipped.
"""

import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


def _canonical_bytes(obj: dict) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def _blake2b256(obj: dict) -> str:
    return hashlib.blake2b(_canonical_bytes(obj), digest_size=32).hexdigest()


GENESIS_HASH = "0" * 64


class AtomicCRAMCommitter:
    def __init__(self, cram_dir: Path):
        self.cram_dir = cram_dir
        self.cram_dir.mkdir(parents=True, exist_ok=True)
        self._prev_hash = self._load_last_hash()
        self._seq = self._load_last_seq()

    def _load_last_hash(self) -> str:
        files = sorted(self.cram_dir.glob("cram_*.json"))
        if not files:
            return GENESIS_HASH
        with files[-1].open("r", encoding="utf-8") as f:
            return json.load(f).get("cram_hash", GENESIS_HASH)

    def _load_last_seq(self) -> int:
        files = sorted(self.cram_dir.glob("cram_*.json"))
        return len(files)

    def commit(self, verdict: dict) -> dict:
        if verdict["verdict"] != "PASS":
            raise ValueError(
                f"AtomicCRAMCommitter.commit: verdict must be PASS, got {verdict['verdict']!r}. "
                "DROP packets must not be committed to CRAM."
            )
        self._seq += 1
        record = {
            "schema":        "ph6.cram_commit.v1",
            "commit_seq":    self._seq,
            "packet_id":     verdict["packet_id"],
            "payload_hash":  verdict["input_hash"],
            "verdict":       "PASS",
            "authority":     "LANE_1",
            "prev_cram_hash": self._prev_hash,
            "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        record["cram_hash"] = _blake2b256(
            {k: v for k, v in record.items() if k != "cram_hash"}
        )

        filename = f"cram_{self._seq:010d}.json"
        final    = self.cram_dir / filename
        tmp      = self.cram_dir / (filename + ".tmp")
        marker   = self.cram_dir / (filename + ".blake2b")
        tmp_marker = self.cram_dir / (filename + ".blake2b.tmp")

        # Atomic write contract: payload
        fd = os.open(str(tmp), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)
        try:
            data = (_canonical_bytes(record) + b"\n")
            os.write(fd, data)
            os.fsync(fd)
        finally:
            os.close(fd)

        os.replace(str(tmp), str(final))

        # Atomic write contract: .blake2b commit marker
        # Object is authoritative only after both final and marker exist.
        marker_data = record["cram_hash"].encode("utf-8") + b"\n"
        fd2 = os.open(str(tmp_marker), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)
        try:
            os.write(fd2, marker_data)
            os.fsync(fd2)
        finally:
            os.close(fd2)

        os.replace(str(tmp_marker), str(marker))

        # Single fsync of parent directory covers both files
        dir_fd = os.open(str(self.cram_dir), os.O_RDONLY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)

        self._prev_hash = record["cram_hash"]
        return record


def commit_pass_verdicts(verdicts: list, cram_dir: Path) -> list:
    committer = AtomicCRAMCommitter(cram_dir)
    committed = []
    for v in verdicts:
        if v["verdict"] == "PASS":
            committed.append(committer.commit(v))
    return committed


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--verdict-log", required=True)
    ap.add_argument("--cram-dir",    required=True)
    args = ap.parse_args()
    with Path(args.verdict_log).open() as f:
        verdicts = [json.loads(l) for l in f if l.strip()]
    committed = commit_pass_verdicts(verdicts, Path(args.cram_dir))
    print(f"COMMITTED: {len(committed)} PASS packets to CRAM")
    # Verify no .tmp files remain
    tmps = list(Path(args.cram_dir).glob("*.tmp"))
    if tmps:
        print(f"ERROR: {len(tmps)} .tmp files remain after commit", file=sys.stderr)
        sys.exit(1)
    sys.exit(0)
