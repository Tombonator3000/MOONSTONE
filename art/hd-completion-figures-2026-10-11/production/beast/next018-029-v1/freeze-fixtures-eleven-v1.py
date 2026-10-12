"""Frys elleve kildeeksakte beistruter med tydelig merkede frontendfixturer."""
from pathlib import Path
import hashlib,json

H=Path(__file__).resolve().parent;R=H.parents[4]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rel=lambda p:str(p.relative_to(R))
proof=H/'verification/runtime-next-v2/test.json';runtime=json.loads(proof.read_text())
geometry=H/'runtime-geometries-v1.json';g=json.loads(geometry.read_text())
assert runtime['status']=='passed' and not runtime['errors']
assert len(g)==15 and len(runtime['fixtures'])==30 and len(runtime['negative'])==150
assert sha(geometry)==runtime['geometry_sha256']
assert sha(H/'runtime-next-v2.cjs')==runtime['test_sha256']
assert sha(proof.parent/'loaded.html')==runtime['html_sha256']
actual={k+'.png'for k in runtime['runtime']['seen']}
assert actual=={'be1.c/014.png','be1.c/016.png','be1.c/018.png','be1.c/020.png'}
observed=set(runtime['unobserved'])
assert observed==set(runtime['assets'])-actual and len(observed)==11
fixture_keys={row['key']for row in runtime['fixtures']}
assert observed<=fixture_keys
fixture_scope='Elleve egne kildeeksakte fotomastere kontrollert visuelt mot originalen og i normal/speilet frontendfixtur. Alle kilde-, alfahull-, palett- og negative eierskapsporter bestaar. Ingen av disse elleve er fanget som HD i den kontrollerte originale kampsekvensen. Ingen naturlig observasjon av disse rutene paastaas.'
for p,h in runtime['production_code_sha256'].items():assert sha(R/p)==h
assert sha(R/'Moonstonecd32-AMIGA.zip')==runtime['source_zip_sha256']
assert sha(R/'web/build/moonstone-core.js')==runtime['wasm_core_sha256']
entries=[];companions={geometry,H/'runtime-next-v1.cjs',H/'runtime-next-v2.cjs',H/'freeze-fixtures-eleven-v1.py',H/'verification/runtime-next-v1/test.json',R/'tools/hd_resterende_ikoner_fixture.cjs'}
for folder,version,gens in [('next012-017-v1','v2','generation-records-v2.json'),('next018-029-v1','v3','generation-records-v3.json')]:
 base=H.parent/folder;gp=base/f'geometries-{version}.json';generation=base/gens;packp=base/f'verification/packing-{version}.json';checkp=base/f'verification/packing-independent-{version}.json'
 photos=json.loads(generation.read_text());pack=json.loads(packp.read_text());check=json.loads(checkp.read_text())
 assert check['status']=='passed' and sha(gp)==pack['geometry_sha256']==check['geometry_sha256']
 assert sha(generation)==pack['generation_records_sha256']==check['generation_records_sha256']
 assert sha(base/f'pack-{version}.cjs')==pack['packing_script_sha256']
 assert sha(base/f'check-{version}.py')==check['script_sha256']
 companions.update([gp,generation,packp,checkp,base/f'pack-{version}.cjs',base/f'check-{version}.py'])
 for c in [c for c in g if c['key']in observed and c['parent_geometry_path']==rel(gp)]:
  assert c['parent_geometry_sha256']==sha(gp)
  photo=next(x for x in photos if x['key']==c['key']);packed=next(x for x in pack['assets']if x['key']==c['key']);png=R/c['packed_candidate_path']
  for name in ['raw','prompt','reference']:assert sha(base/photo[name])==photo[name+'_sha256']
  assert sha(png)==packed['candidate_sha256']==runtime['assets'][c['key']]==next(x['png_sha256']for x in check['assets']if x['key']==c['key'])
  assert sha(R/c['source_palette_contract'])==c['source_palette_contract_sha256']==runtime['palette_case_sha256']
  companions.add(R/c['source_palette_contract']);companions.add(base/photo['reference'])
  record={**photo,**packed,'visual_status':'reviewed_original_and_runtime','geometry_sha256':sha(gp),'runtime_geometry_sha256':sha(geometry),'packing_script_sha256':pack['packing_script_sha256'],'runtime_scope':runtime['scope'],'method':pack['scope']}
  rp=H/f"{c['number']}-final-record-fixtures-v1.json";b=json.dumps(record,indent=2)+'\n'
  if rp.exists():assert rp.read_text()==b
  else:rp.write_text(b)
  entries.append(dict(key=c['key'],bank='be1.c',frame=c['frame'],source_bank_sha256=c['source_bank_sha256'],indices_sha256=c['indices_sha256'],png=rel(png),png_sha256=sha(png),raw=rel(base/photo['raw']),raw_sha256=photo['raw_sha256'],prompt=rel(base/photo['prompt']),prompt_sha256=photo['prompt_sha256'],generation_tool='builtin_image_gen',runtime_proof=rel(proof),runtime_asset_sha256=sha(png),art_record=rel(rp),art_record_sha256=sha(rp),qa=dict(actual_runtime_observed=False,source_alpha_midpoints=c['width']*c['height'],source_midpoints_missing=0,source_transparent_midpoints_filled=0,normal_and_mirror=True,unknown_foreground_rejected=True,original_hd_return='exact',emulated_state='unchanged')))
index=dict(schema=1,visual_status='reviewed_original_and_runtime',source_zip_sha256=runtime['source_zip_sha256'],production_code_sha256=runtime['production_code_sha256'],wasm_core_sha256=runtime['wasm_core_sha256'],proofs=[dict(path=rel(proof),sha256=sha(proof),html_path=rel(proof.parent/'loaded.html'),html_sha256=runtime['html_sha256'])],companion_derivations=[dict(path=rel(p),sha256=sha(p))for p in sorted(companions)],scope=fixture_scope,actual_runtime_observed=False,unobserved_candidates=runtime['unobserved'],entries=entries)
out=H/'activation-set-fixtures-eleven-v1.json';b=json.dumps(index,indent=2)+'\n'
if out.exists():assert out.read_text()==b
else:out.write_text(b)
print(json.dumps(dict(status='frozen_not_activated',routes=len(entries),checks=len(runtime['checks']),sha256=sha(out))))
