"""Pi Zero 2 W sentinel advisory outputs: heartbeat packets and health snapshots.

Authority ZERO. Lane 2 sentinel. Every record produced here is advisory-only —
it never carries a verdict, never reaches CRAM-A, and never escalates to
authority. See PH6_SOURCE/DEPLOYMENT/PH6_HARDWARE_EXPANSION_SCOPE_20260608.md.
"""

HEARTBEAT_SCHEMA = "ph6.hw_hooks.pizero_heartbeat.v1"
HEALTH_SNAPSHOT_SCHEMA = "ph6.hw_hooks.pizero_health_snapshot.v1"

ADVISORY_STATUS_VALUES = frozenset(
    {"UNVERIFIED", "NOT_READY", "NOT_PRESENT", "DEVICE_BUSY", "UNKNOWN", "PRESENT"}
)


def build_heartbeat(node_id, hostname, uptime, temp_millic, now_utc):
    """Assemble an advisory heartbeat packet. Pure data assembly — no hardware access, no verdicts."""
    return {
        "schema": HEARTBEAT_SCHEMA,
        "node_id": node_id,
        "hostname": hostname,
        "authority": "ZERO",
        "lane": "Lane 2 sentinel",
        "non_authoritative": True,
        "created_at_utc": now_utc,
        "uptime": uptime,
        "temp_millic": temp_millic,
    }


def build_health_snapshot(node_id, status, metrics, now_utc):
    """Assemble a point-in-time advisory health snapshot.

    `status` must come from the locked advisory vocabulary — PASS/DROP are not
    members of it and are rejected here, the same way ph6_cram_sim refuses
    forbidden motion fields before they can reach a gate.
    """
    if status not in ADVISORY_STATUS_VALUES:
        raise ValueError(
            f"status must be one of {sorted(ADVISORY_STATUS_VALUES)}, got {status!r}"
        )
    return {
        "schema": HEALTH_SNAPSHOT_SCHEMA,
        "node_id": node_id,
        "authority": "ZERO",
        "lane": "Lane 2 sentinel",
        "non_authoritative": True,
        "status": status,
        "metrics": dict(metrics),
        "created_at_utc": now_utc,
    }
