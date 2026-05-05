import json
import os
import time
import uuid
from dataclasses import asdict
from .constants import SSMT_WRITE_ROOT
from .hash_chain import canon_hash, chain_event
from .audit_log import SSMTAuditLog, GENESIS_HASH


class ReplayReceiptWriter:
    def __init__(self, root: str = SSMT_WRITE_ROOT):
        if not root.startswith("/var/ph6/mram-s/swarms/"):
            raise RuntimeError("SSMT write boundary violation")
        self.root = root

    def write(self, packets, closure_result: dict) -> str:
        cycle_id = str(uuid.uuid4())
        packet_hashes = [canon_hash(asdict(p)) for p in packets]
        all_independent = all(not p.dependency_for_replay for p in packets)

        receipt = {
            "schema": "ph6.ssmt.replay_receipt.v1",
            "cycle_id": cycle_id,
            "packets_validated": len(packets),
            "all_independent": all_independent,
            "packet_hashes": packet_hashes,
            "cycle_hash": canon_hash(packet_hashes),
            "closure_result": closure_result,
            "timestamp": time.time(),
        }

        receipt["receipt_hash"] = canon_hash(
            {k: v for k, v in receipt.items() if k != "receipt_hash"}
        )

        path = os.path.join(self.root, f"replay_receipt_{cycle_id}.json")
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(receipt, f, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)

        return path

    def write_return_dict(self, packets, audit_events: list) -> dict:
        """Write receipt and return the receipt dict (not just path)."""
        cycle_id = str(uuid.uuid4())
        packet_hashes = [canon_hash(asdict(p)) for p in packets]
        audit_hashes = [e.get("event_hash", "") for e in audit_events]
        all_independent = all(not p.dependency_for_replay for p in packets)

        receipt = {
            "schema": "ph6.ssmt.replay_receipt.v1",
            "cycle_id": cycle_id,
            "packets_validated": len(packets),
            "audit_events_included": len(audit_events),
            "all_independent": all_independent,
            "packet_hashes": packet_hashes,
            "audit_hashes": audit_hashes,
            "cycle_hash": canon_hash(packet_hashes),
            "timestamp": time.time(),
        }
        receipt["receipt_hash"] = canon_hash(
            {k: v for k, v in receipt.items() if k != "receipt_hash"}
        )

        path = os.path.join(self.root, f"replay_receipt_{cycle_id}.json")
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(receipt, f, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)

        receipt["_path"] = path
        return receipt

    def verify(self, path: str) -> bool:
        with open(path, "r", encoding="utf-8") as f:
            receipt = json.load(f)

        stored_hash = receipt.pop("receipt_hash", None)
        expected = canon_hash(receipt)
        return stored_hash == expected


def build_replay_receipt(packets, audit_events: list) -> dict:
    """Convenience function for live sidecar use."""
    writer = ReplayReceiptWriter()
    return writer.write_return_dict(packets, audit_events)


class ManifestWriter:
    def __init__(self, root: str = SSMT_WRITE_ROOT):
        if not root.startswith("/var/ph6/mram-s/swarms/"):
            raise RuntimeError("SSMT write boundary violation")
        self.root = root

    def write(self, cycle_id: str, receipt_path: str,
              audit_path: str, packet_count: int) -> str:
        manifest = {
            "schema": "ph6.ssmt.manifest.v1",
            "ssmt_version": "1.0",
            "cycle_id": cycle_id,
            "packet_count": packet_count,
            "receipt_path": receipt_path,
            "audit_path": audit_path,
            "write_root": self.root,
            "timestamp": time.time(),
        }
        manifest["manifest_hash"] = canon_hash(
            {k: v for k, v in manifest.items() if k != "manifest_hash"}
        )

        path = os.path.join(self.root, "ssmt_manifest.json")
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)

        return path
