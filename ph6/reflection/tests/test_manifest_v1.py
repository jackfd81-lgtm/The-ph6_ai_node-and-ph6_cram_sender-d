import pytest

from ph6.reflection import manifest_v1
from ph6.reflection.manifest_v1 import (
    REQUIRED_SOURCE_FIELDS,
    ReflectionSourceError,
    build_reflection_record,
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


def test_record_copies_required_fields_verbatim():
    rec = build_reflection_record(SOURCE_REPORT, "ssh", REFLECTED_AT)
    assert rec["run_id"] == SOURCE_REPORT["run_id"]
    assert rec["test_name"] == SOURCE_REPORT["test_name"]
    assert rec["status"] == SOURCE_REPORT["status"]
    assert rec["report_path"] == SOURCE_REPORT["report_path"]
    assert rec["artifact_paths"] == SOURCE_REPORT["artifact_paths"]


def test_record_is_advisory_zero_authority():
    rec = build_reflection_record(SOURCE_REPORT, "cloud", REFLECTED_AT)
    assert rec["schema"] == manifest_v1.SCHEMA
    assert rec["authority"] == "ZERO"
    assert rec["lane"] == "Lane 2 reflection"
    assert rec["non_authoritative"] is True


def test_record_discloses_both_source_and_reflection_time():
    rec = build_reflection_record(SOURCE_REPORT, "desktop", REFLECTED_AT)
    assert rec["source_generated_at_utc"] == SOURCE_REPORT["generated_at_utc"]
    assert rec["reflected_at_utc"] == REFLECTED_AT
    assert rec["source_generated_at_utc"] != rec["reflected_at_utc"]


def test_record_carries_launched_from_and_visibility():
    rec = build_reflection_record(SOURCE_REPORT, "ssh", REFLECTED_AT, desktop_visible=False)
    assert rec["launched_from"] == "ssh"
    assert rec["desktop_visible"] is False


def test_record_does_not_alias_source_artifact_paths():
    source = dict(SOURCE_REPORT, artifact_paths=["/path/a"])
    rec = build_reflection_record(source, "ssh", REFLECTED_AT)
    source["artifact_paths"].append("/path/b")
    assert rec["artifact_paths"] == ["/path/a"]


def test_record_can_reflect_a_drop_status_verbatim_as_reflected_data():
    source = dict(SOURCE_REPORT, status="DROP")
    rec = build_reflection_record(source, "ssh", REFLECTED_AT)
    assert rec["status"] == "DROP"


@pytest.mark.parametrize("missing_field", REQUIRED_SOURCE_FIELDS)
def test_build_refuses_source_missing_a_required_field(missing_field):
    incomplete = {k: v for k, v in SOURCE_REPORT.items() if k != missing_field}
    with pytest.raises(ReflectionSourceError):
        build_reflection_record(incomplete, "ssh", REFLECTED_AT)


def test_module_exposes_no_aggregate_or_verdict_emitting_symbol():
    """Static contract: Reflection must remain pointer-only by construction —
    no public symbol may compute summaries, rates, or verdicts of its own."""
    forbidden_name_fragments = (
        "aggregate", "summary", "average", "rate", "score",
        "verdict", "certify", "gate", "pass_", "drop_",
    )
    for name in dir(manifest_v1):
        if name.startswith("_"):
            continue
        lowered = name.lower()
        assert not any(frag in lowered for frag in forbidden_name_fragments), (
            f"manifest_v1.{name} looks like it could aggregate or emit a verdict — "
            "Reflection must remain pointer-only"
        )
