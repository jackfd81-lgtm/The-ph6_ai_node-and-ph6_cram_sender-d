"""
ph6.cfc — Canonical Failure Classification v1.0 (CFC-1.0)

All PH6 validation reports emit failures through this module.
Failure records are deterministic canonical JSON artifacts.

Failure families:
  G — Governance       R — Replay       C — CRAM         A — Audit
  S — Schema           O — Operational  T — Thermal/Res  N — Multi-node
  D — Determinism

Severity levels: CRITICAL > HIGH > MEDIUM > LOW > INFO
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any


# ── Family definitions ──────────────────────────────────────────────────────

FAMILIES: dict[str, str] = {
    "G": "Governance",
    "R": "Replay",
    "C": "CRAM",
    "A": "Audit",
    "S": "Schema",
    "O": "Operational",
    "T": "Thermal/Resource",
    "N": "Multi-node",
    "D": "Determinism",
}

SEVERITIES = ("CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO")

# Known failure codes (non-exhaustive — unlisted codes are allowed)
KNOWN_CODES: dict[str, str] = {
    # Governance
    "G1": "governance_manifest_missing_or_invalid",
    "G2": "runtime_document_divergence",
    "G3": "forbidden_term_found",
    "G4": "schema_lock_violation",
    "G5": "authority_boundary_violated",
    "G6": "patch_class_violated",
    "G7": "forbidden_audit_event_type",
    "G8": "gap_open_in_runtime",
    # Replay
    "R1": "replay_parity_failure",
    "R2": "replay_sequence_break",
    "R3": "authority_hash_mismatch",
    "R4": "chain_integrity_failure",
    "R5": "pass_drop_verdict_mismatch",
    "R6": "fixture_hash_invalid",
    # CRAM
    "C1": "atomic_write_contract_violated",
    "C2": "cram_a_mutation_detected",
    "C3": "cram_r_pass_marker_present",
    "C4": "cram_sequence_gap",
    # Audit
    "A1": "audit_continuity_broken",
    "A2": "audit_event_type_forbidden",
    "A3": "audit_field_missing",
    # Schema
    "S1": "forbidden_field_present",
    "S2": "schema_version_mismatch",
    "S3": "required_field_missing",
    "S4": "float_in_authoritative_record",
    # Operational
    "O1": "rsync_blocked_or_deprioritized",
    "O2": "lane2_authority_escalation",
    "O3": "validator_self_verify_failed",
    "O4": "minimum_frame_threshold_not_met",
    # Thermal/Resource
    "T1": "thermal_threshold_exceeded",
    "T2": "resource_starvation_detected",
    # Multi-node
    "N1": "cross_node_hash_rewritten",
    "N2": "node_sequence_conflict",
    # Determinism
    "D1": "non_deterministic_output",
    "D2": "locale_sensitive_formatting",
    "D3": "float_ambiguity_in_report",
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _family(code: str) -> str:
    prefix = code.rstrip("0123456789")
    return FAMILIES.get(prefix, f"Unknown({prefix})")


def _canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(",", ":"))


def make_failure(
    code: str,
    severity: str,
    reason: str,
    *,
    authoritative: bool = True,
    timestamp_utc: str | None = None,
    **extra: Any,
) -> dict:
    """
    Build a canonical CFC-1.0 failure record.

    Required:
        code       — failure code e.g. "R3", "G2"
        severity   — one of CRITICAL/HIGH/MEDIUM/LOW/INFO
        reason     — human-readable description

    Optional kwargs are merged into the record after the standard fields.
    """
    if severity not in SEVERITIES:
        raise ValueError(f"Invalid severity '{severity}'. Must be one of {SEVERITIES}")
    prefix = code.rstrip("0123456789")
    if prefix not in FAMILIES:
        raise ValueError(f"Unknown failure family '{prefix}' in code '{code}'")

    record: dict[str, Any] = {
        "failure_class":  code,
        "failure_family": _family(code),
        "severity":       severity,
        "authoritative":  authoritative,
        "reason":         reason,
        "timestamp_utc":  timestamp_utc or _utc_now(),
    }
    record.update(extra)
    return record


def make_rdd_failure(
    document_claim: str,
    runtime_observation: str,
    *,
    severity: str = "HIGH",
    timestamp_utc: str | None = None,
    **extra: Any,
) -> dict:
    """
    Runtime-Document Divergence failure (G2).
    Runtime evidence is always the authoritative source.
    """
    return make_failure(
        "G2",
        severity,
        "runtime-document divergence",
        authoritative=True,
        timestamp_utc=timestamp_utc,
        document_claim=document_claim,
        runtime_observation=runtime_observation,
        authoritative_source="runtime",
        **extra,
    )


def make_schema_failure(
    code: str,
    severity: str,
    reason: str,
    *,
    field: str | None = None,
    schema_id: str | None = None,
    timestamp_utc: str | None = None,
    **extra: Any,
) -> dict:
    """Schema failure (S-class) with optional field and schema_id context."""
    if not code.startswith("S"):
        raise ValueError(f"Expected S-class code, got '{code}'")
    record = make_failure(code, severity, reason, timestamp_utc=timestamp_utc, **extra)
    if field is not None:
        record["field"] = field
    if schema_id is not None:
        record["schema_id"] = schema_id
    return record


def make_replay_failure(
    code: str,
    severity: str,
    reason: str,
    *,
    object_id: str | None = None,
    expected_hash: str | None = None,
    observed_hash: str | None = None,
    timestamp_utc: str | None = None,
    **extra: Any,
) -> dict:
    """Replay failure (R-class) with optional hash comparison context."""
    if not code.startswith("R"):
        raise ValueError(f"Expected R-class code, got '{code}'")
    record = make_failure(code, severity, reason, timestamp_utc=timestamp_utc, **extra)
    if object_id is not None:
        record["object_id"] = object_id
    if expected_hash is not None:
        record["expected_hash"] = expected_hash
    if observed_hash is not None:
        record["observed_hash"] = observed_hash
    return record


def failure_hash(record: dict) -> str:
    """BLAKE2b-256 hash of a canonical failure record."""
    return hashlib.blake2b(_canonical(record).encode("utf-8"), digest_size=32).hexdigest()


def describe_code(code: str) -> str:
    """Return known description for a code, or 'unknown' if unlisted."""
    return KNOWN_CODES.get(code, f"unlisted code {code} — family {_family(code)}")
