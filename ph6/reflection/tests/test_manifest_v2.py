import pytest

from ph6.reflection.manifest_v1 import ReflectionSourceError, SCHEMA as SCHEMA_V1
from ph6.reflection.manifest_v2 import (
    AUTHORITY_ORIGIN_VALUES,
    SCHEMA,
    build_reflection_record_v2,
)

REFLECTED_AT = "2026-06-08T12:00:00Z"

SOURCE_REPORT = {
    "run_id": "internal_000001",
    "test_name": "PH6_INTERNAL_SYSTEM_TEST",
    "status": "PASS",
    "report_path": "/home/jack/PH6_SOURCE/DEPLOYMENT/PH6_INTERNAL_SYSTEM_TEST_20260608.md",
    "artifact_paths": ["/home/jack/ph6/cram_pu/logs/internal_000001.json"],
    "generated_at_utc": "2026-06-08T11:00:00Z",
}


def test_v2_record_carries_v1_fields_plus_authority_origin():
    rec = build_reflection_record_v2(SOURCE_REPORT, "ssh", REFLECTED_AT, "LANE1_SOURCE_REPORT")
    assert rec["schema"] == SCHEMA
    assert rec["schema"] != SCHEMA_V1
    assert rec["authority_origin"] == "LANE1_SOURCE_REPORT"
    assert rec["run_id"] == SOURCE_REPORT["run_id"]
    assert rec["status"] == SOURCE_REPORT["status"]
    assert rec["source_generated_at_utc"] == SOURCE_REPORT["generated_at_utc"]
    assert rec["reflected_at_utc"] == REFLECTED_AT


def test_v2_record_remains_advisory_zero_authority():
    rec = build_reflection_record_v2(SOURCE_REPORT, "cloud", REFLECTED_AT, "ADVISORY_DESKTOP_STATUS")
    assert rec["authority"] == "ZERO"
    assert rec["non_authoritative"] is True


@pytest.mark.parametrize("origin", sorted(AUTHORITY_ORIGIN_VALUES))
def test_v2_accepts_every_locked_origin_value(origin):
    rec = build_reflection_record_v2(SOURCE_REPORT, "ssh", REFLECTED_AT, origin)
    assert rec["authority_origin"] == origin


def test_v2_rejects_origin_outside_locked_vocabulary():
    with pytest.raises(ValueError):
        build_reflection_record_v2(SOURCE_REPORT, "ssh", REFLECTED_AT, "FABRICATED_TPM_VERDICT")


def test_v2_still_enforces_v1_required_source_fields():
    incomplete = {k: v for k, v in SOURCE_REPORT.items() if k != "report_path"}
    with pytest.raises(ReflectionSourceError):
        build_reflection_record_v2(incomplete, "ssh", REFLECTED_AT, "LANE1_SOURCE_REPORT")


def test_authority_origin_label_is_caller_asserted_not_computed():
    """authority_origin is exactly what the caller passes in — Reflection
    does not infer, verify, or upgrade it. This is what keeps the label a
    pointer-shaped fact rather than a Reflection-originated verdict."""
    rec_a = build_reflection_record_v2(SOURCE_REPORT, "ssh", REFLECTED_AT, "UNKNOWN_SOURCE")
    rec_b = build_reflection_record_v2(SOURCE_REPORT, "ssh", REFLECTED_AT, "LANE1_SOURCE_REPORT")
    assert rec_a["authority_origin"] == "UNKNOWN_SOURCE"
    assert rec_b["authority_origin"] == "LANE1_SOURCE_REPORT"
    assert rec_a["run_id"] == rec_b["run_id"] == SOURCE_REPORT["run_id"]
