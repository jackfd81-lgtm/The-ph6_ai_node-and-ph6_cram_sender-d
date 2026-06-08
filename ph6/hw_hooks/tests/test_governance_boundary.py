"""Governance boundary check (scope hook 6).

Proves that none of the PH6 hardware-hook advisory paths — Pi Zero 2 W,
Pico, or the MRAM-S advisory log — can ever emit a PASS/DROP verdict, and
that every record they produce is locked to authority=ZERO /
non_authoritative=True. This is the test standing behind the scope
document's hard limit: "no PASS/DROP generation from Pi Zero 2 W, Pico,
desktop, or advisory hooks".
"""

import pytest

from ph6.hw_hooks import advisory_log, pico_advisory, pizero_advisory

NOW = "2026-06-08T11:00:00Z"

_FORBIDDEN_VERDICTS = {"PASS", "DROP"}


def _all_string_leaves(value):
    """Yield every string leaf found anywhere inside a nested dict/list/tuple."""
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for v in value.values():
            yield from _all_string_leaves(v)
    elif isinstance(value, (list, tuple)):
        for v in value:
            yield from _all_string_leaves(v)


def _assert_advisory_only(record):
    assert record["authority"] == "ZERO"
    assert record["non_authoritative"] is True
    assert "verdict" not in record
    for leaf in _all_string_leaves(record):
        assert leaf.upper() not in _FORBIDDEN_VERDICTS, f"forbidden verdict token leaked: {leaf!r}"


SAMPLE_RECORDS = [
    pizero_advisory.build_heartbeat("jackjack2", "jackjack", "up 1:00", "47000", NOW),
    pizero_advisory.build_health_snapshot("jackjack2", "UNVERIFIED", {"temp_c": 42.0}, NOW),
    pico_advisory.build_presence_record("pico-01", ["/dev/ttyACM0"], NOW),
    pico_advisory.intake_sample("pico-01", {"temperature_c": 21.4}, NOW),
]


@pytest.mark.parametrize("record", SAMPLE_RECORDS, ids=lambda r: r["schema"])
def test_every_hook_record_is_advisory_only_and_verdict_free(record):
    _assert_advisory_only(record)


def test_pizero_status_vocabulary_excludes_verdicts():
    assert _FORBIDDEN_VERDICTS.isdisjoint(pizero_advisory.ADVISORY_STATUS_VALUES)


def test_pico_presence_vocabulary_excludes_verdicts():
    assert _FORBIDDEN_VERDICTS.isdisjoint(pico_advisory.PRESENCE_STATUS_VALUES)


def test_pico_intake_boundary_refuses_verdict_shaped_input():
    for token in _FORBIDDEN_VERDICTS:
        with pytest.raises(ValueError):
            pico_advisory.intake_sample("pico-01", {"status": token}, NOW)
        with pytest.raises(ValueError):
            pico_advisory.intake_sample("pico-01", {"verdict": token}, NOW)


def test_advisory_log_refuses_anything_not_tagged_authority_zero():
    leaking = {"schema": "x", "authority": "FULL", "non_authoritative": True}
    with pytest.raises(ValueError):
        advisory_log.append_advisory_record("/tmp", "x.jsonl", leaking)


def test_no_hw_hook_module_exposes_a_verdict_emitting_symbol():
    """Static contract: no public symbol in the hook modules is named like
    something that computes or emits a verdict (gate/verdict/certify/...).
    Hardware hooks must remain advisory-only by construction, not by review."""
    forbidden_name_fragments = ("verdict", "gate", "pass_", "drop_", "certify")
    for module in (pizero_advisory, pico_advisory, advisory_log):
        for name in dir(module):
            if name.startswith("_"):
                continue
            lowered = name.lower()
            assert not any(frag in lowered for frag in forbidden_name_fragments), (
                f"{module.__name__}.{name} looks like it could emit a verdict — "
                "hardware hooks must remain advisory-only"
            )
