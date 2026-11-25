from pathlib import Path
import json,hashlib,re
import pandas as pd
from config import ROOT

def save(frame,path):
    path=ROOT/'outputs'/path;path.parent.mkdir(parents=True,exist_ok=True)
    frame.to_csv(path,index=False,float_format='%.12g',compression={'method':'gzip','mtime':0} if str(path).endswith('.gz') else None)

def write_json(obj,path):
    p=ROOT/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj,indent=2,default=str)+'\n')

def filehash(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def status(ids,evidence,command='python run_all.py',state='PASS',issue='None'):
    p=ROOT/'CHECKLIST_STATUS.md'
    if not p.exists():p.write_text('# Checklist status\n\nGenerated evidence log; PASS records execution, HUMAN REVIEW remains outstanding.\n\n| Task | Status | Command | Evidence | Unresolved |\n|---|---|---|---|---|\n')
    with p.open('a') as f:
        for i in ids:f.write(f'| {i} | {state} | `{command}` | {evidence} | {issue} |\n')
