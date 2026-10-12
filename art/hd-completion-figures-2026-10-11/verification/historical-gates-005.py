"""Regresjonsproev historiske leveranseporter med eksakte fryste kodefiler."""
from pathlib import Path
import hashlib,json,os,runpy,shutil,sys,tempfile
R=Path(__file__).resolve().parents[3];F=R/'art/hd-completion-figures-2026-10-11';freeze=F/'verification/source-freezes-005';sys.path.insert(0,str(R/'tools'));import hd_figurer_aktiver as gate
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();maps=json.loads((freeze/'source-map.json').read_text())
for row in maps['files']:assert sha(R/row['frozen_path'])==row['sha256']
def strings(v):
 if isinstance(v,str):yield v
 elif isinstance(v,list):
  for x in v:yield from strings(x)
 elif isinstance(v,dict):
  for x in v.values():yield from strings(x)
reports=[];out=F/'verification/historical-gates-005';out.mkdir(exist_ok=True)
with tempfile.TemporaryDirectory(prefix='moonstone-historical-gate-',dir=F/'verification')as td:
 root=Path(td)
 def link(p,rel=None):
  dest=root/(rel or p.relative_to(R));dest.parent.mkdir(parents=True,exist_ok=True)
  if not dest.exists():os.link(p,dest)
 def refs(p):
  link(p)
  for s in strings(json.loads(p.read_text())):
   if len(s)>500 or '\n'in s:continue
   q=R/s
   if q.is_file():
    link(q)
    if q.name=='art-record.json':refs(q)
 for p in (R/'web/hd').rglob('*'):
  if p.is_file():link(p)
 for row in maps['files']:link(R/row['frozen_path'],row['path'])
 for rel in ['Moonstonecd32-AMIGA.zip','web/build/moonstone-core.js']:link(R/rel)
 for rel in ['production/li1/activation-set-001.json','production/activation-set-troll-003-with-alias.json','production/activation-set-troll-004.json','production/activation-set-troll-005-join-v1.json','production/activation-set-balok-008-attack-seven-ankle-v5.json']:refs(F/rel)
 (root/'art/hd-completion-figures-2026-10-11/verification').mkdir(parents=True,exist_ok=True);gate.ROOT=root
 for name in ['hd_figurer_aktiver_sjekk.py','hd_figurer_alias_sjekk.py']:runpy.run_path(str(R/'tools'/name),run_name='__main__')
 for name in ['activation-gates.json','activation-alias-gates.json']:
  p=root/'art/hd-completion-figures-2026-10-11/verification'/name;d=json.loads(p.read_text());assert d['status']=='passed';shutil.copy2(p,out/name);reports.append({'path':str((out/name).relative_to(R)),'sha256':sha(p),'checks':d['count']})
report=dict(status='passed',scope='Historiske LI1-/Balok-leveranseporter med originale005-JS, ingen paastand om ny renderers runtime. Nye leveranser maa valideres mot gjeldende kode.',source_freeze=str(freeze.relative_to(R)),source_map_sha256=sha(freeze/'source-map.json'),reports=reports)
(F/'verification/historical-gates-005.json').write_text(json.dumps(report,indent=2)+'\n');print('Historisk regresjon bundet til riktig kodefrys.')
