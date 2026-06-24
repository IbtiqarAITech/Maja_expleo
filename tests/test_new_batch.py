import json, subprocess, sys
from pathlib import Path
import pytest
from scripts import maja_batch as mb

def test_yaml_json_and_validation():
    y=mb.load_manifest('examples/maja_batch_manifest.yaml'); j=mb.load_manifest('examples/maja_batch_manifest.json')
    assert len(y['jobs'])==len(j['jobs'])==2
    assert mb.validate_manifest(y)==[]
    bad={'jobs':[{'id':'a','command':['echo']},{'id':'a','command':['echo']}]} ; assert 'duplicate job id' in ';'.join(mb.validate_manifest(bad))

def test_conflicting_output_and_working():
    m={'jobs':[{'id':'a','command':['echo'],'output':'x','working_dir':'w'},{'id':'b','command':['echo'],'output':'x','working_dir':'w2'}]}
    assert 'conflicting output path' in ';'.join(mb.validate_manifest(m))
    m['jobs'][1]['output']='y'; m['jobs'][1]['working_dir']='w'
    assert 'conflicting working path' in ';'.join(mb.validate_manifest(m))

def test_fingerprint_and_lock(tmp_path):
    j={'id':'a','command':['echo','ok'],'output':str(tmp_path/'o'),'working_dir':str(tmp_path/'w')}
    assert mb.fingerprint(j)==mb.fingerprint(dict(j))
    lock=mb.JobLock(tmp_path/'l.lock'); lock.acquire()
    with pytest.raises(mb.LockError): mb.JobLock(tmp_path/'l.lock').acquire()
    lock.release(); assert not (tmp_path/'l.lock').exists()

def test_dry_run_and_integration(tmp_path):
    summary=tmp_path/'summary.json'
    rc=subprocess.run([sys.executable,'scripts/maja_batch.py','--manifest','examples/maja_batch_manifest.yaml','--workers','2','--dry-run','--summary',str(summary)], text=True, capture_output=True)
    assert rc.returncode==0 and summary.exists()
    rc=subprocess.run([sys.executable,'scripts/maja_batch.py','--manifest','examples/maja_batch_manifest.yaml','--workers','2','--summary',str(summary),'--force'], text=True, capture_output=True)
    assert rc.returncode==0, rc.stderr+rc.stdout
    data=json.loads(summary.read_text()); assert data['successful_jobs']==2
    rc=subprocess.run([sys.executable,'scripts/maja_batch.py','--manifest','examples/maja_batch_manifest.yaml','--workers','2','--summary',str(summary),'--resume'], text=True, capture_output=True)
    assert rc.returncode==0
    data=json.loads(summary.read_text()); assert data['skipped_jobs']>=2
