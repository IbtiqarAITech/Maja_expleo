#!/usr/bin/env python3
"""Fetch selected ENSO/ROB1E documentation images into local assets."""
from __future__ import annotations
import argparse, hashlib, json, os, re, sys, tempfile, time
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen
DEFAULT_SOURCE='https://ddp.csum.umontpellier.fr/rob1e/photos'; USER_AGENT='Maja-ENSO-Fetcher/1.2'
IMG_EXT={'.jpg','.jpeg','.png','.gif','.webp','.svg'}
def sanitize_filename(name: str) -> str:
    u=urlparse(name); base=Path(u.path).name or 'enso-image'
    if not Path(base).suffix and u.query:
        base = base + (u.query if u.query.startswith('.') else Path(u.query).suffix)
    base=re.sub(r'[^A-Za-z0-9._-]+','_',base).strip('._')
    return base[:120] or 'enso-image'
def is_image(name: str, ctype: str, data: bytes) -> bool:
    ext=Path(name).suffix.lower()
    if ext in IMG_EXT: return True
    return ctype.startswith('image/') or data.startswith((b'\xff\xd8',b'\x89PNG',b'GIF8',b'<svg'))
def list_remote_images(base_url: str, timeout: int=20) -> list[str]:
    with urlopen(Request(base_url, headers={'User-Agent':USER_AGENT}), timeout=timeout) as r:
        html=r.read().decode('utf-8','replace')
    links=re.findall(r'href=[\'\"]?([^\'\" >]+)', html, flags=re.I)
    return sorted(set(urljoin(base_url.rstrip('/')+'/', l) for l in links if Path(urlparse(l).path).suffix.lower() in IMG_EXT))
def fetch(url: str, timeout:int, retries:int) -> tuple[bytes,str]:
    last=None
    for _ in range(retries+1):
        try:
            with urlopen(Request(url, headers={'User-Agent':USER_AGENT}), timeout=timeout) as r:
                if getattr(r,'status',200) >= 400: raise OSError(f'HTTP {r.status}')
                data=r.read(); ctype=r.headers.get('content-type','')
                if not data: raise ValueError('empty response')
                if not is_image(url, ctype, data): raise ValueError(f'not an image: {ctype}')
                return data, ctype
        except Exception as e:
            last=e; time.sleep(.2)
    raise RuntimeError(str(last))
def atomic_bytes(path: Path, data: bytes):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix=path.name, suffix='.tmp', dir=str(path.parent)); os.close(fd)
    Path(tmp).write_bytes(data); os.replace(tmp,path)
def write_manifest(path:Path, items:list[dict[str,Any]]):
    path.parent.mkdir(parents=True,exist_ok=True); tmp=path.with_suffix('.tmp')
    tmp.write_text(json.dumps({'source':DEFAULT_SOURCE,'items':items}, indent=2, ensure_ascii=False), encoding='utf-8'); tmp.replace(path)
def parse_args(argv=None):
    p=argparse.ArgumentParser(); p.add_argument('--url', default=DEFAULT_SOURCE); p.add_argument('--output-dir','--dest', default='docs/assets/enso'); p.add_argument('--limit', type=int, default=10); p.add_argument('--overwrite', action='store_true'); p.add_argument('--dry-run', action='store_true'); p.add_argument('--timeout', type=int, default=20); p.add_argument('--retries', type=int, default=2); p.add_argument('--manifest', default=None); return p.parse_args(argv)
def main(argv=None):
    a=parse_args(argv); out=Path(a.output_dir); manifest=Path(a.manifest) if a.manifest else out/'manifest.json'
    try: urls=list_remote_images(a.url,a.timeout)[:a.limit]
    except Exception as e: print(f'Warning: could not list remote images: {e}'); urls=[]
    items=[]
    for u in urls:
        name=sanitize_filename(u); dest=out/name
        if a.dry_run:
            print(f'DRY-RUN {u} -> {dest}'); items.append({'source_url':u,'local_name':name,'status':'dry-run'}); continue
        if dest.exists() and not a.overwrite:
            data=dest.read_bytes(); items.append({'source_url':u,'local_name':name,'size':len(data),'sha256':hashlib.sha256(data).hexdigest(),'status':'exists'}); continue
        try:
            data,ctype=fetch(u,a.timeout,a.retries); atomic_bytes(dest,data); items.append({'source_url':u,'local_name':name,'size':len(data),'sha256':hashlib.sha256(data).hexdigest(),'content_type':ctype,'status':'downloaded'}) ; print(f'OK {name}')
        except Exception as e: print(f'FAILED {u}: {e}'); items.append({'source_url':u,'local_name':name,'status':'failed','error':str(e)})
    write_manifest(manifest, items); print(f'Manifest: {manifest}'); return 0 if not any(i.get('status')=='failed' for i in items) else 1
if __name__=='__main__': sys.exit(main())
