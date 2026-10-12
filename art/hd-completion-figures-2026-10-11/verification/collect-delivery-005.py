"""Velg bare femte leveranses konkrete filer; ingen staging eller Git-endring."""
from pathlib import Path
import hashlib,json,subprocess
R=Path(__file__).resolve().parents[3];F=R/'art/hd-completion-figures-2026-10-11';P=F/'production';files=set()
def add(p):
 p=p.resolve();assert p.is_relative_to(R)and p.is_file(),p;rel=str(p.relative_to(R))
 if p.suffix in {'.html','.wasm','.pyc','.bin'}or any(t in rel for t in ['/__pycache__/','/runtime-host/','/package/']):return
 if p.suffix=='.png'and any(t in rel for t in ['/references/','/references4x/','/source/']):return
 files.add(rel)
def strings(v):
 if isinstance(v,str):yield v
 elif isinstance(v,list):
  for x in v:yield from strings(x)
 elif isinstance(v,dict):
  for x in v.values():yield from strings(x)
def refs(p):
 add(p)
 for s in strings(json.loads(p.read_text())):
  if len(s)>500 or '\n'in s or s.startswith('data:'):continue
  for base in [R,p.parent]:
   q=base/s
   if q.is_file()and q.resolve().is_relative_to(R):add(q)
progress=json.loads((F/'delivery-progress-005.json').read_text())
for delivery in progress['deliveries']:
 p=R/delivery['path'];refs(p);d=json.loads(p.read_text())
 for c in d.get('companion_derivations',[]):add(R/c['path'])
 for e in d.get('entries',[]):
  for k in ['png','mask','raw','prompt','art_record']:
   if e.get(k):add(R/e[k])
  if e.get('art_record'):refs(R/e['art_record'])
 for q in d.get('proofs',[]):
  pp=R/q['path'];add(pp)
  for image in pp.parent.glob('*.png'):add(image)
listing=F/'figures/dragon-production/delivery-dragon2-files.txt';add(listing)
for line in listing.read_text().splitlines():
 if line and not line.startswith('#'):add(R/line)
for p in (P/'embedded-knights').iterdir():
 if p.is_file()and p.suffix in {'.py','.cjs','.json'}:add(p)
for name in ['regenerate-references-v1.py','activate-six-v3.py','activation-receipt-six-v3.json','runtime-standard-actual-v1.cjs','runtime-standard-actual-v2.cjs','runtime-standard-actual-frozen-v1.cjs']:
 add(P/'beast'/name)
for p in (P/'embedded-knights/packed').rglob('*.png'):add(p)
for p in (P/'embedded-knights/verification/runtime-v1').glob('*.png'):add(p)
add(P/'embedded-knights/verification/runtime-v1/test.json')
for name in ['standard-005-v1','standard-005-v2']:
 for p in (P/'beast/verification'/name).glob('*'):
  if p.suffix in {'.json','.png'}:add(p)
for proof in progress['proofs']:
 p=R/proof['path'];add(p)
 if 'standard-005' in str(p):
  for image in p.parent.glob('*.png'):add(image)
for p in (F/'verification/integration-005-final/ending').glob('*'):
 if p.suffix in {'.json','.png'}:add(p)
for p in (F/'verification/source-freezes-005').rglob('*'):
 if p.is_file():add(p)
for p in (F/'verification/public-004').rglob('*.json'):add(p)
for n in ['production/li1/runtime-standard-public-004.cjs','production/li1/delivery-li1-files.txt','production/runtime-integration-ending-frozen-v1.cjs','production/guardian/runtime-standard-public-v5.cjs','production/guardian/runtime-standard-actual-v4.cjs','production/guardian/runtime-standard-actual-v5.cjs','production/guardian/runtime-standard-actual-frozen-v1.cjs','production/guardian/runtime-standard-actual-v2.cjs','production/guardian/runtime-standard-actual-v3.cjs','README.md','delivery-progress-005.json','verification/standard-package-005.json','verification/verify-delivery-005.py']:
 p=F/n
 if p.exists():add(p)
manifest=json.loads((R/'web/hd/manifest.json').read_text());old=json.loads(subprocess.check_output(['git','show','ea7fe88:web/hd/manifest.json'],cwd=R));before={r['path']:r for r in old['files']};changed=[r for r in manifest['files']if r!=before.get(r['path'])];assert len(changed)==70
for row in changed:add(R/'web/hd'/row['path'])
for n in ['web/hd/manifest.json','tools/hd_bestilling.py','tools/hd_bestilling_sjekk.py','docs/hd-bestilling-chatgpt.md','docs/hd-bestilling-liste.csv','todo.md','log.md']:
 add(R/n)
add(Path(__file__))
ignored=subprocess.run(['git','check-ignore','--stdin'],cwd=R,input='\n'.join(files)+'\n',text=True,capture_output=True);assert ignored.returncode in(0,1);files.difference_update(ignored.stdout.splitlines());out=F/'delivery-files-005.txt';files.add(str(out.relative_to(R)));out.write_text('\n'.join(sorted(files))+'\n');print(json.dumps(dict(files=len(files),bytes=sum((R/p).stat().st_size for p in files),new_png=len(changed))))
