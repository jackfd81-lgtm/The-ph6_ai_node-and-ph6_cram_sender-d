from ph6.ssmt.models import SwarmInput
from ph6.ssmt.scheduler import SwarmScheduler
from ph6.ssmt.constants import SWARM_IDS


def test_all_swarms_run():
    scheduler = SwarmScheduler()
    packets = scheduler.run_cycle(
        SwarmInput(cram_refs=[], tok_refs=[], advisory_refs=[])
    )
    emitted_ids = {p.swarm_id for p in packets}
    assert emitted_ids == set(SWARM_IDS)


def test_execution_order():
    scheduler = SwarmScheduler()
    packets = scheduler.run_cycle(
        SwarmInput(cram_refs=["cram://frame/0001"], tok_refs=[], advisory_refs=[])
    )
    ids_in_order = [p.swarm_id for p in packets]
    assert ids_in_order[0] == "S4", "S4 (identity) must run first"
    assert ids_in_order[-1] == "S9", "S9 (future acquisition) must run last"


def test_packet_count():
    scheduler = SwarmScheduler()
    packets = scheduler.run_cycle(
        SwarmInput(cram_refs=[], tok_refs=[], advisory_refs=[])
    )
    assert len(packets) == 9
