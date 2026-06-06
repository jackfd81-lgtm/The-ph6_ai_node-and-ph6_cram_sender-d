#!/usr/bin/env python3
"""
PH6 Schema Validator — scans all schema subdirectories, validates structure, delegates to ph6_schema_validate.py.
PROPOSED artifact. Ratified_by: null.
"""

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCHEMAS_ROOT = REPO_ROOT / "SCHEMAS"
FLAT_VALIDATOR = REPO_ROOT / "TOOLS" / "ph6_schema_validate.py"

REQUIRED_FIELDS_BY_SCHEMA_ID = {
    "ph6.evidence.object.v1": ["schema_id","evidence_id","cram_lane","source_sensor_id",
                                "capture_timestamp_utc","raw_hash","canonical_hash","authority_status"],
    "ph6.cram0.record.v1":    ["schema_id","cram0_id","source_sensor_id","capture_timestamp_utc",
                                "raw_artifact_path","raw_hash","pre_interpretation_state"],
    "ph6.crama.record.v1":    ["schema_id","crama_id","evidence_id","pseudo_a_verdict_id",
                                "canonical_hash","blake2b_marker_written","immutable_after_utc"],
    "ph6.cramr.record.v1":    ["schema_id","cramr_id","evidence_id","pseudo_a_verdict_id",
                                "drop_reason","failure_class","blake2b_marker_written"],
    "ph6.sensor.object.v1":   ["schema_id","sensor_id","sensor_class","device_path",
                                "authority_profile","metadata_profile"],
    "ph6.sensor.profile.v1":  ["schema_id","profile_id","sensor_id","profile_type",
                                "created_at_utc","profile_hash"],
    "ph6.sensor.measurement_profile.v1": ["schema_id","profile_id","sensor_class","method_id",
                                          "method_version","metric_outputs","threshold_profile","profile_hash"],
    "ph6.sensor.failure_profile.v1": ["schema_id","profile_id","sensor_id","sensor_class",
                                      "failure_modes","profile_hash"],
    "ph6.replay.certification_record.v1": ["schema_id","replay_id","original_evidence_id",
                                           "original_verdict_id","replay_class","certification_status",
                                           "replayed_at_utc"],
    "ph6.replay.failure_record.v1": ["schema_id","failure_id","replay_id","original_evidence_id",
                                     "failure_type","failure_summary","cram_r_record_id",
                                     "gap_register_entry_id","operator_review_required"],
    "ph6.ai.transform_record.v1":   ["schema_id","transform_id","model_id","model_version",
                                     "source_evidence_id","source_evidence_unchanged",
                                     "authority_status","may_replace_primary_evidence",
                                     "transform_type","input_hash","output_hash",
                                     "executed_at_utc","proposed_by","ratified_by"],
    "ph6.ai.authority_request.v1":  ["schema_id","request_id","requesting_model_id","request_type",
                                     "evidence_basis","requested_action","requested_at_utc",
                                     "authority_required","operator_decision"],
    "ph6.ai.decision_review.v1":    ["schema_id","review_id","model_id","review_context",
                                     "claims","authority_note","reviewed_at_utc"],
    "ph6.token.record.v1":          ["schema_id","token_id","token_class","created_at_utc",
                                     "authority_level","source_ids","parent_token_ids",
                                     "artifact_hash","canonical_hash","payload_hash",
                                     "version","supersedes","superseded_by","operator_review_status"],
    "ph6.token.compression_record.v1": ["schema_id","tcr_id","compression_class","source_token_ids",
                                        "compressed_token_id","compression_hash","created_at_utc",
                                        "reversible","operator_review_status"],
    "ph6.token.dissent_token.v1":   ["schema_id","dissent_id","dissent_class","conflict_type",
                                     "pseudo_verdict_id","dissenting_party","dissent_rationale",
                                     "blocking_status","created_at_utc"],
    "ph6.token.topology_graph.v1":  ["schema_id","graph_id","root_token_id","nodes",
                                     "edges","graph_hash","created_at_utc"],
    "ph6.memory.mrams_object.v1":   ["schema_id","memory_id","memory_tier","claim_class",
                                     "content_hash","created_at_utc","authority_level",
                                     "may_modify_cram","may_modify_evidence"],
    "ph6.memory.living_memory_record.v1": ["schema_id","record_id","source_memory_id","review_event_type",
                                          "tier_before","tier_after","forward_audit_event_created",
                                          "one_way_circle_compliant","created_at_utc"],
    "ph6.audit.chain_of_custody.v1": ["schema_id","custody_id","run_id","acquisition_event",
                                      "preservation_event","transfer_events","custody_hash"],
    "ph6.audit.operator_ratification.v1": ["schema_id","ratification_id","ratified_artifact_id",
                                           "ratified_artifact_type","operator_id","ratified_at_utc",
                                           "prior_status","new_status","ratification_hash"],
}

PASS = 0
FAIL = 0


def check_schema(path: Path) -> bool:
    global PASS, FAIL
    try:
        with open(path) as f:
            data = json.load(f)
    except Exception as e:
        print(f"  FAIL  {path.relative_to(REPO_ROOT)}  — JSON parse error: {e}")
        FAIL += 1
        return False

    schema_id = data.get("$id", "")
    required_in_schema = data.get("required", [])
    props = data.get("properties", {})

    # Check that schema_id const is present
    if "properties" not in data:
        print(f"  FAIL  {path.relative_to(REPO_ROOT)}  — no 'properties' key")
        FAIL += 1
        return False

    if "schema_id" not in props:
        print(f"  FAIL  {path.relative_to(REPO_ROOT)}  — no schema_id property")
        FAIL += 1
        return False

    # Check known required fields
    key = schema_id.replace("https://ph6.local/schemas/", "").split("_v1")[0]
    # Try matching by const value
    schema_const = props.get("schema_id", {}).get("const", "")
    if schema_const in REQUIRED_FIELDS_BY_SCHEMA_ID:
        expected = REQUIRED_FIELDS_BY_SCHEMA_ID[schema_const]
        missing = [f for f in expected if f not in required_in_schema]
        if missing:
            print(f"  FAIL  {path.relative_to(REPO_ROOT)}  — missing required fields: {missing}")
            FAIL += 1
            return False

    print(f"  PASS  {path.relative_to(REPO_ROOT)}")
    PASS += 1
    return True


def main():
    global PASS, FAIL
    print("PH6 SCHEMA VALIDATOR — subdirectory schemas")
    print(f"Scanning: {SCHEMAS_ROOT}")

    schemas = sorted(SCHEMAS_ROOT.rglob("*.json"))
    if not schemas:
        print("  WARN: no schemas found")
        return 1

    for s in schemas:
        check_schema(s)

    print(f"\nSUB-SCHEMA RESULT: {PASS} PASS / {FAIL} FAIL / {PASS+FAIL} total")

    # Also run the flat validator if present
    if FLAT_VALIDATOR.exists():
        print(f"\nRunning flat validator: {FLAT_VALIDATOR.name}")
        result = subprocess.run(
            [sys.executable, str(FLAT_VALIDATOR)],
            capture_output=True, text=True
        )
        print(result.stdout)
        if result.returncode != 0:
            print(result.stderr)
            return result.returncode
    else:
        print(f"  INFO: flat validator not found at {FLAT_VALIDATOR}, skipping")

    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
