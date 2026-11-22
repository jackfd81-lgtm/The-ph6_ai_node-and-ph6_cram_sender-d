import json
from pathlib import Path
import pytest
from ph6.cram_pu.tools import cam3000_harness as h
from ph6.advisory_chain import append_checked,digest
from ph6.cram_pu.crash_replay import CRAMWriter
from ph6.cram_pu._lane1_auth import mint_commit_authorization


def frames(path,rows):
    path.write_text(''.join(json.dumps(r)+'\n' for r in rows))


@pytest.mark.parametrize('value',[float('nan'),float('inf'),-1,0,'0.1',True,None])
def test_reject_bad_latency(tmp_path,value):
    p=tmp_path/'f';frames(p,[{'seq':1,'latency_sec':value,'mono_ts':1},{'seq':2,'latency_sec':.01,'mono_ts':2}])
    with pytest.raises(ValueError):h.load_frames(p)


def test_monotonicity_and_empty(tmp_path):
    p=tmp_path/'f';p.write_text('')
    with pytest.raises(ValueError):h.load_frames(p)
    frames(p,[{'seq':1,'latency_sec':.01,'mono_ts':1},{'seq':2,'latency_sec':.01,'mono_ts':1}])
    with pytest.raises(ValueError):h.load_frames(p)


def test_checkpoint_recomputes_all_records(tmp_path):
    p=tmp_path/'ssmt_audit.jsonl'
    for i in range(3):append_checked(p,{'payload':{'x':i}},'0'*64,sequence=True)
    before=h.verify_checkpoint(tmp_path)
    assert before['count']==3
    rows=[json.loads(line) for line in p.read_text().splitlines()]
    rows[0]['payload']['x']=99;frames(p,rows)
    with pytest.raises(Exception):h.verify_checkpoint(tmp_path)


def test_rehashed_history_and_extra_tail_rejected(tmp_path):
    p=tmp_path/'ssmt_audit.jsonl'
    for i in range(3):append_checked(p,{'payload':{'x':i}},'0'*64,sequence=True)
    before=h.verify_checkpoint(tmp_path)
    append_checked(p,{'payload':{'x':4}},'0'*64,sequence=True)
    checkpoint=Path(str(p)+'.checkpoint.json');checkpoint.write_text(json.dumps(before))
    with pytest.raises(ValueError):h.verify_checkpoint(tmp_path)


def test_cram_checks_payload_and_marker(tmp_path):
    store=tmp_path/'capture/cram_store';store.mkdir(parents=True);payloads=store/'payloads';payloads.mkdir()
    b=b'actual bytes';payloads.joinpath('frame_0000000001.bin').write_bytes(b)
    ih=h.hash_file(payloads/'frame_0000000001.bin');v={'frame_id':1,'verdict':'PASS','input_hash':ih}
    writer=CRAMWriter(store);writer.commit(1,ih,v,mint_commit_authorization(frame_id=1,payload_hash=ih,verdict='PASS'))
    frames(store/'verdict_log.jsonl',[v]);assert h.verify_cram(tmp_path)['commits']==1
    payloads.joinpath('frame_0000000001.bin').write_bytes(b'tampered')
    with pytest.raises(ValueError):h.verify_cram(tmp_path)


def test_statistics_fails_empty_and_uses_nearest_rank():
    with pytest.raises(ValueError):h.stats([])
    assert h.stats(list(range(1,101)))['p99']==99


def test_offline_manifest_tamper_refused(tmp_path):
    p=tmp_path/'evidence';p.write_text('original');h.write(tmp_path/'evidence-manifest.blake2b.json',{'evidence':h.hash_file(p)})
    p.write_text('changed')
    with pytest.raises(ValueError,match='manifest mismatch'):h.evaluate(tmp_path,'A')


@pytest.mark.parametrize('mode',['backlog','partial','complete','tampered'])
def test_stress_requires_saved_outputs_from_all_nine_swarms(tmp_path,mode):
    # Queue admission plus unrelated audit progress reproduced the live false positive.
    reference={'frame_id':1,'payload_hash':'a'*64}
    expected=digest(reference)
    h.write(tmp_path/'stress-input.json',dict(reference,cram_hash=expected))
    h.write(tmp_path/'stress.json',{'accepted':9,'shed':0,'reference_hash':expected})
    packets=tmp_path/'audited-packets';packets.mkdir()
    for i in range(1,2 if mode=='partial' else 10):
        packet={'swarm_id':f'S{i}','cram_packet_hash':'b'*64 if mode=='backlog' else expected}
        name=f'S{i}.json'
        append_checked(tmp_path/'ssmt_audit.jsonl',{'object_id':name,'packet_hash':digest(packet)},'0'*64,sequence=True)
        h.write(packets/name,packet)
    if mode=='tampered':h.write(packets/'S1.json',{'changed':True})
    before={'count':0,'tail':'0'*64}
    if mode=='complete':
        result=h.verify_stress(tmp_path,before)
        assert result['stress_packets_written']==9
        assert result['stress_swarms']==[f'S{i}' for i in range(1,10)]
    else:
        with pytest.raises(ValueError,match='packet hash' if mode=='tampered' else 'all nine swarms'):
            h.verify_stress(tmp_path,before)
