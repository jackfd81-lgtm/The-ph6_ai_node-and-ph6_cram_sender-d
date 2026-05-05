class AuthorityLeakError(RuntimeError):
    """Raised when SSMT payload contains authority-level output fields."""


class SSMTWriteBoundaryError(RuntimeError):
    """Raised when SSMT attempts to write outside the permitted MRAM-S path."""


class ReplayDependencyError(RuntimeError):
    """Raised if a packet is incorrectly flagged as a replay dependency."""
