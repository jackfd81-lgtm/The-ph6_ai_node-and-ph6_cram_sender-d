import pytest

from ph6.hw_hooks.pizero_advisory import (
    ADVISORY_STATUS_VALUES,
    build_health_snapshot,
    build_heartbeat,
)

NOW = "2026-06-08T11:00:00Z"


def test_heartbeat_is_advisory_zero_authority():
    pkt = build_heartbeat("jackjack2", "jackjack", "up 1:00", "47000", NOW)
    assert pkt["authority"] == "ZERO"
    assert pkt["non_authoritative"] is True
    assert pkt["lane"] == "Lane 2 sentinel"
    assert "verdict" not in pkt


def test_heartbeat_carries_no_verdict_tokens():
    pkt = build_heartbeat("jackjack2", "jackjack", "up 1:00", "47000", NOW)
    for value in pkt.values():
        if isinstance(value, str):
            assert value.upper() not in {"PASS", "DROP"}


def test_health_snapshot_accepts_locked_status_vocabulary():
    for status in ADVISORY_STATUS_VALUES:
        snap = build_health_snapshot("jackjack2", status, {"temp_c": 42.0}, NOW)
        assert snap["status"] == status
        assert snap["authority"] == "ZERO"
        assert snap["non_authoritative"] is True


def test_health_snapshot_rejects_verdict_shaped_status():
    with pytest.raises(ValueError):
        build_health_snapshot("jackjack2", "PASS", {}, NOW)
    with pytest.raises(ValueError):
        build_health_snapshot("jackjack2", "DROP", {}, NOW)


def test_health_snapshot_copies_metrics_without_aliasing():
    metrics = {"temp_c": 51.0, "load_avg_1m": 0.4}
    snap = build_health_snapshot("jackjack2", "UNVERIFIED", metrics, NOW)
    assert snap["metrics"] == metrics
    assert snap["metrics"] is not metrics
