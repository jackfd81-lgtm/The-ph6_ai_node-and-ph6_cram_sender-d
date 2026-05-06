"""
TOK-1.0 Advisory Audit Writer

Lane: 2
Authority: ZERO
Write domain: MRAM-S only — tok_advisory_audit.jsonl

Append-only JSONL hash chain for advisory token events.
This module is Lane-2 only and never touches CRAM, PSEUDO,
EvidencePacket, or any Lane-1 authority path.
"""

from ph6.tok.lifecycle import AdvisoryAudit, append_jsonl, canonical_json, blake2b256_hex

__all__ = [
    "AdvisoryAudit",
    "append_jsonl",
    "canonical_json",
    "blake2b256_hex",
]
