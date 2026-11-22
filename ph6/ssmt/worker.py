"""Caged process consuming bounded, one-way advisory notifications.
No retention deletion and no Lane-1 imports. PROPOSED codex-lane2 2026-09-19.
"""
import argparse
import json
import logging
import os
import re
import signal
import socket
import time
from pathlib import Path
from .async_client import MAX_MESSAGE, SOCKET_PATH
from .models import SwarmInput
from .scheduler import SwarmScheduler
from .audit_writer import AdvisoryAuditWriter
from .replay_validator import ReplayValidator


def decode_reference(payload):
    obj = json.loads(payload)
    if not isinstance(obj, dict) or set(obj) != {'cram_ref', 'cram_packet_hash', 'tok_refs'}:
        raise ValueError('Invalid advisory reference fields')
    if not isinstance(obj['cram_ref'], str) or not 0 < len(obj['cram_ref']) <= 1024:
        raise ValueError('Invalid reference')
    if not isinstance(obj['cram_packet_hash'], str) or not re.fullmatch('[0-9a-f]{64}', obj['cram_packet_hash']):
        raise ValueError('Invalid reference hash')
    if not isinstance(obj['tok_refs'], list) or len(obj['tok_refs']) > 16:
        raise ValueError('Invalid token references')
    if any(not isinstance(ref, str) or len(ref) > 256 for ref in obj['tok_refs']):
        raise ValueError('Invalid token reference')
    return obj


def process_reference(obj, scheduler, writer):
    packets = scheduler.run_cycle(SwarmInput(cram_refs=[obj['cram_ref']],
        tok_refs=obj['tok_refs'], advisory_refs=[], cram_packet_hash=obj['cram_packet_hash']))
    if not ReplayValidator().validate_all(packets):
        raise ValueError('Advisory packet boundary violation')
    for packet in packets:
        writer.write_packet(packet)
    return len(packets)


def require_resource_limits(cgroup_root=Path('/sys/fs/cgroup'), membership=None):
    """Refuse startup when systemd settings have no kernel enforcement."""
    membership = membership or Path('/proc/self/cgroup').read_text()
    group = next((line[3:] for line in membership.splitlines() if line.startswith('0::')), None)
    if group is None:
        raise RuntimeError('Unified resource controls are required')
    root = cgroup_root / group.lstrip('/')
    try:
        quota, period = (root / 'cpu.max').read_text().split()
        memory = (root / 'memory.max').read_text().strip()
        swap = (root / 'memory.swap.max').read_text().strip()
        if quota == 'max' or memory == 'max':
            raise ValueError('Unbounded resource limit')
        if not (0 < int(quota) / int(period) <= .30 and 0 < int(memory) <= 512000000 and swap == '0'):
            raise ValueError('Resource limit exceeds advisory budget')
    except (OSError, ValueError) as error:
        raise RuntimeError('Advisory worker requires enforced CPU<=30%, memory<=512MB, swap=0; inspect kernel memory controller') from error


def serve(socket_path=SOCKET_PATH, root='/var/ph6/mram-s/swarms/async-v1/',
          cram_stores=(), reconciliation_batch=8):
    scheduler, writer = SwarmScheduler(), AdvisoryAuditWriter(root)
    reconciler = None
    if cram_stores:
        from ph6.tok.reconciliation import CRAMReconciler
        reconciler = CRAMReconciler(Path(root) / 'continuity-v03', cram_stores)
    path = Path(socket_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    # systemd owns a private RuntimeDirectory and serializes service instances.
    if path.exists():
        path.unlink()
    running = True
    def stop(*_):
        nonlocal running
        running = False
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 65536)
        server.bind(str(path))
        os.chmod(path, 0o600)
        server.settimeout(.5)
        try:
            next_scan = 0.0
            while running:
                # Discovery is independent of delivery, including startup with
                # an empty socket queue. CRAM stores are operator-configured.
                if reconciler is not None and time.monotonic() >= next_scan:
                    reconciler.reconcile_once(reconciliation_batch)
                    next_scan = time.monotonic() + .5
                try:
                    payload = server.recv(MAX_MESSAGE + 1)
                    if len(payload) > MAX_MESSAGE:
                        raise ValueError('Oversized advisory message')
                    obj = json.loads(payload)
                    if isinstance(obj, dict) and obj.get('schema') == 'ph6.tok.handoff.v1':
                        from ph6.tok.handoff import decode_handoff
                        if reconciler is None:
                            raise ValueError('Token recovery requires explicit --cram-store configuration')
                        reconciler.note_notification(decode_handoff(payload))
                    else:
                        process_reference(decode_reference(payload), scheduler, writer)
                except socket.timeout:
                    continue
                except (ValueError, TypeError, KeyError) as error:
                    logging.warning('Invalid advisory input: %s', error)
                # Persistence/checkpoint errors stop this worker; never erase history.
        finally:
            path.unlink(missing_ok=True)
            if reconciler is not None:
                reconciler.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--require-limits', action='store_true')
    parser.add_argument('--socket', default=SOCKET_PATH)
    parser.add_argument('--root', default='/var/ph6/mram-s/swarms/async-v1/')
    parser.add_argument('--cram-store', action='append', default=[],
                        help='Read-only CRAM store to reconcile; repeat for multiple stores')
    parser.add_argument('--reconciliation-batch', type=int, default=8)
    args = parser.parse_args()
    if args.require_limits:
        require_resource_limits()
    if args.reconciliation_batch <= 0:
        parser.error('--reconciliation-batch must be positive')
    serve(args.socket, args.root, args.cram_store, args.reconciliation_batch)
