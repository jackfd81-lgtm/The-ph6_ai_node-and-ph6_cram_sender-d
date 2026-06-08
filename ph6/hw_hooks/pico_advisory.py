"""Raspberry Pi Pico advisory outputs: presence detection and sensor sample intake.

Authority ZERO. The Pico is treated strictly as an external microcontroller /
sensor test node — these helpers never activate it, never certify it, and
never forward verdict-shaped data into PH6. See
PH6_SOURCE/DEPLOYMENT/PH6_HARDWARE_EXPANSION_SCOPE_20260608.md.
"""

PRESENCE_SCHEMA = "ph6.hw_hooks.pico_presence.v1"
INTAKE_SCHEMA = "ph6.hw_hooks.pico_sensor_intake.v1"

PRESENCE_STATUS_VALUES = frozenset({"PRESENT", "NOT_PRESENT", "UNVERIFIED", "UNKNOWN"})

# Locked verdict vocabulary (CLAUDE.md hard rule 5) — none of these may ever
# appear inside an advisory hook record. Listed here only so the intake
# boundary can refuse them, mirroring ph6_cram_sim.check_forbidden_fields.
_FORBIDDEN_VERDICT_TOKENS = frozenset({"PASS", "DROP", "ACCEPT", "REJECT", "OK", "FAIL"})
_FORBIDDEN_KEY_NAMES = frozenset({"verdict", "pass", "drop"})


def classify_presence(candidate_paths):
    """Classify Pico presence from caller-supplied candidate device paths.

    Pure classification — never touches hardware. The caller performs any
    actual device discovery (e.g. serial/USB enumeration); this only maps the
    result onto the locked advisory status vocabulary.
    """
    if candidate_paths is None:
        return "UNKNOWN"
    return "PRESENT" if len(candidate_paths) > 0 else "NOT_PRESENT"


def build_presence_record(node_id, candidate_paths, now_utc):
    """Build a read-only advisory presence record for an external Pico node."""
    status = classify_presence(candidate_paths)
    return {
        "schema": PRESENCE_SCHEMA,
        "node_id": node_id,
        "authority": "ZERO",
        "lane": "Lane 2 advisory",
        "non_authoritative": True,
        "status": status,
        "candidate_paths": list(candidate_paths or []),
        "created_at_utc": now_utc,
    }


def intake_sample(node_id, sample, now_utc):
    """Wrap one raw Pico sensor sample as a non-authoritative advisory record.

    Raises ValueError if the raw sample carries a verdict-shaped key or a
    verdict-token value. The intake boundary refuses to forward authority
    claims from an external microcontroller — sensor data crosses into PH6
    as data, never as a ruling.
    """
    bad_keys = _FORBIDDEN_KEY_NAMES & {k.lower() for k in sample.keys()}
    if bad_keys:
        raise ValueError(f"raw sample carries verdict-shaped keys: {sorted(bad_keys)}")
    for key, value in sample.items():
        if isinstance(value, str) and value.upper() in _FORBIDDEN_VERDICT_TOKENS:
            raise ValueError(
                f"raw sample field {key!r}={value!r} looks like a verdict token; "
                "rejected at the advisory intake boundary"
            )
    return {
        "schema": INTAKE_SCHEMA,
        "node_id": node_id,
        "authority": "ZERO",
        "lane": "Lane 2 advisory",
        "non_authoritative": True,
        "source": "external_microcontroller_test_node",
        "sample": dict(sample),
        "created_at_utc": now_utc,
    }
