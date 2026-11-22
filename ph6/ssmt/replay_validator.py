from .constants import SSMT_VERSION, AUTHORITY, LANE


class ReplayValidator:
    """
    SSMT replay validation proves advisory independence.
    It does NOT validate truth.
    """

    def validate_no_replay_dependency(self, packets) -> bool:
        for packet in packets:
            if packet.dependency_for_replay is not False:
                return False
        return True

    def validate_no_pass_drop(self, packets) -> bool:
        forbidden = {
            "pass", "drop", "verdict", "result", "final",
            "block", "override", "approve", "reject", "certify",
            "authority_decision",
        }
        def safe(value):
            if isinstance(value, dict):
                return not (forbidden & set(value)) and all(safe(v) for v in value.values())
            if isinstance(value, (list, tuple)):
                return all(safe(v) for v in value)
            return True
        return all(safe(packet.advisory_payload) for packet in packets)

    def validate_all(self, packets) -> bool:
        return (
            all(p.ssmt_version == SSMT_VERSION and p.authority == AUTHORITY
                and p.lane == LANE and p.advisory_only is True
                and all(getattr(p, field) is False for field in (
                    "affects_pass_drop", "affects_thresholds", "affects_cram_commit", "affects_rsync"))
                for p in packets)
            and self.validate_no_replay_dependency(packets)
            and self.validate_no_pass_drop(packets)
        )
