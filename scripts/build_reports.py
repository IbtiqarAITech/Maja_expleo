#!/usr/bin/env python3
"""Build French Markdown report sources into small self-contained PDFs."""
from __future__ import annotations
import re, sys, zlib
from pathlib import Path
REPORTS=[('docs/reports/WP_02_Needs_and_Feasibility_Study.md','deliverables/WP_02_Analyse_Besoins_Etude_Faisabilite.pdf','WP_02 — Analyse des besoins et étude de faisabilité'),('docs/reports/MAJA_Improvement_Audit.md','deliverables/Audit_Detaille_Amelioration_MAJA_ENSO.pdf','Audit détaillé et plan d’amélioration du workflow MAJA pour ENSO')]
def esc(s): return s.replace('\\','\\\\').replace('(','\\(').replace(')','\\)')
def pdf(text,title,out):
    lines=[title,'']+[re.sub(r'[#*_`|]',' ',l)[:110] for l in text.splitlines() if l.strip()][:180]
    pages=[lines[i:i+45] for i in range(0,len(lines),45)] or [[title]]
    objs=[]; kids=[]
    for page in pages:
        stream='BT /F1 10 Tf 50 790 Td 14 TL '+''.join(f'({esc(l)}) Tj T* ' for l in page)+'ET'
        comp=zlib.compress(stream.encode('latin-1','replace'))
        cid=len(objs)+1; objs.append(f"{cid} 0 obj<< /Length {len(comp)} /Filter /FlateDecode >>stream\n".encode()+comp+b"\nendstream\nendobj\n")
        pid=len(objs)+1; kids.append(f'{pid} 0 R'); objs.append(f"{pid} 0 obj<< /Type /Page /Parent 0 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 999 0 R >> >> /Contents {cid} 0 R >>endobj\n".encode())
    font=b"999 0 obj<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>endobj\n"; pages_obj_id=len(objs)+1; catalog_id=pages_obj_id+1
    objs=[o.replace(b'/Parent 0 0 R', f'/Parent {pages_obj_id} 0 R'.encode()) for o in objs]
    objs.append(f"{pages_obj_id} 0 obj<< /Type /Pages /Kids [{' '.join(kids)}] /Count {len(kids)} >>endobj\n".encode())
    objs.append(f"{catalog_id} 0 obj<< /Type /Catalog /Pages {pages_obj_id} 0 R >>endobj\n".encode()); objs.append(font)
    data=b'%PDF-1.4\n'; offs=[0]
    for o in objs: offs.append(len(data)); data+=o
    x=len(data); data+=f"xref\n0 {len(objs)+1}\n0000000000 65535 f \n".encode()+b''.join(f"{off:010d} 00000 n \n".encode() for off in offs[1:])
    data+=f"trailer<< /Size {len(objs)+1} /Root {catalog_id} 0 R /Title ({esc(title)}) >>\nstartxref\n{x}\n%%EOF\n".encode()
    Path(out).parent.mkdir(parents=True,exist_ok=True); Path(out).write_bytes(data)
def validate(path,title):
    b=Path(path).read_bytes(); assert b.startswith(b'%PDF') and len(b)>1000
    return {'file':path,'size':len(b),'page_count':b.count(b'/Type /Page'),'title':title}
def main():
    vals=[]
    for src,out,title in REPORTS:
        text=Path(src).read_text(encoding='utf-8'); pdf(text,title,out); vals.append(validate(out,title))
    Path('deliverables/pdf-validation.json').write_text(__import__('json').dumps(vals,indent=2,ensure_ascii=False),encoding='utf-8')
    print('Generated PDFs:'); [print(v) for v in vals]; return 0
if __name__=='__main__': sys.exit(main())
