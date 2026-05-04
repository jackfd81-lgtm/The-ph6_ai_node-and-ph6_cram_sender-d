#!/usr/bin/env bash
# Run CRAM-PU receiver node in the foreground.
# Port 8765. Stop with Ctrl-C.
set -e

cd "$(dirname "$0")"
echo "Starting CRAM-PU on http://0.0.0.0:8765"
exec python3 cram_pu_server.py
