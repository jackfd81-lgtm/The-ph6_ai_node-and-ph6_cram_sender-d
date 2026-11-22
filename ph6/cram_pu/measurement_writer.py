"""Lane-1 write-first optical acquisition and immutable measurement preservation.

PROPOSED codex-lane2, 2026-09-29; ratified_by=None; ADR-MR1-20260929.
Only this Lane-1 writer publishes PASS markers. No advisory callbacks/imports.
"""
from __future__ import annotations
import fcntl
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from ph6.measurement_record import (
    ACQUISITION_SCHEMA, MEASUREMENT_SCHEMA, CRAM_SCHEMA, CONFIG, PROFILE, GENESIS,
    canonical, byte_hash, digest, seal, require, strict_load, read_acquisition,
    validate_acquisition, validate_context, validate_measurement, versions, read_measurements,
    camera_metrics, camera_disposition, MeasurementIntegrityError,
)
from ph6.cram_pu._lane1_auth import mint_commit_authorization, verify_commit_authorization

def utc():return datetime.now(timezone.utc).isoformat(timespec='microseconds').replace('+00:00','Z')

def _fsync_dir(path):
    fd=os.open(str(path),os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(fd)
    finally:os.close(fd)

def _mkdir(path):
    if path.exists():
        require(path.is_dir() and not path.is_symlink(),'Invalid evidence directory')
        return
    path.mkdir()
    _fsync_dir(path.parent)

def _atomic_new(path,data):
    """Single-owner atomic publish. Existing evidence is never overwritten."""
    require(not path.is_symlink(),'Symlink evidence destination')
    if path.exists():
        require(path.read_bytes()==data,'Immutable evidence collision: '+str(path))
        _fsync_dir(path.parent)
        return
    tmp=path.with_name(path.name+'.'+uuid.uuid4().hex+'.tmp')
    fd=os.open(str(tmp),os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    try:
        with os.fdopen(fd,'wb') as stream:
            stream.write(data);stream.flush();os.fsync(stream.fileno())
        # The owner lock serializes all supported publishers of this namespace.
        require(not path.exists(),'Evidence appeared during publication')
        os.replace(tmp,path)
        _fsync_dir(path.parent)
    except BaseException:
        # Keep partial artifacts for inspection. A .tmp file is not a commitment.
        raise

def _json_new(path,value):_atomic_new(path,canonical(value)+b'\n')

def acquisition_context(inventory, cap, root, *, wall_time_ns=None, monotonic_ns=None):
    """Observe host/driver state. Unsupported controls are UNKNOWN, never guessed."""
    import cv2
    from ph6.measurement_record import fixed
    wall_time_ns=wall_time_ns if wall_time_ns is not None else time.time_ns()
    monotonic_ns=monotonic_ns if monotonic_ns is not None else time.monotonic_ns()
    stamp=datetime.fromtimestamp(wall_time_ns//1_000_000_000,timezone.utc).replace(microsecond=(wall_time_ns%1_000_000_000)//1000)
    def property_value(name):
        try:
            value=cap.get(getattr(cv2,name))
            # OpenCV returns zero both for unsupported controls and real zero.
            if value==0:return {'status':'UNKNOWN','value':None}
            return {'status':'DRIVER_REPORTED','value':fixed(value)}
        except (AttributeError,ValueError,TypeError,cv2.error):return {'status':'UNKNOWN','value':None}
    try:thermal={'status':'OBSERVED','host_temperature_millicelsius':int(Path('/sys/class/thermal/thermal_zone0/temp').read_text())}
    except (OSError,ValueError):thermal={'status':'UNKNOWN','host_temperature_millicelsius':None}
    try:
        disk=os.statvfs(root);io={'status':'OBSERVED','free_bytes':disk.f_bavail*disk.f_frsize}
    except OSError:io={'status':'UNKNOWN','free_bytes':None}
    context={'timestamp_utc':stamp.isoformat(timespec='microseconds').replace('+00:00','Z'),
        'wall_time_ns':wall_time_ns,'monotonic_timestamp_ns':monotonic_ns,
        'clock_scope':'HOST_AFTER_CAMERA_READ_NOT_EXPOSURE',
        'sensor':{'device':inventory['device'],'backend':inventory['backend'],
                  'physical_identity':{'status':'UNKNOWN','value':None},'calibration':{'status':'UNKNOWN','value':None}},
        'capture_configuration':{'width_px':inventory['width_px'],'height_px':inventory['height_px'],
            'stated_fps_fp':property_value('CAP_PROP_FPS'),'exposure_fp':property_value('CAP_PROP_EXPOSURE'),
            'gain_fp':property_value('CAP_PROP_GAIN'),'white_balance_fp':property_value('CAP_PROP_WB_TEMPERATURE'),
            'focus_fp':property_value('CAP_PROP_FOCUS')},'thermal_state':thermal,'io_state':io}
    validate_context(context)
    return context


def _commit_record(record, previous_pass):
    sequence=record['sequence_number'];payload_hash=record['encoded_payload']['hash']
    commit={'schema':CRAM_SCHEMA,'frame_id':sequence,'payload_hash':payload_hash,
            'hash_algorithm':'BLAKE2b-256','verdict':'PASS','authority':'LANE_1',
            'prev_cram_hash':previous_pass,'timestamp_utc':record['timestamp_utc'],
            'measurement_id':record['measurement_id'],'measurement_record_hash':record['record_hash'],
            'acquisition_byte_hash':record['acquisition']['acquisition_byte_hash']}
    commit['cram_hash']=digest(commit)
    return commit

class MeasurementWriter:
    """Single-owner new-format namespace. Startup verifies and resumes a valid tail.

    Legacy stores are never migrated. A corrupt final artifact stops recovery.
    A valid acquisition without a final record is remeasured from its original
    bytes. A valid final PASS record without its marker can finish publication.
    A partial raw file without acquisition context cannot be guessed/recovered.
    """
    def __init__(self,root):
        self.root=Path(root).resolve();self._lock=None
        marker=self.root/'measurement_run.json'
        if self.root.exists() and not marker.exists():
            require(not any(self.root.glob('cram_*.json')) and not any(self.root.glob('verdict_log.jsonl')),
                    'A legacy evidence namespace cannot be migrated in place')
        self.root.mkdir(parents=True,exist_ok=True)
        _fsync_dir(self.root.parent)
        lock=self.root/'.measurement-owner.lock'
        require(not lock.is_symlink(),'Symlink owner lock')
        self._lock=lock.open('a+b')
        try:
            fcntl.flock(self._lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
            for name in ('acquisitions','measurements','payloads'):_mkdir(self.root/name)
            if marker.exists():
                run=strict_load(marker)
                require(set(run)=={'schema','run_id','pseudo_version','configuration_hash'},'Malformed measurement run')
                require(run['schema']=='ph6.measurement_run.v1' and run['pseudo_version']==PROFILE and run['configuration_hash']==digest(CONFIG),'Unknown measurement run semantics')
                self.run_id=run['run_id']
            else:
                self.run_id=str(uuid.uuid4())
                _json_new(marker,{'schema':'ph6.measurement_run.v1','run_id':self.run_id,'pseudo_version':PROFILE,'configuration_hash':digest(CONFIG)})
            self.previous=None;self.previous_pass=GENESIS;self.pending=None;self.next_sequence=1
            self.recovered=[]
            self._recover()
        except BaseException:
            self.close();raise

    def close(self):
        if self._lock is not None:self._lock.close();self._lock=None
    def __enter__(self):return self
    def __exit__(self,*_):self.close()

    def _recover(self):
        acquisitions=sorted((self.root/'acquisitions').glob('acquisition_*.json'))
        measurements=list((self.root/'measurements').glob('measurement_*.json'))
        expected_raw={p.with_suffix('.bin').name for p in acquisitions}
        require({p.name for p in (self.root/'acquisitions').glob('acquisition_*.bin')}==expected_raw,
                'Orphan original bytes without immutable acquisition context; unresolved')
        require(len(measurements)<=len(acquisitions),'Measurement exists without acquisition')
        # Verify the entire existing namespace before any recovery publication.
        # Supported crashes leave a complete prefix and at most one pending intake.
        completed=read_measurements(self.root)
        require(len(acquisitions)-len(completed) in (0,1),'Multiple pending acquisitions; unresolved')
        previous_acquisition=GENESIS
        for index,path in enumerate(acquisitions,1):
            require(path.name==f'acquisition_{index:010d}.json' and not path.is_symlink(),'Missing acquisition sequence or symlink')
            acq=strict_load(path);read_acquisition(self.root,acq)
            require(acq['run_id']==self.run_id and acq['sequence_number']==index,'Acquisition run/sequence mismatch')
            require(acq['previous_acquisition_hash']==previous_acquisition,'Acquisition predecessor mismatch')
            previous_acquisition=acq['record_hash']
        pass_names=set();previous_pass=GENESIS
        for record in completed.values():
            if record['disposition']=='PASS':
                commit=_commit_record(record,previous_pass);previous_pass=commit['cram_hash']
                name=f"cram_{record['sequence_number']:010d}.json";pass_names.add(name)
                existing=self.root/name;marker=self.root/(name+'.blake2b')
                require(not existing.is_symlink() and not marker.is_symlink(),'Symlink commit artifact')
                if existing.exists():require(existing.read_bytes()==canonical(commit)+b'\n','Existing CRAM commit mismatch')
                if marker.exists():
                    require(existing.exists() and marker.read_bytes()==(commit['cram_hash']+'\n').encode(),'Existing marker mismatch')
        require({p.name for p in self.root.glob('cram_*.json')}<=pass_names,'Unbound CRAM commit present')
        require({p.name for p in self.root.glob('cram_*.json.blake2b')}<={n+'.blake2b' for n in pass_names},'Unbound PASS marker present')
        for p in acquisitions:
            expected=self.next_sequence
            require(p.name==f'acquisition_{expected:010d}.json' and not p.is_symlink(),'Missing acquisition sequence or symlink')
            acq=strict_load(p);read_acquisition(self.root,acq)
            require(acq['run_id']==self.run_id and acq['sequence_number']==expected,'Acquisition run/sequence mismatch')
            require(acq['previous_acquisition_hash']==(self.previous['acquisition_record_hash'] if self.previous else GENESIS),'Acquisition predecessor mismatch')
            final=self.root/'measurements'/f'measurement_{expected:010d}.json'
            self.pending=acq
            if final.exists():
                record=strict_load(final);validate_measurement(self.root,record,self.previous)
                require(record['acquisition']==acq,'Final measurement references another acquisition')
                was_complete=(self.root/f'cram_{expected:010d}.json.blake2b').exists() if record['disposition']=='PASS' else True
                self._preserve_disposition(record)
                if not was_complete:self.recovered.append(record['measurement_id'])
                self.previous=record;self.pending=None;self.next_sequence+=1
            else:
                record=self.finalize();self.recovered.append(record['measurement_id'])
        require({p.name for p in (self.root/'measurements').glob('measurement_*.json')}==
                {f'measurement_{i:010d}.json' for i in range(1,self.next_sequence)},'Unknown measurement record filename')
        # Refuse unknown final records, including PASS records without a measurement.
        expected_pass={f"cram_{r['sequence_number']:010d}.json" for r in self._records() if r['disposition']=='PASS'}
        require({p.name for p in self.root.glob('cram_*.json')}==expected_pass,'Unbound CRAM commit present')

    def _records(self):
        return [strict_load(p) for p in sorted((self.root/'measurements').glob('measurement_*.json'))]

    def begin(self,frame,context):
        import numpy as np
        require(self._lock is not None and not self._lock.closed,'Writer does not hold ownership')
        require(self.pending is None,'Prior acquisition has not completed preservation')
        require(frame.dtype==np.uint8 and frame.ndim==3 and frame.shape[2]==3,'Expected acquisition BGR8')
        validate_context(context)
        sequence=self.next_sequence
        # These exact packed image bytes are durably retained before PSEUDO runs.
        raw=np.ascontiguousarray(frame).tobytes(order='C')
        raw_hash=byte_hash(raw)
        identity={'run_id':self.run_id,'sequence_number':sequence,'acquisition_byte_hash':raw_hash,'context_hash':digest(context)}
        rec=seal({'schema':ACQUISITION_SCHEMA,'measurement_id':'m_'+digest(identity),
            'run_id':self.run_id,'sequence_number':sequence,'context':context,
            'dimensions':list(frame.shape),'pixel_format':'BGR8_UINT8',
            'layout':{'order':'C','row_stride_bytes':frame.shape[1]*3,'pixel_stride_bytes':3,'original_strides_bytes':list(frame.strides)},
            'acquisition_byte_hash':raw_hash,'hash_algorithm':'BLAKE2b-256',
            'raw_ref':f'acquisitions/acquisition_{sequence:010d}.bin',
            'previous_acquisition_hash':self.previous['acquisition_record_hash'] if self.previous else GENESIS,
            'pseudo_version':PROFILE,'pseudo_configuration_hash':digest(CONFIG)})
        validate_acquisition(rec)
        _atomic_new(self.root/rec['raw_ref'],raw)
        _json_new(self.root/'acquisitions'/f'acquisition_{sequence:010d}.json',rec)
        # Reload, so neither caller mutation nor an in-memory image substitutes for preserved input.
        self.pending=strict_load(self.root/'acquisitions'/f'acquisition_{sequence:010d}.json')
        return self.pending

    def finalize(self):
        import cv2
        require(self._lock is not None and not self._lock.closed,'Writer does not hold ownership')
        require(self.pending is not None,'No acquisition to finalize')
        acq=self.pending;sequence=acq['sequence_number']
        frame=read_acquisition(self.root,acq)
        prev_acq=self.previous['acquisition'] if self.previous else None
        previous=read_acquisition(self.root,prev_acq) if prev_acq else None
        metrics=camera_metrics(frame,previous)
        disposition,reasons=camera_disposition(metrics)
        ok,buffer=cv2.imencode('.jpg',frame,[cv2.IMWRITE_JPEG_QUALITY,CONFIG['jpeg_quality']])
        require(ok,'JPEG encoding failed; original acquisition remains preserved')
        payload=buffer.tobytes();payload_path=f'payloads/frame_{sequence:010d}.bin'
        _atomic_new(self.root/payload_path,payload)
        record=seal({'schema':MEASUREMENT_SCHEMA,'measurement_id':acq['measurement_id'],
            'sequence_number':sequence,'acquisition':acq,'acquisition_record_hash':acq['record_hash'],
            'pseudo':{'version':PROFILE,'configuration':dict(CONFIG),'configuration_hash':digest(CONFIG),
                'library_versions':versions(),'inputs':{'original_acquisition_hash':acq['acquisition_byte_hash'],
                    'previous_acquisition_hash':prev_acq['acquisition_byte_hash'] if prev_acq else None,
                    'previous_measurement_id':self.previous['measurement_id'] if self.previous else None,
                    'entropy_input':'BGR_TO_GRAY_ALL_PIXELS','laplacian_input':'BGR_TO_GRAY_CV64F',
                    'motion_input':'CURRENT_AND_PREVIOUS_GRAY_ABSDIFF_GT_15'},'metrics':metrics},
            'disposition':disposition,'reasons':reasons,
            'encoded_payload':{'path':payload_path,'hash':byte_hash(payload),'hash_algorithm':'BLAKE2b-256',
                'size_bytes':len(payload),'encoding':{'format':'JPEG','quality':85,'encoder':'OpenCV','version':versions()['opencv']}},
            'previous_record_hash':self.previous['record_hash'] if self.previous else GENESIS,
            'timestamp_utc':utc()})
        validate_measurement(self.root,record,self.previous)
        _json_new(self.root/'measurements'/f'measurement_{sequence:010d}.json',record)
        self._preserve_disposition(record)
        self.previous=record;self.pending=None;self.next_sequence+=1
        return record

    def _preserve_disposition(self,record):
        sequence=record['sequence_number']
        marker=self.root/f'cram_{sequence:010d}.json.blake2b'
        if record['disposition']=='DROP':
            require(not marker.exists() and not (self.root/f'cram_{sequence:010d}.json').exists(),'DROP has a PASS artifact')
            return # immutable hashed measurement is the DROP record; no .blake2b marker
        payload_hash=record['encoded_payload']['hash']
        auth_fields={'frame_id':sequence,'payload_hash':payload_hash,'verdict':'PASS','measurement_record_hash':record['record_hash']}
        authorization=mint_commit_authorization(**auth_fields)
        verify_commit_authorization(authorization,**auth_fields)
        commit=_commit_record(record,self.previous_pass)
        _json_new(self.root/f'cram_{sequence:010d}.json',commit)
        # LAST: all original bytes, context, encoded payload, measurement and CRAM JSON are durable.
        _atomic_new(marker,(commit['cram_hash']+'\n').encode())
        self.previous_pass=commit['cram_hash']
