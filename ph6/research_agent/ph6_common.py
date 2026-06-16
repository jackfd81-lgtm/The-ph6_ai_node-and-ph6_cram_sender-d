#!/usr/bin/env python3
"""
PH6 Common - shared scoring primitives for Lane 2 advisory tools.

Single source of truth for:
  - SCORING_AXES         the canonical axis set
  - compute_ph6_fit      weighted-sum fit score
  - resolve_threshold    keep_threshold (accept_threshold back-compat)
  - validate_candidate   --file candidate structure check
  - load_ontology_checked  ontology load + weight/axis validation

Both ph6_agent.py and ph6_score.py import from here so their scoring logic
cannot drift apart. Lane 2 advisory only; zero governance authority.
"""

import yaml
from typing import Dict

# ========== Scoring axes (single source of truth) ==========
SCORING_AXES = (
    "Measurement",
    "Validation",
    "Preservation",
    "Continuity",
    "Methodology",
    "Epistemics",
    "Determinism",
    "Explainability",
    "EvidenceIntegrity",
    "OpenSourceAvailability",
    "ScientificCredibility",
)

DEFAULT_THRESHOLD = 6.0

# ========== Binary admissibility gate ==========
# Doctrine: cloud-only authority and advisory-override-of-measurement are
# HARD admissibility gates, not graded axes. A candidate that trips either is
# DISCARDed regardless of ph6_fit. The model ADVISES these booleans; code
# DECIDES. This is deterministic and must not live in LLM prose.
ADMISSIBILITY_FIELDS = (
    "requires_cloud_only_authority",
    "allows_advisory_override_of_measurement",
)

# Maps each admissibility field (when True) to its recorded reject reason.
_ADMISSIBILITY_REASONS = {
    "requires_cloud_only_authority": "REQUIRES_CLOUD_ONLY_AUTHORITY",
    "allows_advisory_override_of_measurement": "ALLOWS_ADVISORY_OVERRIDE_OF_MEASUREMENT",
}


def admissibility_reasons(result: Dict) -> list:
    """Return the list of hard-reject reasons tripped by a scored result.
    Only an explicit boolean True trips a gate; missing/None/false does not.
    Empty list means admissible."""
    reasons = []
    for field in ADMISSIBILITY_FIELDS:
        if result.get(field) is True:
            reasons.append(_ADMISSIBILITY_REASONS[field])
    return reasons


def decide_recommendation(ph6_fit: float, threshold: float, result: Dict):
    """Deterministic KEEP/DISCARD decision.

    Binary admissibility gate runs FIRST: if any hard-reject reason is present,
    the result is DISCARD regardless of ph6_fit. Only admissible candidates
    reach the threshold comparison.

    Returns (recommendation, reject_reasons) where reject_reasons is a list
    (possibly empty) recorded for audit.
    """
    reasons = admissibility_reasons(result)
    if reasons:
        return "DISCARD", reasons
    if ph6_fit >= threshold:
        return "KEEP", []
    return "DISCARD", ["BELOW_THRESHOLD"]


class OntologyError(ValueError):
    """Raised when an ontology fails structural or weight validation."""


def compute_ph6_fit(scores: Dict[str, float], weights: Dict[str, float]) -> float:
    """Weighted sum of axis scores. Axes absent from `weights` contribute 0.
    PH6Fit is never itself a weighted input."""
    weighted_sum = 0.0
    for axis, w in weights.items():
        if axis == "PH6Fit":
            continue
        weighted_sum += scores.get(axis, 0) * w
    return round(weighted_sum, 2)


def resolve_threshold(ontology: Dict) -> float:
    """keep_threshold is canonical; accept_threshold kept for back-compat."""
    return ontology.get(
        "keep_threshold",
        ontology.get("accept_threshold", DEFAULT_THRESHOLD),
    )


def validate_weights(ontology: Dict) -> None:
    """Fail loud if ph6_weights does not match SCORING_AXES exactly, or does
    not sum to 1.0. Prevents the silent-mismatch failure where the LLM scores
    one axis set while ph6_fit is computed against a different set."""
    weights = ontology.get("ph6_weights")
    if not isinstance(weights, dict):
        raise OntologyError("ontology missing 'ph6_weights' mapping")
    weight_axes = {k for k in weights if k != "PH6Fit"}
    expected = set(SCORING_AXES)
    if weight_axes != expected:
        missing = sorted(expected - weight_axes)
        extra = sorted(weight_axes - expected)
        raise OntologyError(
            f"ph6_weights does not match SCORING_AXES. missing={missing} extra={extra}"
        )
    total = sum(v for k, v in weights.items() if k != "PH6Fit")
    if abs(total - 1.0) > 1e-6:
        raise OntologyError(f"ph6_weights must sum to 1.0 (got {total:.6f})")


def validate_candidate(candidate: Dict, weights: Dict[str, float]) -> Dict:
    """Validate and normalize a --file candidate.

    - Must be a dict.
    - If 'scores' present, (re)compute 'ph6_fit' from it.
    - Else 'ph6_fit' must already be present.
    - Neither -> OntologyError (no silent default).
    Returns the candidate with 'ph6_fit' guaranteed present.
    """
    if not isinstance(candidate, dict):
        raise OntologyError(
            f"candidate must be an object, got: {type(candidate).__name__}"
        )
    if "scores" in candidate:
        candidate["ph6_fit"] = compute_ph6_fit(candidate["scores"], weights)
    elif "ph6_fit" not in candidate:
        raise OntologyError(
            f"candidate missing both 'scores' and 'ph6_fit': {candidate.get('title', '?')}"
        )
    return candidate


def validate_scored_result(result: Dict) -> Dict:
    """Validate a model-scored result before it is used for a decision.

    Requires every SCORING_AXES field and both ADMISSIBILITY_FIELDS to be
    present. Admissibility fields must be explicit booleans -- a missing or
    non-boolean admissibility field is a hard error, because a silently-absent
    gate is exactly the failure this gate exists to prevent.
    """
    missing_axes = [ax for ax in SCORING_AXES if ax not in result]
    if missing_axes:
        raise OntologyError(f"scored result missing axes: {missing_axes}")
    for field in ADMISSIBILITY_FIELDS:
        if field not in result:
            raise OntologyError(f"scored result missing admissibility field: {field}")
        if not isinstance(result[field], bool):
            raise OntologyError(
                f"admissibility field {field!r} must be boolean, got "
                f"{type(result[field]).__name__}"
            )
    return result


def load_ontology_checked(path: str = "ph6_ontology.yaml") -> Dict:
    """Load an ontology and validate its weights against SCORING_AXES.
    Raises OntologyError on any structural problem; readable errors on
    missing file or parse failure."""
    try:
        with open(path, "r") as f:
            ontology = yaml.safe_load(f)
    except FileNotFoundError:
        raise OntologyError(f"ontology not found: {path}")
    except yaml.YAMLError as e:
        raise OntologyError(f"ontology parse error in {path}: {e}")
    if not isinstance(ontology, dict):
        raise OntologyError(f"ontology root must be a mapping: {path}")
    validate_weights(ontology)
    return ontology
