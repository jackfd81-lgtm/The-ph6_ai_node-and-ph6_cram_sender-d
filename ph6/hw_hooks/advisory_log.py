"""Optional MRAM-S-only advisory log path for hardware-hook records.

Authority ZERO. Append-only JSONL under the sealed advisory tier. This module
refuses to write anywhere outside its MRAM-S advisory root, and refuses any
record that is not already tagged authority=ZERO / non_authoritative=True —
it is a destination for advisory data, never a path back into CRAM-0/CRAM-A/CRAM-R.
"""

import json
import os

MRAM_S_ADVISORY_SUBPATH = os.path.join("mram-s", "hw_hooks_advisory")


class AdvisoryLogPathError(ValueError):
    """Raised when a resolved log path would escape the MRAM-S advisory root."""


def resolve_advisory_log_path(base_dir, filename):
    """Resolve `filename` under <base_dir>/mram-s/hw_hooks_advisory, refusing escapes."""
    root = os.path.abspath(os.path.join(base_dir, MRAM_S_ADVISORY_SUBPATH))
    path = os.path.abspath(os.path.join(root, filename))
    if os.path.commonpath([root, path]) != root:
        raise AdvisoryLogPathError(f"advisory log path escapes MRAM-S advisory root: {path}")
    return path


def append_advisory_record(base_dir, filename, record):
    """Append one JSON record line to an MRAM-S advisory log file.

    The record must already declare authority=ZERO and non_authoritative=True;
    this function does not stamp those fields itself — it only refuses to
    write a record that lacks them, so nothing can launder itself into the
    advisory tier without already carrying its own ZERO-authority declaration.
    """
    if record.get("authority") != "ZERO" or record.get("non_authoritative") is not True:
        raise ValueError("advisory log records must declare authority=ZERO and non_authoritative=True")
    path = resolve_advisory_log_path(base_dir, filename)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, sort_keys=True) + "\n")
    return path
