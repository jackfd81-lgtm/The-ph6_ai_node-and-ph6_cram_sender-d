#!/usr/bin/env python3
"""
PH6CRAM Replay Verification Engine — runtime block verifier.
Imports from SENSORS.measurement_engine and re-evaluates historical records.
Separate from replay_engine.py (governance replay classes).
PROPOSED artifact. Ratified_by: null.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from SENSORS.measurement_engine import evaluate_sensor_frame, BLAKE2B_EMPTY


def verify_historical_block(historical_record: dict) -> bool:
    """Recomputes sensor metrics to detect computation shifts."""
    try:
        recalculated_output = evaluate_sensor_frame(
            historical_record["source_evidence_hash"],
            historical_record["metric_value"],
        )
    except ValueError as exc_err:
        print(f"[REPLAY FAILURE] Structural validation crash: {exc_err}")
        return False

    if recalculated_output["verdict"] != historical_record["verdict"]:
        print("[REPLAY FAILURE] Result state mismatch detected.")
        return False
    if recalculated_output["execution_hash"] != historical_record["execution_hash"]:
        print("[REPLAY FAILURE] Diagnostic signature shift identified.")
        return False
    if recalculated_output["measurement_id"] != historical_record["measurement_id"]:
        print("[REPLAY FAILURE] Object identification track mismatch.")
        return False

    return True


if __name__ == "__main__":
    TEST_INPUT = 42.7
    computed_reference = evaluate_sensor_frame(BLAKE2B_EMPTY, TEST_INPUT)

    if verify_historical_block(computed_reference):
        print("[REPLAY SUCCESS] Execution track verified against state invariants.")
    else:
        print("[CRITICAL FAULT] Analytical drift encountered during replay.")
        sys.exit(1)
