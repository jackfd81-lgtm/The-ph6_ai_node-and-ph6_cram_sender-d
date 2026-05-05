import math


def exponential_decay_fp(age_seconds: float, half_life_seconds: float = 300.0) -> int:
    """
    Returns decay pressure in fixed point.
    0 = no decay.
    10000 = fully decayed.
    """
    if age_seconds <= 0:
        return 0

    remaining = math.pow(0.5, age_seconds / half_life_seconds)
    decay = 1.0 - remaining
    return int(round(decay * 10000))
