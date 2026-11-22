#!/usr/bin/env python3
"""CAM-3000 installed-runtime qualification. Advisory TESTED evidence only.
Run via sudo: capture/service commands are explicitly executed as user jack.
Timing thresholds are proposed test limits, not PSEUDO rules. No auto recovery.
PROPOSED codex-lane2 2026-09-19, ratified_by=None.
"""
import argparse
import contextlib
import datetime
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import threading
import time
import uuid

ROOT=Path('/home/jack')
sys.path.insert(0,str(ROOT))
from ph6.advisory_chain import locked, verified_tip, digest
from ph6.ssmt.async_client import submit_reference

UNIT='ph6-advisory.service'
SWARMS=Path('/var/ph6/mram-s/swarms/async-v1')
SOCKET='/run/user/1000/ph6-advisory/input.sock'
AUDIT=SWARMS/'ssmt_audit.jsonl'
CHECKPOINT=Path(str(AUDIT)+'.checkpoint.json')
TARGET=3000
USER_PREFIX=['runuser','-u','jack','--','env','XDG_RUNTIME_DIR=/run/user/1000','DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus']


def command(args,timeout=30,required=False):
    try:
        p=subprocess.run(args,capture_output=True,text=True,timeout=timeout,cwd=ROOT)
        result={'args':args,'rc':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
    except Exception as error:
        result={'args':args,'rc':-1,'error':repr(error)}
    if required and result['rc']!=0:
        raise RuntimeError(json.dumps(result))
    return result


def user(args,**kwargs):
    return command((USER_PREFIX if os.geteuid()==0 else [])+args,**kwargs)


def service(action,required=True):
    return user(['systemctl','--user',action,UNIT],required=required)


def show():
    result=user(['systemctl','--user','show',UNIT,'-p','ActiveState','-p','SubState','-p','MainPID','-p','ControlGroup','-p','CPUUsageNSec','-p','MemoryCurrent','-p','TasksCurrent'],required=True)
    return dict(line.split('=',1) for line in result['stdout'].splitlines() if '=' in line)


def write(path,obj):
    path.write_text(json.dumps(obj,indent=2,sort_keys=True,allow_nan=False)+'\n')


def hash_file(path):
    h=hashlib.blake2b(digest_size=32)
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()


def manifest(path):
    if not path.is_dir():raise ValueError('Missing evidence directory')
    return {str(f.relative_to(path)):hash_file(f) for f in sorted(path.rglob('*')) if f.is_file()}


def snapshot(destination):
    # Shares the writer lock so checkpoint and log represent one durable state.
    with locked(AUDIT):
        count,tail=verified_tip(AUDIT,'0'*64,sequence=True)
        ck=json.loads(CHECKPOINT.read_text())
        if ck!={'count':count,'tail':tail}:raise ValueError('Live log/checkpoint mismatch; preserved recovery required')
        shutil.copyfile(AUDIT,destination/'ssmt_audit.jsonl')
        shutil.copyfile(CHECKPOINT,destination/'ssmt_audit.jsonl.checkpoint.json')
    return ck


def sample():
    state=show();state['mono']=time.monotonic();state['wall_ns']=time.time_ns()
    group=state.get('ControlGroup')
    if group:
        cg=Path('/sys/fs/cgroup')/group.lstrip('/')
        state['kernel']={}
        for name in ['cpu.max','cpu.stat','memory.max','memory.current','memory.events','memory.swap.max','pids.max','pids.current','cgroup.procs']:
            try:state['kernel'][name]=(cg/name).read_text().strip()
            except OSError:state['kernel'][name]=None
        state['pid_start_ticks']={}
        for pid in (state['kernel'].get('cgroup.procs') or '').split():
            try:state['pid_start_ticks'][pid]=Path('/proc',pid,'stat').read_text().rsplit(')',1)[1].split()[19]
            except OSError:pass
        if int(state.get('MainPID','0'))>0:
            state['io_priority']=command(['ionice','-p',state['MainPID']])
    return state


def stats(values):
    if not values or any(not math.isfinite(v) or v<=0 for v in values):raise ValueError('Missing, nonfinite or nonpositive timing')
    values=sorted(values);return {'mean':sum(values)/len(values),'p99':values[math.ceil(.99*len(values))-1],'max':values[-1]}


def load_frames(path):
    rows=[];previous=None
    for line in path.read_text().splitlines():
        if not line.strip():raise ValueError('Blank frame record')
        r=json.loads(line)
        if not isinstance(r,dict) or type(r.get('seq')) is not int:raise ValueError('Invalid frame sequence')
        for name in ['latency_sec','mono_ts']:
            if type(r.get(name)) not in (float,int) or not math.isfinite(r[name]) or r[name]<=0:raise ValueError('Invalid numeric timing')
        if previous is not None and r['mono_ts']<=previous:raise ValueError('Nonmonotonic frame timing')
        previous=r['mono_ts'];rows.append(r)
    if len(rows)<2:raise ValueError('At least two frames required')
    return rows


def verify_checkpoint(directory,before=None):
    path=directory/'ssmt_audit.jsonl';ck=json.loads((directory/'ssmt_audit.jsonl.checkpoint.json').read_text())
    count,tail=verified_tip(path,'0'*64,sequence=True)
    if type(ck.get('count')) is not int or ck!={'count':count,'tail':tail}:raise ValueError('Snapshot checkpoint mismatch')
    if before:
        if count<before['count']:raise ValueError('Audit rollback')
        rows=path.read_text().splitlines()
        anchored='0'*64 if before['count']==0 else json.loads(rows[before['count']-1])['event_hash']
        if anchored!=before['tail']:raise ValueError('Audit history rewrite')
    return ck


def verify_cram(directory):
    store=directory/'capture/cram_store';verdicts=[json.loads(line) for line in (store/'verdict_log.jsonl').read_text().splitlines()]
    if len({v['frame_id'] for v in verdicts})!=len(verdicts):raise ValueError('Duplicate verdict IDs')
    previous='GENESIS';commits=0
    for v in verdicts:
        fid=v['frame_id'];payload=store/'payloads'/f'frame_{fid:010d}.bin'
        # The writer uses frame_##########.bin; never assume another path silently.
        if hash_file(payload)!=v['input_hash']:raise ValueError('Payload hash mismatch')
        record_path=store/f'cram_{fid:010d}.json';marker=Path(str(record_path)+'.blake2b')
        if v['verdict']=='PASS':
            record=json.loads(record_path.read_text());h=record.pop('cram_hash')
            if digest(record)!=h or marker.read_text().strip()!=h:raise ValueError('Commit hash/marker mismatch')
            if record['payload_hash']!=v['input_hash'] or record['frame_id']!=fid:raise ValueError('Commit identity mismatch')
            if commits and record['prev_cram_hash']!=previous:raise ValueError('Commit predecessor mismatch')
            if not commits and record['prev_cram_hash'] not in ('GENESIS','0'*64,None):raise ValueError('Unexpected genesis')
            previous=h;commits+=1
        elif v['verdict']=='DROP':
            if marker.exists() or record_path.exists():raise ValueError('Unexpected authoritative record for DROP')
        else:raise ValueError('Invalid verdict vocabulary')
    return {'verdicts':len(verdicts),'commits':commits,'tail':previous}


def freeze_stress_packets(directory,before):
    """Preserve packet bodies needed to attribute this run's audit events."""
    destination=directory/'audited-packets';destination.mkdir(exist_ok=True)
    events=[json.loads(line) for line in (directory/'ssmt_audit.jsonl').read_text().splitlines()]
    for event in events[before['count']:]:
        name=event['object_id']
        if not name or Path(name).name!=name:raise ValueError('Invalid packet snapshot name')
        shutil.copyfile(event['packet_path'],destination/name)


def verify_stress(directory,before):
    """Queue admission is insufficient: all nine swarms must produce evidence."""
    stress=json.loads((directory/'stress.json').read_text())
    if stress['accepted']<1:raise ValueError('No stress accepted by worker')
    reference=json.loads((directory/'stress-input.json').read_text())
    expected=reference.pop('cram_hash')
    if digest(reference)!=expected or stress.get('reference_hash')!=expected:
        raise ValueError('Stress reference hash mismatch')
    checkpoint=verify_checkpoint(directory,before)
    events=[json.loads(line) for line in (directory/'ssmt_audit.jsonl').read_text().splitlines()][before['count']:]
    matched=[]
    for event in events:
        name=event['object_id']
        if not name or Path(name).name!=name:raise ValueError('Invalid packet snapshot name')
        packet=json.loads((directory/'audited-packets'/name).read_text())
        if digest(packet)!=event['packet_hash']:raise ValueError('Audited packet hash mismatch')
        if packet.get('cram_packet_hash')==expected:matched.append(packet)
    swarms={packet.get('swarm_id') for packet in matched}
    if swarms!={f'S{i}' for i in range(1,10)}:
        raise ValueError('No completed stress coverage across all nine swarms')
    return dict(stress,new_audited_packets=checkpoint['count']-before['count'],
                stress_packets_written=len(matched),stress_swarms=sorted(swarms))


def evaluate(directory,label,target=TARGET):
    checks={};details={}
    seal=directory/'evidence-manifest.blake2b.json'
    if seal.exists():
        entries=json.loads(seal.read_text())
        if any(not (directory/name).is_file() or hash_file(directory/name)!=expected for name,expected in entries.items()):
            raise ValueError('Run-local evidence manifest mismatch')
    def check(name,fn):
        try:
            result=fn();details[name]=result;checks[name]='PASS'
        except Exception as error:checks[name]='FAIL';details[name]=str(error)
    def frames_check():
        rows=load_frames(directory/'frame_metrics.jsonl')
        if [r['seq'] for r in rows]!=list(range(1,target+1)):raise ValueError('Wrong frame count/order')
        if any(r.get('error_count',0) or r.get('capture_fail_count',0) for r in rows):raise ValueError('Capture reported errors')
        return {'frames':len(rows),'advisory_enqueued':sum(r.get('advisory_enqueued') is True for r in rows),'advisory_shed':sum(r.get('advisory_enqueued') is False for r in rows)}
    check('frames',frames_check)
    def timing_check():
        rows=load_frames(directory/'frame_metrics.jsonl');lat=stats([r['latency_sec'] for r in rows]);delta=stats([b['mono_ts']-a['mono_ts'] for a,b in zip(rows,rows[1:])]);details['timing_metrics']={'latency':lat,'interframe':delta}
        if any(s['mean']>.100 or s['p99']>.110 or s['max']>.150 for s in (lat,delta)):raise ValueError('Proposed latency limits exceeded')
        return details['timing_metrics']
    check('proposed_timing',timing_check)
    if label in ('B','C'):
        def regression():
            prior=json.loads((directory.parent/'run_a/evaluation.json').read_text())
            if prior['checks'].get('frames')!='PASS':raise ValueError('Invalid A frame baseline')
            baseline=prior['details']['timing_metrics'];current=details['timing_metrics']
            rates={key:current[key]['mean']/baseline[key]['mean'] for key in ('latency','interframe')}
            if any(r>1.05 for r in rates.values()):raise ValueError('Regression exceeds 5%: '+str(rates))
            return rates
        check('regression_vs_A',regression)
    check('cram_payloads_commits_markers',lambda:verify_cram(directory))
    before=json.loads((directory/'preflight.json').read_text())
    check('audit_checkpoint',lambda:verify_checkpoint(directory,before['checkpoint']))
    run=json.loads((directory/'execution.json').read_text())
    def execution():
        if run.get('error') or run.get('snapshot_error') or run.get('capture_rc')!=0:raise ValueError(str(run))
        return {'capture_rc':0}
    check('capture_execution',execution)
    samples=[json.loads(line) for line in (directory/'samples.jsonl').read_text().splitlines()]
    if label!='A':
        def limits():
            active=[s for s in samples if s.get('ActiveState')=='active']
            if not active:raise ValueError('No active worker samples')
            if label in ('B','C') and len(active)!=len(samples):raise ValueError('Worker inactive or sample missing during run')
            peak_mem=peak_tasks=0
            for s in active:
                k=s['kernel'];q,p=k['cpu.max'].split()
                if q=='max' or not 0<int(q)/int(p)<=.3:raise ValueError('CPU cap not enforced')
                if not 0<int(k['memory.max'])<=512000000 or k['memory.swap.max']!='0':raise ValueError('Memory/swap cap not enforced')
                if not 0<int(k['pids.max'])<=16:raise ValueError('Task cap not enforced')
                if 'idle' not in s.get('io_priority',{}).get('stdout',''):raise ValueError('IO priority not idle')
                peak_mem=max(peak_mem,int(k['memory.current']));peak_tasks=max(peak_tasks,int(k['pids.current']))
            if peak_mem>512000000 or peak_tasks>16:raise ValueError('Observed memory/task budget exceeded')
            return {'samples':len(active),'peak_memory':peak_mem,'peak_tasks':peak_tasks}
        check('kernel_resource_caps',limits)
    def isolation():
        setup=json.loads((directory/'audit-setup.json').read_text());query=json.loads((directory/'audit-query.json').read_text())
        if setup['rc']!=0 or query['rc']!=0:raise ValueError('Audit evidence unavailable')
        end=json.loads((directory/'audit-status-after.json').read_text())
        initial=before['audit_status']['stdout']
        def lost(text):return int(re.search(r'^lost\s+(\d+)',text,re.M)[1])
        if end['rc']!=0 or lost(end['stdout'])!=lost(initial):raise ValueError('Kernel audit events lost')
        known={int(pid) for s in samples for pid in s.get('pid_start_ticks',{})}
        for s in samples:
            if int(s.get('MainPID','0')):known.add(int(s['MainPID']))
        if label!='A' and not known:raise ValueError('No worker identities observed')
        events=[]
        for line in query['stdout'].splitlines():
            if 'type=SYSCALL' not in line:continue
            fields=dict(re.findall(r'(?:^|\s)(pid|ppid|success)=([^\s]+)',line))
            if 'pid' in fields:events.append(fields)
        changed=True
        while changed:
            changed=False
            for e in events:
                if int(e.get('ppid','0')) in known and int(e['pid']) not in known:known.add(int(e['pid']));changed=True
        touches=[e for e in events if int(e['pid']) in known]
        if touches:raise ValueError('Worker/descendant CRAM access events: '+str(touches[:5]))
        prior=json.loads((directory/'cram-before.json').read_text());after=json.loads((directory/'cram-after.json').read_text())
        altered=[p for p,h in prior.items() if after.get(p)!=h]
        if altered:raise ValueError('Pre-existing protected files changed')
        if not events:raise ValueError('No positive capture audit events; watch effectiveness unproven')
        return {'capture_syscall_events':len(events),'worker_pids':sorted(known),'worker_events':0}
    check('observed_authority_isolation',isolation)
    if label=='C':
        check('message_driven_stress',lambda:verify_stress(directory,before['checkpoint']))
    if label=='D':
        def kill():
            k=json.loads((directory/'kill.json').read_text());rows=load_frames(directory/'frame_metrics.jsonl')
            if k['result']['rc']!=0 or k['before_pid']<=0 or k['after_pid']!=0 or not 1500<=k['frame']<target:raise ValueError('Kill not established')
            pre=[r['latency_sec'] for r in rows if r['mono_ts']<k['mono']];post=[r['latency_sec'] for r in rows if r['mono_ts']>=k['mono']]
            if not pre or not post or stats(post)['mean']>stats(pre)['mean']*1.05:raise ValueError('Post-kill regression or absent windows')
            return {'frame':k['frame'],'pre':stats(pre),'post':stats(post)}
        check('capture_survived_kill',kill)
        def recovery():
            r=json.loads((directory/'restart.json').read_text())
            if not r.get('resumed') or r.get('new_events',0)<9:raise ValueError(str(r))
            return r
        check('explicit_restart_progress',recovery)
    overall='TESTED_PASS' if checks and all(v=='PASS' for v in checks.values()) else 'TESTED_FAIL'
    result={'run':label,'overall':overall,'checks':checks,'details':details,'scope':'Host frame continuity and proposed timing; observed audit isolation. No driver-sequence or remote RSYNC proof. No human verification.'}
    write(directory/'evaluation.json',result);return result


def run(label,out_root,timeout=1800):
    directory=out_root/f'run_{label.lower()}'
    directory.mkdir(parents=True,exist_ok=False);os.chown(directory,1000,1000)
    capture=directory/'capture';store=capture/'cram_store';store.mkdir(parents=True)
    for p in [capture,store]:os.chown(p,1000,1000)
    original=show()['ActiveState'];key='ph6cam_'+uuid.uuid4().hex[:16]
    stop=threading.Event();threads=[];cap=None;rule=False;result={};stress={'accepted':0,'shed':0,'kind':'References queued to the existing caged SSMT worker; no external CPU stress process'}
    def collect():
        with (directory/'samples.jsonl').open('a') as stream:
            while not stop.is_set():
                try:record=sample()
                except Exception as error:record={'error':repr(error),'mono':time.monotonic()}
                stream.write(json.dumps(record)+'\n');stream.flush();stop.wait(1)
    def load():
        reference=ROOT/'PH6_LOCAL_BACKUPS/component-audit-e565a6e1/four-pass/pass_1/cram_store/cram_0000000001.json'
        h=json.loads(reference.read_text())['cram_hash']
        shutil.copyfile(reference,directory/'stress-input.json')
        stress['reference_hash']=h
        while not stop.is_set():
            accepted=submit_reference(str(reference),h,socket_path=SOCKET)
            stress['accepted' if accepted else 'shed']+=1;stop.wait(.02)
    try:
        # Reset C's ephemeral queue so B's backlog cannot masquerade as stress work.
        # Existing audit history and checkpoint remain intact.
        service('restart' if label=='C' else ('stop' if label=='A' else 'start'));time.sleep(1)
        if label!='A' and show()['ActiveState']!='active':raise RuntimeError('Worker did not start')
        checkpoint=snapshot(directory)
        pf={'label':label,'git':command(['git','rev-parse','HEAD']),'dirty_diff':command(['git','diff','--stat']),'unit':user(['systemctl','--user','cat',UNIT]),'checkpoint':checkpoint,'sample':sample(),'audit_status':command(['/usr/sbin/auditctl','-s'],required=True),'original_service_state':original}
        pf['advisory_queue_reset']=label=='C'
        write(directory/'preflight.json',pf);write(directory/'cram-before.json',manifest(store))
        setup=command(['/usr/sbin/auditctl','-w',str(store),'-p','wa','-k',key]);write(directory/'audit-setup.json',setup)
        if setup['rc']!=0:raise RuntimeError('Audit watch installation failed')
        rule=True;thread=threading.Thread(target=collect,daemon=True);thread.start();threads.append(thread)
        if label=='C':
            thread=threading.Thread(target=load,daemon=True);thread.start();threads.append(thread)
        args=USER_PREFIX+['/usr/bin/python3',str(ROOT/'ph6/cram_pu/tools/life_cram_lcc_01_live_camera.py'),'--frames',str(TARGET),'--device','/dev/video0','--run-dir',str(capture),'--metrics-log',str(directory/'frame_metrics.jsonl')]
        write(directory/'capture-command.json',args)
        with (directory/'capture.stdout.log').open('w') as stdout:
            cap=subprocess.Popen(args,cwd=ROOT,stdout=stdout,stderr=subprocess.STDOUT,start_new_session=True)
            started=time.monotonic();killed=False;last_count=-1;last_print=0
            while cap.poll() is None:
                if time.monotonic()-started>timeout:raise TimeoutError('Capture deadline exceeded')
                try:n=sum(1 for _ in (directory/'frame_metrics.jsonl').open())
                except FileNotFoundError:n=0
                if label=='D' and not killed and n>=1500:
                    before=int(show()['MainPID']);mono=time.monotonic();kr=user(['systemctl','--user','kill','-s','SIGKILL',UNIT]);time.sleep(.2)
                    after=int(show()['MainPID']);write(directory/'kill.json',{'frame':n,'mono':mono,'before_pid':before,'after_pid':after,'result':kr});killed=True
                if time.monotonic()-last_print>20:
                    print(f'RUN {label}: {n}/{TARGET} frames',flush=True);last_print=time.monotonic()
                time.sleep(.1)
            result['capture_rc']=cap.returncode
        if label=='D':
            restart={'resumed':False}
            try:
                before_ck=verify_checkpoint_live();service('start');time.sleep(.5)
                ref=next(store.glob('cram_*.json'));h=json.loads(ref.read_text())['cram_hash']
                if not submit_reference(str(ref),h,socket_path=SOCKET):raise RuntimeError('Restart notification unavailable')
                for _ in range(100):
                    ck=verify_checkpoint_live()
                    if ck['count']>=before_ck['count']+9:break
                    time.sleep(.1)
                restart={'resumed':show()['ActiveState']=='active' and ck['count']>=before_ck['count']+9,'new_events':ck['count']-before_ck['count'],'new_pid':int(show()['MainPID'])}
            except Exception as error:restart['error']=repr(error)
            write(directory/'restart.json',restart)
    except Exception as error:
        result['error']=repr(error)
    finally:
        if cap is not None and cap.poll() is None:
            os.killpg(cap.pid,signal.SIGTERM)
            try:cap.wait(timeout=10)
            except subprocess.TimeoutExpired:os.killpg(cap.pid,signal.SIGKILL);cap.wait()
            result['capture_rc']=cap.returncode
        stop.set()
        for thread in threads:thread.join(35)
        write(directory/'stress.json',stress)
        if rule:
            # Removing only our UUID-keyed watch; query preserved kernel records after drain.
            write(directory/'audit-remove.json',command(['/usr/sbin/auditctl','-W',str(store),'-p','wa','-k',key]))
            time.sleep(2)
            write(directory/'audit-query.json',command(['/usr/sbin/ausearch','-k',key,'--raw'],timeout=120))
        write(directory/'audit-status-after.json',command(['/usr/sbin/auditctl','-s']))
        try:
            snapshot(directory)
            if label=='C':freeze_stress_packets(directory,pf['checkpoint'])
        except Exception as error:result['snapshot_error']=repr(error)
        write(directory/'cram-after.json',manifest(store))
        write(directory/'execution.json',result)
        restoration=service('start' if original=='active' else 'stop',required=False)
        write(directory/'service-restoration.json',restoration)
    try:r=evaluate(directory,label)
    except Exception as error:
        r={'run':label,'overall':'TESTED_FAIL','error':repr(error)};write(directory/'evaluation.json',r)
    write(directory/'evidence-manifest.blake2b.json',manifest(directory))
    print(json.dumps(r),flush=True)
    return r


def verify_checkpoint_live():
    with locked(AUDIT):
        n,h=verified_tip(AUDIT,'0'*64,sequence=True);ck=json.loads(CHECKPOINT.read_text())
        if ck!={'count':n,'tail':h}:raise ValueError('Interrupted audit/checkpoint transaction; no auto recovery')
        return ck


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run',choices=['A','B','C','D','ALL'],required=True);p.add_argument('--output-dir',type=Path,required=True);p.add_argument('--evaluate-only',action='store_true');p.add_argument('--timeout',type=int,default=1800);a=p.parse_args()
    if not a.evaluate_only and os.geteuid()!=0:raise SystemExit('Root harness required for auditctl; capture and user service remain jack-owned')
    labels='ABCD' if a.run=='ALL' else a.run
    for label in labels:
        if a.evaluate_only:print(json.dumps(evaluate(a.output_dir/f'run_{label.lower()}',label),indent=2))
        else:run(label,a.output_dir,a.timeout)
