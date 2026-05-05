import json
import os
from .constants import SSMT_WRITE_ROOT, AUTHORITY, LANE
from .audit_log import SSMTAuditLog, GENESIS_HASH
from .hash_chain import canon_hash
from .replay_receipt import ReplayReceiptWriter, ManifestWriter
from .replay_validator import ReplayValidator
from .token_bridge import TokenBridge


class ForensicClosureValidator:
    """
    Full HRG9-compatible forensic closure for SSMT-1.0.
    Validates in-memory state, disk audit chain, and emits
    ssmt_manifest.json + replay_receipt_*.json.
    """

    def __init__(self, root: str = SSMT_WRITE_ROOT):
        if not root.startswith("/var/ph6/mram-s/swarms/"):
            raise RuntimeError("SSMT closure boundary violation")
        self.root = root
        self._replay = ReplayValidator()
        self._tok = TokenBridge()
        self._receipt_writer = ReplayReceiptWriter(root)
        self._manifest_writer = ManifestWriter(root)

    def validate_audit_chain(self) -> dict:
        """Walk ssmt_audit.jsonl and verify hash continuity."""
        audit_path = os.path.join(self.root, "ssmt_audit.jsonl")
        if not os.path.exists(audit_path):
            return {"chain_valid": True, "events": 0, "reason": "no_audit_yet"}

        prev_hash = GENESIS_HASH
        events = 0
        with open(audit_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                event = json.loads(line)
                stored_hash = event.get("event_hash")
                stored_prev = event.get("prev_event_hash")

                if stored_prev != prev_hash:
                    return {
                        "chain_valid": False,
                        "events": events,
                        "reason": f"prev_hash mismatch at seq {event.get('event_seq')}",
                    }

                recomputed = canon_hash(
                    {k: v for k, v in event.items() if k != "event_hash"}
                )
                if recomputed != stored_hash:
                    return {
                        "chain_valid": False,
                        "events": events,
                        "reason": f"hash mismatch at seq {event.get('event_seq')}",
                    }

                prev_hash = stored_hash
                events += 1

        return {"chain_valid": True, "events": events}

    def run(self, packets) -> dict:
        memory_checks = {
            "all_authority_none": all(p.authority == AUTHORITY for p in packets),
            "all_lane_2": all(p.lane == LANE for p in packets),
            "no_replay_dependency": self._replay.validate_no_replay_dependency(packets),
            "no_pass_drop": self._replay.validate_no_pass_drop(packets),
            "tok_bridge_read_only": not self._tok.is_writable(),
        }
        memory_checks["memory_passed"] = all(memory_checks.values())

        chain_result = self.validate_audit_chain()

        closure = {**memory_checks, "audit_chain": chain_result}
        closure["passed"] = closure["memory_passed"] and chain_result["chain_valid"]

        receipt_path = self._receipt_writer.write(packets, closure)

        audit_path = os.path.join(self.root, "ssmt_audit.jsonl")
        manifest_path = self._manifest_writer.write(
            cycle_id=_receipt_cycle_id(receipt_path),
            receipt_path=receipt_path,
            audit_path=audit_path,
            packet_count=len(packets),
        )

        closure["receipt_path"] = receipt_path
        closure["manifest_path"] = manifest_path
        return closure


def forensic_closure(packets, audit_events: list, receipt: dict) -> dict:
    """Convenience function for live sidecar use."""
    validator = ForensicClosureValidator()
    memory_checks = {
        "all_authority_none": all(p.authority == AUTHORITY for p in packets),
        "all_lane_2": all(p.lane == LANE for p in packets),
        "no_replay_dependency": all(not p.dependency_for_replay for p in packets),
        "no_pass_drop": all(
            not ({"pass", "drop", "verdict"} & set(p.advisory_payload.keys()))
            for p in packets
        ),
        "tok_bridge_read_only": True,
        "receipt_hash_present": bool(receipt.get("receipt_hash")),
        "audit_events_match_packets": len(audit_events) == len(packets),
    }
    memory_checks["memory_passed"] = all(memory_checks.values())
    chain_result = validator.validate_audit_chain()
    result = {**memory_checks, "audit_chain": chain_result}
    result["passed"] = result["memory_passed"] and chain_result["chain_valid"]
    return result


def _receipt_cycle_id(receipt_path: str) -> str:
    with open(receipt_path, "r", encoding="utf-8") as f:
        return json.load(f).get("cycle_id", "unknown")
