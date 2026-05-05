from abc import ABC, abstractmethod
from .errors import AuthorityLeakError
from .models import SwarmInput, SwarmPacket
from .constants import AUTHORITY, LANE, SSMT_VERSION, FORBIDDEN_OUTPUT_FIELDS


class BaseSwarm(ABC):
    swarm_id: str
    role: str
    ttl_seconds: int

    @abstractmethod
    def compute_payload(self, data: SwarmInput) -> dict:
        ...

    def run(self, data: SwarmInput) -> SwarmPacket:
        payload = self.compute_payload(data)
        self._assert_no_authority_leak(payload)
        return SwarmPacket(
            swarm_id=self.swarm_id,
            role=self.role,
            authority=AUTHORITY,
            lane=LANE,
            ssmt_version=SSMT_VERSION,
            ttl_seconds=self.ttl_seconds,
            output_type="advisory",
            advisory_payload=payload,
            drift_score=payload.pop("_drift_score", 0),
            confidence_fp=payload.pop("_confidence_fp", 100),
            dependency_for_replay=False,
        )

    def _assert_no_authority_leak(self, payload: dict) -> None:
        leaked = FORBIDDEN_OUTPUT_FIELDS & set(payload.keys())
        if leaked:
            raise AuthorityLeakError(
                f"{self.swarm_id} emitted forbidden fields: {leaked}"
            )
