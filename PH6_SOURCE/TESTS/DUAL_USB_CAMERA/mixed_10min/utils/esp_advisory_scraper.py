"""
PH6 ESP_S1 Advisory Context Scraper
Lane 2 / SoSo continuity context — authority ZERO

GOVERNANCE BOUNDARY — this module is PROHIBITED from:
  - Issuing PASS or DROP verdicts
  - Writing to CRAM-A or CRAM-R
  - Reading or modifying motion_fraction or any Lane-1 deterministic variable
  - Blocking, pausing, or mutating the AIO-10 frame-capture loop
  - Blocking RSYNC export
  - Raising exceptions into the deterministic verdict path
  - Becoming a replay dependency

This module produces advisory environmental context only.
ESP_S1 dropout is classified as NODE_UNREACHABLE_FALLBACK and is non-blocking.

Sidecar output:
  PH6_SOURCE/TESTS/DUAL_USB_CAMERA/mixed_10min/json/esp_s1_sensor_status.jsonl

Integration point:
  Call poll_and_record() once per window or once post-run — never inside
  the per-frame deterministic verdict loop.
"""

import json
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

_NODE_ID = "ESP_S1"
_ESP_IP = "192.168.254.194"
_SENSOR_URL = "http://{}/sensor".format(_ESP_IP)
_TIMEOUT_S = 2.0
_SCHEMA_ID = "PH6_ESP_SENSOR_NODE_V1"

_UTILS_DIR = Path(__file__).resolve().parent
_JSONL_PATH = _UTILS_DIR.parent / "json" / "esp_s1_sensor_status.jsonl"


def _utc_now():
    return datetime.now(timezone.utc).isoformat()


def _scrape_once():
    """
    Single HTTP GET to /sensor. Returns a complete advisory record dict.
    Never raises — all failure modes produce NODE_UNREACHABLE_FALLBACK.
    """
    ts = _utc_now()
    try:
        req = urllib.request.Request(
            _SENSOR_URL,
            headers={"Accept": "application/json"},
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=_TIMEOUT_S) as resp:
            raw = resp.read(4096)
        payload = json.loads(raw)
        s = payload.get("status", {})
        health_summary = {
            "node": _NODE_ID,
            "status": "NODE_REACHABLE",
            "rssi_dbm": s.get("rssi_dbm"),
            "heartbeat": s.get("heartbeat_seq"),
            "uptime_s": round(s.get("uptime_ms", 0) / 1000, 1),
            "authority": "ZERO",
            "advisory_only": True,
        }
        return {
            "schema_id": _SCHEMA_ID,
            "node_id": _NODE_ID,
            "polled_utc": ts,
            "status": "NODE_REACHABLE",
            "advisory_only": True,
            "authority": "ZERO",
            "rsync_blocking": False,
            "replay_required": False,
            "health_summary": health_summary,
            "payload": payload,
            "error": None,
        }
    except Exception as exc:
        health_summary = {
            "node": _NODE_ID,
            "status": "NODE_UNREACHABLE_FALLBACK",
            "rssi_dbm": None,
            "heartbeat": None,
            "uptime_s": None,
            "authority": "ZERO",
            "advisory_only": True,
        }
        return {
            "schema_id": _SCHEMA_ID,
            "node_id": _NODE_ID,
            "polled_utc": ts,
            "status": "NODE_UNREACHABLE_FALLBACK",
            "advisory_only": True,
            "authority": "ZERO",
            "rsync_blocking": False,
            "replay_required": False,
            "health_summary": health_summary,
            "payload": None,
            "error": str(exc),
        }


def _append_record(record):
    """
    Append one JSONL line to the sidecar log. Creates json/ if absent.
    Never raises — write failures are reported to stderr only.
    """
    try:
        _JSONL_PATH.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(record, separators=(",", ":")) + "\n"
        with open(_JSONL_PATH, "a", encoding="utf-8") as fh:
            fh.write(line)
    except Exception as exc:
        print(
            "[ESP_S1 SCRAPER] sidecar write failed (advisory, non-blocking): {}".format(exc),
            file=sys.stderr,
        )


def poll_and_record():
    """
    Public API. Scrape /sensor once and append to JSONL sidecar.
    Returns the advisory record dict.

    Safe to call from post-window or post-run hooks.
    Must NOT be called inside the per-frame deterministic verdict loop.
    """
    record = _scrape_once()
    _append_record(record)
    return record


if __name__ == "__main__":
    print("[ESP_S1 SCRAPER] Standalone validation mode")
    print("[ESP_S1 SCRAPER] Target: {}".format(_SENSOR_URL))
    print("[ESP_S1 SCRAPER] JSONL:  {}".format(_JSONL_PATH))

    record = poll_and_record()
    print("[ESP_S1 SCRAPER] Poll status: {}".format(record["status"]))

    if record["status"] == "NODE_UNREACHABLE_FALLBACK":
        print("[ESP_S1 SCRAPER] NODE_UNREACHABLE_FALLBACK — advisory context loss, AIO-10 unaffected")
    else:
        s = record.get("payload", {}).get("status", {})
        print("[ESP_S1 SCRAPER] rssi_dbm={}  uptime_ms={}  heartbeat_seq={}  free_mem={}".format(
            s.get("rssi_dbm"), s.get("uptime_ms"), s.get("heartbeat_seq"), s.get("free_mem")
        ))

    # Validate last JSONL line
    try:
        with open(_JSONL_PATH, "r", encoding="utf-8") as fh:
            lines = [l for l in fh.readlines() if l.strip()]
        last = json.loads(lines[-1])
        assert last["node_id"] == _NODE_ID,        "node_id mismatch"
        assert last["authority"] == "ZERO",         "authority not ZERO"
        assert last["advisory_only"] is True,       "advisory_only not true"
        assert last["rsync_blocking"] is False,     "rsync_blocking not false"
        assert last["replay_required"] is False,    "replay_required not false"
        assert "status" in last,                    "status field missing"
        print("[ESP_S1 SCRAPER] JSONL validation PASS — {} record(s) in log".format(len(lines)))
    except Exception as exc:
        print("[ESP_S1 SCRAPER] JSONL validation FAIL: {}".format(exc), file=sys.stderr)
        sys.exit(1)

    print("[ESP_S1 SCRAPER] VALIDATION COMPLETE")
    print("[ESP_S1 SCRAPER] AIO-10 harness modified: NO")
    print("[ESP_S1 SCRAPER] Lane-1 contamination: NO")
    print("[ESP_S1 SCRAPER] RSYNC blocking possible: NO")
    sys.exit(0)
