"""Eksplisitt filutvalg for leveransen; ingen Git- eller manifestendring."""
from pathlib import Path
import hashlib,json,subprocess
R=Path(__file__).resolve().parents[3];F=R/'art/hd-completion-figures-2026-10-11';P=F/'production'
files=set()
def add(p):
 p=p.resolve()
 assert p.is_relative_to(R) and p.is_file(),p
 rel=str(p.relative_to(R))
 assert p.suffix not in {'.html','.wasm','.pyc'} and not any(x in rel for x in ['/__pycache__/','/runtime-host/','/package/']),rel
 if p.suffix=='.bin':return
 # Regenererbare original-/NN-bildereferanser er lokale, som beskrevet i README.
 if p.suffix=='.png' and any(x in rel for x in ['/references/','/references4x/','/source/']):return
 files.add(rel)
def strings(v):
 if isinstance(v,str):yield v
 elif isinstance(v,list):
  for a in v:yield from strings(a)
 elif isinstance(v,dict):
  for a in v.values():yield from strings(a)
def refs(p):
 add(p)
 for s in strings(json.loads(p.read_text())):
  if len(s)>500 or '\n' in s or s.startswith('data:'):continue
  for base in [R,p.parent]:
   q=base/s
   if q.is_file() and q.resolve().is_relative_to(R) and q.suffix not in {'.html','.wasm','.pyc'}:
    if '/package/' not in str(q) and '/runtime-host/' not in str(q):add(q)
for listing in [P/'delivery-balok28-files.txt',P/'li1/delivery-li1-files.txt',F/'figures/dragon-production/delivery-dragon1-files.txt']:
 add(listing)
 for line in listing.read_text().splitlines():
  if line and not line.startswith('#'):add(R/line)
kn=F/'figures/kn5-production'
for p in kn.iterdir():
 if p.is_file() and p.suffix in {'.py','.cjs','.json','.png'}:add(p)
for name in ['identity','raw','prompts','references','packed']:
 for p in (kn/name).rglob('*'):
  if p.is_file() and p.suffix in {'.py','.cjs','.json','.png','.txt'}:add(p)
for p in (kn/'verification').glob('*.json'):add(p)
for p in (kn/'verification').glob('comparison-*.png'):add(p)
for name in ['all-routes-final','dragon-final']:
 add(kn/'verification'/name/'test.json')
for p in (kn/'verification/dragon-final').glob('*.png'):add(p)
for name in ['KN5.ob-000-original.png','KN5.ob-000-hd.png','KN5.ob-000-mirror-hd.png','KN5.ob-004-red-hd.png','KN5.ob-004-blue-hd.png','KN5.ob-058-orange-hd.png']:
 p=kn/'verification/all-routes-final'/name
 if p.exists():add(p)
h=P/'hen-ritual';delivery=json.loads((h/'activation-set-001.json').read_text());refs(h/'activation-set-001.json')
for companion in delivery['companion_derivations']:add(R/companion['path'])
for row in delivery['entries']:
 for k in ['png','mask','raw','prompt','art_record']:
  if row.get(k):add(R/row[k])
for record in (h/'generation-calls').glob('*.json'):
 d=json.loads(record.read_text())
 accepted=any(d['raw_sha256']==row.get('raw_sha256') for row in delivery['entries'])
 if accepted:
  add(record);add(h/d['source_reference'])
for n in ['freeze-proof.json','ascending-blue-comparison-v2.png','electric-all-comparison-v2.png','knight-comparison-v1.png']:add(h/'verification'/n)
for proof in delivery['proofs']:add(R/proof['path'])
for n in ['natural-037-hd.png','ending-2770-hd.png','ending-2770-original.png']:
 p=h/'verification/all-current-v4'/n
 if p.exists():add(p)
t=P/'activation-set-troll2-006-baked-death-current-v1.json';refs(t)
for row in json.loads(t.read_text())['entries']:
 refs(R/row['art_record'])
 for p in (R/row['art_record']).parent.iterdir():
  if p.is_file():add(p)
for n in ['freeze_batch.py','runtime-troll-baked-v3.cjs','runtime-integration-ending.cjs','runtime-integration-ending-v1.cjs']:
 add(P/n)
for name in ['troll-baked-v5','troll-baked-v6']:
 for n in ['test.json','input-index.json']:
  p=P/'verification'/name/n
  if p.exists():add(p)
for n in ['TROLL2.CEL-014-original.png','TROLL2.CEL-014-candidate.png']:
 p=P/'verification/troll-baked-v5'/n
 if p.exists():add(p)
add(P/'verification/troll-death-background-contract-v3.json')
for name in ['activation-gates.json','activation-html-gates.json','activation-alias-gates.json']:
 add(F/'verification'/name)
for name in ['README.md','delivery-progress-004.json','verification/standard-package-004.json']:
 add(F/name)
for p in (F/'verification/source-freezes-004').iterdir():add(p)
for p in (F/'verification/integration-004-final/ending').glob('*'):
 if p.suffix in {'.json','.png'}:add(p)
for p in (F/'verification/public-003').rglob('*.json'):add(p)
manifest=json.loads((R/'web/hd/manifest.json').read_text());before=json.loads(subprocess.check_output(['git','show','94c7064:web/hd/manifest.json'],cwd=R));old={r['path']:r for r in before['files']}
changed=[r for r in manifest['files']if r!=old.get(r['path'])]
assert len(changed)==283 and all(r['path'].endswith('.png')for r in changed)
for row in changed:add(R/'web/hd'/row['path'])
for n in ['web/hd/manifest.json','web/src/render.js','web/src/scenes.js','tools/hd_bestilling.py','tools/hd_figurer_aktiver.py','tools/hd_figurer_aktiver_sjekk.py','tools/hd_figurer_alias_sjekk.py','docs/hd-bestilling-chatgpt.md','docs/hd-bestilling-liste.csv','log.md','todo.md']:
 add(R/n)
add(Path(__file__))
add(F/'verification/verify-delivery-004.py')
ignored=subprocess.run(['git','check-ignore','--stdin'],cwd=R,input='\n'.join(files)+'\n',text=True,capture_output=True)
assert ignored.returncode in (0,1),ignored.stderr
files.difference_update(ignored.stdout.splitlines())
out=F/'delivery-files-004.txt';files.add(str(out.relative_to(R)));out.write_text('\n'.join(sorted(files))+'\n')
print(json.dumps({'files':len(files),'bytes':sum((R/p).stat().st_size for p in files),'new_PNG':len(changed),'path':str(out.relative_to(R))}))
