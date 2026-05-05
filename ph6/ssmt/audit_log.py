import os
import json
import time
from dataclasses import asdict
from .constants import SSMT_WRITE_ROOT
from .hash_chain import chain_event, canon_hash


GENESIS_HASH = "0" * 64


class SSMTAuditLog:
    def __init__(self, root: str = SSMT_WRITE_ROOT):
        if not root.startswith("/var/ph6/mram-s/swarms/"):
            raise RuntimeError("SSMT audit boundary violation")

        self.root = root
        self.audit_path = os.path.join(root, "ssmt_audit.jsonl")
        os.makedirs(root, exist_ok=True)

    def _last_hash_and_seq(self):
        if not os.path.exists(self.audit_path):
            return GENESIS_HASH, 0

        last = None
        with open(self.audit_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    last = json.loads(line)

        if last is None:
            return GENESIS_HASH, 0

        return last["event_hash"], last["event_seq"]

    def append_packet_event(self, packet, packet_path: str) -> dict:
        prev_hash, prev_seq = self._last_hash_and_seq()

        packet_dict = asdict(packet)

        event = {
            "schema": "ph6.ssmt.audit_event.v1",
            "event_seq": prev_seq + 1,
            "event_type": "SSMT_PACKET_WRITE",
            "object_id": f"{packet.swarm_id}:{int(packet.created_at)}",
            "packet_hash": canon_hash(packet_dict),
            "packet_path": packet_path,
            "swarm_id": packet.swarm_id,
            "authority": packet.authority,
            "lane": packet.lane,
            "dependency_for_replay": packet.dependency_for_replay,
            "timestamp": time.time(),
        }

        chained = chain_event(event, prev_hash)

        with open(self.audit_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(
                chained,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            ))
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())

        return chained
