import os
import json
import time
from dataclasses import asdict
from datetime import datetime, timezone
from .constants import SSMT_WRITE_ROOT
from .hash_chain import canon_hash
from ph6.advisory_chain import append_checked, verified_tip
from .write_boundary import SSMT_APPROVED_ROOT, confine_root, open_confined_dir


GENESIS_HASH = "0" * 64


class SSMTAuditLog:
    def __init__(self, root: str = SSMT_WRITE_ROOT, *, approved_root: str = SSMT_APPROVED_ROOT):
        # Canonical containment first; directories are created only afterwards,
        # one component at a time without following symlinks.
        real, base, parts = confine_root(root, approved_root)
        os.close(open_confined_dir(base, parts, create=True))

        self.root = real
        self.audit_path = os.path.join(real, "ssmt_audit.jsonl")

    def _last_hash_and_seq(self):
        count, tail = verified_tip(self.audit_path, GENESIS_HASH, sequence=True)
        return tail, count

    def append_packet_event(self, packet, packet_path: str) -> dict:

        packet_dict = asdict(packet)

        event = {
            "schema":               "ph6.ssmt.audit_event.v1",
            "event_type":           "SSMT_PACKET_WRITE",
            "object_id":            os.path.basename(packet_path),
            "authority_hash":       canon_hash(packet_dict),
            "node_id":              packet.swarm_id,
            "stage":                "PACKET_WRITE",
            "status":               "OK",
            "timestamp_utc":        datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            # Legacy fields preserved for existing consumers
            "packet_hash":          canon_hash(packet_dict),
            "packet_path":          packet_path,
            "swarm_id":             packet.swarm_id,
            "authority":            packet.authority,
            "lane":                 packet.lane,
            "dependency_for_replay": packet.dependency_for_replay,
        }

        return append_checked(self.audit_path, event, GENESIS_HASH, sequence=True)
