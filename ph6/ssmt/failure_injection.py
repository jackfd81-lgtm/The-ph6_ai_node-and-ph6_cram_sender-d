"""
Failure injection harness for SSMT write path testing.
All injectors are context managers that restore state on exit.

FI-SSMT-01: disk full mid-write
FI-SSMT-02: tmp write crash (partial write)
FI-SSMT-03: audit log partial write (fsync failure)
FI-SSMT-04: concurrent scheduler runs
FI-SSMT-05: timestamp collision (same second, same swarm)
"""
import os
import stat
import errno
import builtins
import threading
from contextlib import contextmanager
from unittest.mock import patch


@contextmanager
def disk_full():
    """FI-SSMT-01: Simulate ENOSPC on any write-mode open()."""
    real_open = builtins.open

    def failing_open(path, mode="r", **kwargs):
        if "w" in mode or "a" in mode or "x" in mode:
            raise OSError(errno.ENOSPC, "No space left on device", path)
        return real_open(path, mode, **kwargs)

    with patch("builtins.open", side_effect=failing_open):
        yield


@contextmanager
def partial_write(truncate_at: int = 10):
    """FI-SSMT-02: Simulate crash mid-write by truncating output."""
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
def fsync_failure():
    """FI-SSMT-03: Simulate os.fsync() failing (EIO)."""
    def failing_fsync(fd):
        raise OSError(errno.EIO, "Input/output error")

    with patch("os.fsync", side_effect=failing_fsync):
        yield


@contextmanager
def concurrent_writes(n_threads: int = 4):
    """
    FI-SSMT-04: Context manager that provides a barrier and thread list
    for running concurrent write operations.

    Usage:
        with concurrent_writes() as run_parallel:
            errors = run_parallel(my_write_fn, args_list)
    """
    errors = []
    lock = threading.Lock()

    def run_parallel(fn, args_list):
        barrier = threading.Barrier(len(args_list))
        threads = []

        def worker(args):
            barrier.wait()
            try:
                fn(*args)
            except Exception as e:
                with lock:
                    errors.append(e)

        for args in args_list:
            t = threading.Thread(target=worker, args=(args,))
            threads.append(t)

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        return errors

    yield run_parallel


@contextmanager
def frozen_clock(ts: float = 1700000000.0):
    """FI-SSMT-05: Fix time.time() to force timestamp collisions."""
    with patch("time.time", return_value=ts):
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
