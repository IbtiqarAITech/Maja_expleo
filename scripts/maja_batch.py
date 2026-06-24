#!/usr/bin/env python3
"""Safe multiprocessing MAJA batch runner.

The runner is additive: each job executes an explicit command or the discovered
MAJA wrapper command provided in the manifest. It provides manifest validation,
per-job work/log/output isolation, lock files, atomic success metadata and
resume by stable fingerprint.
"""
from __future__ import annotations

import argparse, concurrent.futures, datetime as dt, hashlib, json, os, shlex, shutil, signal, subprocess, sys, tempfile, time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any
try:
    import yaml
except Exception:  # pragma: no cover
    yaml = None

TOOL_VERSION = "1.2.0"
ROOT = Path.cwd()

class ManifestError(ValueError): pass
class LockError(RuntimeError): pass

def atomic_write(path: Path, data: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name, suffix='.tmp', dir=str(path.parent))
    with os.fdopen(fd, 'w', encoding='utf-8') as f: f.write(data)
    os.replace(tmp, path)

def load_manifest(path: str|Path) -> dict[str, Any]:
    p=Path(path); raw=p.read_text(encoding='utf-8')
    if p.suffix.lower() in {'.yml','.yaml'}:
        if yaml is None: raise ManifestError('PyYAML is required for YAML manifests')
        data=yaml.safe_load(raw)
    else: data=json.loads(raw)
    if not isinstance(data, dict): raise ManifestError('manifest root must be an object')
    data.setdefault('_manifest_path', str(p))
    return data

def _resolve(path: str|Path) -> Path: return (ROOT / Path(path)).resolve() if not Path(path).is_absolute() else Path(path).resolve()

def normalize_jobs(manifest: dict[str, Any], *, output_root: str|None=None, working_root: str|None=None, timeout: int|None=None, only: list[str]|None=None) -> list[dict[str, Any]]:
    defaults=manifest.get('defaults') or {}
    out_root=Path(output_root or defaults.get('output_root','outputs/batch'))
    work_root=Path(working_root or defaults.get('working_root','.work/maja-batch'))
    log_root=Path(defaults.get('log_root','logs/maja-batch'))
    jobs=[]
    for i,j in enumerate(manifest.get('jobs') or []):
        if j.get('enabled', True) is False: continue
        jid=str(j.get('id') or f"job_{i:04d}")
        if only and jid not in only: continue
        jj=dict(j); jj['id']=jid
        jj['output']=str(Path(jj.get('output') or out_root/jid))
        jj['working_dir']=str(Path(jj.get('working_dir') or work_root/jid))
        jj['log_file']=str(Path(jj.get('log_file') or log_root/f'{jid}.log'))
        jj['timeout']=int(jj.get('timeout') or timeout or defaults.get('timeout_seconds',3600))
        jobs.append(jj)
    return jobs

def command_for_job(job: dict[str, Any]) -> list[str]:
    if 'command' in job:
        return job['command'] if isinstance(job['command'], list) else shlex.split(str(job['command']))
    wrapper=job.get('wrapper') or './3_startmaja_example.sh'
    return [str(wrapper)]

def fingerprint(job: dict[str, Any]) -> str:
    relevant={k:job.get(k) for k in sorted(job) if k not in {'log_file'}}
    relevant['command']=command_for_job(job); relevant['tool_version']=TOOL_VERSION
    for key in ('input','config','wrapper'):
        if job.get(key):
            p=_resolve(job[key]); relevant[key+'_exists']=p.exists(); relevant[key+'_mtime']=p.stat().st_mtime if p.exists() else None
    return hashlib.sha256(json.dumps(relevant, sort_keys=True, default=str).encode()).hexdigest()

def validate_manifest(manifest: dict[str, Any], **kwargs: Any) -> list[str]:
    errors=[]
    if not isinstance(manifest.get('jobs'), list) or not manifest.get('jobs'): return ["Missing 'jobs' list in manifest"]
    jobs=normalize_jobs(manifest, **kwargs)
    ids=set(); outs=[]; works=[]
    for j in jobs:
        if j['id'] in ids: errors.append(f"duplicate job id: {j['id']}")
        ids.add(j['id'])
        if 'command' not in j and 'wrapper' not in j: errors.append(f"{j['id']}: missing 'command'")
        elif not command_for_job(j): errors.append(f"{j['id']}: empty command")
        outs.append(_resolve(j['output'])); works.append(_resolve(j['working_dir']))
    for name, vals in [('output', outs), ('working', works)]:
        seen={}
        for idx,p in enumerate(vals):
            if p in seen: errors.append(f"conflicting {name} path: {p}")
            seen[p]=idx
        for a in vals:
            for b in vals:
                if a!=b and (a in b.parents or b in a.parents): errors.append(f"unsafe nested {name} paths: {a} / {b}")
    return sorted(set(errors))

class JobLock:
    def __init__(self, path: Path): self.path=path; self.acquired=False
    def acquire(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            os.mkdir(self.path); self.acquired=True
            atomic_write(self.path/'owner.json', json.dumps({'pid':os.getpid(),'time':dt.datetime.now(dt.UTC).isoformat()}))
        except FileExistsError as e: raise LockError(f'active lock exists: {self.path}') from e
    def release(self) -> None:
        if self.acquired and self.path.exists(): shutil.rmtree(self.path, ignore_errors=True); self.acquired=False
    def __enter__(self): self.acquire(); return self
    def __exit__(self,*a): self.release()

def success_meta(job: dict[str,Any]) -> Path: return _resolve(job['output'])/'.maja_batch_success.json'
def required_outputs_exist(job: dict[str,Any]) -> bool:
    req=job.get('required_outputs') or ['.maja_batch_success.json']
    out=_resolve(job['output'])
    return all((out/r).exists() for r in req)
def can_resume(job: dict[str,Any]) -> bool:
    meta=success_meta(job)
    if not meta.exists() or (_resolve(job['working_dir']).with_suffix('.lock')).exists(): return False
    try: data=json.loads(meta.read_text(encoding='utf-8'))
    except Exception: return False
    return data.get('status')=='success' and data.get('fingerprint')==fingerprint(job) and required_outputs_exist(job)

def run_job(job: dict[str,Any], dry_run: bool=False, force: bool=False) -> dict[str,Any]:
    jid=job['id']; out=_resolve(job['output']); work=_resolve(job['working_dir']); log=_resolve(job['log_file']); lock=JobLock(work.with_suffix('.lock'))
    fp=fingerprint(job); cmd=command_for_job(job); start=dt.datetime.now(dt.UTC); t0=time.monotonic()
    result={'id':jid,'status':'unknown','command':cmd,'output':str(out),'working_dir':str(work),'log':str(log),'fingerprint':fp,'start':start.isoformat(),'returncode':None}
    if dry_run: result.update(status='dry-run', duration_s=0); return result
    if not force and can_resume(job): result.update(status='skipped', duration_s=0); return result
    out.mkdir(parents=True, exist_ok=True); work.mkdir(parents=True, exist_ok=True); log.parent.mkdir(parents=True, exist_ok=True)
    with lock:
        with log.open('a', encoding='utf-8') as lf:
            lf.write(f"{start.isoformat()} INFO job={jid} pid={os.getpid()} command={shlex.join(cmd)}\n")
            try:
                proc=subprocess.run(cmd, cwd=str(work), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=job['timeout'], shell=False)
                lf.write(proc.stdout); lf.write(proc.stderr)
                result['returncode']=proc.returncode; result['stdout_tail']=proc.stdout[-2000:]; result['stderr_tail']=proc.stderr[-2000:]
                result['status']='success' if proc.returncode==0 else 'failed'
            except subprocess.TimeoutExpired as e:
                result.update(status='timeout', returncode=-9, error=str(e))
            except Exception as e:
                result.update(status='error', returncode=-1, error=str(e))
    result['end']=dt.datetime.now(dt.UTC).isoformat(); result['duration_s']=round(time.monotonic()-t0,3)
    if result['status']=='success': atomic_write(success_meta(job), json.dumps(result, indent=2, ensure_ascii=False))
    else: atomic_write(out/'.maja_batch_failure.json', json.dumps(result, indent=2, ensure_ascii=False))
    return result

def write_summary(results: list[dict[str,Any]], path: Path, workers:int) -> dict[str,Any]:
    s={'timestamp':dt.datetime.now(dt.UTC).isoformat(),'total_jobs':len(results),'successful_jobs':sum(r['status']=='success' for r in results),'failed_jobs':sum(r['status'] in {'failed','error','timeout'} for r in results),'skipped_jobs':sum(r['status']=='skipped' for r in results),'dry_run_jobs':sum(r['status']=='dry-run' for r in results),'worker_count':workers,'jobs':results}
    atomic_write(path, json.dumps(s, indent=2, ensure_ascii=False))
    md=path.with_suffix('.md')
    lines=['# Batch Summary','',f"- Total jobs: {s['total_jobs']}",f"- Successful jobs: {s['successful_jobs']}",f"- Failed jobs: {s['failed_jobs']}",f"- Skipped jobs: {s['skipped_jobs']}",'','| Job | Status | Duration | Log |','|---|---|---:|---|']
    for r in results: lines.append(f"| {r['id']} | {r['status']} | {r.get('duration_s',0)} | {r.get('log','')} |")
    atomic_write(md, '\n'.join(lines)+'\n'); return s

def parse_args(argv=None):
    p=argparse.ArgumentParser(description='Safe MAJA multiprocessing batch runner')
    p.add_argument('manifest_pos', nargs='?'); p.add_argument('--manifest', dest='manifest_opt')
    p.add_argument('--workers', type=int, default=2); p.add_argument('--resume', action='store_true'); p.add_argument('--dry-run', action='store_true'); p.add_argument('--fail-fast', action='store_true'); p.add_argument('--force', action='store_true')
    p.add_argument('--summary', default='outputs/batch/batch-summary.json'); p.add_argument('--log-level', default='INFO'); p.add_argument('--job', action='append'); p.add_argument('--timeout', type=int); p.add_argument('--output-root'); p.add_argument('--working-root'); p.add_argument('--keep-workdir', action='store_true')
    return p.parse_args(argv)

def main(argv=None) -> int:
    a=parse_args(argv); mpath=a.manifest_opt or a.manifest_pos
    if not mpath: print('Error: --manifest is required', file=sys.stderr); return 2
    try:
        manifest=load_manifest(mpath); errs=validate_manifest(manifest, output_root=a.output_root, working_root=a.working_root, timeout=a.timeout, only=a.job)
        if errs: raise ManifestError('; '.join(errs))
        jobs=normalize_jobs(manifest, output_root=a.output_root, working_root=a.working_root, timeout=a.timeout, only=a.job)
    except Exception as e: print(f'Manifest error: {e}', file=sys.stderr); return 2
    if a.dry_run:
        for j in jobs: print(f"DRY-RUN {j['id']}: {shlex.join(command_for_job(j))}")
        summary=write_summary([run_job(j, dry_run=True) for j in jobs], _resolve(a.summary), a.workers); print(json.dumps(summary, indent=2)); return 0
    pending=[j for j in jobs if not (a.resume and not a.force and can_resume(j))]
    results=[{**j,'status':'skipped','duration_s':0,'log':j['log_file'],'fingerprint':fingerprint(j)} for j in jobs if j not in pending]
    try:
        with concurrent.futures.ProcessPoolExecutor(max_workers=a.workers) as ex:
            futs=[ex.submit(run_job,j,False,a.force) for j in pending]
            for fut in concurrent.futures.as_completed(futs):
                r=fut.result(); results.append(r); print(f"{r['id']}: {r['status']}")
                if a.fail_fast and r['status'] not in {'success','skipped'}: break
    except KeyboardInterrupt:
        print('Interrupted; preserving diagnostics', file=sys.stderr); return 130
    s=write_summary(results, _resolve(a.summary), a.workers)
    return 1 if s['failed_jobs'] else 0

if __name__=='__main__': sys.exit(main())

# Backward-compatible helpers retained for existing tests/importers.
LOCK_DIR = Path('logs/locks')
STATE_DIR = Path('logs/state')
def _acquire_lock(lock_name: str, timeout: float = 30.0) -> Path | None:
    deadline=time.monotonic()+timeout; lock=LOCK_DIR/f'{lock_name}.lockdir'
    while time.monotonic()<deadline:
        try:
            jl=JobLock(lock); jl.acquire(); return lock
        except LockError: time.sleep(0.05)
    return None
def _release_lock(lock_path: Path | None) -> None:
    if lock_path and lock_path.exists(): shutil.rmtree(lock_path, ignore_errors=True)
def _load_state(manifest_name: str) -> dict[str, Any]:
    p=STATE_DIR/f'{manifest_name}_state.json'
    return json.loads(p.read_text(encoding='utf-8')) if p.exists() else {}
def _save_state(manifest_name: str, state: dict[str, Any]) -> None:
    atomic_write(STATE_DIR/f'{manifest_name}_state.json', json.dumps(state, indent=2, default=str))
