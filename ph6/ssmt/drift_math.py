def clamp_fp(value: int, lo: int = 0, hi: int = 10000) -> int:
    return max(lo, min(hi, int(value)))


def drift_from_decay(decay_fp: int, contradiction_fp: int = 0, gap_fp: int = 0) -> int:
    """
    Advisory only.
    Higher score = more drift pressure.
    """
    return clamp_fp(
        int((decay_fp * 0.5) + (contradiction_fp * 0.3) + (gap_fp * 0.2))
    )


def confidence_from_drift(base_confidence_fp: int, drift_fp: int) -> int:
    return clamp_fp(base_confidence_fp - drift_fp)
