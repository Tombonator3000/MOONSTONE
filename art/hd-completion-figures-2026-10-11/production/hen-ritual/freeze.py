"""Frys37 egne ritualmastere,74 originale ruter og30 oppstigningsmasker."""
from pathlib import Path
import argparse,json,hashlib
from PIL import Image
H=Path(__file__).resolve().parent;R=H.parents[3]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rel=lambda p:str(p.resolve().relative_to(R))
p=argparse.ArgumentParser();p.add_argument('--visual-reviewed',action='store_true');a=p.parse_args();assert a.visual_reviewed
cs=json.loads((H/'source-contracts.json').read_text());gs=sum([json.loads((H/f).read_text())for f in ['generation-records-v1.json','generation-records-effects-v1.json','generation-records-ascending-v1.json']],[])
assert len(cs)==len(gs)==len({g['raw_sha256']for g in gs})==len({g['tool_call_id']for g in gs})==37
proof_paths=[H/'verification'/d/'test.json'for d in ['all-current-v4','negative-current-v4','negative-klift-current-v4']];proofs=[json.loads(p.read_text())for p in proof_paths];runtime=proofs[0]
for p,d in zip(proof_paths,proofs):
 assert d['status']=='passed' and not d['errors'],p
 for k in ['production_code_sha256','wasm_core_sha256','source_zip_sha256','html_sha256']:assert d[k]==runtime[k],(p,k)
assert sha(H/'runtime-all-current.cjs')==runtime['test_sha256']
for d in proofs[1:]:assert sha(H/'runtime-negative-current.cjs')==d['script_sha256'] and len(d['normal_photo_exact'])==15
for f,d in runtime['production_code_sha256'].items():assert sha(R/f)==d
assert len(runtime['runtime']['seen'])==37 and len(runtime['fixtures'])==208
assert '2750_allblack_exact' in runtime['checks']
for d in proofs[1:]:assert all(x['mode3_sha256']==x['mode0_sha256']for x in d['normal_photo_exact'])
entries=[];midpoints=0
for c in cs:
 g=next(g for g in gs if g['key']==c['key']);png=H/'packed'/c['key'];raw=H/g['raw'];prompt=H/g['prompt'];mask=png.with_name(png.stem+'.mask.png')
 assert g['generation_tool']=='builtin_image_gen' and sha(raw)==g['raw_sha256'] and sha(prompt)==g['prompt_sha256']
 assert sha(H/g['source_reference'])==g['source_reference_sha256']
 im=Image.open(png);assert im.mode=='RGBA' and im.size==(c['width']*4,c['height']*4)
 for q,i in enumerate(c['indices']):assert (im.getpixel((q%c['width']*4+2,q//c['width']*4+2))[3]>=128)==bool(i);midpoints+=1
 assert runtime['assets'][c['key']]==runtime['assets'][c['alias']]==sha(png)
 if c['frame']>=40:
  m=Image.open(mask);assert m.mode=='RGBA' and m.size==im.size
  for y in range(m.height):
   for x in range(m.width):
    i=c['indices'][y//4*c['width']+x//4];v=m.getpixel((x,y));assert v[0]==(i+1 if i else 0) and v[2]==(255 if i else 0) and v[3]==255
  for key in [c['key'],c['alias']]:assert runtime['assets'][key.replace('.png','.mask.png')]==sha(mask)
  for d,key in zip(proofs[1:],[c['key'],c['alias']]):assert d['assets'][key]==sha(png) and d['assets'][key.replace('.png','.mask.png')]==sha(mask)
 natural=runtime['runtime']['seen'][str(c['frame'])];assert natural['state']==natural['state_after']
 record={**g,'candidate_sha256':sha(png),'source_bank_sha256':c['source_bank_sha256'],'source_indices_sha256':c['indices_sha256'],'identity':c['identity'],'observed_palette':c['palette'],'palette_source':c.get('palette_source','ending_original_scanout_verified_against_source_call_palette'),'runtime_frame':natural['frame'],'geometry_gate_passed':True,'visual_status':'reviewed_original_and_runtime','scope':'One separate generated light/material master per original frame. Source-contour registration and restrained source-color lighting. Ascending normal color is blue, with strict mode3 masks; historical purple generation references are preserved only as material provenance.'}
 rp=H/f"records/{c['frame']:03}-final.json";rp.parent.mkdir(exist_ok=True);rp.write_text(json.dumps(record,indent=2,ensure_ascii=False)+'\n')
 master=dict(key=c['key'],bank='hen1.c',frame=c['frame'],source_bank_sha256=c['source_bank_sha256'],indices_sha256=c['indices_sha256'],png=rel(png),png_sha256=sha(png),raw=rel(raw),raw_sha256=sha(raw),prompt=rel(prompt),prompt_sha256=sha(prompt),generation_tool='builtin_image_gen',runtime_proof=rel(proof_paths[0]),runtime_asset_sha256=sha(png),art_record=rel(rp),art_record_sha256=sha(rp),qa=dict(natural_original_call_frame=natural['frame'],source_midpoints_missing=0,source_transparent_midpoints_filled=0,normal_and_mirror=True,original_hd_return='exact',emulated_state='unchanged',aliases_source_byteidentical=True,strict_NN_mask=c['frame']>=40))
 if c['frame']>=40:master.update(mask=rel(mask),mask_sha256=sha(mask))
 entries.append(master);alias={**master,'key':c['alias'],'bank':'Klift1.CEL','master_key':c['key']}
 for k in ['raw','raw_sha256','prompt','prompt_sha256','generation_tool']:alias.pop(k)
 entries.append(alias)
companions=[H/f for f in ['prepare.py','source-contracts.json','source-contracts-memory-palette-v1.json','palette-correction-v2.json','generation-records-v1.json','generation-records-effects-v1.json','generation-records-ascending-v1.json','geometries.json','geometries-effects.json','geometries-ascending.json','geometries-effects-build.py','geometries-ascending-build.py','pack.cjs','pack-effects.cjs','pack-ascending.cjs','mask-build.py','freeze.py','runtime-all-current.cjs','runtime-negative-current.cjs','verification/knight-independent-v1.json','verification/packing-effects-v1.json','verification/packing-ascending-v1.json','verification/ascending-all-v1/test.json','source/ending-runtime-catalog-v1.json']]+[H.parent/'contours.py']
# Alle kilde- og materialderivasjoner skal fortsatt finnes med nøyaktig samme SHA.
for f in companions:assert f.is_file(),f
html=H/'verification/all-current-v4/loaded.html';assert sha(html)==runtime['html_sha256']
delivery=dict(schema=1,visual_status='reviewed_original_and_runtime',source_zip_sha256=runtime['source_zip_sha256'],production_code_sha256=runtime['production_code_sha256'],wasm_core_sha256=runtime['wasm_core_sha256'],proofs=[dict(path=rel(p),sha256=sha(p),html_path=rel(html),html_sha256=sha(html))for p in proof_paths],companion_derivations=[dict(path=rel(p),sha256=sha(p))for p in companions],scope=runtime['scope'],entries=entries)
target=H/'activation-set-001.json';assert not target.exists();target.write_text(json.dumps(delivery,indent=2,ensure_ascii=False)+'\n');summary=dict(status='passed',distinct_generated_masters=37,source_routes=74,pngs=104,source_alpha_midpoints=midpoints,fixtures=208,checks=sum(len(p['checks'])for p in proofs),activation_sha256=sha(target));(H/'verification/freeze-proof.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary))
