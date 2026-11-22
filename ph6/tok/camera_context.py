"""Downstream optical interpretation from an already replay-checked measurement.
PROPOSED codex-lane2, 2026-09-29; Authority ZERO; ratified_by=None.
"""
def soso_from_measurement(record):
    brightness=record['pseudo']['metrics']['mean_brightness_fp']
    state='STABLE' if brightness>1500000 else 'MODERATE' if brightness>800000 else 'UNSTABLE'
    return {'state':state,'authority':'ZERO','advisory_only':True,
            'interpretation_version':'ph6.soso.brightness.v1',
            'measurement_record_hash':record['record_hash']}


def legacy_context(context,rec):
    """Legacy context cannot acquire bound measurement provenance by being copied."""
    if context is None:return None,'UNAVAILABLE'
    if type(context) is not dict or '_invalid' in context:return None,'INVALID_CONTEXT'
    import json
    try:
        json.dumps(context,allow_nan=False)
        allowed={'schema','frame_id','verdict','reasons','metrics','motion_gate','input_hash',
                 'hash_algorithm','fixed_point_scale','authority','soso_advisory','timestamp_utc','capture_timestamp_ns'}
        if set(context)-allowed:return None,'INVALID_CONTEXT'
        if (context.get('schema') not in ('ph6.pseudo_verdict.v2','ph6.pseudo_verdict.v3','ph6.pseudo_verdict.camera.v1') or
            context.get('input_hash')!=rec['payload_hash'] or type(context.get('frame_id')) is not int or
            context['frame_id']!=rec['frame_id'] or context.get('authority')!='LANE_1' or
            context.get('hash_algorithm')!='BLAKE2b-256' or context.get('verdict')!='PASS'):
            return None,'INVALID_CONTEXT'
        metrics=context['metrics']
        camera=context['schema']=='ph6.pseudo_verdict.camera.v1'
        names={'metric_schema','metric_scale','laplacian_var_fp','motion_fraction_fp',
               'mean_brightness_fp' if camera else 'entropy_fp'}
        if set(metrics)!=names or metrics['metric_schema']!=('ph6.metrics.camera.fixedpoint.v1' if camera else 'ph6.metrics.fixedpoint.v1'):
            return None,'INVALID_CONTEXT'
        if type(metrics['metric_scale']) is not int or metrics['metric_scale']!=10000:return None,'INVALID_CONTEXT'
        if not all(type(v) is int and v>=0 for k,v in metrics.items() if k not in ('metric_schema','metric_scale')):return None,'INVALID_CONTEXT'
        if metrics['motion_fraction_fp']>10000:return None,'INVALID_CONTEXT'
        soso=context.get('soso_advisory')
        if soso is None:return None,'LEGACY_CONTEXT_UNVERIFIED'
        if (set(soso)!={'state','authority'} or soso['authority']!='NONE' or
            soso['state'] not in ('STABLE','MODERATE','UNSTABLE')):return None,'INVALID_CONTEXT'
        return {'state':soso['state'],'authority':'ZERO','advisory_only':True},'LEGACY_CONTEXT_UNVERIFIED'
    except (ValueError,TypeError,KeyError):return None,'INVALID_CONTEXT'
