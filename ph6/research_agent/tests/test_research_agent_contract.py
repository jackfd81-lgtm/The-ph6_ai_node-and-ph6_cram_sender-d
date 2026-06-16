#!/usr/bin/env python3
"""Contract tests for the PH6 research agent's deterministic gate logic.

These tests prove the hard-reject gates (cloud-only authority,
advisory-override-of-measurement) are enforced in code and cannot be
bypassed by a high ph6_fit score or by an incomplete/malformed model
response.
"""

import os
import tempfile

import pytest

from ph6.research_agent.ph6_common import (
    SCORING_AXES,
    ADMISSIBILITY_FIELDS,
    OntologyError,
    compute_ph6_fit,
    decide_recommendation,
    validate_scored_result,
    load_ontology_checked,
)
from ph6.research_agent.hashing import blake2b256_bytes
from ph6.research_agent.atomic import atomic_write


WEIGHTS = {ax: round(1.0 / len(SCORING_AXES), 6) for ax in SCORING_AXES}


def _perfect_scores(**admissibility):
    scores = {ax: 10 for ax in SCORING_AXES}
    scores.update(admissibility)
    return scores


def test_high_score_cloud_only_is_discarded():
    scores = _perfect_scores(
        requires_cloud_only_authority=True,
        allows_advisory_override_of_measurement=False,
    )
    validate_scored_result(scores)
    ph6_fit = compute_ph6_fit(scores, WEIGHTS)
    assert ph6_fit >= 9.9  # near-perfect score

    admissibility = {f: scores[f] for f in ADMISSIBILITY_FIELDS}
    recommendation, reasons = decide_recommendation(ph6_fit, 6.0, admissibility)

    assert recommendation == "DISCARD"
    assert reasons == ["REQUIRES_CLOUD_ONLY_AUTHORITY"]


def test_high_score_advisory_override_is_discarded():
    scores = _perfect_scores(
        requires_cloud_only_authority=False,
        allows_advisory_override_of_measurement=True,
    )
    validate_scored_result(scores)
    ph6_fit = compute_ph6_fit(scores, WEIGHTS)

    admissibility = {f: scores[f] for f in ADMISSIBILITY_FIELDS}
    recommendation, reasons = decide_recommendation(ph6_fit, 6.0, admissibility)

    assert recommendation == "DISCARD"
    assert reasons == ["ALLOWS_ADVISORY_OVERRIDE_OF_MEASUREMENT"]


def test_clean_high_scorer_keeps():
    scores = _perfect_scores(
        requires_cloud_only_authority=False,
        allows_advisory_override_of_measurement=False,
    )
    validate_scored_result(scores)
    ph6_fit = compute_ph6_fit(scores, WEIGHTS)

    admissibility = {f: scores[f] for f in ADMISSIBILITY_FIELDS}
    recommendation, reasons = decide_recommendation(ph6_fit, 6.0, admissibility)

    assert recommendation == "KEEP"
    assert reasons == []


def test_below_threshold_admissible_is_discarded():
    scores = {ax: 1 for ax in SCORING_AXES}
    scores["requires_cloud_only_authority"] = False
    scores["allows_advisory_override_of_measurement"] = False
    validate_scored_result(scores)
    ph6_fit = compute_ph6_fit(scores, WEIGHTS)

    admissibility = {f: scores[f] for f in ADMISSIBILITY_FIELDS}
    recommendation, reasons = decide_recommendation(ph6_fit, 6.0, admissibility)

    assert recommendation == "DISCARD"
    assert reasons == ["BELOW_THRESHOLD"]


def test_validate_rejects_missing_admissibility_fields():
    scores = {ax: 10 for ax in SCORING_AXES}
    # No admissibility fields at all.
    with pytest.raises(OntologyError):
        validate_scored_result(scores)


def test_validate_rejects_non_boolean_admissibility_field():
    scores = {ax: 10 for ax in SCORING_AXES}
    scores["requires_cloud_only_authority"] = "true"
    scores["allows_advisory_override_of_measurement"] = False
    with pytest.raises(OntologyError):
        validate_scored_result(scores)


def test_validate_rejects_missing_axis():
    scores = {ax: 10 for ax in SCORING_AXES if ax != "Measurement"}
    scores["requires_cloud_only_authority"] = False
    scores["allows_advisory_override_of_measurement"] = False
    with pytest.raises(OntologyError):
        validate_scored_result(scores)


def test_blake2b256_bytes_is_blake2b_256_hex():
    import hashlib

    data = b"ph6-research-agent"
    expected = hashlib.blake2b(data, digest_size=32).hexdigest()
    assert blake2b256_bytes(data) == expected


def test_atomic_write_writes_file_durably():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "out.json")
        atomic_write(path, b'{"ok": true}')
        with open(path, "rb") as f:
            assert f.read() == b'{"ok": true}'
        # no leftover temp file
        assert not os.path.exists(path + ".tmp")


def test_scaffold_ontology_loads_and_validates():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ontology_path = os.path.join(here, "ph6_ontology.yaml")
    ontology = load_ontology_checked(ontology_path)
    assert "scaffold_domain" in ontology["domains"]
