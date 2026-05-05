from .models import SwarmInput
from .scheduler import SwarmScheduler
from .audit_writer import AdvisoryAuditWriter
from .tok_index import TOKIndex
from .replay_receipt import build_replay_receipt
from .forensic_closure import forensic_closure
from .hash_chain import canon_hash


class SSMTLiveSidecar:
    """
    PH6-Lite live sidecar.

    Reads:  CRAM references, TOK advisory references.
    Writes: MRAM-S swarm packets only.

    Never:  writes CRAM, affects PSEUDO, affects PASS/DROP, blocks RSYNC.

    Runtime order:
      1. CRAM commit (caller)
      2. SSMT reads CRAM ref + TOK refs
      3. SSMT writes MRAM-S advisory packets
      4. SSMT emits replay receipt + closure
      5. PH6 continues even if SSMT raises
    """

    def __init__(self):
        self.scheduler = SwarmScheduler()
        self.writer = AdvisoryAuditWriter()
        self.tok_index = TOKIndex()

    def process_cram_ref(self, cram_ref: str,
                         cram_packet_hash: str = "") -> dict:
        # Canonical hash of the ref string when actual packet hash not provided.
        # In production the caller passes the real CRAM commit hash.
        if not cram_packet_hash:
            cram_packet_hash = canon_hash({"cram_ref": cram_ref})

        tok_refs = self.tok_index.refs_for_cram(cram_ref)

        packets = self.scheduler.run_cycle(
            SwarmInput(
                cram_refs=[cram_ref],
                tok_refs=tok_refs,
                advisory_refs=[],
                cram_packet_hash=cram_packet_hash,
            )
        )

        audit_events = []
        for packet in packets:
            result = self.writer.write_packet(packet)
            audit_events.append(result["audit_event"])

        receipt = build_replay_receipt(packets, audit_events)
        closure = forensic_closure(packets, audit_events, receipt)

        return {
            "cram_ref": cram_ref,
            "cram_packet_hash": cram_packet_hash,
            "tok_refs": tok_refs,
            "packet_count": len(packets),
            "audit_event_count": len(audit_events),
            "receipt": receipt,
            "closure": closure,
        }
