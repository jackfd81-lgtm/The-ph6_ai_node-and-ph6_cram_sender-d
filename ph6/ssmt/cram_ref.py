from dataclasses import dataclass


@dataclass(frozen=True)
class CRAMRef:
    ref_id: str
    frame_id: int
    packet_hash: str
    timestamp: float
    source: str = "CRAM"
