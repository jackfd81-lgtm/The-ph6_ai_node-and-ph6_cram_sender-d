#!/usr/bin/env python3
"""Atomic write helper for the PH6 research agent.

4-step contract: write-tmp -> fsync(fd) -> os.replace -> fsync(dir).
"""

import os
from pathlib import Path


def atomic_write(path, data: bytes) -> None:
    """Write `data` to `path` atomically (write-tmp/fsync/replace/fsync-dir)."""
    path = Path(path)
    tmp_path = path.with_name(path.name + ".tmp")

    fd = os.open(tmp_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)
    try:
        os.write(fd, data)
        os.fsync(fd)
    finally:
        os.close(fd)

    os.replace(tmp_path, path)

    dir_fd = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(dir_fd)
    finally:
        os.close(dir_fd)
