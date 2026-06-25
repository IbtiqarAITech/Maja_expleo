import json, subprocess, sys
from pathlib import Path
from scripts.fetch_enso_images import sanitize_filename, is_image, write_manifest

def test_sanitize_and_image():
    assert sanitize_filename('https://x/a b/c?.jpg').endswith('.jpg')
    assert is_image('x.bin','image/png',b'abc')
    assert not is_image('x.txt','text/html',b'<html>')

def test_manifest_generation(tmp_path):
    p=tmp_path/'manifest.json'; write_manifest(p,[{'local_name':'a.png'}])
    assert json.loads(p.read_text())['items'][0]['local_name']=='a.png'

def test_fetch_dry_run_manifest(tmp_path, monkeypatch):
    import scripts.fetch_enso_images as f
    monkeypatch.setattr(f,'list_remote_images', lambda *a,**k:['https://example/a.png'])
    assert f.main(['--output-dir',str(tmp_path),'--dry-run'])==0
    assert (tmp_path/'manifest.json').exists()

def test_build_reports():
    rc=subprocess.run([sys.executable,'scripts/build_reports.py'], text=True, capture_output=True)
    assert rc.returncode==0, rc.stderr+rc.stdout
    for p in ['deliverables/WP_02_Analyse_Besoins_Etude_Faisabilite.pdf','deliverables/Audit_Detaille_Amelioration_MAJA_ENSO.pdf']:
        assert Path(p).exists() and Path(p).stat().st_size>1000
