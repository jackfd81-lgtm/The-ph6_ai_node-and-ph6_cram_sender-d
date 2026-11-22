"""Nonblocking best-effort advisory notifications. No response path.
PROPOSED: codex-lane2, 2026-09-19; ratified_by=None.
"""
import json
import os
import socket

SOCKET_PATH = os.path.join(os.environ.get('XDG_RUNTIME_DIR', f'/run/user/{os.getuid()}'), 'ph6-advisory/input.sock')
MAX_MESSAGE = 4096


def submit_reference(cram_ref, cram_packet_hash, tok_refs=(), socket_path=SOCKET_PATH):
    try:
        payload = json.dumps({'cram_ref': cram_ref, 'cram_packet_hash': cram_packet_hash,
                              'tok_refs': list(tok_refs)}, allow_nan=False).encode()
        if len(payload) > MAX_MESSAGE:
            return False
        with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as client:
            client.setblocking(False)
            return client.sendto(payload, socket_path) == len(payload)
    except (OSError, ValueError, TypeError):
        return False
