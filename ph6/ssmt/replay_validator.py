from .constants import SSMT_VERSION, AUTHORITY, LANE

# Boolean packet fields that would let advisory output reach Lane-1 decisions.
AFFECTS_FIELDS = ("affects_pass_drop", "affects_thresholds", "affects_cram_commit", "affects_rsync")

# Keys that would claim authority if they appeared anywhere inside an advisory
# payload. Lane-2 payloads never carry them; their presence fails closed.
_PAYLOAD_AUTHORITY_KEYS = {"authority", "lane", "advisory_only", "lane_1", "lane1"}

_MISSING = object()


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

    def validate_no_authority_escalation(self, packets) -> bool:
        """Fail closed on any Lane-1 claim, whoever the caller is.

        Exact types and values only: authority must be the str "NONE", lane the
        str "LANE_2_ADVISORY", advisory_only the bool True, every affects_* the
        bool False. A missing attribute, a truthy look-alike (1, "False"), a
        str subclass, or an authority/lane/affects_* key anywhere inside the
        advisory payload is a rejection.
        """
        def exact(value, expected):
            return type(value) is type(expected) and value == expected

        def payload_clean(value):
            if isinstance(value, dict):
                for key, inner in value.items():
                    if not isinstance(key, str):
                        return False
                    k = key.lower()
                    if k in _PAYLOAD_AUTHORITY_KEYS or k.startswith("affects_"):
                        return False
                    if not payload_clean(inner):
                        return False
                return True
            if isinstance(value, (list, tuple)):
                return all(payload_clean(v) for v in value)
            if isinstance(value, str):
                return value.upper() not in ("LANE_1", "LANE1")
            return True

        try:
            for p in packets:
                if not exact(getattr(p, "ssmt_version", _MISSING), SSMT_VERSION):
                    return False
                if not exact(getattr(p, "authority", _MISSING), AUTHORITY):
                    return False
                if not exact(getattr(p, "lane", _MISSING), LANE):
                    return False
                if getattr(p, "advisory_only", _MISSING) is not True:
                    return False
                if any(getattr(p, f, _MISSING) is not False for f in AFFECTS_FIELDS):
                    return False
                payload = getattr(p, "advisory_payload", _MISSING)
                if not isinstance(payload, dict) or not payload_clean(payload):
                    return False
        except Exception:
            return False
        return True

    def validate_all(self, packets) -> bool:
        try:
            packets = list(packets)
            return (
                self.validate_no_authority_escalation(packets)
                and self.validate_no_replay_dependency(packets)
                and self.validate_no_pass_drop(packets)
            )
        except Exception:
            return False
