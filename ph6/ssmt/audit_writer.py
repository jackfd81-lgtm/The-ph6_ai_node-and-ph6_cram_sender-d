import json
import os
import uuid
from dataclasses import asdict
from .constants import SSMT_WRITE_ROOT
from .audit_log import SSMTAuditLog
from .write_boundary import (
    SSMT_APPROVED_ROOT, WriteBoundaryError, check_name, confine_root,
    open_confined_dir, same_directory,
)


class AdvisoryAuditWriter:
    def __init__(self, root: str = SSMT_WRITE_ROOT, *, approved_root: str = SSMT_APPROVED_ROOT):
        # Canonical containment, validated before any directory is created.
        self.root, self._approved_real, self._rel_parts = confine_root(root, approved_root)
        self.audit = SSMTAuditLog(self.root, approved_root=approved_root)

    def _open_root(self):
        # Test fixtures may build the writer without __init__; then the root
        # itself is the confinement base (no components to walk).
        base = getattr(self, "_approved_real", None)
        if base is None:
            return open_confined_dir(os.path.realpath(self.root), (), create=False)
        return open_confined_dir(base, self._rel_parts, create=True)

    def write_packet(self, packet) -> dict:
        name = check_name(f"{packet.swarm_id}_{int(packet.created_at)}_{uuid.uuid4().hex}.json")
        tmp_name = name + ".tmp"
        final_path = os.path.join(self.root, name)

        dir_fd = self._open_root()
        try:
            fd = os.open(tmp_name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
                         0o666, dir_fd=dir_fd)
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(
                    asdict(packet),
                    f,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                    allow_nan=False,
                )
                f.write("\n")
                f.flush()
                os.fsync(f.fileno())

            os.replace(tmp_name, name, src_dir_fd=dir_fd, dst_dir_fd=dir_fd)
            os.fsync(dir_fd)
            # The audit chain is path-based: refuse if the root path no longer
            # names the directory the packet was just written into.
            if not same_directory(self.root, dir_fd):
                raise WriteBoundaryError("SSMT write boundary violation: root changed during write")
        finally:
            os.close(dir_fd)

        audit_event = self.audit.append_packet_event(packet, final_path)
        return {"packet_path": final_path, "audit_event": audit_event}
