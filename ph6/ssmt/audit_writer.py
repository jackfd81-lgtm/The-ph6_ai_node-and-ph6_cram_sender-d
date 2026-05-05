import json
import os
from dataclasses import asdict
from .constants import SSMT_WRITE_ROOT
from .audit_log import SSMTAuditLog


class AdvisoryAuditWriter:
    def __init__(self, root: str = SSMT_WRITE_ROOT):
        if not root.startswith("/var/ph6/mram-s/swarms/"):
            raise RuntimeError("SSMT write boundary violation")

        self.root = root
        self.audit = SSMTAuditLog(root)

    def write_packet(self, packet) -> dict:
        os.makedirs(self.root, exist_ok=True)

        final_path = os.path.join(
            self.root,
            f"{packet.swarm_id}_{int(packet.created_at)}.json",
        )
        tmp_path = final_path + ".tmp"

        with open(tmp_path, "w", encoding="utf-8") as f:
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

        os.replace(tmp_path, final_path)

        dir_fd = os.open(self.root, os.O_DIRECTORY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)

        audit_event = self.audit.append_packet_event(packet, final_path)
        return {"packet_path": final_path, "audit_event": audit_event}
