#!/usr/bin/env python3
"""BLAKE2b-256 hashing helper for the PH6 research agent.

BLAKE2b-256 (digest_size=32) is the sole authority hash per PH6 doctrine.
"""

import hashlib


def blake2b256_bytes(data: bytes) -> str:
    """Return the hex digest of BLAKE2b-256 (digest_size=32) over data."""
    return hashlib.blake2b(data, digest_size=32).hexdigest()
