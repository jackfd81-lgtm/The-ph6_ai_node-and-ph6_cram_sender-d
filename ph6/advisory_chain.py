"""Locked Lane-2 audit append with a separate durable checkpoint.

Checkpoint protects against log-only rewrites, not an attacker able to replace
both files. An interrupted log/checkpoint transaction stops further appends.
PROPOSED: codex-lane2, 2026-09-19; ratified_by=None.
"""
import fcntl
import hashlib
import json
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path


class AuditIntegrityError(RuntimeError):
    pass


def digest(value):
    return hashlib.blake2b(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                    allow_nan=False, separators=(',', ':')).encode(),
                           digest_size=32).hexdigest()


def durable_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=path.name + '.')
    try:
        with os.fdopen(fd, 'w') as stream:
            json.dump(value, stream, sort_keys=True, allow_nan=False)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp, path)
        fd = os.open(path.parent, os.O_DIRECTORY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


@contextmanager
def locked(path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(str(path) + '.lock', 'a') as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


def verified_tip(path, genesis, sequence=False):
    count, previous = 0, genesis
    if not Path(path).exists():
        return count, previous
    try:
        with open(path) as stream:
            for line in stream:
                if not line.strip():
                    raise AuditIntegrityError('Empty audit record')
                if not line.endswith('\n'):
                    raise AuditIntegrityError('Incomplete audit record')
                event = json.loads(line)
                stored = event.pop('event_hash')
                if digest(event) != stored or event['prev_event_hash'] != previous:
                    raise AuditIntegrityError('Audit hash/link mismatch')
                count += 1
                if sequence and event['event_seq'] != count:
                    raise AuditIntegrityError('Audit sequence mismatch')
                previous = stored
    except (ValueError, KeyError, TypeError) as error:
        raise AuditIntegrityError('Malformed audit history') from error
    return count, previous


def read_checked(path, genesis, checkpoint=None, sequence=False):
    """Verify persisted history and checkpoint before advisory rehydration."""
    checkpoint = Path(checkpoint or (str(path) + '.checkpoint.json'))
    with locked(path):
        count, tail = verified_tip(path, genesis, sequence)
        if checkpoint.exists():
            try:
                anchored = json.loads(checkpoint.read_text())
            except (ValueError, OSError) as error:
                raise AuditIntegrityError('Unreadable audit checkpoint') from error
            if anchored != {'count': count, 'tail': tail}:
                raise AuditIntegrityError('Audit checkpoint mismatch')
        elif count:
            raise AuditIntegrityError('Existing audit requires explicit trusted anchoring')
        return count, tail


def append_checked(path, event, genesis, checkpoint=None, sequence=False):
    path = Path(path)
    checkpoint = Path(checkpoint or (str(path) + '.checkpoint.json'))
    with locked(path):
        count, previous = verified_tip(path, genesis, sequence)
        expected = {'count': count, 'tail': previous}
        if checkpoint.exists():
            try:
                anchored = json.loads(checkpoint.read_text())
            except (ValueError, OSError) as error:
                raise AuditIntegrityError('Unreadable audit checkpoint') from error
            if anchored != expected:
                raise AuditIntegrityError('Audit checkpoint mismatch; recovery required')
        elif count:
            raise AuditIntegrityError('Existing audit requires explicit trusted anchoring')
        else:
            durable_json(checkpoint, expected)
        result = dict(event, prev_event_hash=previous)
        if sequence:
            result['event_seq'] = count + 1
        result['event_hash'] = digest(result)
        with open(path, 'a') as stream:
            stream.write(json.dumps(result, sort_keys=True, ensure_ascii=False,
                                    allow_nan=False, separators=(',', ':')) + '\n')
            stream.flush()
            os.fsync(stream.fileno())
        fd = os.open(path.parent, os.O_DIRECTORY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
        durable_json(checkpoint, {'count': count + 1, 'tail': result['event_hash']})
        return result


def anchor_existing(path, genesis, expected_count, expected_tail, checkpoint=None, sequence=False):
    """Explicit migration using an independently established expected tip."""
    checkpoint = Path(checkpoint or (str(path) + '.checkpoint.json'))
    with locked(path):
        if checkpoint.exists():
            raise AuditIntegrityError('Refusing to replace an existing checkpoint')
        count, tail = verified_tip(path, genesis, sequence)
        if (count, tail) != (expected_count, expected_tail):
            raise AuditIntegrityError('History differs from supplied trusted checkpoint')
        durable_json(checkpoint, {'count': count, 'tail': tail})
