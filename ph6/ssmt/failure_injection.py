"""
Failure injection harness for SSMT write path testing.
All injectors are context managers that restore state on exit.
"""
import os
import stat
import json
import time
import builtins
from contextlib import contextmanager
from unittest.mock import patch, MagicMock


@contextmanager
def disk_full():
    """Simulate ENOSPC on open() calls inside the write path."""
    import errno
    real_open = builtins.open

    def failing_open(path, mode="r", **kwargs):
        if "w" in mode or "a" in mode or "x" in mode:
            raise OSError(errno.ENOSPC, "No space left on device", path)
        return real_open(path, mode, **kwargs)

    with patch("builtins.open", side_effect=failing_open):
        yield


@contextmanager
def permission_denied(path: str):
    """Remove write permission on a path, restore after."""
    original = stat.S_IMODE(os.stat(path).st_mode)
    os.chmod(path, original & ~(stat.S_IWRITE | stat.S_IWGRP | stat.S_IWOTH))
    try:
        yield
    finally:
        os.chmod(path, original)


@contextmanager
def partial_write(truncate_at: int = 10):
    """Simulate a partial write by truncating data mid-stream."""
    real_open = builtins.open

    class TruncatingFile:
        def __init__(self, inner):
            self._inner = inner

        def write(self, data):
            self._inner.write(data[:truncate_at])

        def flush(self):
            self._inner.flush()

        def fileno(self):
            return self._inner.fileno()

        def __enter__(self):
            return self

        def __exit__(self, *args):
            self._inner.__exit__(*args)

    def truncating_open(path, mode="r", **kwargs):
        f = real_open(path, mode, **kwargs)
        if "w" in mode or "a" in mode:
            return TruncatingFile(f)
        return f

    with patch("builtins.open", side_effect=truncating_open):
        yield


@contextmanager
def frozen_clock(ts: float = 1700000000.0):
    """Fix time.time() to a constant to force timestamp collisions."""
    with patch("time.time", return_value=ts):
        yield


@contextmanager
def fsync_failure():
    """Simulate os.fsync() failing (e.g. EIO)."""
    import errno
    real_fsync = os.fsync

    def failing_fsync(fd):
        raise OSError(errno.EIO, "Input/output error")

    with patch("os.fsync", side_effect=failing_fsync):
        yield
