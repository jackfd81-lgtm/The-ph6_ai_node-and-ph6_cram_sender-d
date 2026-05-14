"""
Tests A-F: SoSo-family contract enforcement — PH6-SOSO-FAMILY-CONTRACT-v1.0

Lane: 2 / Authority: ZERO / advisory_only: True
"""

import pytest
from ph6.ssmt.models import SwarmInput
from ph6.ssmt.scheduler import SwarmScheduler
from ph6.ssmt.replay_validator import ReplayValidator
from ph6.ssmt.constants import FORBIDDEN_OUTPUT_FIELDS, SSMT_WRITE_ROOT


# ---------------------------------------------------------------------------
# Test F — Schema contract
# ---------------------------------------------------------------------------

def test_swarm_packets_schema_contract():
    """Test F: All SwarmPackets carry contract-required authority fields and
    no forbidden verdict/result fields."""
    scheduler = SwarmScheduler()
    packets = scheduler.run_cycle(
        SwarmInput(cram_refs=["cram://frame/0001"], tok_refs=[], advisory_refs=[])
    )
    for packet in packets:
        assert packet.authority == "NONE", f"{packet.swarm_id}: authority must be NONE"
        assert packet.advisory_only is True, f"{packet.swarm_id}: advisory_only must be True"
        assert packet.dependency_for_replay is False, (
            f"{packet.swarm_id}: dependency_for_replay must be False"
        )
        assert packet.affects_pass_drop is False, (
            f"{packet.swarm_id}: affects_pass_drop must be False"
        )
        assert packet.affects_thresholds is False, (
            f"{packet.swarm_id}: affects_thresholds must be False"
        )
        assert packet.affects_cram_commit is False, (
            f"{packet.swarm_id}: affects_cram_commit must be False"
        )
        assert packet.affects_rsync is False, f"{packet.swarm_id}: affects_rsync must be False"
        assert "verdict" not in packet.advisory_payload, (
            f"{packet.swarm_id}: verdict is forbidden in advisory_payload"
        )
        assert "result" not in packet.advisory_payload, (
            f"{packet.swarm_id}: result is forbidden in advisory_payload"
        )


# ---------------------------------------------------------------------------
# Test D — Authority language scan
# ---------------------------------------------------------------------------

def test_forbidden_output_fields_complete():
    """Test D: FORBIDDEN_OUTPUT_FIELDS covers all PH6-SOSO-FAMILY-CONTRACT-v1.0
    authority verbs."""
    required = {
        "verdict", "result", "pass", "drop",
        "final", "block", "override", "approve", "reject", "certify",
    }
    missing = required - FORBIDDEN_OUTPUT_FIELDS
    assert not missing, f"FORBIDDEN_OUTPUT_FIELDS is missing: {missing}"


def test_swarm_payloads_have_no_authority_verbs():
    """Test D: Advisory payloads contain no authority-emitting field names."""
    scheduler = SwarmScheduler()
    packets = scheduler.run_cycle(
        SwarmInput(
            cram_refs=["cram://frame/0001"],
            tok_refs=["tok://vdt/0001"],
            advisory_refs=[],
        )
    )
    validator = ReplayValidator()
    assert validator.validate_no_pass_drop(packets) is True


# ---------------------------------------------------------------------------
# Test A — PSEUDO isolation
# ---------------------------------------------------------------------------

def test_swarm_determinism_independent_of_advisory_refs():
    """Test A: Swarm authority properties are identical whether or not advisory
    refs (SoSo sidecars) are present — simulates PSEUDO reading frames with or
    without SoSo sidecars and producing the same authority result."""
    scheduler = SwarmScheduler()
    base_input = SwarmInput(
        cram_refs=["cram://frame/0001"],
        tok_refs=["tok://rt/0001"],
        advisory_refs=[],
    )
    soso_input = SwarmInput(
        cram_refs=["cram://frame/0001"],
        tok_refs=["tok://rt/0001"],
        advisory_refs=["soso://prior_sidecar/0001"],
    )

    packets_base = scheduler.run_cycle(base_input)
    packets_soso = scheduler.run_cycle(soso_input)

    for pb, ps in zip(packets_base, packets_soso):
        assert pb.authority == ps.authority
        assert pb.dependency_for_replay == ps.dependency_for_replay
        assert pb.affects_pass_drop == ps.affects_pass_drop


def test_pseudo_evaluate_takes_no_soso_input():
    """Test A: The pseudo_evaluate function signature does not accept SoSo
    output — verifies structural isolation."""
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "bin"))
    try:
        import pseudo_soso_agent as agent
        import inspect
        sig = inspect.signature(agent.pseudo_evaluate)
        param_names = list(sig.parameters.keys())
        assert "soso" not in param_names, (
            "pseudo_evaluate must not accept soso output as a parameter"
        )
    finally:
        sys.path.pop(0)


# ---------------------------------------------------------------------------
# Test B — SoSo non-blocking
# ---------------------------------------------------------------------------

def test_soso_absence_does_not_block_advisory_cycle():
    """Test B: Scheduler completes even with empty/minimal inputs — SoSo
    absence does not block the advisory cycle or any downstream path."""
    scheduler = SwarmScheduler()
    packets = scheduler.run_cycle(
        SwarmInput(cram_refs=[], tok_refs=[], advisory_refs=[])
    )
    assert len(packets) > 0
    for packet in packets:
        assert packet.output_type == "advisory"
        assert packet.authority == "NONE"


def test_soso_output_not_required_for_completion():
    """Test B: Varying advisory_refs (stale, absent, or present) does not
    change the number of packets or their authority properties."""
    scheduler = SwarmScheduler()
    base = scheduler.run_cycle(
        SwarmInput(cram_refs=["cram://frame/0001"], tok_refs=[], advisory_refs=[])
    )
    with_stale = scheduler.run_cycle(
        SwarmInput(cram_refs=["cram://frame/0001"], tok_refs=[], advisory_refs=["stale://ref"])
    )
    assert len(base) == len(with_stale)
    for pb, ps in zip(base, with_stale):
        assert pb.authority == ps.authority
        assert pb.affects_pass_drop == ps.affects_pass_drop


# ---------------------------------------------------------------------------
# Test C — MRAM-S write boundary
# ---------------------------------------------------------------------------

def test_ssmt_write_root_is_mram_s_advisory_path():
    """Test C: SSMT_WRITE_ROOT is under MRAM-S advisory path — not under
    any CRAM, export, audit, or authority path."""
    assert SSMT_WRITE_ROOT.startswith("/var/ph6/mram-s/"), (
        f"SSMT_WRITE_ROOT must be under /var/ph6/mram-s/, got: {SSMT_WRITE_ROOT}"
    )
    for forbidden_segment in ("cram", "export", "/audit", "rsync", "evidence"):
        assert forbidden_segment not in SSMT_WRITE_ROOT.lower(), (
            f"SSMT_WRITE_ROOT must not contain '{forbidden_segment}': {SSMT_WRITE_ROOT}"
        )


# ---------------------------------------------------------------------------
# Test E — Replay independence
# ---------------------------------------------------------------------------

def test_replay_independence_with_and_without_sidecars():
    """Test E: Deterministic replay result is identical whether SoSo sidecars
    are present or deleted (simulated by advisory_refs=[] vs non-empty)."""
    scheduler = SwarmScheduler()
    validator = ReplayValidator()

    with_sidecars = scheduler.run_cycle(
        SwarmInput(
            cram_refs=["cram://frame/0001"],
            tok_refs=["tok://rt/0001"],
            advisory_refs=["soso://sidecar/0001"],
        )
    )
    without_sidecars = scheduler.run_cycle(
        SwarmInput(
            cram_refs=["cram://frame/0001"],
            tok_refs=["tok://rt/0001"],
            advisory_refs=[],
        )
    )

    assert validator.validate_no_replay_dependency(with_sidecars) is True
    assert validator.validate_no_replay_dependency(without_sidecars) is True

    for pw, po in zip(with_sidecars, without_sidecars):
        assert pw.dependency_for_replay == po.dependency_for_replay is False
        assert pw.authority == po.authority == "NONE"
        assert pw.affects_pass_drop == po.affects_pass_drop is False
