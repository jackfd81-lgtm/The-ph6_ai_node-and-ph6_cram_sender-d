from .swarms import (
    S1ActiveMemorySwarm,
    S2ContextAnchorSwarm,
    S3SemanticSummarySwarm,
    S4ProjectIdentitySwarm,
    S5HistoricalAwarenessSwarm,
    S6LatentKnowledgeSwarm,
    S7UpdateIntakeSwarm,
    S8DriftTrackingSwarm,
    S9FutureAcquisitionSwarm,
)
from .execution_graph import EXECUTION_GRAPH
from .models import SwarmInput, SwarmPacket
from typing import List

_SWARM_REGISTRY = {
    "S1": S1ActiveMemorySwarm,
    "S2": S2ContextAnchorSwarm,
    "S3": S3SemanticSummarySwarm,
    "S4": S4ProjectIdentitySwarm,
    "S5": S5HistoricalAwarenessSwarm,
    "S6": S6LatentKnowledgeSwarm,
    "S7": S7UpdateIntakeSwarm,
    "S8": S8DriftTrackingSwarm,
    "S9": S9FutureAcquisitionSwarm,
}


class SwarmScheduler:
    def run_cycle(self, data: SwarmInput) -> List[SwarmPacket]:
        packets = []
        for stage in EXECUTION_GRAPH:
            for swarm_id in stage:
                swarm = _SWARM_REGISTRY[swarm_id]()
                packets.append(swarm.run(data))
        return packets
