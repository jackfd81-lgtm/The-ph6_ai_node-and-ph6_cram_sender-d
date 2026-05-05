import pytest
from ph6.ssmt.models import SwarmInput
from ph6.ssmt.scheduler import SwarmScheduler
from ph6.ssmt.replay_validator import ReplayValidator


@pytest.fixture
def packets_fixture():
    scheduler = SwarmScheduler()
    return scheduler.run_cycle(
        SwarmInput(
            cram_refs=["cram://frame/0001"],
            tok_refs=["tok://rt/0001"],
            advisory_refs=[],
        )
    )


def test_replay_independence(packets_fixture):
    validator = ReplayValidator()
    assert validator.validate_no_replay_dependency(packets_fixture) is True
