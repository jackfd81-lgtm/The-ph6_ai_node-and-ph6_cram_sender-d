from ph6.ssmt.models import SwarmInput
from ph6.ssmt.scheduler import SwarmScheduler
from ph6.ssmt.replay_validator import ReplayValidator


def test_ssmt_never_has_authority():
    scheduler = SwarmScheduler()
    packets = scheduler.run_cycle(
        SwarmInput(
            cram_refs=["cram://frame/0001"],
            tok_refs=["tok://rt/0001"],
            advisory_refs=[],
        )
    )

    for packet in packets:
        assert packet.authority == "NONE"
        assert packet.lane == "LANE_2_ADVISORY"
        assert packet.dependency_for_replay is False


def test_ssmt_never_outputs_pass_drop():
    scheduler = SwarmScheduler()
    packets = scheduler.run_cycle(
        SwarmInput(
            cram_refs=["cram://frame/0001"],
            tok_refs=[],
            advisory_refs=[],
        )
    )

    validator = ReplayValidator()
    assert validator.validate_no_pass_drop(packets) is True
