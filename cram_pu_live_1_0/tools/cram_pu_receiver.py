#!/usr/bin/env python3
import argparse, shutil
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
from ph6_common import read_jsonl, append_jsonl, file_hash, now_utc

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--departure-log", required=True)
    ap.add_argument("--arrival-dir", required=True)
    ap.add_argument("--arrival-log", required=True)
    args = ap.parse_args()
    arrival_dir = Path(args.arrival_dir)
    arrival_dir.mkdir(parents=True, exist_ok=True)
    packets = read_jsonl(args.departure_log)
    for idx, pkt in enumerate(packets, start=1):
        src = Path(pkt["payload_path"])
        dst = arrival_dir / f'{pkt["packet_id"]}.bin'
        shutil.copy2(src, dst)
        received_hash = file_hash(dst)
        arrival = {
            "schema": "ph6.cram_pu.arrival.v1",
            "packet_id": pkt["packet_id"],
            "source_node_id": pkt["source_node_id"],
            "departure_seq": pkt["departure_seq"],
            "arrival_seq": idx,
            "arrival_timestamp": now_utc(),
            "departure_hash": pkt["payload_hash"],
            "received_hash": received_hash,
            "payload_path": str(dst),
            "size_bytes": dst.stat().st_size,
            "transfer_status": "OK" if received_hash == pkt["payload_hash"] else "HASH_MISMATCH"
        }
        append_jsonl(args.arrival_log, arrival)
    print(f"arrivals={len(packets)}")

if __name__ == "__main__":
    main()
