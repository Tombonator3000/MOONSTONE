"""Kontroller femte avgrensede leveranse mot publisert baseline og frosne bevis."""
from pathlib import Path
import csv,hashlib,json,subprocess,sys
R=Path(__file__).resolve().parents[3];F=R/'art/hd-completion-figures-2026-10-11';P=F/'production';sys.path.insert(0,str(R/'tools'))
from hd_figurer_aktiver import validate
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:str(p.relative_to(R));checks=0
def check(v):
 global checks
 assert v
 checks+=1
names=[F/'figures/dragon-production/activation-set-dragon2-001.json',*[P/('activation-set-balok-'+n+'.json')for n in ['009-upper-held-four-v5','010-roar-four-v5','012-crouch-three-v5','013-prone-four-v5']],P/'guardian/first18-v1/activation-set-001.json',P/'beast/activation-set-six-v3.json']
manifest=json.loads((R/'web/hd/manifest.json').read_text());before=json.loads(subprocess.check_output(['git','show','ea7fe88:web/hd/manifest.json'],cwd=R));old={r['path']:r for r in before['files']};active={r['path']:r for r in manifest['files']};check(manifest['images']==1498 and len(active)==1504)
for row in manifest['files']:
 p=R/'web/hd'/row['path'];check(p.stat().st_size==row['bytes']);check(sha(p)==row['sha256'])
for k,v in old.items():check(active[k]==v)
new=set();routes=[];photos=[];shadow=[];deliveries=[];proofs=[]
for p in names:
 d=json.loads(p.read_text());checked=validate(d);check(bool(checked));deliveries.append(dict(path=rel(p),sha256=sha(p)))
 for q in d['proofs']:
  report=json.loads((R/q['path']).read_text());check(report['status']=='passed'and not report.get('errors'));proofs.append(dict(path=q['path'],sha256=q['sha256'],checks=len(report['checks'])))
 for row in d['entries']:
  check(not row.get('existing_master'));check(active[row['key']]['sha256']==row['png_sha256']);new.add(row['key']);routes.append(row['key'])
  if row.get('mask'):
   key=row['key'].replace('.png','.mask.png');check(active[key]['sha256']==row['mask_sha256']);new.add(key)
  if row.get('master_key'):continue
  check(sha(R/row['raw'])==row['raw_sha256']);check(sha(R/row['prompt'])==row['prompt_sha256'])
  if row['generation_tool']=='builtin_image_gen':photos.append(row['raw_sha256'])
  else:check(row['generation_tool']=='preserved_original_black_shadow');shadow.append(row['key'])
repair=P/'embedded-knights/activation-receipt-v1.json';rd=json.loads(repair.read_text());check(rd['status']=='locally_activated');proof=json.loads((R/rd['runtime_proof_path']).read_text());check(sha(R/rd['runtime_proof_path'])==rd['runtime_proof_sha256']and proof['status']=='passed'and not proof['errors']);proofs.append(dict(path=rd['runtime_proof_path'],sha256=rd['runtime_proof_sha256'],checks=len(proof['checks'])));deliveries.append(dict(path=rel(repair),sha256=sha(repair)))
for k,h in rd['existing_photographs_unchanged'].items():check(active[k]['sha256']==h==old[k]['sha256'])
for row in rd['new_masks']:check(active[row['path']]==row);new.add(row['path'])
changed={k for k,v in active.items()if old.get(k)!=v};check(changed==new and len(new)==70);check(len(routes)==len(set(routes))==65);check(len(photos)==len(set(photos))==64);check(shadow==['DRAGON2.CEL/027.png']);check(sum('.mask.'in k for k in new)==5)
rows=list(csv.DictReader((R/'docs/hd-bestilling-liste.csv').open(),delimiter=';'));check(len(rows)==1205);check(sum(r['trenger_maske']=='ja'for r in rows)==99)
html=F/'verification/integration-005-final/package/moonstone.html';check(sha(html)=='bfeebb4274c260e1bf484b098bf08caad016c5eda360de088758e77649dbb272');check(sha(R/'web/hd/manifest.json')=='1dc3c650acc95948a4efbd95d137bbeb2a28cb5b0ae030a86ebc9f8b5156294c')
for name in ['verification/integration-005-final/ending/test.json','production/beast/verification/standard-005-v2/test.json','production/guardian/verification/standard-005-v5/test.json']:
 p=F/name;d=json.loads(p.read_text());check(d['status']=='passed'and not d.get('errors'));check(d['html_sha256']==sha(html));check(d['manifest_sha256']==sha(R/'web/hd/manifest.json'));proofs.append(dict(path=rel(p),sha256=sha(p),checks=len(d['checks'])))
code={f'web/src/{n}':sha(R/'web/src'/n)for n in ['core.js','render.js','scenes.js','hd.js']};source_map=F/'verification/source-freezes-005/source-map.json';fm=json.loads(source_map.read_text())
for row in fm['files']:check(sha(R/row['frozen_path'])==row['sha256']==code[row['path']])
package=dict(status='passed',checks=checks,images=1498,files=1504,manifest_sha256=sha(R/'web/hd/manifest.json'),html_sha256=sha(html),production_code_sha256=code,wasm_core_sha256=sha(R/'web/build/moonstone-core.js'),source_zip_sha256=sha(R/'Moonstonecd32-AMIGA.zip'),source_freeze_path=rel(source_map),source_freeze_sha256=sha(source_map),scope='Alle1504 manifestfiler har eksakt stoerrelse/SHA. Alle1434 tidligere publiserte filer er uendret.70 nyePNG binder65 kilderuter til64 selvstendige fotomastere,en bevart svart skygge og fem masker. Standardkamper og sluttsekvens er faktisk kontrollert; ingen full gjennomspilling paastaas.')
pp=F/'verification/standard-package-005.json';pp.write_text(json.dumps(package,indent=2,ensure_ascii=False)+'\n');progress=dict(status='locally_activated_standard_verified_public_pending',images=1498,files=1504,backgrounds=81,new_png_files=70,source_masters=65,new_photographic_material_masters=64,concrete_routes=65,preserved_original_black_shadows=1,new_palette_masks=5,remaining_masters=1205,remaining_routes=1275,remaining_master_masks=99,deliveries=deliveries,proofs=proofs,standard_package=dict(path=rel(pp),sha256=sha(pp)),limits=['Ingen full naturlig gjennomspilling eller fysisk telefonproeve.','RATMEN2/058 sin nye maske er provd i kildefixturer for fem farger og speiling; ingen ny naturlig kampbruk paastaas.','Guardian018..047, Dragon5 og andre uferdige kandidater er utenfor denne leveransen.','Frosset frontend og originale spill-/kjernefiler er uendret.','Guardian-kampens bakgrunn cbc31cbf mangler i HD-manifestet og bruker kontrollert Original-fallback;81 bakgrunnsfiler betyr ikke full bakgrunnsdekning.'])
(F/'delivery-progress-005.json').write_text(json.dumps(progress,indent=2,ensure_ascii=False)+'\n');print(json.dumps(dict(status='passed',checks=checks,images=1498,new_png=70,photos=64,routes=65,remaining=1205)))
