"""
CRAM-PU Lane-1 transfer sender.

Runs on the RAW Pi. Reads departure records, encodes payloads as base64,
POSTs each to the CRAM-PU receiver, and returns the arrival acknowledgment.

stdlib only — no external dependencies required on the RAW Pi.

Lane: LANE_1 boundary (departure authority=NONE; transfer is Lane-5 export)
"""

from __future__ import annotations

import base64
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent))

from ph6.cram_pu.departure_logger import DepartureLogger

DEFAULT_RECEIVER_URL = "http://127.0.0.1:9100"


class TransferSender:
    """
    Send departure records + payloads to the CRAM-PU receiver.
    Each send() call is synchronous — caller knows the packet was
    acknowledged (and arrival-logged with fsync) before returning.
    """

    def __init__(self, departure_log: Path,
                 receiver_url: str = DEFAULT_RECEIVER_URL,
                 timeout: float = 10.0):
        self.departure_logger = DepartureLogger(departure_log)
        self.receiver_url     = receiver_url.rstrip("/")
        self.timeout          = timeout
        self.stats            = {"sent": 0, "ok": 0, "errors": 0, "hash_mismatches": 0}

    def send(self, frame_id: int, payload: bytes,
             media_type: str = "FRAME") -> dict:
        """
        Write departure record, then POST to receiver.
        Returns the receiver's arrival acknowledgment.
        Raises TransferError if the network call fails.
        """
        dep = self.departure_logger.log(frame_id, payload, media_type)

        body = json.dumps({
            "schema":              "ph6.raw_departure.v1",
            "frame_id":            frame_id,
            "payload_hash":        dep["payload_hash"],
            "hash_algorithm":      "BLAKE2b-256",
            "media_type":          media_type,
            "size_bytes":          len(payload),
            "departure_timestamp": dep["departure_timestamp"],
            "payload_b64":         base64.b64encode(payload).decode(),
        }, separators=(",", ":"), ensure_ascii=False).encode()

        req = urllib.request.Request(
            f"{self.receiver_url}/receive_packet",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        self.stats["sent"] += 1
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                ack = json.loads(resp.read())
        except urllib.error.URLError as e:
            self.stats["errors"] += 1
            raise TransferError(frame_id, str(e)) from e

        if ack.get("status") == "HASH_MISMATCH":
            self.stats["hash_mismatches"] += 1
        else:
            self.stats["ok"] += 1

        return {**dep, "ack": ack}


class TransferError(RuntimeError):
    def __init__(self, frame_id: int, reason: str):
        super().__init__(f"transfer failed frame_id={frame_id}: {reason}")
        self.frame_id = frame_id
        self.reason   = reason


def check_receiver_health(receiver_url: str = DEFAULT_RECEIVER_URL,
                          timeout: float = 3.0) -> bool:
    try:
        req = urllib.request.Request(f"{receiver_url}/health", method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read())
        return data.get("lane") == "LANE_1"
    except Exception:
        return False
