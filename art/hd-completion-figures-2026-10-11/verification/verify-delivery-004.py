"""Kontroller aktivt filsett og frys en sannferdig, delvis leveransekvittering."""
from pathlib import Path
import csv,hashlib,json,subprocess
R=Path(__file__).resolve().parents[3];F=R/'art/hd-completion-figures-2026-10-11';P=F/'production'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rel=lambda p:str(p.relative_to(R))
names=[F/'figures/kn5-production/activation-set-kn5-001.json',P/'activation-set-balok-003-reaching-five-join-v1.json',P/'activation-set-balok-004-crouch-first-v1.json',P/'activation-set-balok-005-first-eight-li1-v1.json',P/'activation-set-balok-007-jump-five-v5.json',P/'activation-set-balok-008-attack-seven-ankle-v5.json',P/'activation-set-troll2-006-baked-death-current-v1.json',P/'hen-ritual/activation-set-001.json',P/'li1/activation-set-001.json',F/'figures/dragon-production/activation-set-dragon1-001.json']
manifest=json.loads((R/'web/hd/manifest.json').read_text());old=json.loads(subprocess.check_output(['git','show','94c7064:web/hd/manifest.json'],cwd=R));before={r['path']:r for r in old['files']};active={r['path']:r for r in manifest['files']};checks=0
def check(v):
 global checks
 assert v
 checks+=1
check(manifest['images']==1428 and len(active)==1434)
for f in manifest['files']:
 p=R/'web/hd'/f['path'];check(sha(p)==f['sha256']);check(p.stat().st_size==f['bytes'])
for key,row in before.items():check(active[key]==row)
routes=[];masters=[];new=set();proofs=[];deliveries=[]
for p in names:
 d=json.loads(p.read_text());check(d['visual_status']=='reviewed_original_and_runtime');deliveries.append(dict(path=rel(p),sha256=sha(p)))
 for proof in d['proofs']:
  q=R/proof['path'];check(sha(q)==proof['sha256']);data=json.loads(q.read_text());check(data['status']=='passed' and not data.get('errors'));check(data['html_sha256']==proof['html_sha256']);proofs.append(dict(path=rel(q),sha256=sha(q),checks=len(data['checks']),production_code_sha256=d['production_code_sha256']))
 for row in d['entries']:
  if row.get('existing_master'):continue
  check(active[row['key']]['sha256']==row['png_sha256']);check(sha(R/row['png'])==row['png_sha256']);new.add(row['key']);routes.append(row['key'])
  if row.get('mask'):
   k=row['key'].replace('.png','.mask.png');check(active[k]['sha256']==row['mask_sha256']);check(sha(R/row['mask'])==row['mask_sha256']);new.add(k)
  if not row.get('master_key'):
   check(row['generation_tool']=='builtin_image_gen');check(sha(R/row['raw'])==row['raw_sha256']);check(sha(R/row['prompt'])==row['prompt_sha256']);masters.append(row['raw_sha256'])
changed={k for k,v in active.items()if before.get(k)!=v}
check(changed==new and len(new)==283);check(len(routes)==len(set(routes))==215);check(len(masters)==len(set(masters))==178)
csv_rows=list(csv.DictReader((R/'docs/hd-bestilling-liste.csv').open(),delimiter=';'));check(len(csv_rows)==1270)
html=F/'verification/integration-004-final/package/moonstone.html';code={f'web/src/{n}':sha(R/'web/src'/n)for n in ['core.js','render.js','scenes.js','hd.js']}
for n in ['verification/integration-004-final/ending/test.json','production/li1/verification/standard-final-v1/test.json','production/verification/troll-baked-v6/test.json']:
 p=F/n;d=json.loads(p.read_text());check(d['status']=='passed' and not d.get('errors'));proofs.append(dict(path=rel(p),sha256=sha(p),checks=len(d['checks'])))
package=dict(status='passed',checks=checks,images=1428,files=1434,manifest_sha256=sha(R/'web/hd/manifest.json'),html_sha256=sha(html),production_code_sha256=code,wasm_core_sha256=sha(R/'web/build/moonstone-core.js'),source_zip_sha256=sha(R/'Moonstonecd32-AMIGA.zip'),scope='All1434 manifest files have exact lengths/SHA256; all1151 previous files are unchanged.283 new PNG assets bind215 source routes to178 unique photographic masters and68 masks. Actual runtime and visual approval are separate bound receipts; no complete-game claim.')
(F/'verification/standard-package-004.json').write_text(json.dumps(package,indent=2,ensure_ascii=False)+'\n')
progress=dict(status='locally_activated_standard_verified_public_pending',images=1428,files=1434,backgrounds=sum(f['kind']=='background'for f in manifest['files']),new_png_files=283,source_masters=178,new_photographic_material_masters=178,concrete_routes=215,new_palette_masks=68,remaining_masters=1270,remaining_routes=1340,remaining_master_masks=5,deliveries=deliveries,proofs=proofs,standard_package=dict(path=rel(F/'verification/standard-package-004.json'),sha256=sha(F/'verification/standard-package-004.json')),limits=['No full natural playthrough or physical phone test.','Fixture coverage is distinct from natural source use; LI1/023..029 have no natural-use claim.','Guardian and unfinished Dragon2/5 or Balok candidates are not activated by this delivery.','Historical code hashes are preserved; fresh standard intro/ending and TROLL persistence use final production code.'])
(F/'delivery-progress-004.json').write_text(json.dumps(progress,indent=2,ensure_ascii=False)+'\n')
print(json.dumps({'status':'passed','checks':checks,'images':1428,'new_png':283,'masters':178,'routes':215,'remaining_masters':1270,'html_sha256':sha(html)}))
