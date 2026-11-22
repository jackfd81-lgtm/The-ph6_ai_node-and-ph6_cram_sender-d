import dataclasses
import json
import os
import socket
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import pytest
from ph6.ssmt.async_client import submit_reference
from ph6.ssmt.models import SwarmInput
from ph6.ssmt.scheduler import SwarmScheduler
from ph6.ssmt.worker import decode_reference, process_reference
from ph6.ssmt.audit_writer import AdvisoryAuditWriter
from ph6.ssmt.audit_log import SSMTAuditLog
from ph6.ssmt.replay_validator import ReplayValidator
from ph6.advisory_chain import verified_tip, AuditIntegrityError


def packet():
    return SwarmScheduler().run_cycle(SwarmInput(cram_refs=['ref'],tok_refs=[],advisory_refs=[]))[0]


def writer_at(path):
    path.mkdir()
    writer = AdvisoryAuditWriter.__new__(AdvisoryAuditWriter)
    writer.root = str(path)
    writer.audit = SSMTAuditLog.__new__(SSMTAuditLog)
    writer.audit.root = str(path)
    writer.audit.audit_path = str(path / 'ssmt_audit.jsonl')
    return writer


def test_missing_worker_and_full_queue_do_not_wait(tmp_path):
    name = str(tmp_path / 'input.sock')
    assert not submit_reference('ref','a'*64,socket_path=name)
    with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as receiver:
        receiver.bind(name)
        outcomes = []
        start = time.monotonic()
        for _ in range(int(Path("/proc/sys/net/unix/max_dgram_qlen").read_text()) + 4):
            outcomes.append(submit_reference('ref','a'*64,socket_path=name))
        elapsed = time.monotonic()-start
    assert any(outcomes) and not all(outcomes)
    assert elapsed < 1.0


def test_oversized_notification_is_shed(tmp_path):
    assert not submit_reference('x'*5000,'a'*64,socket_path=str(tmp_path/'sock'))


@pytest.mark.parametrize('change', [{'ssmt_version':'fake'}, {'authority':'LANE_1'},
    {'advisory_payload':{'nested':[{'verdict':'PASS'}]}}, {'affects_rsync':True}])
def test_worker_boundary_rejects_bad_packets(change):
    assert not ReplayValidator().validate_all([dataclasses.replace(packet(), **change)])


def test_frozen_clock_snapshots_unique_and_chain_serialized(tmp_path):
    writer = writer_at(tmp_path / 'swarms')
    p = packet()
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda _:writer.write_packet(p), range(12)))
    assert len({r['packet_path'] for r in results}) == 12
    assert len({r['audit_event']['object_id'] for r in results}) == 12
    assert verified_tip(writer.audit.audit_path, '0'*64, sequence=True)[0] == 12


def test_worker_runs_and_persists_all_nine_swarms(tmp_path):
    writer = writer_at(tmp_path/'swarms')
    obj = decode_reference(json.dumps({'cram_ref':'ref','cram_packet_hash':'a'*64,'tok_refs':['tok://rt/1']}))
    assert process_reference(obj,SwarmScheduler(),writer)==9
    assert verified_tip(writer.audit.audit_path,'0'*64,sequence=True)[0]==9


def test_ssmt_log_tamper_refuses_append(tmp_path):
    writer = writer_at(tmp_path/'swarms')
    writer.write_packet(packet())
    path = tmp_path/'swarms'/'ssmt_audit.jsonl'
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    rows[0]['node_id']='changed'
    path.write_text(json.dumps(rows[0])+'\n')
    with pytest.raises(AuditIntegrityError):
        writer.audit.append_packet_event(packet(),'ref')


@pytest.mark.parametrize('cpu,memory,swap,allowed', [
    ('30000 100000','512000000','0',True),
    ('max 100000','512000000','0',False),
    ('40000 100000','512000000','0',False),
    ('30000 100000','max','0',False),
    ('30000 100000','600000000','0',False),
    ('30000 100000','512000000','max',False),
])
def test_startup_requires_enforced_limits(tmp_path,cpu,memory,swap,allowed):
    from ph6.ssmt.worker import require_resource_limits
    (tmp_path/'cpu.max').write_text(cpu)
    (tmp_path/'memory.max').write_text(memory)
    (tmp_path/'memory.swap.max').write_text(swap)
    if allowed:
        require_resource_limits(tmp_path,'0::/')
    else:
        with pytest.raises(RuntimeError):
            require_resource_limits(tmp_path,'0::/')


def test_missing_memory_controller_refuses_startup(tmp_path):
    from ph6.ssmt.worker import require_resource_limits
    (tmp_path/'cpu.max').write_text('30000 100000')
    with pytest.raises(RuntimeError):
        require_resource_limits(tmp_path,'0::/')
