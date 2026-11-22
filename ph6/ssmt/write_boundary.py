"""SSMT advisory write boundary (Lane-2, Authority ZERO).

Canonical containment for advisory write roots. Replaces the lexical
``startswith("/var/ph6/mram-s/swarms/")`` check, which accepted ``..``
escapes such as ``/var/ph6/mram-s/swarms/../../cram-0/x``.

Rules (fail closed):
  * root must be an absolute ``str`` with no NUL and no ``..`` component;
  * the symlink-resolved root must lie inside the symlink-resolved approved
    root (the approved root itself is allowed);
  * validation never touches the filesystem beyond ``realpath`` lookups, so
    it happens before any directory is created;
  * at write time every component below the approved root is opened with
    ``O_NOFOLLOW | O_DIRECTORY`` relative to its parent fd, so a symlink
    swapped in after validation is refused instead of followed;
  * file names written inside the root are a single safe component.

PROPOSED by claude-code-lane2; ratified_by=null.
"""
import os
import re

SSMT_APPROVED_ROOT = "/var/ph6/mram-s/swarms"

_SAFE_NAME = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_.-]{0,254}")
_DIR_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC


class WriteBoundaryError(RuntimeError):
    """Raised when an advisory write would leave the approved root."""


def confine_root(root, approved_root=SSMT_APPROVED_ROOT):
    """Return (canonical_root, canonical_approved_root, relative_parts).

    Pure validation: creates nothing. Raises WriteBoundaryError on any doubt.
    """
    if not isinstance(root, str) or not isinstance(approved_root, str):
        raise WriteBoundaryError("SSMT write boundary violation: root must be str")
    if not root or "\x00" in root or "\x00" in approved_root:
        raise WriteBoundaryError("SSMT write boundary violation: empty or NUL in root")
    if not os.path.isabs(root) or not os.path.isabs(approved_root):
        raise WriteBoundaryError("SSMT write boundary violation: root must be absolute")
    if ".." in root.split("/"):
        raise WriteBoundaryError("SSMT write boundary violation: '..' component in root")
    base = os.path.realpath(approved_root)
    real = os.path.realpath(root)
    if os.path.commonpath([real, base]) != base:
        raise WriteBoundaryError(f"SSMT write boundary violation: {root!r} resolves outside {base!r}")
    rel = os.path.relpath(real, base)
    parts = () if rel == "." else tuple(rel.split(os.sep))
    if any(p in ("", ".", "..") for p in parts):
        raise WriteBoundaryError("SSMT write boundary violation: unexpected path component")
    return real, base, parts


def open_confined_dir(base, parts, create):
    """Open base/parts... as a directory fd without following symlinks below base.

    ``base`` must already be canonical (from confine_root). Missing components
    are created with mode 0o700 when ``create`` is true. Caller closes the fd.
    """
    fd = os.open(base, _DIR_FLAGS)
    try:
        for part in parts:
            if create:
                try:
                    os.mkdir(part, 0o700, dir_fd=fd)
                except FileExistsError:
                    pass
            try:
                nxt = os.open(part, _DIR_FLAGS, dir_fd=fd)
            except OSError as error:
                raise WriteBoundaryError(
                    f"SSMT write boundary violation: cannot open {part!r} without following links"
                ) from error
            os.close(fd)
            fd = nxt
        return fd
    except BaseException:
        os.close(fd)
        raise


def check_name(name):
    """A file name written inside the root must be one safe path component."""
    if not isinstance(name, str) or not _SAFE_NAME.fullmatch(name):
        raise WriteBoundaryError(f"SSMT write boundary violation: unsafe file name {name!r}")
    return name


def same_directory(path, fd):
    """True when ``path`` (followed) is the very directory open as ``fd``."""
    try:
        a, b = os.stat(path), os.fstat(fd)
    except OSError:
        return False
    return (a.st_dev, a.st_ino) == (b.st_dev, b.st_ino)
