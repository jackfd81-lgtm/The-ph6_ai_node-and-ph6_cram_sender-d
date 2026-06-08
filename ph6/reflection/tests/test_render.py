import pytest

from ph6.reflection.manifest_v1 import SCHEMA as SCHEMA_V1, build_reflection_record
from ph6.reflection.manifest_v2 import SCHEMA as SCHEMA_V2, build_reflection_record_v2
from ph6.reflection.render import (
    REFLECTED_DATA_LABEL,
    format_reflection_summary,
    render_reflection_summary_lines,
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


def test_format_summary_handles_v1_record_without_authority_origin():
    rec = build_reflection_record(SOURCE_REPORT, "ssh", REFLECTED_AT)
    summary = format_reflection_summary(rec)
    assert summary["schema"] == SCHEMA_V1
    assert "authority_origin" not in summary
    assert summary["run_id"] == SOURCE_REPORT["run_id"]
    assert summary["status"] == "PASS"
    assert summary["status_label"] == REFLECTED_DATA_LABEL


def test_format_summary_handles_v2_record_with_authority_origin():
    rec = build_reflection_record_v2(SOURCE_REPORT, "cloud", REFLECTED_AT, "LANE1_SOURCE_REPORT")
    summary = format_reflection_summary(rec)
    assert summary["schema"] == SCHEMA_V2
    assert summary["authority_origin"] == "LANE1_SOURCE_REPORT"


def test_format_summary_rejects_unrecognized_schema():
    with pytest.raises(ValueError):
        format_reflection_summary({"schema": "some.other.schema.v9"})


def test_format_summary_discloses_both_timestamps_distinctly():
    rec = build_reflection_record(SOURCE_REPORT, "desktop", REFLECTED_AT)
    summary = format_reflection_summary(rec)
    assert summary["source_generated_at_utc"] == SOURCE_REPORT["generated_at_utc"]
    assert summary["reflected_at_utc"] == REFLECTED_AT
    assert summary["source_generated_at_utc"] != summary["reflected_at_utc"]


def test_format_summary_does_not_alias_artifact_paths():
    rec = build_reflection_record(SOURCE_REPORT, "ssh", REFLECTED_AT)
    summary = format_reflection_summary(rec)
    rec["artifact_paths"].append("/sneaky/path")
    assert summary["artifact_paths"] == SOURCE_REPORT["artifact_paths"]


def test_render_lines_labels_status_as_reflected_data_and_includes_origin_for_v2():
    v1_rec = build_reflection_record(SOURCE_REPORT, "ssh", REFLECTED_AT)
    v2_rec = build_reflection_record_v2(SOURCE_REPORT, "ssh", REFLECTED_AT, "UNKNOWN_SOURCE")

    v1_lines = render_reflection_summary_lines(v1_rec)
    v2_lines = render_reflection_summary_lines(v2_rec)

    assert any(REFLECTED_DATA_LABEL in line for line in v1_lines)
    assert not any("authority_origin=" in line for line in v1_lines)
    assert any("authority_origin=UNKNOWN_SOURCE" in line for line in v2_lines)


def test_render_lines_never_states_a_bare_verdict_outside_the_status_line():
    """Static contract: PASS/DROP may appear only on the explicitly-labeled
    status line — never floating elsewhere as if Reflection asserted it."""
    rec = build_reflection_record(SOURCE_REPORT, "ssh", REFLECTED_AT)
    lines = render_reflection_summary_lines(rec)
    for line in lines:
        if "PASS" in line or "DROP" in line:
            assert "status=" in line and REFLECTED_DATA_LABEL in line
