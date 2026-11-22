"""New measurement-boundary regressions; synthetic inputs, no live camera/worker.
PROPOSED codex-lane2, 2026-09-29; ratified_by=None.
"""
import json
from pathlib import Path
import numpy as np
import pytest

def image():
    return np.random.default_rng(3022).integers(50, 200, (48, 64, 3), dtype=np.uint8)

def fake_camera(monkeypatch):
    from ph6.cram_pu.tools import life_cram_lcc_01_live_camera as camera
    class Camera:
        def read(self): return True, image()
        def release(self): pass
        def get(self, prop): return 0.0
    def opened(device):
        return Camera(), {'schema':'ph6.camera_inventory.v1', 'device':'TEST_SYNTHETIC',
            'device_index':-1, 'backend':'TEST_FIXTURE', 'width_px':64, 'height_px':48,
            'stated_fps':0.0, 'real_source':False, 'opened_utc':'2026-09-29T00:00:00Z'}
    monkeypatch.setattr(camera, '_open_camera', opened)
    monkeypatch.setattr('ph6.ssmt.async_client.submit_reference', lambda *a, **kw: False)
    return camera

def test_camera_preserves_despite_soso_exception(tmp_path, monkeypatch):
    camera = fake_camera(monkeypatch)
    def advisory_failure(*a, **kw): raise RuntimeError('simulated SoSo failure')
    monkeypatch.setattr(camera, '_soso_advisory_camera', advisory_failure, raising=False)
    camera.run_lcc01(1, 'TEST_SYNTHETIC', tmp_path, tok_enabled=False)
    assert len(list((tmp_path/'cram_store').glob('cram_*.json'))) == 1
    final=json.loads((tmp_path/'lcc01_final_manifest.json').read_text())
    assert final['pass_count'] == 1 and final['error_count'] == 0

from datetime import datetime, timezone
import hashlib
import multiprocessing
import os
import signal
import cv2
from ph6.measurement_record import (
    read_measurements, digest, byte_hash, canonical, camera_metrics, camera_disposition,
    MeasurementIntegrityError, validate_commit_binding,
)
from ph6.cram_pu.measurement_writer import MeasurementWriter
from ph6.tok.reconciliation import CRAMReconciler


def context(sequence=1):
    return {'timestamp_utc':datetime.fromtimestamp(1790640000+sequence,timezone.utc).isoformat().replace('+00:00','Z'),
        'wall_time_ns':1790640000000000000+sequence*1000000000,
        'monotonic_timestamp_ns':sequence*1000000000,
        'clock_scope':'HOST_AFTER_CAMERA_READ_NOT_EXPOSURE',
        'sensor':{'device':'TEST_SYNTHETIC','backend':'TEST_FIXTURE',
            'physical_identity':{'status':'UNKNOWN','value':None},'calibration':{'status':'UNKNOWN','value':None}},
        'capture_configuration':{'width_px':64,'height_px':48,
            **{k:{'status':'UNKNOWN','value':None} for k in ('stated_fps_fp','exposure_fp','gain_fp','white_balance_fp','focus_fp')}},
        'thermal_state':{'status':'UNKNOWN','host_temperature_millicelsius':None},
        'io_state':{'status':'UNKNOWN','free_bytes':None}}


def produce(store,count=1):
    records=[]
    with MeasurementWriter(store) as writer:
        for i in range(count):
            writer.begin(image(),context(i+1));records.append(writer.finalize())
    return records


def fingerprint(root):
    return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob('*') if p.is_file()}


def test_original_bytes_are_durable_before_pseudo_and_immune_to_caller_mutation(tmp_path, monkeypatch):
    import ph6.cram_pu.measurement_writer as module
    observed=[];original=module.camera_metrics
    def checked(frame,previous):
        assert (tmp_path/'acquisitions/acquisition_0000000001.json').exists()
        assert (tmp_path/'acquisitions/acquisition_0000000001.bin').read_bytes()==image().tobytes()
        observed.append(True)
        return original(frame,previous)
    monkeypatch.setattr(module,'camera_metrics',checked)
    with MeasurementWriter(tmp_path) as writer:
        supplied=image();writer.begin(supplied,context());supplied[:]=0
        record=writer.finalize()
    assert observed and record['disposition']=='PASS'
    assert record['acquisition']['acquisition_byte_hash']==hashlib.blake2b(image().tobytes(),digest_size=32).hexdigest()
    assert record['encoded_payload']['hash']!=record['acquisition']['acquisition_byte_hash']
    assert record['pseudo']['inputs']['original_acquisition_hash']==record['acquisition']['acquisition_byte_hash']
    assert 'soso_advisory' not in canonical(record).decode()


def test_independent_hashes_and_metrics_match_preserved_original(tmp_path):
    record=produce(tmp_path)[0]
    raw=(tmp_path/record['acquisition']['raw_ref']).read_bytes()
    frame=np.frombuffer(raw,dtype=np.uint8).reshape(record['acquisition']['dimensions'])
    gray=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
    from decimal import Decimal, ROUND_HALF_EVEN
    fp=lambda x:int((Decimal(str(float(x)))*10000).to_integral_value(rounding=ROUND_HALF_EVEN))
    assert record['pseudo']['metrics']['mean_brightness_fp']==fp(gray.mean())
    assert record['pseudo']['metrics']['laplacian_var_fp']==fp(cv2.Laplacian(gray,cv2.CV_64F).var())
    assert record['pseudo']['metrics']['motion_input_status']=='NO_PREDECESSOR'
    for obj in (record,record['acquisition']):
        body={k:v for k,v in obj.items() if k!='record_hash'}
        independent=json.dumps(body,sort_keys=True,ensure_ascii=False,allow_nan=False,separators=(',',':')).encode()
        assert hashlib.blake2b(independent,digest_size=32).hexdigest()==obj['record_hash']
    commit=json.loads((tmp_path/'cram_0000000001.json').read_text())
    assert commit['measurement_record_hash']==record['record_hash']
    assert (tmp_path/'cram_0000000001.json.blake2b').read_text().strip()==commit['cram_hash']


def test_drop_is_bound_without_pass_marker_and_is_the_next_motion_parent(tmp_path):
    with MeasurementWriter(tmp_path) as writer:
        writer.begin(image(),context(1));first=writer.finalize()
        writer.begin(np.zeros_like(image()),context(2));drop=writer.finalize()
        writer.begin(image(),context(3));third=writer.finalize()
    assert first['disposition']=='PASS' and drop['disposition']=='DROP'
    assert not (tmp_path/'cram_0000000002.json.blake2b').exists()
    assert third['previous_record_hash']==drop['record_hash']
    assert third['pseudo']['inputs']['previous_measurement_id']==drop['measurement_id']
    assert third['pseudo']['inputs']['previous_acquisition_hash']==drop['acquisition']['acquisition_byte_hash']
    assert len(read_measurements(tmp_path))==3


def test_identical_images_have_distinct_measurement_identities_and_restart_is_idempotent(tmp_path):
    records=produce(tmp_path,3);before=fingerprint(tmp_path)
    assert len({r['acquisition']['acquisition_byte_hash'] for r in records})==1
    assert len({r['measurement_id'] for r in records})==3
    with MeasurementWriter(tmp_path) as writer:assert writer.next_sequence==4
    assert fingerprint(tmp_path)==before


def test_advisory_notification_exception_cannot_stop_next_capture(tmp_path, monkeypatch):
    camera=fake_camera(monkeypatch)
    def fail(*a,**kw):raise RuntimeError('worker unavailable')
    monkeypatch.setattr('ph6.ssmt.async_client.submit_reference',fail)
    camera.run_lcc01(3,'TEST_SYNTHETIC',tmp_path,tok_enabled=False)
    assert len(list((tmp_path/'cram_store').glob('cram_*.json')))==3


def test_no_soso_call_or_persistence_in_synthetic_primary_runner(tmp_path, monkeypatch):
    from ph6.cram_pu import verdict_logger,cram_pu_live
    def fail(*a,**kw):raise RuntimeError('SoSo must not enter Lane 1')
    monkeypatch.setattr(verdict_logger,'_soso_advisory',fail)
    result=cram_pu_live.run(3,tmp_path,tok_enabled=False)
    assert result['ok']
    assert all('soso_advisory' not in json.loads(l) for l in (tmp_path/'cram_store/verdict_log.jsonl').read_text().splitlines())


@pytest.mark.parametrize('attack',['metric','schema','missing_context','nan','parent','identity','raw','jpeg','reencode','marker','predecessor'])
def test_corruption_or_unknown_semantics_never_becomes_recovered(tmp_path,attack):
    source=tmp_path/'source';record=produce(source)[0]
    path=source/'measurements/measurement_0000000001.json'
    if attack=='metric':record['pseudo']['metrics']['mean_brightness_fp']+=100
    elif attack=='schema':record['schema']='unknown'
    elif attack=='missing_context':record['acquisition']['context'].pop('sensor')
    elif attack=='nan':record['pseudo']['metrics']['laplacian_var_fp']=float('nan')
    elif attack=='parent':record['pseudo']['inputs']['previous_acquisition_hash']='e'*64
    elif attack=='identity':record['measurement_id']='bogus'
    elif attack=='predecessor':record['previous_record_hash']='e'*64
    elif attack=='raw':(source/record['acquisition']['raw_ref']).write_bytes(b'bad-original')
    elif attack=='jpeg':(source/record['encoded_payload']['path']).write_bytes(b'bad-jpeg')
    elif attack=='reencode':
        ok,encoded=cv2.imencode('.jpg',image(),[cv2.IMWRITE_JPEG_QUALITY,75]);assert ok
        (source/record['encoded_payload']['path']).write_bytes(encoded.tobytes())
        record['encoded_payload']['hash']=byte_hash(encoded.tobytes());record['encoded_payload']['size_bytes']=len(encoded)
    elif attack=='marker':(source/'cram_0000000001.json.blake2b').write_text('e'*64+'\n')
    if attack not in ('raw','jpeg','marker'):
        if attack!='nan':record['record_hash']=digest({k:v for k,v in record.items() if k!='record_hash'})
        path.write_text(json.dumps(record)+'\n')
    with CRAMReconciler(tmp_path/'advisory',[source]) as worker:
        state=worker.reconcile_once()
        assert state['token_count']==0
        assert state['stores'][str(source)]['unresolved']
    assert not list((tmp_path/'advisory/snapshots').glob('*.json'))


@pytest.mark.parametrize('stage',['raw','acquisition','jpeg','measurement','cram','marker'])
def test_interrupted_publication_recovery_and_marker_order(tmp_path,monkeypatch,stage):
    import ph6.cram_pu.measurement_writer as module
    original=module._atomic_new
    def matches(path):
        return {'raw':path.name=='acquisition_0000000001.bin',
            'acquisition':path.name=='acquisition_0000000001.json',
            'jpeg':path.name=='frame_0000000001.bin',
            'measurement':path.name=='measurement_0000000001.json',
            'cram':path.name=='cram_0000000001.json',
            'marker':path.name=='cram_0000000001.json.blake2b'}[stage]
    def fail_after(path,data):
        original(path,data)
        if matches(path):raise OSError('injected interruption after '+stage)
    with pytest.raises(OSError):
        with monkeypatch.context() as patch:
            patch.setattr(module,'_atomic_new',fail_after)
            with MeasurementWriter(tmp_path) as writer:
                writer.begin(image(),context());writer.finalize()
    if stage=='raw':
        with pytest.raises(MeasurementIntegrityError,match='Orphan'):MeasurementWriter(tmp_path)
        assert not list(tmp_path.glob('*.blake2b'))
    else:
        if stage!='marker':assert not list(tmp_path.glob('*.blake2b'))
        with MeasurementWriter(tmp_path) as writer:assert writer.next_sequence==2
        assert len(read_measurements(tmp_path))==1
        assert (tmp_path/'cram_0000000001.json.blake2b').exists()
        before=fingerprint(tmp_path)
        with MeasurementWriter(tmp_path):pass
        assert fingerprint(tmp_path)==before


def _kill_writer(path,stage):
    import ph6.cram_pu.measurement_writer as module
    original=module._atomic_new
    def killed(p,data):
        original(p,data)
        if p.name==stage:os.kill(os.getpid(),signal.SIGKILL)
    module._atomic_new=killed
    with MeasurementWriter(path) as writer:
        writer.begin(image(),context());writer.finalize()


@pytest.mark.parametrize('stage',['acquisition_0000000001.json','measurement_0000000001.json','cram_0000000001.json'])
def test_sigkill_resume_from_durable_tail(tmp_path,stage):
    process=multiprocessing.get_context('fork').Process(target=_kill_writer,args=(tmp_path,stage))
    process.start();process.join(10)
    try:assert process.exitcode==-signal.SIGKILL
    finally:
        if process.is_alive():process.kill();process.join(5)
    assert not list(tmp_path.glob('*.blake2b'))
    with MeasurementWriter(tmp_path) as writer:assert writer.next_sequence==2
    assert len(read_measurements(tmp_path))==1


def test_discovery_without_hint_and_restart_preserves_exact_provenance(tmp_path):
    source=tmp_path/'source';records=produce(source,3)
    before=fingerprint(source)
    with CRAMReconciler(tmp_path/'advisory',[source]) as worker:
        state=worker.reconcile_once()
        assert state['token_count']==3 and state['notifications_admitted']==0
        assert not state['stores'][str(source)]['unresolved']
        assert worker.reconcile_once()['processed_this_scan']==0
    with CRAMReconciler(tmp_path/'advisory',[source]) as worker:assert worker.reconcile_once()['processed_this_scan']==0
    assert fingerprint(source)==before
    snapshots=[json.loads(p.read_text()) for p in (tmp_path/'advisory/snapshots').glob('*.json')]
    assert len(snapshots)==3
    assert all(s['measurement_provenance_status']=='BOUND_AND_REPLAY_CHECKED' and s['soso_status']=='DERIVED_FROM_BOUND_MEASUREMENT' for s in snapshots)


def test_missing_discovery_path_stays_unresolved(tmp_path):
    source=tmp_path/'missing'
    with CRAMReconciler(tmp_path/'advisory',[source]) as worker:
        state=worker.reconcile_once()
        assert state['token_count']==0 and state['stores'][str(source)]['unresolved']


def _stall_soso(source,root,entered):
    import ph6.tok.reconciliation as module
    def stalled(record):
        entered.set();__import__('time').sleep(30)
    module.soso_from_measurement=stalled
    with CRAMReconciler(root,[source]) as worker:worker.reconcile_once()


def test_worker_soso_timeout_and_crash_cannot_block_lane1(tmp_path):
    source=tmp_path/'source';produce(source)
    ctx=multiprocessing.get_context('fork');entered=ctx.Event()
    process=ctx.Process(target=_stall_soso,args=(source,tmp_path/'advisory',entered))
    process.start()
    try:
        assert entered.wait(5),'Worker did not reach injected timeout'
        with MeasurementWriter(source) as writer:
            writer.begin(image(),context(2));second=writer.finalize()
        assert second['disposition']=='PASS' and (source/'cram_0000000002.json.blake2b').exists()
        process.kill();process.join(5)
        with MeasurementWriter(source) as writer:
            writer.begin(image(),context(3));third=writer.finalize()
        assert third['disposition']=='PASS'
        with CRAMReconciler(tmp_path/'advisory',[source]) as worker:
            assert worker.reconcile_once()['token_count']==3
    finally:
        if process.is_alive():process.kill();process.join(5)


def test_existing_capture_directory_is_never_rewritten(tmp_path,monkeypatch):
    camera=fake_camera(monkeypatch);camera.run_lcc01(1,'TEST_SYNTHETIC',tmp_path,tok_enabled=False)
    before=fingerprint(tmp_path)
    with pytest.raises(ValueError,match='empty evidence'):camera.run_lcc01(1,'TEST_SYNTHETIC',tmp_path,tok_enabled=False)
    assert fingerprint(tmp_path)==before
