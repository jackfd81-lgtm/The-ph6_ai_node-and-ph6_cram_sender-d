"""Reflection record rendering — the read-only Evidence Review Center
integration point for Reflection Manifest v1/v2 records.

Governed by PH6_SOURCE/DRAFT/PH6-REFLECTION-DOCTRINE-v1.0.md (RATIFIED — LOCKED).

Pure formatting only. Takes an already-built v1 or v2 record (dict) and
arranges its existing fields for an operator to read — nothing is computed,
derived, aggregated, or inferred. `status` is explicitly labeled as
REFLECTED DATA so a displayed PASS/DROP is never mistaken for a verdict
Reflection itself produced. Both `source_generated_at_utc` and
`reflected_at_utc` are always carried through together, per the doctrine's
age-disclosure constraint. This module performs no I/O and no artifact
discovery — wiring it to a search/collection layer (e.g. the Desktop
Evidence Review Center's artifact walk) is a separate, later concern.
"""

from ph6.reflection.manifest_v1 import SCHEMA as SCHEMA_V1
from ph6.reflection.manifest_v2 import SCHEMA as SCHEMA_V2

RECOGNIZED_SCHEMAS = (SCHEMA_V1, SCHEMA_V2)

REFLECTED_DATA_LABEL = "REFLECTED DATA (verbatim from source — not Reflection-generated)"


def format_reflection_summary(record):
    """Return a read-only display summary dict for a v1 or v2 reflection record.

    Raises ValueError if `record` does not carry a recognized Reflection
    Manifest schema string — Reflection has nothing to display for a record
    it cannot trace to its own builders.
    """
    schema = record.get("schema")
    if schema not in RECOGNIZED_SCHEMAS:
        raise ValueError(f"not a recognized reflection manifest schema: {schema!r}")

    summary = {
        "schema": schema,
        "run_id": record["run_id"],
        "test_name": record["test_name"],
        "launched_from": record["launched_from"],
        "status": record["status"],
        "status_label": REFLECTED_DATA_LABEL,
        "report_path": record["report_path"],
        "artifact_paths": list(record["artifact_paths"]),
        "desktop_visible": record["desktop_visible"],
        "source_generated_at_utc": record["source_generated_at_utc"],
        "reflected_at_utc": record["reflected_at_utc"],
    }
    if schema == SCHEMA_V2:
        summary["authority_origin"] = record["authority_origin"]
    return summary


def render_reflection_summary_lines(record):
    """Return a list of read-only display lines for `record`.

    Plain text, terminal-framework-agnostic — the Desktop (or any other
    Lane-2 surface) can print these lines as-is or wrap them in its own
    layout. No line here states or implies a verdict of Reflection's own;
    every verdict-shaped value is explicitly tagged with REFLECTED_DATA_LABEL.
    """
    summary = format_reflection_summary(record)
    lines = [
        f"[{summary['schema']}] run_id={summary['run_id']}  test={summary['test_name']}",
        f"  launched_from={summary['launched_from']}  desktop_visible={summary['desktop_visible']}",
        f"  status={summary['status']}   <- {summary['status_label']}",
        f"  source_generated_at_utc={summary['source_generated_at_utc']}",
        f"  reflected_at_utc={summary['reflected_at_utc']}",
        f"  report_path={summary['report_path']}",
        f"  artifact_paths={summary['artifact_paths']}",
    ]
    if "authority_origin" in summary:
        lines.append(f"  authority_origin={summary['authority_origin']}")
    return lines
