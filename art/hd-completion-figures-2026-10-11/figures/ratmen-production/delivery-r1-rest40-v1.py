"""Frys foerste Ratmen-banks40 resterende kildekontrollerte ruter uten aktivering."""
from pathlib import Path
import json,hashlib
ART=Path(__file__).resolve().parent;ROOT=ART.parents[3]
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:str(p.relative_to(ROOT))
def write(p,v):
 text=json.dumps(v,indent=2,ensure_ascii=False)+'\n'
 if p.exists():assert p.read_text()==text,'Bevar frossen fil '+str(p)
 else:p.write_text(text)
keys=set(read(ART/'selection-r1-rest40.json')['keys']);assert len(keys)==40
sources=read(ART/'source-contracts.json')['entries'];selected=[c for c in sources if c['key'] in keys];assert len(selected)==40
summary=read(ART/'verification/r1-rest40-fixtures-v2/summary.json');assert summary['status']=='passed' and summary['routes']==40
packing=read(ART/'verification/packing-r1-rest40-v2.json');assert packing['status']=='passed' and {a['key']for a in packing['assets']}==keys
records={r['key']:r for r in read(ART/'generation-records.json')['assets']if r['key'] in keys};assert len(records)==40
frozenRecords=ART/'generation-records-r1-rest40-v1.json';write(frozenRecords,dict(schema=1,assets=list(records.values())))
production={p:sha(ROOT/p)for p in ['web/src/core.js','web/src/render.js','web/src/scenes.js','web/src/hd.js']}
host=ART.parent/'dragon-production/runtime-host-retention-v7';baseline=ART/'verification/runtime-baseline-r1-rest40';baseline.mkdir(exist_ok=True)
for name in ['moonstone.html','package-ledger.json']:
 p=baseline/name
 if p.exists():assert sha(p)==sha(host/name)
 else:p.write_bytes((host/name).read_bytes())
proofs=[];byKey={}
for row in summary['proofs']:
 p=ROOT/row['path'];r=read(p);assert sha(p)==row['sha256'] and r['status']=='passed' and not r['errors'];assert r['production_code_sha256']==production;assert r['runtime_script_sha256']==sha(ART/'runtime-ratmen-r1-rest40-fixtures-v2.cjs');assert r['html_sha256']==sha(baseline/'moonstone.html');assert r['package_ledger_sha256']==sha(baseline/'package-ledger.json');assert r['wasm_core_sha256']==sha(host/'moonstone-core-used.js')
 for key,h in r['packed_png_sha256'].items():assert sha(ART/'packed'/key)==h
 assert {a['key']for a in r['assets']}==set(row['keys'])
 for key in row['keys']:assert key not in byKey;byKey[key]=rel(p)
 proofs.append(dict(path=rel(p),sha256=sha(p),html_path=rel(baseline/'moonstone.html'),html_sha256=r['html_sha256']))
assert set(byKey)==keys
entries=[];photos=shadows=0
for c in selected:
 key=c['key'];r=records[key];png=ART/'packed'/key;prompt=ART/'prompts'/f"{c['bank']}-{c['frame']:03}.txt";isShadow=set(c['indices'])<={0,5};raw=png if isShadow else ART/'raw'/key
 if not isShadow:assert sha(raw)==r['raw_sha256'];photos+=1
 else:assert r['tool']=='preserved_original_black_shadow';shadows+=1
 e=dict(key=key,bank=c['bank'],frame=c['frame'],source_bank_sha256=c['source_bank']['sha256'],indices_sha256=c['indices_sha256'],png=rel(png),png_sha256=sha(png),raw=rel(raw),raw_sha256=sha(raw),prompt=rel(prompt),prompt_sha256=sha(prompt),generation_tool=r['tool'],runtime_proof=byKey[key],runtime_asset_sha256=sha(png),actual_runtime_observed=False,runtime_scope='source_exact_fixture_only')
 if c['needs_mask']:
  mask=png.with_name(png.stem+'.mask.png');e.update(mask=rel(mask),mask_sha256=sha(mask))
 entries.append(e)
assert (photos,shadows)==(39,1)
review=ART/'root-review-r1-rest40-v1.json';rv=read(review);assert rv['status']=='root_visually_reviewed' and {r['key']:r['png_sha256']for r in rv['candidates']}=={e['key']:e['png_sha256']for e in entries};
activation=ART/'activation-set-ratmen-r1-rest40-v1.json';write(activation,dict(companion_derivations=[dict(path=rel(review),sha256=sha(review)),dict(path=rel(ART/'verification/foliage063-color-v2.json'),sha256=sha(ART/'verification/foliage063-color-v2.json'))],schema=1,visual_status='reviewed_original_and_runtime',source_zip_sha256=sha(ROOT/'Moonstonecd32-AMIGA.zip'),production_code_sha256=production,wasm_core_sha256=sha(host/'moonstone-core-used.js'),proofs=proofs,entries=entries,fixture_only=sorted(keys),actual_runtime_observed=False))
delivery=ART/'delivery-r1-rest40-v1.json';write(delivery,dict(schema=1,status='ready_for_sequential_integration',scope='RATMEN1/011..037,044,051,053..063.39 separate egne fotomastere og059 ren svart originalskygge uten fotoendring. Alle40 har streng faktisk frontend-kildefixture normal/speilet, men denne gruppen paastaar ingen faktisk kampfangst. Begge levende6..8-masker er proevd i fem originalpaletter.',visible_photo_material_masters=photos,preserved_opaque_black_shadow_masters=shadows,actual_runtime_observed=False,fixture_only=sorted(keys),source_contracts_sha256=sha(ART/'source-contracts.json'),source_color_contract_sha256=sha(ART/'identity/source-color-contract.json'),generation_records_sha256=sha(frozenRecords),activation_set_sha256=sha(activation),packing_test_sha256=sha(ART/'verification/packing-r1-rest40-v2.json'),runtime_summary_sha256=sha(ART/'verification/r1-rest40-fixtures-v2/summary.json'),checks=summary['checks'],production_code_sha256=production,entries=[dict(**e,source_size=[c['width'],c['height']],target_size=[c['target_width'],c['target_height']],original=c['original'])for e,c in zip(entries,selected)],limitations=['Original kildekontur og transparente hull er laast. Fotoet gir overflatematerialet; fri anatomitolkning er ikke gjort.','024 bruker egenv2-raamaster og14 kildebundne lyse fotomaterialceller.063 bruker kildeindeksbundet groenn/teal-fargeregistrering, samme nygenererte foto.','51 er kildeobservert som bakingsfragment; ingen ny retensjonsstoette paastaas i denne fixtureleveransen.','63 er busk-/bladfragment. Spillerpaletten6..8 gjelder kun023/025, aldri miljoefargene22/24/25/28.']))
files={review,Path(__file__),activation,delivery,frozenRecords,ART/'selection-r1-rest40.json',ART/'source-contracts.json',ART/'queue-subset.json',ART/'packing-material-overrides.json',ART/'register-foliage063-v2.py',ART/'verification/foliage063-color-v2.json',ART/'identity/source-color-contract.json',ART/'verification/packing-r1-rest40-v2.json',ART/'verification/r1-rest40-fixtures-v2/summary.json',baseline/'package-ledger.json'}
files.update(ART/n for n in ['pack-v3.cjs','record.py','masks.py','verify.py','build-runtime.py','runtime-proof.cjs','runtime-host.cjs','runtime-ratmen-r1-rest40-fixtures-v2.cjs','run-r1-rest40-fixtures-v2.py'])
files.update(ART/f'comparison-r1-rest40-v2-{n}.png'for n in range(1,5));files.update(ROOT/p['path']for p in proofs)
for e in entries:
 files.update(ROOT/e[k]for k in ['raw','prompt','png']);files.add(ART/'references'/e['key'])
 if e.get('mask'):files.add(ROOT/e['mask'])
#063s ikke-aktive v1 er en reproduksjonsinngang for den smale fotofargeregistreringen.
files.add(ART/'revisions/063-packed-v1/063.png')
#Bevar et lite representativt bildeutvalg fra hvert selvstendige proeveforloep.
for n,row in enumerate(summary['proofs']):
 key=row['keys'][0];stem=key.replace('/','-').replace('.png','');directory=(ROOT/row['path']).parent
 files.update(directory/f'{stem}-{kind}.png'for kind in ['original','hd','mirror-original','mirror-hd'])
listing=ART/'delivery-r1-rest40-files.txt';files.add(listing);assert all(p.exists()or p==listing for p in files)
text='\n'.join(sorted(rel(p)for p in files))+'\n'
if listing.exists():assert listing.read_text()==text
else:listing.write_text(text)
print(json.dumps(dict(status='ready',routes=40,png=42,photos=photos,original_shadows=shadows,actual_observed=0,fixture_only=40,checks=summary['checks'],activation_sha256=sha(activation),files=len(files))))
