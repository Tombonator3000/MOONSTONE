#!/usr/bin/env python3
"""Frys ferdigkontrollerte kandidatfiler. Ingen produksjonsaktivering."""
from pathlib import Path
import hashlib,json,shutil
ART=Path(__file__).resolve().parent;ROOT=ART.parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rel=lambda p:str(p.relative_to(ROOT))
source=json.loads((ART/'source-contract.json').read_text())
proof_names=['natural-v22-blue/math-figure-palette-test.json','natural-v22-red/math-figure-palette-test.json','routes-v22/math-routes-test.json']
proofs=[];html=ROOT/'web/build/moonstone-math-proof.html';html_hash=sha(html)
for name in proof_names:
 p=ART/'verification'/name;r=json.loads(p.read_text());assert r['status']=='passed',name;assert r['html_sha256']==html_hash
 for k,h in r.get('sources',r.get('source_files',{})).items():assert sha(ROOT/k)==h,k
 for k,h in r.get('assets',{}).items() if isinstance(r.get('assets'),dict) else []:
  f=ART/'packed'/k
  if f.exists():assert sha(f)==h,k
 for k,h in r.get('files',{}).items():assert sha(ART/'packed/Wi1.C'/k)==h,k
 for k,h in r.get('candidate_files',{}).items():assert sha(ROOT/k)==h,k
 if 'static_plate' in r:assert sha(ROOT/r['static_plate']['path'])==r['static_plate']['sha256']
 proofs.append({'path':rel(p),'sha256':sha(p),'html_path':rel(ART/'verification/runtime-v22/moonstone.html'),'html_sha256':html_hash})
origins={4:'004-v7-scene-context',5:'005-v4-registered',6:'006-v6-context',7:'007-v4-context',10:'010-v4-registered',11:'011-v5-context',12:'012-v4-context',3:'003-v3'}
entries=[]
for row in source['routes']:
 n=row['frame'];stem=origins.get(n,f'{n:03}-v1');raw=ART/'raw'/f'{stem}.png';prompt=ART/'prompts'/f'{stem}.txt';png=ART/'packed'/row['target'];record=png.with_suffix('.json');pack=json.loads(record.read_text());assert sha(png)==pack['output_sha256'];assert sha(ART/f'source/indices/{n:03}.bin')==row['indices_sha256']
 entry={'key':row['target'],'bank':'Wi1.C','frame':n,'source_bank_sha256':row['source_bank_sha256'],'indices_sha256':row['indices_sha256'],'png':rel(png),'png_sha256':sha(png),'raw':rel(raw),'raw_sha256':sha(raw),'prompt':rel(prompt),'prompt_sha256':sha(prompt),'generation_tool':'builtin_image_gen','pack_record':rel(record),'pack_record_sha256':sha(record),'runtime_proof':rel(ART/'verification/routes-v22/math-routes-test.json'),'runtime_asset_sha256':sha(png)}
 if pack.get('mask_sha256'):
  m=png.with_name(png.stem+'.mask.png');assert sha(m)==pack['mask_sha256'];entry.update(mask=rel(m),mask_sha256=sha(m))
 entries.append(entry)
material_files=[*sorted((ART/'material').glob('*.json')),*sorted((ART/'material').glob('*.png')),ART/'raw/head-root-v1.png',ART/'prompts/head-root-v1.txt',ART/'raw/cloth-context-v1.png',ART/'prompts/cloth-context-v1.txt',ART/'register-head-root.cjs',ART/'register-eye-material.cjs',ART/'complete-cloth-material.cjs',ART/'repack-current.cjs',*sorted(ART.glob('*registration.json')),ART/'shared-cloth.json',ART/'shared-face-cloth-007-012.json',ART/'cloak-bottom-seam-007-012.json',ROOT/'tools/hd_math_figurer_pakk.cjs']
static_png=ART/'packed/embedded/math-static.png';static=json.loads((ART/'static-source-contract.json').read_text())
result={'schema':1,'visual_status':'reviewed_original_and_runtime','scope':'17 separate Wi1.C figure/fragment masters plus one embedded Math figure plate from WI1.P. Four empty3x3 routes008/009/013/014 are deliberately excluded. Separate shared hair-root and cloak material repair assets are documented and do not count as additional animation masters.','source_zip_sha256':sha(ROOT/'Moonstonecd32-AMIGA.zip'),'production_code_sha256':{str(p):sha(ROOT/p) for p in ['web/src/core.js','web/src/render.js','web/src/scenes.js']},'wasm_core_sha256':sha(ROOT/'web/build/moonstone-core.js'),'source_contract':rel(ART/'source-contract.json'),'source_contract_sha256':sha(ART/'source-contract.json'),'proofs':proofs,'entries':entries,'embedded_entries':[{'key':'embedded/math-static.png','png':rel(static_png),'png_sha256':sha(static_png),'raw':rel(ART/'raw/math-static-v1.png'),'raw_sha256':sha(ART/'raw/math-static-v1.png'),'prompt':rel(ART/'prompts/math-static-v1.txt'),'prompt_sha256':sha(ART/'prompts/math-static-v1.txt'),'source_contract':rel(ART/'static-source-contract.json'),'source_contract_sha256':sha(ART/'static-source-contract.json'),'source_file_sha256':static['source_file_sha256'],'source_mask_sha256':static['mask_sha256'],'mask_pixels':static['mask_pixels'],'scene_id':'math-balcony','overlay':{'key':'embedded/math-static','rect':static['rect'],'uv_rect':[0,0,1,1],'foreground':True}}],'material_derivations':[{'path':rel(p),'sha256':sha(p)} for p in material_files],'mask_revision':{'path':rel(ART/'verification/mask-revision-v22.json'),'sha256':sha(ART/'verification/mask-revision-v22.json')},'visual_identity':{'photo_files_byteidentical_to_v21':True,'parent_approval':'v21 alternate, closed, natural2651/2976 accepted; v22 only live NN mask repair','v21_index':rel(ART/'verification/frozen-v21/activation-set-001.json'),'v21_index_sha256':sha(ART/'verification/frozen-v21/activation-set-001.json')},'alpha_proof':{'path':rel(ART/'verification/alpha-v21.json'),'sha256':sha(ART/'verification/alpha-v21.json')}}
(ART/'verification/runtime-v22').mkdir(exist_ok=True);shutil.copyfile(html,ART/'verification/runtime-v22/moonstone.html')
(ART/'activation-set-002.json').write_text(json.dumps(result,indent=2)+'\n');print(sha(ART/'activation-set-002.json'),len(entries))
