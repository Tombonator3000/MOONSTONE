"""Frys tre faktisk observerte beistruter med originalkilde og faktisk runtimebevis."""
from pathlib import Path
import json, hashlib
from PIL import Image
H=Path(__file__).resolve().parent;R=H.parents[4]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rel=lambda p:str(p.relative_to(R))
g=json.loads((H/'geometries-v3.json').read_text());gens=json.loads((H/'generation-records-v1.json').read_text());pack=json.loads((H/'verification/packing-v3.json').read_text());check=json.loads((H/'verification/packing-independent-v3.json').read_text());proof=H/'verification/runtime-v5/test.json';runtime=json.loads(proof.read_text())
assert runtime['status']==check['status']=='passed' and not runtime['errors']
assert len(g)==len(gens)==len(pack['assets'])==6 and len(runtime['fixtures'])==6 and len(runtime['negative'])==30
assert set(runtime['assets'])=={'be1.c/007.png','be1.c/008.png','be1.c/009.png'}
assert sha(H/'geometries-v3.json')==runtime['geometry_sha256']==pack['geometry_sha256']==check['geometry_sha256']
assert sha(H/'runtime-v5.cjs')==runtime['test_sha256'] and sha(H/'pack-v3.cjs')==pack['packing_script_sha256'] and sha(H/'check-v3.py')==check['script_sha256']
assert sha(H/'generation-records-v1.json')==pack['generation_records_sha256']==check['generation_records_sha256']
assert sha(proof.parent/'loaded.html')==runtime['html_sha256']
assert {k.lower().replace('.png','')for k in runtime['assets']}==set(runtime['runtime']['seen'])
for p,h in runtime['production_code_sha256'].items():assert sha(R/p)==h
assert sha(R/'Moonstonecd32-AMIGA.zip')==runtime['source_zip_sha256'] and sha(R/'web/build/moonstone-core.js')==runtime['wasm_core_sha256']
entries=[]
for c in [c for c in g if c['key'] in runtime['assets']]:
 photo=next(x for x in gens if x['key']==c['key']);packed=next(x for x in pack['assets']if x['key']==c['key']);png=H/'packed-v3'/c['key']
 for k in ['raw','prompt','reference']:assert sha(H/photo[k])==photo[k+'_sha256']
 assert sha(png)==packed['candidate_sha256']==runtime['assets'][c['key']]==next(x['png_sha256']for x in check['assets']if x['key']==c['key'])
 assert sha(R/c['source_palette_contract'])==c['source_palette_contract_sha256']==runtime['palette_case_sha256']
 record={**photo,**packed,'visual_status':'reviewed_original_and_runtime','geometry_sha256':runtime['geometry_sha256'],'packing_script_sha256':pack['packing_script_sha256'],'runtime_scope':runtime['scope'],'method':pack['scope']}
 rp=H/f"{c['number']}-final-record-three-v1.json";rp.write_text(json.dumps(record,indent=2)+'\n')
 entries.append(dict(key=c['key'],bank='be1.c',frame=c['frame'],source_bank_sha256=c['source_bank_sha256'],indices_sha256=c['indices_sha256'],png=rel(png),png_sha256=sha(png),raw=rel(H/photo['raw']),raw_sha256=photo['raw_sha256'],prompt=rel(H/photo['prompt']),prompt_sha256=photo['prompt_sha256'],generation_tool='builtin_image_gen',runtime_proof=rel(proof),runtime_asset_sha256=sha(png),art_record=rel(rp),art_record_sha256=sha(rp),qa=dict(source_alpha_midpoints=c['width']*c['height'],source_midpoints_missing=0,source_transparent_midpoints_filled=0,normal_and_mirror=True,unknown_foreground_rejected=True,original_hd_return='exact',emulated_state='unchanged')))
companions=[H/p for p in ['geometries-v3.json','generation-records-v1.json','verification/packing-v3.json','verification/packing-independent-v3.json','pack-v3.cjs','check-v3.py','runtime-v5.cjs','freeze-three-v1.py','prepare-v3.py','runtime-v2.cjs','runtime-v3.cjs','runtime-v4.cjs','verification/runtime-v2/test.json','verification/runtime-v3/test.json','verification/runtime-v4/test.json']]+[R/g[0]['source_palette_contract'],R/'tools/hd_resterende_ikoner_fixture.cjs']+[H/x['reference']for x in gens]
index=dict(schema=1,visual_status='reviewed_original_and_runtime',source_zip_sha256=runtime['source_zip_sha256'],production_code_sha256=runtime['production_code_sha256'],wasm_core_sha256=runtime['wasm_core_sha256'],proofs=[dict(path=rel(proof),sha256=sha(proof),html_path=rel(proof.parent/'loaded.html'),html_sha256=runtime['html_sha256'])],companion_derivations=[dict(path=rel(p),sha256=sha(p))for p in companions],scope=runtime['scope'],unobserved_candidates=['be1.c/006.png','be1.c/010.png','be1.c/011.png'],entries=entries)
out=H/'activation-set-three-v1.json';out.write_text(json.dumps(index,indent=2)+'\n');print(json.dumps(dict(status='frozen_not_activated',routes=3,checks=len(runtime['checks']),sha256=sha(out))))
