"""Read-only MEASUREMENT_RECORD_V1 contract and deterministic optical profile.

PSEUDO owns metrics/disposition; consumers may verify but gain no authority.
No writers, hardware access, advisory imports, or implicit format migration.
PROPOSED codex-lane2, 2026-09-29; ratified_by=None; ADR-MR1-20260929.
"""
from __future__ import annotations
import hashlib
import json
import math
import re
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_EVEN
from pathlib import Path

ACQUISITION_SCHEMA = 'ph6.acquisition_commit.v1'
MEASUREMENT_SCHEMA = 'ph6.measurement_record.v1'
CRAM_SCHEMA = 'ph6.cram_commit.v2'
PROFILE = 'ph6.pseudo_vis.installed_camera.v1'
METRIC_SCHEMA = 'ph6.metrics.camera.fixedpoint.v2'
GENESIS = '0' * 64
CONFIG = {'metric_scale':10000, 'brightness_min_fp':200000,
          'brightness_max_fp':2350000, 'laplacian_min_fp':150000,
          'motion_max_fp':4000, 'motion_pixel_difference':15,
          'first_motion_policy':'ZERO_WITH_NO_PREDECESSOR_STATUS',
          'entropy_gate':'DISABLED', 'jpeg_quality':85}

class MeasurementIntegrityError(ValueError): pass

def canonical(value):
    return json.dumps(value,sort_keys=True,ensure_ascii=False,allow_nan=False,
                      separators=(',', ':')).encode('utf-8')

def byte_hash(data):return hashlib.blake2b(data,digest_size=32).hexdigest()
def digest(value):return byte_hash(canonical(value))
def seal(value):return dict(value,record_hash=digest(value))
def require(condition, message):
    if not condition:raise MeasurementIntegrityError(message)
def keys(value, names, label):
    require(type(value) is dict and set(value)==set(names.split()),'Malformed '+label+' fields')
def integer(value, minimum=0):return type(value) is int and value>=minimum
def hexhash(value):return type(value) is str and re.fullmatch('[0-9a-f]{64}',value) is not None
def fixed(value):
    number=Decimal(str(value))
    require(number.is_finite(),'Non-finite metric')
    return int((number*10000).to_integral_value(rounding=ROUND_HALF_EVEN))

def strict_load(path):
    def constant(value):raise MeasurementIntegrityError('Non-finite JSON value: '+value)
    def pairs(items):
        obj={}
        for k,v in items:
            require(k not in obj,'Duplicate JSON field: '+k);obj[k]=v
        return obj
    try:return json.loads(Path(path).read_text(),parse_constant=constant,object_pairs_hook=pairs)
    except (OSError,ValueError,TypeError) as e:raise MeasurementIntegrityError(str(e)) from e

def timestamp(value):
    require(type(value) is str and value.endswith('Z'),'Expected UTC timestamp_utc')
    try:datetime.fromisoformat(value.replace('Z','+00:00'))
    except ValueError as e:raise MeasurementIntegrityError('Invalid UTC timestamp') from e

def checked_file(root, relative):
    root=Path(root).resolve();path=root/relative
    require(type(relative) is str and not Path(relative).is_absolute(),'Absolute evidence reference')
    require('..' not in Path(relative).parts,'Escaping evidence reference')
    for p in [path,*path.parents]:
        if p==root:break
        require(not p.is_symlink(),'Symlink evidence reference')
    require(path.is_file(),'Missing evidence: '+relative)
    return path

def versions():
    import cv2
    import numpy as np
    import platform
    return {'opencv':cv2.__version__,'numpy':np.__version__, 'python':platform.python_version()}

def camera_metrics(frame, previous=None):
    """Same installed gates; entropy is recorded, never added to adjudication."""
    import cv2
    import numpy as np
    require(frame.dtype==np.uint8 and frame.ndim==3 and frame.shape[2]==3,'Expected BGR8 image')
    gray=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
    histogram=np.bincount(gray.ravel(),minlength=256)
    n=int(gray.size)
    entropy=-math.fsum((int(c)/n)*math.log2(int(c)/n) for c in histogram if c)
    if previous is None:motion=0.0
    else:
        prior=cv2.cvtColor(previous,cv2.COLOR_BGR2GRAY)
        require(prior.shape==gray.shape,'Motion predecessor dimensions differ')
        motion=float(np.mean(cv2.absdiff(gray,prior)>15))
    return {'metric_schema':METRIC_SCHEMA,'metric_scale':10000,
            'mean_brightness_fp':fixed(float(np.mean(gray))),
            'laplacian_var_fp':fixed(float(cv2.Laplacian(gray,cv2.CV_64F).var())),
            'motion_fraction_fp':fixed(motion),'entropy_fp':fixed(entropy),
            'motion_input_status':'NO_PREDECESSOR' if previous is None else 'MEASURED'}

def camera_disposition(metrics):
    reasons=[]
    if metrics['mean_brightness_fp']<CONFIG['brightness_min_fp']:reasons.append('brightness_low')
    if metrics['mean_brightness_fp']>CONFIG['brightness_max_fp']:reasons.append('brightness_high')
    if metrics['laplacian_var_fp']<CONFIG['laplacian_min_fp']:reasons.append('blur_low_detail')
    if metrics['motion_fraction_fp']>CONFIG['motion_max_fp']:reasons.append('motion_high')
    return ('PASS' if not reasons else 'DROP'),reasons

def validate_context(c):
    keys(c,'timestamp_utc wall_time_ns monotonic_timestamp_ns clock_scope sensor capture_configuration thermal_state io_state','acquisition context')
    timestamp(c['timestamp_utc'])
    require(integer(c['wall_time_ns'],1) and integer(c['monotonic_timestamp_ns'],1),'Invalid acquisition clock')
    instant=datetime.fromtimestamp(c['wall_time_ns']//1_000_000_000,timezone.utc).replace(microsecond=(c['wall_time_ns']%1_000_000_000)//1000)
    require(datetime.fromisoformat(c['timestamp_utc'].replace('Z','+00:00'))==instant,'Acquisition UTC/wall clock mismatch')
    require(c['clock_scope']=='HOST_AFTER_CAMERA_READ_NOT_EXPOSURE','Unknown acquisition clock semantics')
    sensor=c['sensor']
    keys(sensor,'device backend physical_identity calibration','sensor')
    require(all(type(sensor[k]) is str and sensor[k] for k in ('device','backend')),'Missing sensor locator')
    for k in ('physical_identity','calibration'):
        require(sensor[k]=={'status':'UNKNOWN','value':None},'Unsupported instrument identity/calibration claim')
    config=c['capture_configuration']
    keys(config,'width_px height_px stated_fps_fp exposure_fp gain_fp white_balance_fp focus_fp','capture configuration')
    require(integer(config['width_px'],1) and integer(config['height_px'],1),'Invalid image dimensions')
    for k in ('stated_fps_fp','exposure_fp','gain_fp','white_balance_fp','focus_fp'):
        sample=config[k];keys(sample,'status value','instrument property')
        require((sample['status']=='UNKNOWN' and sample['value'] is None) or
                (sample['status']=='DRIVER_REPORTED' and type(sample['value']) is int),'Invalid instrument property state')
    for key,field in [('thermal_state','host_temperature_millicelsius'),('io_state','free_bytes')]:
        value=c[key];keys(value,'status '+field,'acquisition state')
        require((value['status']=='UNKNOWN' and value[field] is None) or
                (value['status']=='OBSERVED' and integer(value[field])),'Invalid '+key)
    canonical(c)

def validate_acquisition(rec):
    keys(rec,'schema measurement_id run_id sequence_number context dimensions pixel_format layout acquisition_byte_hash hash_algorithm raw_ref previous_acquisition_hash pseudo_version pseudo_configuration_hash record_hash','acquisition')
    require(rec['schema']==ACQUISITION_SCHEMA,'Unknown acquisition schema')
    require(type(rec['run_id']) is str and re.fullmatch('[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}',rec['run_id']) is not None,'Malformed run identity')
    require(integer(rec['sequence_number'],1),'Malformed sequence number')
    shape=rec['dimensions'];require(type(shape) is list and len(shape)==3 and all(integer(x,1) for x in shape) and shape[2]==3,'Invalid BGR dimensions')
    require(shape[0]*shape[1]*3<=256*1024*1024,'Acquisition size limit')
    require(rec['pixel_format']=='BGR8_UINT8','Unknown pixel format')
    keys(rec['layout'],'order row_stride_bytes pixel_stride_bytes original_strides_bytes','layout')
    require(rec['layout']['order']=='C' and rec['layout']['row_stride_bytes']==shape[1]*3 and rec['layout']['pixel_stride_bytes']==3,'Invalid preserved layout')
    strides=rec['layout']['original_strides_bytes']
    require(type(strides) is list and len(strides)==3 and all(type(x) is int for x in strides),'Missing original layout')
    require(rec['hash_algorithm']=='BLAKE2b-256','Unknown hash algorithm')
    for k in ('acquisition_byte_hash','previous_acquisition_hash','record_hash'):require(hexhash(rec[k]),'Malformed '+k)
    require(rec['raw_ref']==f"acquisitions/acquisition_{rec['sequence_number']:010d}.bin",'Unknown acquisition byte reference')
    require(rec['pseudo_version']==PROFILE and rec['pseudo_configuration_hash']==digest(CONFIG),'Unknown PSEUDO profile/configuration')
    validate_context(rec['context'])
    require(rec['context']['capture_configuration']['width_px']==shape[1] and rec['context']['capture_configuration']['height_px']==shape[0],'Acquisition configuration dimensions mismatch')
    identity={k:rec[k] for k in ('run_id','sequence_number','acquisition_byte_hash')}
    identity['context_hash']=digest(rec['context'])
    require(rec['measurement_id']=='m_'+digest(identity),'Malformed measurement identity')
    require(digest({k:v for k,v in rec.items() if k!='record_hash'})==rec['record_hash'],'Acquisition commitment mismatch')

def read_acquisition(root,rec):
    import numpy as np
    validate_acquisition(rec)
    data=checked_file(root,rec['raw_ref']).read_bytes()
    require(len(data)==math.prod(rec['dimensions']) and byte_hash(data)==rec['acquisition_byte_hash'],'Original acquisition bytes mismatch')
    return np.frombuffer(data,dtype=np.uint8).reshape(rec['dimensions'])

def validate_measurement(root,rec,previous=None):
    keys(rec,'schema measurement_id sequence_number acquisition acquisition_record_hash pseudo disposition reasons encoded_payload previous_record_hash timestamp_utc record_hash','measurement record')
    require(rec['schema']==MEASUREMENT_SCHEMA,'Unknown measurement schema')
    acquisition=rec['acquisition'];frame=read_acquisition(root,acquisition)
    require(rec['measurement_id']==acquisition['measurement_id'] and rec['sequence_number']==acquisition['sequence_number'],'Measurement identity mismatch')
    require(type(rec['sequence_number']) is int and rec['acquisition_record_hash']==acquisition['record_hash'],'Measurement acquisition reference mismatch')
    ref=f"acquisitions/acquisition_{rec['sequence_number']:010d}.json"
    require(strict_load(checked_file(root,ref))==acquisition,'Acquisition commitment changed')
    predecessor=previous['record_hash'] if previous else GENESIS
    prior_acquisition=previous['acquisition'] if previous else None
    require(rec['previous_record_hash']==predecessor,'Measurement predecessor mismatch')
    require(acquisition['previous_acquisition_hash']==(prior_acquisition['record_hash'] if prior_acquisition else GENESIS),'Acquisition predecessor mismatch')
    require(rec['sequence_number']==(previous['sequence_number']+1 if previous else 1),'Missing measurement sequence')
    if previous:require(previous['acquisition']['run_id']==acquisition['run_id'],'Run identity changed')
    pseudo=rec['pseudo'];keys(pseudo,'version configuration configuration_hash library_versions inputs metrics','PSEUDO record')
    require(pseudo['version']==PROFILE and pseudo['configuration']==CONFIG and pseudo['configuration_hash']==digest(CONFIG),'Unknown PSEUDO semantics')
    require(pseudo['library_versions']==versions(),'Unsupported numerical replay environment')
    expected_inputs={'original_acquisition_hash':acquisition['acquisition_byte_hash'],
                     'previous_acquisition_hash':prior_acquisition['acquisition_byte_hash'] if prior_acquisition else None,
                     'previous_measurement_id':previous['measurement_id'] if previous else None,
                     'entropy_input':'BGR_TO_GRAY_ALL_PIXELS', 'laplacian_input':'BGR_TO_GRAY_CV64F',
                     'motion_input':'CURRENT_AND_PREVIOUS_GRAY_ABSDIFF_GT_15'}
    require(pseudo['inputs']==expected_inputs,'Unknown or nonexistent metric derivation input')
    prior=read_acquisition(root,prior_acquisition) if prior_acquisition else None
    expected_metrics=camera_metrics(frame,prior)
    require(canonical(pseudo['metrics'])==canonical(expected_metrics),'PSEUDO metrics mismatch')
    verdict,reasons=camera_disposition(expected_metrics)
    require(rec['disposition']==verdict and rec['reasons']==reasons,'Deterministic disposition mismatch')
    encoded=rec['encoded_payload'];keys(encoded,'path hash hash_algorithm size_bytes encoding','encoded payload')
    require(encoded['path']==f"payloads/frame_{rec['sequence_number']:010d}.bin",'Unknown encoded payload reference')
    require(encoded['hash_algorithm']=='BLAKE2b-256' and hexhash(encoded['hash']),'Invalid encoded hash')
    require(encoded['encoding']=={'format':'JPEG','quality':85,'encoder':'OpenCV','version':versions()['opencv']},'Unknown encoding parameters')
    data=checked_file(root,encoded['path']).read_bytes()
    require(integer(encoded['size_bytes'],1) and len(data)==encoded['size_bytes'] and byte_hash(data)==encoded['hash'],'Encoded payload mismatch')
    # Re-encoding verifies the declared derivation, not just two independently valid hashes.
    import cv2
    ok,jpeg=cv2.imencode('.jpg',frame,[cv2.IMWRITE_JPEG_QUALITY,85])
    require(ok and jpeg.tobytes()==data,'JPEG does not derive from committed original under declared encoder')
    timestamp(rec['timestamp_utc'])
    require(hexhash(rec['record_hash']) and digest({k:v for k,v in rec.items() if k!='record_hash'})==rec['record_hash'],'Measurement record hash mismatch')
    if verdict=='DROP':require(not (Path(root)/f"cram_{rec['sequence_number']:010d}.json.blake2b").exists(),'DROP has forbidden PASS marker')
    return rec

def read_measurements(root):
    """Read-only full measurement-chain verification; no silent partial semantic recovery."""
    result={};previous=None
    for path in sorted((Path(root)/'measurements').glob('measurement_*.json')):
        require(not path.is_symlink() and not path.parent.is_symlink(),'Symlink measurement')
        rec=strict_load(path)
        require(path.name==f"measurement_{len(result)+1:010d}.json",'Missing or malformed measurement filename')
        validate_measurement(root,rec,previous)
        result[rec['sequence_number']]=rec;previous=rec
    return result

def validate_commit_binding(rec,measurements):
    keys(rec,'schema frame_id payload_hash hash_algorithm verdict authority prev_cram_hash timestamp_utc measurement_id measurement_record_hash acquisition_byte_hash cram_hash','CRAM v2 commit')
    require(rec['schema']==CRAM_SCHEMA and type(rec['frame_id']) is int,'Invalid CRAM v2 identity')
    measurement=measurements.get(rec['frame_id'])
    require(measurement is not None,'Missing bound measurement')
    require(measurement['disposition']=='PASS' and rec['verdict']=='PASS' and rec['authority']=='LANE_1','Invalid preservation disposition')
    require(rec['measurement_id']==measurement['measurement_id'] and rec['measurement_record_hash']==measurement['record_hash'],'CRAM measurement binding mismatch')
    require(rec['payload_hash']==measurement['encoded_payload']['hash'] and rec['acquisition_byte_hash']==measurement['acquisition']['acquisition_byte_hash'],'CRAM payload binding mismatch')
    require(rec['timestamp_utc']==measurement['timestamp_utc'] and rec['hash_algorithm']=='BLAKE2b-256','CRAM contract mismatch')
    require(hexhash(rec['prev_cram_hash']) and digest({k:v for k,v in rec.items() if k!='cram_hash'})==rec['cram_hash'],'CRAM hash mismatch')
    return measurement
