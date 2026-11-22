"""Negative/positive tests for the SSMT write boundary and Lane-1 claim rejection.

All filesystem work happens under pytest tmp_path. Nothing touches /var/ph6:
the one test using the production approved root fails in pure validation,
before any directory is created.

PROPOSED by claude-code-lane2; ratified_by=null.
"""
import dataclasses
import json
import os
import types
from pathlib import Path

import pytest

from ph6.advisory_chain import verified_tip
from ph6.ssmt.audit_log import SSMTAuditLog
from ph6.ssmt.audit_writer import AdvisoryAuditWriter
from ph6.ssmt.closure import ClosureValidator
from ph6.ssmt.models import SwarmInput
from ph6.ssmt.replay_validator import ReplayValidator
from ph6.ssmt.scheduler import SwarmScheduler
from ph6.ssmt.write_boundary import WriteBoundaryError, confine_root


def packets():
    return SwarmScheduler().run_cycle(SwarmInput(cram_refs=['ref'], tok_refs=[], advisory_refs=[]))


@pytest.fixture
def layout(tmp_path):
    approved = tmp_path / 'var' / 'ph6' / 'mram-s' / 'swarms'
    outside = tmp_path / 'var' / 'ph6' / 'cram-0'
    approved.mkdir(parents=True)
    outside.mkdir(parents=True)
    return approved, outside


def files_under(path):
    return sorted(str(p.relative_to(path)) for p in Path(path).rglob('*'))


# ---------------------------------------------------------------- traversal

def test_production_dotdot_escape_rejected_before_any_write():
    with pytest.raises(WriteBoundaryError):
        AdvisoryAuditWriter('/var/ph6/mram-s/swarms/../../cram-0/x')
    with pytest.raises(WriteBoundaryError):
        SSMTAuditLog('/var/ph6/mram-s/swarms/../../cram-0/x')


@pytest.mark.parametrize('suffix', ['../cram-0/x', '../../cram-0', 'run/../../cram-0/x',
                                    'run/../ok', '..'])
def test_dotdot_rejected_and_nothing_created(layout, suffix):
    approved, outside = layout
    with pytest.raises(WriteBoundaryError):
        AdvisoryAuditWriter(f'{approved}/{suffix}', approved_root=str(approved))
    assert files_under(outside) == []
    assert files_under(approved) == []


@pytest.mark.parametrize('make_root', [
    lambda a, o: str(o / 'x'),                       # absolute path elsewhere
    lambda a, o: os.path.join(str(a), str(o / 'x')),  # join() absolute injection
    lambda a, o: str(a) + '-evil/x',                 # prefix confusion
    lambda a, o: 'var/ph6/mram-s/swarms/x',          # relative root
    lambda a, o: '',                                 # empty
    lambda a, o: str(a) + '/x\x00y',                 # NUL
    lambda a, o: (str(a) + '/x').encode(),           # bytes, not str
    lambda a, o: None,                               # not a path at all
])
def test_invalid_or_injected_roots_rejected(layout, make_root):
    approved, outside = layout
    with pytest.raises(WriteBoundaryError):
        AdvisoryAuditWriter(make_root(approved, outside), approved_root=str(approved))
    assert files_under(outside) == []


def test_existing_symlink_escape_rejected(layout):
    approved, outside = layout
    (approved / 'link').symlink_to(outside, target_is_directory=True)
    with pytest.raises(WriteBoundaryError):
        AdvisoryAuditWriter(str(approved / 'link' / 'x'), approved_root=str(approved))
    with pytest.raises(WriteBoundaryError):
        AdvisoryAuditWriter(str(approved / 'link'), approved_root=str(approved))
    assert files_under(outside) == []


def test_symlink_swap_after_validation_is_refused(layout):
    approved, outside = layout
    writer = AdvisoryAuditWriter(str(approved / 'run'), approved_root=str(approved))
    os.rename(approved / 'run', approved / 'run.moved')
    (approved / 'run').symlink_to(outside, target_is_directory=True)
    with pytest.raises(WriteBoundaryError):
        writer.write_packet(packets()[0])
    assert files_under(outside) == []


def test_symlink_swap_of_middle_component_is_refused(layout):
    approved, outside = layout
    writer = AdvisoryAuditWriter(str(approved / 'mid' / 'run'), approved_root=str(approved))
    os.rename(approved / 'mid', approved / 'mid.moved')
    (outside / 'run').mkdir()
    (approved / 'mid').symlink_to(outside, target_is_directory=True)
    with pytest.raises(WriteBoundaryError):
        writer.write_packet(packets()[0])
    assert files_under(outside) == ['run']


def test_symlinked_approved_root_is_resolved_not_escaped(tmp_path):
    real = tmp_path / 'real_swarms'
    real.mkdir()
    alias = tmp_path / 'alias_swarms'
    alias.symlink_to(real, target_is_directory=True)
    writer = AdvisoryAuditWriter(str(alias / 'run'), approved_root=str(alias))
    assert writer.root == str(real / 'run')
    writer.write_packet(packets()[0])
    assert (real / 'run' / 'ssmt_audit.jsonl').exists()


def test_unsafe_packet_file_name_rejected(layout):
    approved, outside = layout
    writer = AdvisoryAuditWriter(str(approved / 'run'), approved_root=str(approved))
    bad = dataclasses.replace(packets()[0], swarm_id='../../cram-0/evil')
    with pytest.raises(WriteBoundaryError):
        writer.write_packet(bad)
    assert files_under(outside) == []


def test_missing_approved_root_fails_closed(tmp_path):
    with pytest.raises((WriteBoundaryError, OSError)):
        AdvisoryAuditWriter(str(tmp_path / 'nope' / 'run'), approved_root=str(tmp_path / 'nope'))
    assert not (tmp_path / 'nope').exists()


# ---------------------------------------------------------------- positive paths

def test_nonexistent_trailing_components_created_inside(layout):
    approved, outside = layout
    writer = AdvisoryAuditWriter(str(approved / 'spine-x' / 'deep') + '/', approved_root=str(approved))
    result = writer.write_packet(packets()[0])
    assert result['packet_path'].startswith(str(approved / 'spine-x' / 'deep') + os.sep)
    assert os.path.exists(result['packet_path'])
    assert files_under(outside) == []


def test_valid_swarm_path_writes_all_nine_and_chains(layout):
    approved, outside = layout
    writer = AdvisoryAuditWriter(str(approved / 'spine-20260929T222027Z'), approved_root=str(approved))
    for p in packets():
        writer.write_packet(p)
    root = approved / 'spine-20260929T222027Z'
    assert len(list(root.glob('S*_*.json'))) == 9
    assert not list(root.glob('*.tmp'))
    assert verified_tip(str(root / 'ssmt_audit.jsonl'), '0' * 64, sequence=True)[0] == 9
    assert files_under(outside) == []


def test_approved_root_itself_is_allowed(layout):
    approved, _ = layout
    real, base, parts = confine_root(str(approved) + '/', str(approved))
    assert real == base == str(approved) and parts == ()
    AdvisoryAuditWriter(str(approved) + '/', approved_root=str(approved)).write_packet(packets()[0])


# ---------------------------------------------------------------- forged authority

class _Str(str):
    pass


@pytest.mark.parametrize('change', [
    {'authority': 'LANE_1'}, {'authority': _Str('NONE')}, {'authority': None},
    {'lane': 'LANE_1'}, {'ssmt_version': 'fake'},
    {'advisory_only': False}, {'advisory_only': 1},
    {'affects_cram_commit': True}, {'affects_rsync': 1}, {'affects_pass_drop': 'False'},
    {'affects_thresholds': None},
    {'advisory_payload': {'authority': 'LANE_1'}},
    {'advisory_payload': {'x': [{'affects_cram_commit': True}]}},
    {'advisory_payload': {'Lane': 'LANE_2_ADVISORY'}},
    {'advisory_payload': {'note': 'lane_1'}},
    {'advisory_payload': {1: 'x'}},
    {'advisory_payload': ['not', 'a', 'dict']},
])
def test_lane1_claims_rejected_by_every_entry_point(change):
    bad = dataclasses.replace(packets()[0], **change)
    mixed = packets()[1:] + [bad]
    v = ReplayValidator()
    assert v.validate_no_authority_escalation([bad]) is False
    assert v.validate_all([bad]) is False
    assert v.validate_all(mixed) is False
    assert ClosureValidator().validate([bad])['passed'] is False


def test_missing_attribute_fails_closed_without_raising():
    fields = {f.name: getattr(packets()[0], f.name) for f in dataclasses.fields(packets()[0])}
    del fields['authority']
    fake = types.SimpleNamespace(**fields)
    assert ReplayValidator().validate_no_authority_escalation([fake]) is False
    assert ReplayValidator().validate_all([fake]) is False


def test_real_advisory_packets_still_accepted():
    good = packets()
    assert len(good) == 9
    assert ReplayValidator().validate_all(good) is True
    assert ReplayValidator().validate_no_authority_escalation(good) is True
    assert ClosureValidator().validate(good)['all_authority_none'] is True


def test_worker_drops_forged_packet_without_writing(layout, monkeypatch):
    from ph6.ssmt import worker
    approved, _ = layout
    writer = AdvisoryAuditWriter(str(approved / 'run'), approved_root=str(approved))
    forged = [dataclasses.replace(p, affects_cram_commit=True) for p in packets()]
    monkeypatch.setattr(SwarmScheduler, 'run_cycle', lambda self, inp: forged)
    obj = worker.decode_reference(json.dumps({'cram_ref': 'ref', 'cram_packet_hash': 'a' * 64, 'tok_refs': []}))
    with pytest.raises(ValueError, match='boundary violation'):
        worker.process_reference(obj, SwarmScheduler(), writer)
    assert not list((approved / 'run').glob('S*_*.json'))
