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
        for packet in packets:
            if forbidden & set(packet.advisory_payload.keys()):
                return False
        return True

    def validate_all(self, packets) -> bool:
        return (
            self.validate_no_replay_dependency(packets)
            and self.validate_no_pass_drop(packets)
        )
