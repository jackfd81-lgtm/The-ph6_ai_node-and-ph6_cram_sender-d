from .constants import SSMT_WRITE_ROOT, AUTHORITY, LANE
from .replay_validator import ReplayValidator
from .token_bridge import TokenBridge


class ClosureValidator:
    """HRG9-compatible closure rule validator for SSMT-1.0."""

    def __init__(self, write_root: str = SSMT_WRITE_ROOT):
        self.write_root = write_root
        self._replay = ReplayValidator()
        self._tok = TokenBridge()

    def validate(self, packets) -> dict:
        results = {
            "all_authority_none": all(p.authority == AUTHORITY for p in packets),
            "all_lane_2": all(p.lane == LANE for p in packets),
            "no_replay_dependency": self._replay.validate_no_replay_dependency(packets),
            "no_pass_drop": self._replay.validate_no_pass_drop(packets),
            "tok_bridge_read_only": not self._tok.is_writable(),
        }
        results["passed"] = all(results.values())
        return results
