"""
ph6_l2_expand.mram_s_writer

Lane: 2
Authority: ZERO
Write domain: MRAM-S only

The only module in ph6_l2_expand permitted to perform filesystem writes.
Every write:
  - is confined to a configured MRAM-S output directory
  - rejects path traversal
  - rejects any path containing a CRAM-0 / CRAM-A / CRAM-R segment
  - is canonical JSON (sort_keys, ensure_ascii=False, allow_nan=False,
    compact separators)
  - is atomic: write temp -> fsync(fd) -> close -> rename -> fsync(dir)
  - is boundary-checked; payloads containing forbidden authority language
    are quarantined whole, never sanitized
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any, Dict, Tuple

from ph6_l2_expand.boundary_guard import classify
from ph6_l2_expand.schemas import canonical_json

# Path segments that must never appear in an MRAM-S write target.
FORBIDDEN_PATH_SEGMENTS = ("cram-0", "cram-a", "cram-r")


class MRAMSWriteError(Exception):
    pass


def _check_forbidden_segments(path: Path) -> None:
    parts_lower = [p.lower() for p in path.parts]
    for forbidden in FORBIDDEN_PATH_SEGMENTS:
        if forbidden in parts_lower:
            raise MRAMSWriteError(f"refused: path contains forbidden CRAM segment '{forbidden}': {path}")


def resolve_target(out_dir: Path, filename: str) -> Path:
    """
    Resolve a write target inside out_dir, rejecting traversal and CRAM
    path segments. Does not require out_dir or the file to already exist.
    """
    out_dir = Path(out_dir)

    if os.path.isabs(filename) or ".." in Path(filename).parts:
        raise MRAMSWriteError(f"refused: invalid filename {filename!r}")

    base = os.path.normpath(str(out_dir if out_dir.is_absolute() else (Path.cwd() / out_dir)))
    joined = os.path.normpath(os.path.join(base, filename))

    if not (joined == base or joined.startswith(base + os.sep)):
        raise MRAMSWriteError(f"refused: path traversal outside MRAM-S root: {filename!r}")

    _check_forbidden_segments(Path(joined))
    return Path(joined)


def write_json_atomic(path: Path, payload: Any) -> None:
    """write-tmp -> fsync(fd) -> close -> rename -> fsync(dir)"""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    data = canonical_json(payload)

    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()

    dir_fd = os.open(str(path.parent), os.O_RDONLY)
    try:
        os.fsync(dir_fd)
    finally:
        os.close(dir_fd)


def write_advisory(out_dir: Path, filename: str, payload: Dict[str, Any]) -> Tuple[Path, str, list]:
    """
    Write an advisory payload to MRAM-S.

    Returns (path_written, status, violations) where status is one of
    "WRITTEN" or "QUARANTINED". Quarantined payloads are written under
    out_dir/quarantine/<filename> unchanged, alongside their violations.
    """
    out_dir = Path(out_dir)
    status, violations = classify(payload)

    if status == "OK":
        target = resolve_target(out_dir, filename)
        write_json_atomic(target, payload)
        return target, "WRITTEN", []

    quarantine_target = resolve_target(out_dir, os.path.join("quarantine", filename))
    write_json_atomic(quarantine_target, {"DRIFT_FAIL": True, "violations": violations, "payload": payload})
    return quarantine_target, "QUARANTINED", violations
