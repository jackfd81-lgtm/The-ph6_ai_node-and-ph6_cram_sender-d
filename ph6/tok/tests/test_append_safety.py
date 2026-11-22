"""Adversarial checks for verified, serialized Lane-2 appends."""
import json
import multiprocessing
from concurrent.futures import ThreadPoolExecutor
import pytest
from ph6.tok.lifecycle import AdvisoryAudit
from ph6.advisory_chain import AuditIntegrityError, digest, anchor_existing
from ph6.tok.reconstruct import validate_chain_integrity


def seed(path):
    writer = AdvisoryAudit(path)
    for i in range(3):
        writer.emit('RT_GENESIS', {'token_id': str(i)}, i + 1)
    return writer


@pytest.mark.parametrize('attack', ['payload', 'reorder', 'rehash', 'truncate', 'malformed'])
def test_bad_history_cannot_be_extended(tmp_path, attack):
    path = tmp_path / 'audit.jsonl'
    seed(path)
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    if attack == 'payload':
        rows[0]['payload']['token_id'] = 'tampered'
    elif attack in ('reorder', 'rehash'):
        rows.reverse()
    elif attack == 'truncate':
        rows.pop()
    if attack == 'rehash':
        prev = 'GENESIS'
        for row in rows:
            row.pop('event_hash')
            row['prev_event_hash'] = prev
            row['event_hash'] = digest(row)
            prev = row['event_hash']
    path.write_text(''.join(json.dumps(row) + '\n' for row in rows))
    if attack == 'malformed':
        with path.open('a') as stream:
            stream.write('{broken\n')
    before = path.read_bytes()
    with pytest.raises(AuditIntegrityError):
        AdvisoryAudit(path).emit('RT_GENESIS', {'token_id': 'child'}, 9)
    assert path.read_bytes() == before


def test_stale_writer_refreshes_tip(tmp_path):
    path = tmp_path / 'audit.jsonl'
    first = seed(path)
    second = AdvisoryAudit(path)
    a = first.emit('RT_GENESIS', {'token_id': 'a'}, 4)
    b = second.emit('RT_GENESIS', {'token_id': 'b'}, 5)
    assert b['prev_event_hash'] == a['event_hash']
    assert validate_chain_integrity(path)[:2] == (True, 5)


def emit_many(path):
    writer = AdvisoryAudit(path)
    for i in range(8):
        writer.emit('RT_GENESIS', {'token_id': str(i)}, i)


def test_multiprocess_writers_serialize(tmp_path):
    path = tmp_path / 'audit.jsonl'
    context = multiprocessing.get_context('fork')
    children = [context.Process(target=emit_many, args=(path,)) for _ in range(4)]
    for child in children:
        child.start()
    for child in children:
        child.join(15)
        assert child.exitcode == 0
    assert validate_chain_integrity(path)[:2] == (True, 32)


def test_existing_log_requires_explicit_checkpoint(tmp_path):
    path = tmp_path / 'audit.jsonl'
    seed(path)
    checkpoint = tmp_path / 'audit.jsonl.checkpoint.json'
    trusted = json.loads(checkpoint.read_text())
    checkpoint.unlink()
    with pytest.raises(AuditIntegrityError):
        AdvisoryAudit(path).emit('RT_GENESIS', {})
    anchor_existing(path, 'GENESIS', trusted['count'], trusted['tail'])
    AdvisoryAudit(path).emit('RT_GENESIS', {})
    assert validate_chain_integrity(path)[:2] == (True, 4)


def test_interrupted_checkpoint_update_stops_next_append(tmp_path, monkeypatch):
    import ph6.advisory_chain as chain
    path = tmp_path / 'audit.jsonl'
    writer = seed(path)
    original = chain.durable_json
    def fail(*args):
        raise OSError('simulated checkpoint disk error')
    monkeypatch.setattr(chain, 'durable_json', fail)
    with pytest.raises(OSError):
        writer.emit('RT_GENESIS', {})
    monkeypatch.setattr(chain, 'durable_json', original)
    with pytest.raises(AuditIntegrityError):
        writer.emit('RT_GENESIS', {})
