import pytest
from ph6.ssmt.models import SwarmInput
from ph6.ssmt.scheduler import SwarmScheduler
from ph6.ssmt.closure import ClosureValidator
from ph6.ssmt.constants import SSMT_WRITE_ROOT


def test_all_packets_stay_advisory():
    scheduler = SwarmScheduler()
    packets = scheduler.run_cycle(
        SwarmInput(cram_refs=["cram://frame/0001"], tok_refs=[], advisory_refs=[])
    )
    for packet in packets:
        assert packet.output_type == "advisory"


def test_closure_validator_passes():
    scheduler = SwarmScheduler()
    packets = scheduler.run_cycle(
        SwarmInput(cram_refs=["cram://frame/0001"], tok_refs=[], advisory_refs=[])
    )
    validator = ClosureValidator(write_root=SSMT_WRITE_ROOT)
    result = validator.validate(packets)
    assert result["all_authority_none"] is True
    assert result["all_lane_2"] is True
    assert result["no_replay_dependency"] is True
    assert result["no_pass_drop"] is True
    assert result["tok_bridge_read_only"] is True


def test_ssmt_version_constant():
    from ph6.ssmt.constants import SSMT_VERSION
    assert SSMT_VERSION == "1.0"
