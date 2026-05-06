"""
CRAM-PU Lane-1 transfer receiver.

Runs on the CRAM-PU Pi. Receives packets sent by the RAW Pi, verifies
payload hash, writes arrival records (fsync before response), and
acknowledges. Hash mismatch is logged as HASH_MISMATCH — not silently dropped.

Usage (standalone CRAM-PU Pi):
    python3 transfer_receiver.py --cram-store /var/ph6/cram-0 --port 9100

Usage (loopback test — called by run_two_pi_transfer_test.py):
    Instantiate TransferReceiver directly.

Lane: LANE_1
Authority: LANE_1 on arrival records
Port: 9100 (default); must not share with Lane-2 advisory port 8000
"""

from __future__ import annotations

import base64
import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent))

from ph6.cram_pu.arrival_logger import ArrivalLogger


class _PacketHandler(BaseHTTPRequestHandler):
    """Single-endpoint handler: POST /receive_packet"""

    # Injected by TransferReceiver
    arrival_logger: ArrivalLogger = None
    stats: dict = None

    def log_message(self, fmt, *args):
        pass  # suppress default access log

    def do_POST(self):
        if self.path != "/receive_packet":
            self._respond(404, {"error": "not_found"})
            return

        length = int(self.headers.get("Content-Length", 0))
        body   = self.rfile.read(length)
        try:
            req = json.loads(body)
        except Exception as e:
            self._respond(400, {"error": f"bad_json: {e}"})
            return

        frame_id     = req.get("frame_id")
        payload_b64  = req.get("payload_b64", "")
        payload_hash = req.get("payload_hash", "")

        if frame_id is None or not payload_b64 or not payload_hash:
            self._respond(400, {"error": "missing_fields"})
            return

        try:
            payload = base64.b64decode(payload_b64)
        except Exception as e:
            self._respond(400, {"error": f"bad_payload_b64: {e}"})
            return

        # Write arrival record — fsync before responding
        arr = self.arrival_logger.log(
            frame_id=frame_id,
            payload=payload,
            expected_hash=payload_hash,
        )

        self.stats["received"] += 1
        if arr["transfer_status"] == "HASH_MISMATCH":
            self.stats["hash_mismatches"] += 1

        self._respond(200, {
            "status":          arr["transfer_status"],
            "frame_id":        frame_id,
            "arrival_hash":    arr["payload_hash"],
            "authority":       arr["authority"],
        })

    def _respond(self, code: int, body: dict) -> None:
        data = json.dumps(body, separators=(",", ":"), ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/health":
            self._respond(200, {
                "node":      "CRAM_PU_TRANSFER_RECEIVER",
                "lane":      "LANE_1",
                "authority": "LANE_1",
                "status":    "OK",
            })
        else:
            self._respond(404, {"error": "not_found"})


class TransferReceiver:
    """
    Manages a Lane-1 HTTP receiver for incoming CRAM-PU packets.
    Runs in a background thread; call start() / stop().
    """

    def __init__(self, arrival_log: Path, host: str = "127.0.0.1",
                 port: int = 9100):
        self.host    = host
        self.port    = port
        self.stats   = {"received": 0, "hash_mismatches": 0}

        logger = ArrivalLogger(arrival_log)

        class _Handler(_PacketHandler):
            pass
        _Handler.arrival_logger = logger
        _Handler.stats          = self.stats

        self._server  = HTTPServer((host, port), _Handler)
        self._thread  = threading.Thread(target=self._serve, daemon=True)

    def _serve(self):
        self._server.serve_forever()

    def start(self):
        self._thread.start()

    def stop(self):
        self._server.shutdown()
        self._thread.join(timeout=5)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--cram-store", type=Path, required=True)
    ap.add_argument("--host",       default="0.0.0.0")
    ap.add_argument("--port",       type=int, default=9100)
    args = ap.parse_args()

    arrival_log = args.cram_store / "arrival_log.jsonl"
    arrival_log.parent.mkdir(parents=True, exist_ok=True)

    r = TransferReceiver(arrival_log, host=args.host, port=args.port)
    r.start()
    print(f"CRAM-PU transfer receiver listening on {args.host}:{args.port}")
    print(f"Arrival log: {arrival_log}")
    print("Press Ctrl-C to stop.")
    try:
        r._thread.join()
    except KeyboardInterrupt:
        r.stop()
        print(f"\nReceived: {r.stats}")
