"""Bounded capture-side hints. No token store, disk I/O, retry or response path.

PROPOSED codex-lane2, 2026-09-22; Authority ZERO; ratified_by=None.
"""
import errno
import json
import os
import re
import socket
from pathlib import Path

SCHEMA = 'ph6.tok.handoff.v1'
MAX_MESSAGE = 4096
SOCKET_PATH = os.path.join(os.environ.get('XDG_RUNTIME_DIR', f'/run/user/{os.getuid()}'),
                           'ph6-advisory/input.sock')


def decode_handoff(payload):
    if len(payload) > MAX_MESSAGE:
        raise ValueError('Oversized token hint')
    obj = json.loads(payload)
    if not isinstance(obj, dict) or set(obj) != {'schema', 'cram_ref', 'payload_hash', 'frame_id'}:
        raise ValueError('Invalid token hint fields')
    if obj['schema'] != SCHEMA:
        raise ValueError('Unsupported token hint schema')
    if not isinstance(obj['cram_ref'], str) or not 0 < len(obj['cram_ref']) <= 1024:
        raise ValueError('Invalid CRAM reference')
    if not isinstance(obj['payload_hash'], str) or not re.fullmatch('[0-9a-f]{64}', obj['payload_hash']):
        raise ValueError('Invalid payload hash')
    if type(obj['frame_id']) is not int or not 0 < obj['frame_id'] < 10**10:
        raise ValueError('Invalid frame ID')
    return obj


class TokenHandoff:
    """Admission accounting is not completion accounting.

    Counters are memory-only; capture may save them in its end-of-run report.
    A crash may lose those counters. Recovery must use configured CRAM stores,
    including records for which no notification or attempt counter survived.
    """
    def __init__(self, cram_store, enabled=True, socket_path=SOCKET_PATH):
        # absolute() is lexical: do not resolve or inspect CRAM/advisory files here.
        self.cram_store = Path(cram_store).absolute()
        self.enabled = enabled
        self.socket_path = str(socket_path)
        self.counts = dict.fromkeys(('ADMITTED', 'SHED', 'FAILED', 'BYPASSED'), 0)
        self.last_outcome = None

    def on_pass(self, frame_id, cram_ref_hash):
        outcome = 'BYPASSED'
        if self.enabled:
            try:
                # Bound caller-controlled fields before allocating a JSON payload.
                if type(frame_id) is not int or not 0 < frame_id < 10**10:
                    raise ValueError('Invalid frame ID')
                if not isinstance(cram_ref_hash, str) or not re.fullmatch('[0-9a-f]{64}', cram_ref_hash):
                    raise ValueError('Invalid payload hash')
                ref = str(self.cram_store / f'cram_{frame_id:010d}.json')
                if len(ref) > 1024:
                    raise ValueError('Oversized CRAM reference')
                payload = json.dumps({'schema': SCHEMA, 'cram_ref': ref,
                                      'payload_hash': cram_ref_hash, 'frame_id': frame_id},
                                     separators=(',', ':')).encode()
                if len(payload) > MAX_MESSAGE:
                    raise ValueError('Oversized token hint')
                with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as client:
                    client.setblocking(False)
                    sent = client.sendto(payload, self.socket_path)
                outcome = 'ADMITTED' if sent == len(payload) else 'FAILED'
            except OSError as error:
                outcome = ('SHED' if error.errno in (errno.EAGAIN, errno.EWOULDBLOCK,
                                                    errno.ENOBUFS) else 'FAILED')
            except Exception:
                # Observable through accounting; no disk or blocking logger here.
                outcome = 'FAILED'
        self.counts[outcome] += 1
        self.last_outcome = outcome
        return outcome

    def rt_count(self):
        # No query/ack path: the capture process cannot know worker completion.
        return None

    def accounting(self):
        return {'schema': 'ph6.tok.handoff_accounting.v1', 'authority': 'ZERO',
                'advisory_only': True, 'attempts': sum(self.counts.values()),
                'outcomes': dict(self.counts), 'token_completion': 'UNKNOWN',
                'scope': 'PROCESS_LIFETIME_COUNTERS'}
