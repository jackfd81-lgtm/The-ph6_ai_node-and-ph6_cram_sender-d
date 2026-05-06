#!/usr/bin/env python3
import argparse, shutil, uuid
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
from ph6_common import file_hash, append_jsonl, now_utc

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--payload", required=True)
    ap.add_argument("--source-node-id", default="source-pi")
    ap.add_argument("--seq", type=int, required=True)
    ap.add_argument("--media-type", default="test")
    ap.add_argument("--outbox", required=True)
    ap.add_argument("--departure-log", required=True)
    args = ap.parse_args()
    payload = Path(args.payload)
    if not payload.exists():
        raise SystemExit(f"missing payload: {payload}")
    packet_id = f"pkt-{args.seq:06d}-{uuid.uuid4().hex[:12]}"
    h = file_hash(payload)
    outbox = Path(args.outbox)
    outbox.mkdir(parents=True, exist_ok=True)
    copied_payload = outbox / f"{packet_id}.bin"
    shutil.copy2(payload, copied_payload)
    packet = {
        "schema": "ph6.cram_pu.packet.v1",
        "packet_id": packet_id,
        "source_node_id": args.source_node_id,
        "departure_seq": args.seq,
        "departure_timestamp": now_utc(),
        "payload_hash": h,
        "media_type": args.media_type,
        "size_bytes": copied_payload.stat().st_size,
        "payload_path": str(copied_payload)
    }
    append_jsonl(args.departure_log, packet)
    print(packet_id)

if __name__ == "__main__":
    main()
