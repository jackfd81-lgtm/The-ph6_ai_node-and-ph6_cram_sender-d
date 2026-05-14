SSMT_VERSION = "1.0"
AUTHORITY = "NONE"
LANE = "LANE_2_ADVISORY"

SSMT_WRITE_ROOT = "/var/ph6/mram-s/swarms/"
TOK_READ_ROOT = "/var/ph6/mram-s/tokens/"
CRAM_READ_ONLY = True

FORBIDDEN_OUTPUT_FIELDS = {
    "pass",
    "drop",
    "verdict",
    "result",
    "final",
    "block",
    "override",
    "approve",
    "reject",
    "certify",
    "authority_decision",
}

SWARM_IDS = ["S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "S9"]
