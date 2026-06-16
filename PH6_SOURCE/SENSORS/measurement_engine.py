#!/usr/bin/env python3
"""
PH6CRAM Layer 1 PSEUDO-M & PSEUDO-A Real-Time Measurement Core.
Authority hash: BLAKE2b-256 (digest_size=32). SHA-256 is forbidden for authority IDs.
PROPOSED artifact. Ratified_by: null.
"""

import hashlib

MIN_THRESHOLD_METRIC = 12.5
MAX_THRESHOLD_METRIC = 87.2
EXECUTION_VERSION = "2026.06.06.v1"
SCHEMA_ID = "ph6.pseudo_measurement.v1"

BLAKE2B_EMPTY = hashlib.blake2b(b"", digest_size=32).hexdigest()


def _blake2b(data: str) -> str:
    return hashlib.blake2b(data.encode("utf-8"), digest_size=32).hexdigest()


def evaluate_sensor_frame(source_hash: str, raw_metric: float) -> dict:
    """Calculates deterministic pass gates without external state drift."""
    if not isinstance(source_hash, str) or len(source_hash) != 64:
        raise ValueError(
            f"PH6 validation fault: malformed source evidence hash string: '{source_hash}'"
        )

    hash_context = f"{source_hash}:{raw_metric}:{MIN_THRESHOLD_METRIC}:{MAX_THRESHOLD_METRIC}:{EXECUTION_VERSION}"
    execution_signature = _blake2b(hash_context)

    identity_context = f"{source_hash}:{raw_metric}:{SCHEMA_ID}:{EXECUTION_VERSION}"
    deterministic_measurement_id = _blake2b(identity_context)

    if MIN_THRESHOLD_METRIC <= raw_metric <= MAX_THRESHOLD_METRIC:
        adjudication_verdict = "PASS"
    else:
        adjudication_verdict = "DROP"

    return {
        "schema_id": SCHEMA_ID,
        "measurement_id": deterministic_measurement_id,
        "source_evidence_hash": source_hash,
        "metric_value": float(raw_metric),
        "threshold_bounds": [MIN_THRESHOLD_METRIC, MAX_THRESHOLD_METRIC],
        "verdict": adjudication_verdict,
        "execution_hash": execution_signature,
    }


if __name__ == "__main__":
    sample_payload = evaluate_sensor_frame(BLAKE2B_EMPTY, 42.7)
    print(f"[CONGRUENT] Derived Identity: {sample_payload['measurement_id']}")
    print(f"[CONGRUENT] Verdict Allocation: {sample_payload['verdict']}")
