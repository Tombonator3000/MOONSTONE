"""Frys seks selvstendige beistruter med originalkilde og faktisk runtimebevis."""
from pathlib import Path
import json, hashlib
from PIL import Image
H=Path(__file__).resolve().parent;R=H.parents[3]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rel=lambda p:str(p.relative_to(R))
g=json.loads((H/'geometries-six-v3.json').read_text());gens=json.loads((H/'generation-records-six-v1.json').read_text());pack=json.loads((H/'verification/packing-six-v3.json').read_text());check=json.loads((H/'verification/packing-independent-six-v3.json').read_text());proof=H/'verification/runtime-six-v3/test.json';runtime=json.loads(proof.read_text())
assert runtime['status']==check['status']=='passed' and not runtime['errors']
assert len(g)==len(gens)==len(pack['assets'])==6 and len(runtime['fixtures'])==12 and len(runtime['negative'])==60
assert sha(H/'geometries-six-v3.json')==runtime['geometry_sha256']==pack['geometry_sha256']==check['geometry_sha256']
assert sha(H/'runtime-six-v3.cjs')==runtime['test_sha256'] and sha(H/'pack-six-v3.cjs')==pack['packing_script_sha256'] and sha(H/'check-six-v3.py')==check['script_sha256']
assert sha(H/'generation-records-six-v1.json')==pack['generation_records_sha256']==check['generation_records_sha256']
assert sha(proof.parent/'loaded.html')==runtime['html_sha256']
assert {k.lower().replace('.png','')for k in runtime['assets']}==set(runtime['runtime']['seen'])
for p,h in runtime['production_code_sha256'].items():assert sha(R/p)==h
assert sha(R/'Moonstonecd32-AMIGA.zip')==runtime['source_zip_sha256'] and sha(R/'web/build/moonstone-core.js')==runtime['wasm_core_sha256']
entries=[]
for c in g:
 photo=next(x for x in gens if x['key']==c['key']);packed=next(x for x in pack['assets']if x['key']==c['key']);png=H/'packed-six-v3'/c['key']
 for k in ['raw','prompt','reference']:assert sha(H/photo[k])==photo[k+'_sha256']
 assert sha(png)==packed['candidate_sha256']==runtime['assets'][c['key']]==next(x['png_sha256']for x in check['assets']if x['key']==c['key'])
 assert sha(R/c['source_palette_contract'])==c['source_palette_contract_sha256']==runtime['palette_case_sha256']
 record={**photo,**packed,'visual_status':'reviewed_original_and_runtime','geometry_sha256':runtime['geometry_sha256'],'packing_script_sha256':pack['packing_script_sha256'],'runtime_scope':runtime['scope'],'method':pack['scope']}
 rp=H/f"{c['number']}-final-record-six-v3.json";rp.write_text(json.dumps(record,indent=2)+'\n')
 entries.append(dict(key=c['key'],bank='be1.c',frame=c['frame'],source_bank_sha256=c['source_bank_sha256'],indices_sha256=c['indices_sha256'],png=rel(png),png_sha256=sha(png),raw=rel(H/photo['raw']),raw_sha256=photo['raw_sha256'],prompt=rel(H/photo['prompt']),prompt_sha256=photo['prompt_sha256'],generation_tool='builtin_image_gen',runtime_proof=rel(proof),runtime_asset_sha256=sha(png),art_record=rel(rp),art_record_sha256=sha(rp),qa=dict(source_alpha_midpoints=c['width']*c['height'],source_midpoints_missing=0,source_transparent_midpoints_filled=0,normal_and_mirror=True,unknown_foreground_rejected=True,original_hd_return='exact',emulated_state='unchanged')))
companions=[H/p for p in ['geometries-six-v3.json','generation-records-six-v1.json','verification/packing-six-v3.json','verification/packing-independent-six-v3.json','pack-six-v3.cjs','check-six-v3.py','runtime-six-v3.cjs','freeze-six-v3.py','generation-calls-six-v1.json','prepare-six-v3.py','geometries-first3-v1.json','geometries-003-005-v1.json']]+[R/g[0]['source_palette_contract'],R/'tools/hd_resterende_ikoner_fixture.cjs']+[H/x['reference']for x in gens]
index=dict(schema=1,visual_status='reviewed_original_and_runtime',source_zip_sha256=runtime['source_zip_sha256'],production_code_sha256=runtime['production_code_sha256'],wasm_core_sha256=runtime['wasm_core_sha256'],proofs=[dict(path=rel(proof),sha256=sha(proof),html_path=rel(proof.parent/'loaded.html'),html_sha256=runtime['html_sha256'])],companion_derivations=[dict(path=rel(p),sha256=sha(p))for p in companions],scope=runtime['scope'],entries=entries)
out=H/'activation-set-six-v3.json';out.write_text(json.dumps(index,indent=2)+'\n');print(json.dumps(dict(status='frozen_not_activated',routes=6,checks=len(runtime['checks']),sha256=sha(out))))
