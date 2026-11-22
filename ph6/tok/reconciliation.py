"""Read-only CRAM discovery with durable, gap-aware advisory coverage.

PROPOSED codex-lane2, 2026-09-22; Authority ZERO; ratified_by=None.
Only explicit CRAM stores are read. Notifications never register new stores.
This first migration slice retains full-history TOK append verification.
"""
import argparse
import fcntl
import hashlib
import json
import re
import sqlite3
from datetime import datetime
from pathlib import Path

from ph6.advisory_chain import AuditIntegrityError, digest, read_checked
from ph6.tok.lifecycle import RT, TokenStore, atomic_write_json
from ph6.measurement_record import CRAM_SCHEMA, MEASUREMENT_SCHEMA, read_measurements, validate_commit_binding
from ph6.tok.camera_context import legacy_context, soso_from_measurement

SCHEMA = 'ph6.tok.cram_coverage.v1'
GENESIS = '0' * 64


def _file_hash(path):
    h = hashlib.blake2b(digest_size=32)
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1048576), b''):
            h.update(chunk)
    return h.hexdigest()


def _hex(value):
    return isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value)


class CRAMReconciler:
    """One owner per new MRAM-S namespace; legacy directories are not migrated.

    SQLite is a reconstructable coverage ledger, not CRAM authority. A scan
    checks every current CRAM record/marker/payload and existing covered entry.
    The watermark is derived from the contiguous RECONCILED prefix, never the
    largest discovered frame number. Higher entries remain explicit gaps.
    """
    def __init__(self, root, cram_stores):
        self.root = Path(root).resolve()
        self.bound_measurements = {}
        self.stores = tuple(sorted({str(Path(p).resolve()) for p in cram_stores}))
        if not self.stores:
            raise ValueError('At least one explicit CRAM store is required')
        for store in self.stores:
            source = Path(store)
            if self.root == source or self.root in source.parents or source in self.root.parents:
                raise ValueError('CRAM and advisory write roots must not overlap')
        self.root.mkdir(parents=True, exist_ok=True)
        self._lock = (self.root / 'owner.lock').open('a')
        self.db = None
        self._failed = False
        try:
            fcntl.flock(self._lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.db = sqlite3.connect(self.root / 'coverage.sqlite3')
            self.db.execute('PRAGMA synchronous=FULL')
            if self.db.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                raise AuditIntegrityError('Corrupt advisory coverage ledger')
            self.db.executescript('''
                CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS records (
                    store TEXT NOT NULL, name TEXT NOT NULL, commit_hash TEXT,
                    state TEXT NOT NULL, error TEXT, PRIMARY KEY(store,name));
                CREATE TABLE IF NOT EXISTS notifications (
                    store TEXT NOT NULL, name TEXT NOT NULL, payload_hash TEXT NOT NULL,
                    attempts INTEGER NOT NULL, state TEXT NOT NULL,
                    PRIMARY KEY(store,name));
            ''')
            old = self.db.execute("SELECT value FROM metadata WHERE key='schema'").fetchone()
            if old and old[0] != SCHEMA:
                raise AuditIntegrityError('Unsupported coverage schema')
            with self.db:
                self.db.execute('INSERT OR IGNORE INTO metadata VALUES (?,?)', ('schema', SCHEMA))
            # Validate the materialized format before legacy loading can swallow
            # an error and append a warning to a suspect advisory history.
            live = self.root / 'tokens/live_tokens.json'
            if live.exists():
                data = json.loads(live.read_text())
                if data.get('schema') != 'ph6.tok.live_store.v1' or data.get('authority') != 'ZERO' or data.get('advisory_only') is not True:
                    raise AuditIntegrityError('Invalid RT materialization envelope')
                if data.get('vdt_store') or data.get('vlt_store'):
                    raise AuditIntegrityError('Dedicated reconciliation namespace requires RT-only state')
                for key, value in data['rt_store'].items():
                    rt = RT(**value)
                    if rt.is_invalid() or key != rt.cram_ref_hash:
                        raise AuditIntegrityError('Invalid materialized RT')
            self.tokens = TokenStore(str(self.root / 'tokens'))
            self.genesis = self._audit_index()
            for ref, rt in self.tokens.rt_store.items():
                if self.genesis.get(ref) != rt.state_hash():
                    raise AuditIntegrityError('Materialized RT does not match audit evidence')
        except BaseException:
            self.close()
            raise

    def close(self):
        if self.db is not None:
            self.db.close()
            self.db = None
        if not self._lock.closed:
            self._lock.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def _audit_index(self):
        path = self.root / 'tokens/tok_advisory_audit.jsonl'
        read_checked(path, 'GENESIS')
        result = {}
        if path.exists():
            for line in path.read_text().splitlines():
                event = json.loads(line)
                payload = event['payload']
                ref = payload.get('cram_ref_hash')
                if event['event_type'] != 'RT_GENESIS' or ref in result or not _hex(ref):
                    raise AuditIntegrityError('Unexpected or duplicate reconciliation genesis')
                result[ref] = payload['token_state_hash']
        return result

    def note_notification(self, hint):
        path = Path(hint['cram_ref'])
        # resolve() here is worker-side, and prevents a hinted symlink escape.
        store = str(path.parent.resolve())
        if store not in self.stores or path.name != f"cram_{hint['frame_id']:010d}.json":
            raise ValueError('Token hint is outside configured CRAM stores')
        with self.db:
            self.db.execute('''INSERT INTO notifications VALUES (?,?,?,?,?)
                ON CONFLICT(store,name) DO UPDATE SET attempts=attempts+1,
                payload_hash=excluded.payload_hash, state=excluded.state''',
                (store, path.name, hint['payload_hash'], 1, 'ADMITTED'))
        # This is admission only; processing never trusts the hinted hash.

    def _state(self, store, name, state, error=None, commit_hash=None):
        self.db.execute('''INSERT INTO records VALUES (?,?,?,?,?)
            ON CONFLICT(store,name) DO UPDATE SET state=excluded.state,
            error=excluded.error, commit_hash=COALESCE(records.commit_hash,excluded.commit_hash)''',
            (store, name, commit_hash, state, error))

    def _invalidate_snapshots(self, store):
        # Advisory output is mutable and must not retain a current-valid claim
        # after its preserved evidence becomes unavailable or fails verification.
        rows=self.db.execute("SELECT commit_hash,error FROM records WHERE store=? AND state='UNRESOLVED'",(store,))
        for ref,error in rows:
            if not _hex(ref):continue
            path=self.root/'snapshots'/(ref+'.json')
            if path.exists():
                data={'schema':'ph6.tok.cram_advisory.v2','authority':'ZERO','advisory_only':True,
                      'cram_ref_hash':ref,'soso':None,'soso_status':'UNRESOLVED',
                      'measurement_provenance_status':'UNRESOLVED','error':error}
                atomic_write_json(path,data)

    def _discover(self, store):
        source = Path(store)
        files = sorted(source.glob('cram_*.json'), key=lambda p: p.name)
        known = dict(self.db.execute("SELECT name,commit_hash FROM records WHERE store=? AND name!='<store unavailable>'", (store,)))
        present = {p.name for p in files}
        missing = set(known) - present
        if not source.is_dir() or source.resolve() != source or missing:
            with self.db:
                for name in sorted(missing) or ['<store unavailable>']:
                    self._state(store, name, 'UNRESOLVED', 'Previously observed record or store is missing')
            return []
        with self.db:
            self.db.execute("DELETE FROM records WHERE store=? AND name='<store unavailable>'", (store,))
            for p in files:
                self.db.execute('INSERT OR IGNORE INTO records VALUES (?,?,?,?,?)',
                                (store, p.name, None, 'DISCOVERED', None))
        previous = GENESIS
        valid = []
        self.bound_measurements = getattr(self, "bound_measurements", {})
        self.bound_measurements[store] = None
        for p in files:
            try:
                if not re.fullmatch(r'cram_[0-9]{10}\.json', p.name) or p.is_symlink():
                    raise ValueError('Invalid CRAM record name or symlink')
                rec = json.loads(p.read_text())
                if (rec.get('schema') not in ('ph6.cram_commit.v1', CRAM_SCHEMA) or
                        rec.get('authority') != 'LANE_1' or rec.get('verdict') != 'PASS' or
                        rec.get('hash_algorithm') != 'BLAKE2b-256' or
                        type(rec.get('frame_id')) is not int or rec['frame_id'] <= 0 or
                        p.name != f"cram_{rec['frame_id']:010d}.json"):
                    raise ValueError('Invalid authoritative commit envelope')
                body = {k: v for k, v in rec.items() if k != 'cram_hash'}
                if not _hex(rec.get('cram_hash')) or digest(body) != rec['cram_hash']:
                    raise ValueError('CRAM record hash mismatch')
                if rec['prev_cram_hash'] != previous:
                    raise ValueError('CRAM predecessor mismatch')
                marker = p.with_name(p.name + '.blake2b')
                if marker.is_symlink() or marker.read_text().strip() != rec['cram_hash']:
                    raise ValueError('CRAM commit marker mismatch')
                if known.get(p.name) not in (None, rec['cram_hash']):
                    raise ValueError('Previously discovered CRAM record was rewritten')
                payload = source / 'payloads' / f"frame_{rec['frame_id']:010d}.bin"
                if payload.is_symlink() or payload.parent.is_symlink() or not _hex(rec.get('payload_hash')) or _file_hash(payload) != rec['payload_hash']:
                    raise ValueError('Preserved payload hash mismatch')
                if rec['schema'] == CRAM_SCHEMA:
                    if self.bound_measurements[store] is None:
                        self.bound_measurements[store] = read_measurements(source)
                    validate_commit_binding(rec, self.bound_measurements[store])
                # Require a deterministic timestamp before any RT append.
                datetime.fromisoformat(rec['timestamp_utc'].replace('Z', '+00:00'))
                previous = rec['cram_hash']
                valid.append((p.name, rec))
            except (OSError, ValueError, KeyError, TypeError) as error:
                with self.db:
                    self._state(store, p.name, 'UNRESOLVED', str(error)[:512])
                    # Entries after an invalid predecessor are not covered even
                    # if a previous scan had completed them.
                    for later in files[files.index(p) + 1:]:
                        self._state(store, later.name, 'UNRESOLVED', 'Earlier CRAM record is unresolved')
                break
        return valid

    @staticmethod
    def _rt(rec):
        stamp = datetime.fromisoformat(rec['timestamp_utc'].replace('Z', '+00:00'))
        if stamp.tzinfo is None:
            raise ValueError('CRAM timestamp requires timezone')
        metadata = {'frame_id': rec['frame_id'], 'payload_hash': rec['payload_hash']}
        if rec['schema'] == CRAM_SCHEMA:
            metadata.update(measurement_id=rec['measurement_id'], measurement_record_hash=rec['measurement_record_hash'],
                            acquisition_byte_hash=rec['acquisition_byte_hash'], measurement_schema=MEASUREMENT_SCHEMA)
        return RT(token_id='rt_' + rec['cram_hash'], cram_ref_hash=rec['cram_hash'],
                  timestamp_ms=int(stamp.timestamp() * 1000), metadata=metadata)

    def _ensure_rt(self, rec):
        rt = self._rt(rec)
        ref = rt.cram_ref_hash
        expected = rt.state_hash()
        if ref in self.genesis:
            if self.genesis[ref] != expected:
                raise AuditIntegrityError('Reference identity collides with different RT state')
            existing = self.tokens.rt_store.get(ref)
            if existing is not None and existing.state_hash() != expected:
                raise AuditIntegrityError('Materialized RT state changed')
            if existing is None:
                # Crash after audit append, before materialization: reconstruct
                # the deterministic state without appending a second genesis.
                self.tokens.rt_store[ref] = rt
                self.tokens._save_all()
            return
        self.tokens.add_rt(rt)
        self.genesis[ref] = expected

    @staticmethod
    def _contexts(store):
        result = {}
        path = Path(store) / 'verdict_log.jsonl'
        if path.exists():
            try:
                with path.open() as stream:
                    for line in stream:
                        if not line.endswith('\n'):
                            result[None] = {'_invalid': 'Incomplete legacy context'}
                            break
                        def nonfinite(value): raise ValueError('Non-finite legacy context')
                        row = json.loads(line, parse_constant=nonfinite)
                        if type(row) is not dict or type(row.get('frame_id')) is not int or row['frame_id'] in result:
                            raise ValueError('Missing, malformed or duplicate context identity')
                        result[row['frame_id']] = row
            except (ValueError, OSError, TypeError) as error:
                result[None] = {'_invalid': str(error)}
        return result

    def _snapshot(self, rec, context, store):
        if rec['schema'] == CRAM_SCHEMA:
            measurement = self.bound_measurements[store][rec['frame_id']]
            # This is the only new camera SoSo execution site: worker-side,
            # after full preserved-original/metric/disposition/payload checks.
            soso = soso_from_measurement(measurement)
            status = 'DERIVED_FROM_BOUND_MEASUREMENT'
            provenance = 'BOUND_AND_REPLAY_CHECKED'
        else:
            soso, status = legacy_context(context, rec)
            provenance = 'LEGACY_UNBOUND'
        data = {'schema': 'ph6.tok.cram_advisory.v2', 'authority': 'ZERO',
                'advisory_only': True, 'cram_ref_hash': rec['cram_hash'],
                'frame_id': rec['frame_id'], 'soso': soso,
                'soso_status': status, 'measurement_provenance_status': provenance}
        path = self.root / 'snapshots' / (rec['cram_hash'] + '.json')
        if path.exists() and json.loads(path.read_text()) == data:
            return
        atomic_write_json(path, data)

    def reconcile_once(self, max_records=64):
        if self._failed:
            raise AuditIntegrityError('Reconciler must restart and verify after a persistence failure')
        if type(max_records) is not int or max_records <= 0:
            raise ValueError('Positive reconciliation batch size required')
        processed = 0
        for store in self.stores:
            records = self._discover(store)
            self._invalidate_snapshots(store)
            contexts = self._contexts(store) if self.bound_measurements.get(store) is None else {}
            budget = max_records
            for name, rec in records:
                status = self.db.execute('SELECT state FROM records WHERE store=? AND name=?', (store, name)).fetchone()[0]
                complete = (status == 'RECONCILED' and rec['cram_hash'] in self.tokens.rt_store)
                if not complete and budget == 0:
                    break
                try:
                    self._ensure_rt(rec)
                    self._snapshot(rec, contexts.get(None, contexts.get(rec['frame_id'])), store)
                    if not complete:
                        with self.db:
                            self._state(store, name, 'PROCESSED', commit_hash=rec['cram_hash'])
                        with self.db:
                            self._state(store, name, 'RECONCILED', commit_hash=rec['cram_hash'])
                        processed += 1
                        budget -= 1
                except Exception as error:
                    # Persist an observable failure; stop this process on storage
                    # or integrity errors. Reopen verifies the full audit first.
                    self._failed = True
                    with self.db:
                        self._state(store, name, 'FAILED', str(error)[:512], rec['cram_hash'])
                    atomic_write_json(self.root / 'health.json', self.coverage())
                    raise
        result = self.coverage()
        result['processed_this_scan'] = processed
        atomic_write_json(self.root / 'health.json', result)
        return result

    def coverage(self):
        stores = {}
        for store in self.stores:
            rows = list(self.db.execute('SELECT name,state,error,commit_hash FROM records WHERE store=? ORDER BY name', (store,)))
            watermark = None
            prefix = True
            gaps = []
            for name, state, error, commit in rows:
                if state != 'RECONCILED':
                    prefix = False
                    gaps.append({'record': name, 'state': state, 'error': error})
                elif prefix:
                    watermark = {'record': name, 'cram_hash': commit}
            stores[store] = {'discovered': len(rows), 'reconciled': sum(row[1] == 'RECONCILED' for row in rows),
                             'contiguous_watermark': watermark, 'unresolved': gaps}
        admitted = self.db.execute('SELECT COALESCE(SUM(attempts),0) FROM notifications').fetchone()[0]
        return {'schema': SCHEMA, 'authority': 'ZERO', 'advisory_only': True,
                'coverage_scope': 'COMMITTED_PASS_REFERENCE_TOKENS',
                'notifications_admitted': admitted, 'stores': stores,
                'token_count': len(self.tokens.rt_store)}


def main():
    parser = argparse.ArgumentParser(description='Read-only CRAM to advisory RT reconciliation')
    parser.add_argument('--root', type=Path, required=True, help='New isolated MRAM-S output namespace')
    parser.add_argument('--cram-store', type=Path, action='append', required=True)
    parser.add_argument('--batch', type=int, default=64)
    args = parser.parse_args()
    with CRAMReconciler(args.root, args.cram_store) as worker:
        print(json.dumps(worker.reconcile_once(args.batch), indent=2))


if __name__ == '__main__':
    main()
