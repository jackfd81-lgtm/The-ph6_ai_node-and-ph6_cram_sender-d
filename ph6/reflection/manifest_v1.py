"""Reflection Manifest v1 — pure pointer record builder.

Governed by PH6_SOURCE/DRAFT/PH6-REFLECTION-DOCTRINE-v1.0.md (RATIFIED — LOCKED).
"Reflection consumes authority. Reflection does not generate authority."

This module builds advisory records that point at an existing, authority-bearing
Lane-1 source report. It copies a fixed set of fields verbatim — including
`status`, which may legitimately carry a Lane-1 PASS/DROP value as REFLECTED
DATA — and never computes, aggregates, or originates a verdict of its own.
Every record also carries the source's own `generated_at_utc` alongside the
time Reflection observed it, so a stale reflection can never be mistaken for
a live result.
"""

SCHEMA = "ph6.reflection.manifest.v1"

REQUIRED_SOURCE_FIELDS = ("run_id", "test_name", "status", "report_path", "generated_at_utc")


class ReflectionSourceError(ValueError):
    """Raised when a source report lacks a field Reflection must copy verbatim."""


def build_reflection_record(source_report, launched_from, reflected_at_utc, desktop_visible=True):
    """Build a Reflection Manifest v1 record pointing at `source_report`.

    `source_report` is the authority-bearing Lane-1 record being reflected;
    its required fields are copied verbatim, never recomputed. Raises
    ReflectionSourceError if any required field is absent — Reflection has
    nothing of its own to substitute.
    """
    missing = [field for field in REQUIRED_SOURCE_FIELDS if field not in source_report]
    if missing:
        raise ReflectionSourceError(
            f"source report missing required field(s) for verbatim reflection: {missing}"
        )
    return {
        "schema": SCHEMA,
        "authority": "ZERO",
        "lane": "Lane 2 reflection",
        "non_authoritative": True,
        "run_id": source_report["run_id"],
        "test_name": source_report["test_name"],
        "launched_from": launched_from,
        "status": source_report["status"],
        "report_path": source_report["report_path"],
        "artifact_paths": list(source_report.get("artifact_paths", [])),
        "desktop_visible": bool(desktop_visible),
        "source_generated_at_utc": source_report["generated_at_utc"],
        "reflected_at_utc": reflected_at_utc,
    }
