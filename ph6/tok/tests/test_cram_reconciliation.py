"""v0.3 boundary/recovery regressions. Authority ZERO; ratified_by=None."""
import hashlib
import json
import multiprocessing
import os
import signal
import socket
import time
from pathlib import Path

import pytest

from ph6.cram_pu.cram_pu_live import _TokSidecar, _write_payload_bin
from ph6.cram_pu.crash_replay import CRAMWriter
from ph6.cram_pu.verdict_logger import VerdictLogger
from ph6.cram_pu._lane1_auth import mint_commit_authorization
from ph6.advisory_chain import AuditIntegrityError, read_checked
from ph6.tok.handoff import TokenHandoff, decode_handoff
from ph6.tok.reconciliation import CRAMReconciler

def test_capture_sidecar_does_not_create_persistent_advisory_state(tmp_path):
    root = tmp_path / "run" / "mram_s" / "swarms"
    sidecar = _TokSidecar(root, enabled=True, socket_path=str(tmp_path/'missing.sock'))
    sidecar.on_pass(1, "a" * 64)
    assert not root.exists(), "Capture must not open or persist advisory token state"
    assert sidecar.accounting()['outcomes']['FAILED'] == 1
    assert sidecar.rt_count() is None


def make_store(root, count=3, repeated_payload=False):
    store = root / 'cram_store'
    writer = CRAMWriter(store)
    logger = VerdictLogger(store / 'verdict_log.jsonl')
    commits = []
    for i in range(1, count + 1):
        seed = 1 if repeated_payload else i
        payload = bytes([(seed * 37 + j * 13) % 180 + 25 for j in range(300)])
        h = hashlib.blake2b(payload, digest_size=32).hexdigest()
        _write_payload_bin(store / 'payloads', i, payload)
        verdict = logger.log(i, payload, h)
        assert verdict['verdict'] == 'PASS'
        auth = mint_commit_authorization(frame_id=i, payload_hash=h, verdict='PASS')
        commits.append(writer.commit(i, h, verdict, auth))
    return store, commits


def hashes(root):
    return {str(p.relative_to(root)): hashlib.blake2b(p.read_bytes(), digest_size=32).hexdigest()
            for p in root.rglob('*') if p.is_file()}


def audit_count(root):
    return read_checked(root/'tokens/tok_advisory_audit.jsonl', 'GENESIS')[0]


def test_missing_and_full_queues_are_bounded_and_accounted(tmp_path):
    # AF_UNIX paths have a platform length limit independent of MAX_MESSAGE.
    name = '/tmp/ph6-v03-test-' + str(__import__('os').getpid()) + '.sock'
    with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as server:
        server.bind(name)
        try:
            sender = TokenHandoff(tmp_path/'cram_store', socket_path=name)
            count = int(Path('/proc/sys/net/unix/max_dgram_qlen').read_text()) + 4
            start = time.monotonic()
            outcomes = [sender.on_pass(i+1, 'a'*64) for i in range(count)]
            assert time.monotonic() - start < 1.0
            assert 'ADMITTED' in outcomes and 'SHED' in outcomes
            assert sender.accounting()['attempts'] == count
            assert sender.rt_count() is None
            hint = decode_handoff(server.recv(4096))
            assert hint['frame_id'] == 1
        finally:
            Path(name).unlink()


@pytest.mark.parametrize('frame,ref', [(True,'a'*64), (0,'a'*64), (1,'x'*100000), (10**10,'a'*64)])
def test_bad_hints_fail_before_delivery(tmp_path, frame, ref):
    sender = TokenHandoff(tmp_path, socket_path='/not/a/socket')
    assert sender.on_pass(frame, ref) == 'FAILED'
    assert not list(tmp_path.iterdir())


def test_bypass_is_not_reported_as_token_completion(tmp_path):
    sender = TokenHandoff(tmp_path, enabled=False)
    assert sender.on_pass(1, 'a'*64) == 'BYPASSED'
    assert sender.accounting()['token_completion'] == 'UNKNOWN'


def test_no_notification_recovery_is_idempotent_and_read_only(tmp_path):
    store, commits = make_store(tmp_path/'input')
    before = hashes(store)
    root = tmp_path/'advisory'
    with CRAMReconciler(root, [store]) as worker:
        first = worker.reconcile_once()
        assert first['notifications_admitted'] == 0
        assert first['token_count'] == 3
        assert first['stores'][str(store)]['unresolved'] == []
        assert first['stores'][str(store)]['contiguous_watermark']['cram_hash'] == commits[-1]['cram_hash']
        assert worker.reconcile_once()['processed_this_scan'] == 0
    with CRAMReconciler(root, [store]) as worker:
        assert worker.reconcile_once()['processed_this_scan'] == 0
    assert audit_count(root) == 3
    assert hashes(store) == before
    assert len(list((root/'snapshots').glob('*.json'))) == 3


def test_batch_cursor_does_not_skip_unfinished_lower_records(tmp_path):
    store, commits = make_store(tmp_path/'input')
    with CRAMReconciler(tmp_path/'advisory', [store]) as worker:
        first = worker.reconcile_once(max_records=1)['stores'][str(store)]
        assert first['contiguous_watermark']['cram_hash'] == commits[0]['cram_hash']
        assert len(first['unresolved']) == 2
        second = worker.reconcile_once(max_records=1)['stores'][str(store)]
        assert second['contiguous_watermark']['cram_hash'] == commits[1]['cram_hash']


@pytest.mark.parametrize('attack', ['marker', 'record', 'payload', 'missing'])
def test_corrupt_middle_record_blocks_coverage_and_later_work(tmp_path, attack):
    store, commits = make_store(tmp_path/'input')
    record = store/'cram_0000000002.json'
    target = {'marker': record.with_name(record.name+'.blake2b'),
              'record': record, 'payload': store/'payloads/frame_0000000002.bin',
              'missing': record}[attack]
    saved = target.read_bytes()
    if attack == 'missing':target.unlink()
    else:target.write_bytes(b'corruption')
    root = tmp_path/'advisory'
    with CRAMReconciler(root, [store]) as worker:
        state = worker.reconcile_once()
        assert state['token_count'] == 1
        assert state['stores'][str(store)]['contiguous_watermark']['cram_hash'] == commits[0]['cram_hash']
        assert state['stores'][str(store)]['unresolved']
        target.write_bytes(saved)
        assert worker.reconcile_once()['token_count'] == 3
    assert audit_count(root) == 3


def test_previously_covered_missing_tail_does_not_disappear_from_cursor(tmp_path):
    store, commits = make_store(tmp_path/'input')
    with CRAMReconciler(tmp_path/'advisory', [store]) as worker:
        worker.reconcile_once()
        (store/'cram_0000000002.json').unlink()
        result = worker.reconcile_once()['stores'][str(store)]
        assert any(g['record'] == 'cram_0000000002.json' for g in result['unresolved'])
        assert result['contiguous_watermark']['cram_hash'] == commits[0]['cram_hash']


def test_duplicate_hints_do_not_duplicate_tokens_and_cannot_register_stores(tmp_path):
    store, commits = make_store(tmp_path/'input', 1)
    hint = {'cram_ref': str(store/'cram_0000000001.json'), 'frame_id': 1, 'payload_hash': 'f'*64}
    root = tmp_path/'advisory'
    with CRAMReconciler(root, [store]) as worker:
        worker.note_notification(hint)
        worker.note_notification(hint)
        with pytest.raises(ValueError):
            worker.note_notification(dict(hint, cram_ref='/outside/cram_0000000001.json'))
        state = worker.reconcile_once()
        assert state['notifications_admitted'] == 2
        assert state['token_count'] == 1
        rt = worker.tokens.rt_store[commits[0]['cram_hash']]
        assert rt.metadata['payload_hash'] == commits[0]['payload_hash']
    assert audit_count(root) == 1


def test_repeated_payloads_still_have_distinct_record_references(tmp_path):
    store, commits = make_store(tmp_path/'input', repeated_payload=True)
    assert len({r['payload_hash'] for r in commits}) == 1
    with CRAMReconciler(tmp_path/'advisory', [store]) as worker:
        assert worker.reconcile_once()['token_count'] == 3
        assert set(worker.tokens.rt_store) == {r['cram_hash'] for r in commits}


def test_snapshot_failure_recovers_without_duplicate_audit_genesis(tmp_path, monkeypatch):
    store, _ = make_store(tmp_path/'input', 1)
    root = tmp_path/'advisory'
    with CRAMReconciler(root, [store]) as worker:
        with monkeypatch.context() as patch:
            def disk_full():raise OSError('simulated materialization failure')
            patch.setattr(worker.tokens, '_save_all', disk_full)
            with pytest.raises(OSError):worker.reconcile_once()
        assert worker.coverage()['stores'][str(store)]['contiguous_watermark'] is None
        with pytest.raises(AuditIntegrityError):worker.reconcile_once()
    assert audit_count(root) == 1
    with CRAMReconciler(root, [store]) as worker:
        assert worker.reconcile_once()['token_count'] == 1
    assert audit_count(root) == 1


def test_checkpoint_failure_is_fail_closed_on_restart(tmp_path, monkeypatch):
    import ph6.advisory_chain as chain
    store, _ = make_store(tmp_path/'input', 2)
    root = tmp_path/'advisory'
    with CRAMReconciler(root, [store]) as worker:
        worker.reconcile_once(max_records=1)
        with monkeypatch.context() as patch:
            def fail(*_):raise OSError('checkpoint failure')
            patch.setattr(chain, 'durable_json', fail)
            with pytest.raises(OSError):worker.reconcile_once()
    with pytest.raises(AuditIntegrityError):CRAMReconciler(root, [store])


def test_single_owner_and_disjoint_write_root(tmp_path):
    store, _ = make_store(tmp_path/'input', 1)
    with pytest.raises(ValueError):CRAMReconciler(store/'advisory', [store])
    root = tmp_path/'advisory'
    with CRAMReconciler(root, [store]):
        with pytest.raises(BlockingIOError):CRAMReconciler(root, [store])


def test_store_can_appear_after_worker_starts(tmp_path):
    store = tmp_path/'input/cram_store'
    with CRAMReconciler(tmp_path/'advisory', [store]) as worker:
        assert worker.reconcile_once()['stores'][str(store)]['unresolved']
        make_store(tmp_path/'input', 1)
        assert worker.reconcile_once()['stores'][str(store)]['unresolved'] == []


def test_tampered_materialization_is_not_silently_replaced(tmp_path):
    store, _ = make_store(tmp_path/'input', 1)
    root = tmp_path/'advisory'
    with CRAMReconciler(root, [store]) as worker:worker.reconcile_once()
    p = root/'tokens/live_tokens.json'
    data = json.loads(p.read_text())
    next(iter(data['rt_store'].values()))['timestamp_ms'] += 1
    p.write_text(json.dumps(data))
    before = hashes(root/'tokens')
    with pytest.raises(AuditIntegrityError):CRAMReconciler(root, [store])
    assert hashes(root/'tokens') == before


def test_primary_non_camera_capture_has_parity_under_advisory_io_failure(tmp_path, monkeypatch):
    from ph6.cram_pu import cram_pu_live as capture
    original_write = capture._atomic_write_json
    def forbid_advisory_write(path, record):
        assert 'mram_s' not in Path(path).parts, 'Persistent advisory I/O entered capture'
        return original_write(path, record)
    def socket_unavailable(*args, **kwargs):
        raise PermissionError('Simulated unavailable advisory IPC')
    monkeypatch.setattr(capture, '_atomic_write_json', forbid_advisory_write)
    monkeypatch.setattr(socket, 'socket', socket_unavailable)
    off = capture.run(300, tmp_path/'off', tok_enabled=False)
    on = capture.run(300, tmp_path/'on', tok_enabled=True)
    assert off['ok'] and on['ok']
    assert off['result_set_hash'] == on['result_set_hash']
    assert on['tok_rt_count'] is None
    counts = on['tok_handoff']['outcomes']
    assert counts['FAILED'] > 0 and counts['ADMITTED'] == 0
    assert not list((tmp_path/'on/mram_s').rglob('*.json'))
    manifest = json.loads((tmp_path/'on/manifest.json').read_text())
    assert manifest['schema'] == 'ph6.cram_pu.live_manifest.v2'
    assert manifest['tok_handoff']['token_completion'] == 'UNKNOWN'


@pytest.mark.parametrize('changes', [{'schema':'unknown'}, {'authority':'LANE_1'},
                                  {'frame_id':True}, {'payload_hash':'not-a-hash'}])
def test_hint_schema_fails_closed_on_drift(changes):
    hint = {'schema':'ph6.tok.handoff.v1','cram_ref':'/read/only/cram_0000000001.json',
            'frame_id':1,'payload_hash':'a'*64}
    hint.update(changes)
    with pytest.raises(ValueError):decode_handoff(json.dumps(hint).encode())


def _crash_after_audit(root, store):
    with CRAMReconciler(root, [store]) as worker:
        def die():os.kill(os.getpid(), signal.SIGKILL)
        worker.tokens._save_all = die
        worker.reconcile_once()


def test_sigkill_after_audit_recovers_without_duplicate_genesis(tmp_path):
    store, _ = make_store(tmp_path/'input', 3)
    root = tmp_path/'advisory'
    process = multiprocessing.get_context('fork').Process(target=_crash_after_audit, args=(root, store))
    process.start()
    process.join(10)
    try:
        assert process.exitcode == -signal.SIGKILL
        assert audit_count(root) == 1
        with CRAMReconciler(root, [store]) as worker:
            result = worker.reconcile_once()
            assert result['token_count'] == 3
            assert not result['stores'][str(store)]['unresolved']
        assert audit_count(root) == 3
    finally:
        if process.is_alive():process.kill();process.join(5)


def _serve_test_worker(socket_path, root, store):
    from ph6.ssmt import worker
    # Legacy SSMT output is not exercised here. Avoid its /var-only constructor;
    # the new socket dispatch, CRAM reader, ledger and token persistence are real.
    worker.AdvisoryAuditWriter = lambda root: None
    worker.serve(socket_path, str(root), [store], reconciliation_batch=2)


def test_worker_scans_without_notifications_then_accounts_a_hint(tmp_path):
    store, commits = make_store(tmp_path/'input', 3)
    root = tmp_path/'worker'
    socket_path = str(tmp_path/'worker.sock')
    process = multiprocessing.get_context('fork').Process(target=_serve_test_worker,
                                                          args=(socket_path, root, store))
    process.start()
    health = root/'continuity-v03/health.json'
    try:
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            if health.exists() and json.loads(health.read_text())['token_count'] == 3:break
            assert process.is_alive()
            time.sleep(.02)
        assert json.loads(health.read_text())['notifications_admitted'] == 0
        assert TokenHandoff(store, socket_path=socket_path).on_pass(1, commits[0]['payload_hash']) == 'ADMITTED'
        while time.monotonic() < deadline:
            if json.loads(health.read_text())['notifications_admitted'] == 1:break
            time.sleep(.02)
        assert json.loads(health.read_text())['notifications_admitted'] == 1
        assert audit_count(root/'continuity-v03') == 3
    finally:
        process.terminate()
        process.join(5)
        if process.is_alive():process.kill();process.join(5)
    assert process.exitcode == 0
