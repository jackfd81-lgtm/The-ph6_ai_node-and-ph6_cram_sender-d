from dataclasses import dataclass


@dataclass(frozen=True)
class RT:
    token_id: str
    cram_ref: str
    label: str
    confidence_fp: int


@dataclass(frozen=True)
class VDT:
    token_id: str
    cram_ref: str
    decay_fp: int
    age_seconds: float


@dataclass(frozen=True)
class VLT:
    token_id: str
    cram_ref: str
    longevity_fp: int
    stability_fp: int
