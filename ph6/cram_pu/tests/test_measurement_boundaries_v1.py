"""Additional evidence-boundary faults, isolated synthetic stores only.
PROPOSED codex-lane2 2026-09-29; ratified_by=None.
"""
import json
import pytest
from ph6.cram_pu.tests.test_measurement_record_v1 import (
    produce, image, context, fake_camera, fingerprint, MeasurementWriter,
    MeasurementIntegrityError, CRAMReconciler, read_measurements,
)


def test_camera_failed_read_does_not_misidentify_later_measurement(tmp_path, monkeypatch):
    camera=fake_camera(monkeypatch)
    original=camera._open_camera
    def opened(device):
        cap,inventory=original(device);read=cap.read;calls=[]
        def failing_once():
            calls.append(1)
            return (False,None) if len(calls)==2 else read()
        cap.read=failing_once
        return cap,inventory
    monkeypatch.setattr(camera,'_open_camera',opened)
    camera.run_lcc01(4,'TEST_SYNTHETIC',tmp_path,tok_enabled=False)
    assert len(read_measurements(tmp_path/'cram_store'))==3
    final=json.loads((tmp_path/'lcc01_final_manifest.json').read_text())
    assert final['capture_fail_count']==1 and final['error_count']==0
    assert final['real_source'] is False
    rows=[json.loads(line) for line in (tmp_path/'cram_store/verdict_log.jsonl').read_text().splitlines()]
    assert [r['frame_id'] for r in rows]==[1,2,3]


@pytest.mark.parametrize('attack',['corruption','missing_record','missing_store'])
def test_prior_advisory_validation_is_invalidated_on_evidence_loss(tmp_path,attack):
    source=tmp_path/'source';produce(source,2)
    with CRAMReconciler(tmp_path/'advisory',[source]) as worker:
        worker.reconcile_once()
        if attack=='corruption':
            (source/'acquisitions/acquisition_0000000001.bin').write_bytes(b'corrupt')
        elif attack=='missing_record':
            (source/'cram_0000000001.json').unlink()
        else:source.rename(tmp_path/'offline')
        state=worker.reconcile_once()
        assert state['stores'][str(source)]['unresolved']
        snapshots=[json.loads(p.read_text()) for p in (tmp_path/'advisory/snapshots').glob('*.json')]
        affected=[s for s in snapshots if s['measurement_provenance_status']=='UNRESOLVED']
        assert affected and all(s['soso'] is None for s in affected)


def test_recovery_validates_all_existing_evidence_before_publishing_missing_marker(tmp_path):
    produce(tmp_path,2)
    (tmp_path/'cram_0000000001.json.blake2b').unlink()
    (tmp_path/'acquisitions/acquisition_0000000002.bin').write_bytes(b'corrupt')
    before=fingerprint(tmp_path)
    with pytest.raises(MeasurementIntegrityError):MeasurementWriter(tmp_path)
    assert fingerprint(tmp_path)==before


def test_unknown_marker_and_stale_closed_writer_fail_closed(tmp_path):
    writer=MeasurementWriter(tmp_path)
    writer.close()
    with pytest.raises(MeasurementIntegrityError,match='ownership'):writer.begin(image(),context())
    (tmp_path/'cram_0000000001.json.blake2b').write_text('0'*64+'\n')
    with pytest.raises(MeasurementIntegrityError,match='Unbound PASS marker'):MeasurementWriter(tmp_path)


def test_concurrent_writer_is_refused_without_changing_evidence(tmp_path):
    with MeasurementWriter(tmp_path):
        before=fingerprint(tmp_path)
        with pytest.raises(BlockingIOError):MeasurementWriter(tmp_path)
        assert before==fingerprint(tmp_path)


@pytest.mark.parametrize('attack',['utc_mismatch','missing_sensor','nan','infinity','bool_sequence'])
def test_malformed_acquisition_context_stops_before_preserving_raw(tmp_path,attack):
    value=context()
    if attack=='utc_mismatch':value['timestamp_utc']='2025-01-01T00:00:00Z'
    elif attack=='missing_sensor':value.pop('sensor')
    elif attack=='nan':value['monotonic_timestamp_ns']=float('nan')
    elif attack=='infinity':value['wall_time_ns']=float('inf')
    else:value['monotonic_timestamp_ns']=True
    with MeasurementWriter(tmp_path) as writer:
        with pytest.raises((MeasurementIntegrityError,ValueError)):writer.begin(image(),value)
    assert not list((tmp_path/'acquisitions').iterdir())


def test_published_structural_schemas_validate_real_records_and_reject_unknown_fields(tmp_path):
    from pathlib import Path
    from jsonschema import Draft202012Validator, FormatChecker, ValidationError
    record=produce(tmp_path)[0]
    commit=json.loads((tmp_path/'cram_0000000001.json').read_text())
    schemas=Path(__file__).parents[1]/'schemas'
    for name,value in [('acquisition_commit_v1',record['acquisition']),('measurement_record_v1',record),('cram_commit_v2',commit)]:
        schema=json.loads((schemas/(name+'.schema.json')).read_text())
        Draft202012Validator.check_schema(schema)
        validator=Draft202012Validator(schema,format_checker=FormatChecker())
        validator.validate(value)
        with pytest.raises(ValidationError):validator.validate(dict(value,unknown_semantics=True))
