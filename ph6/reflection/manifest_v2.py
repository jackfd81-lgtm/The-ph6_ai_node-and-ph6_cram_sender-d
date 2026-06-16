"""Reflection Manifest v2 — adds authority_origin provenance labeling.

Governed by PH6_SOURCE/DRAFT/PH6-REFLECTION-DOCTRINE-v1.0.md (RATIFIED — LOCKED).

v2 extends the v1 pure-pointer record with a single fixed-vocabulary label,
`authority_origin`, that lets an operator tell whether a displayed record
reflects a Lane-1 result, a Desktop-generated advisory status, a Lane-2-native
record, or an unclassified source. This label *describes provenance the
caller already knows* — it is asserted by whoever calls the builder, not
computed or verified by Reflection. Reflection still performs no
certification: it only attaches the caller's own classification as a
read-only marker, exactly as it would attach any other pointer field.
"""

from ph6.reflection.manifest_v1 import SCHEMA as SCHEMA_V1, build_reflection_record

SCHEMA = "ph6.reflection.manifest.v2"

AUTHORITY_ORIGIN_VALUES = frozenset({
    "REFLECTED_ONLY",
    "LANE1_SOURCE_REPORT",
    "ADVISORY_DESKTOP_STATUS",
    "UNKNOWN_SOURCE",
})


def build_reflection_record_v2(source_report, launched_from, reflected_at_utc,
                               authority_origin, desktop_visible=True):
    """Build a Reflection Manifest v2 record: a v1 record plus authority_origin.

    `authority_origin` must be one of AUTHORITY_ORIGIN_VALUES; raises ValueError
    otherwise. All v1 field-copying and validation (including
    ReflectionSourceError on an incomplete source_report) still applies —
    this function defers to build_reflection_record() for that and only adds
    the provenance label on top.
    """
    if authority_origin not in AUTHORITY_ORIGIN_VALUES:
        raise ValueError(
            f"authority_origin must be one of {sorted(AUTHORITY_ORIGIN_VALUES)}, "
            f"got {authority_origin!r}"
        )
    record = build_reflection_record(source_report, launched_from, reflected_at_utc, desktop_visible)
    record["schema"] = SCHEMA
    record["authority_origin"] = authority_origin
    return record
