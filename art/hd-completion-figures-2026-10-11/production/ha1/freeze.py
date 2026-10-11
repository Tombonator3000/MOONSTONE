"""Bind HA1 candidates to original bytes, distinct photos and actual frontend proof."""
from pathlib import Path
import argparse,hashlib,json
from PIL import Image
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rel=lambda p:str(p.relative_to(ROOT))
parser=argparse.ArgumentParser();parser.add_argument('--visual-reviewed',action='store_true');parser.add_argument('--runtime',default='verification/runtime-v1/test.json');args=parser.parse_args()
proof=HERE/args.runtime;runtime=json.loads(proof.read_text());assert runtime['status']=='passed' and not runtime['errors']
assert len(runtime['fixtures'])==44 and set(runtime['runtime']['seen'])==set(map(str,range(7)))
contracts=json.loads((HERE/'source-contracts.json').read_text());packing=json.loads((HERE/'verification/packing-v1.json').read_text());generation=json.loads((HERE/'generation-records-v1.json').read_text())
assert len(contracts)==len(packing['assets'])==len(generation)==22
independent=json.loads((HERE/'verification/packing-independent-v1.json').read_text());assert independent['status']=='passed' and len(independent['assets'])==22 and independent['script_sha256']==sha(HERE/'check.py') and independent['geometry_sha256']==sha(HERE/'geometries.json')
assert packing['packing_script_sha256']==sha(HERE/'pack.cjs') and packing['geometry_sha256']==sha(HERE/'geometries.json') and packing['generation_records_sha256']==sha(HERE/'generation-records-v1.json')
assert len({g['generated_output'] for g in generation})==len({g['raw_sha256'] for g in generation})==22
assert runtime['geometry_sha256']==sha(HERE/'geometries.json') and runtime['test_sha256']==sha(HERE/'runtime.cjs')
assert sha(proof.parent/'loaded.html')==runtime['html_sha256']
for f,h in runtime['production_code_sha256'].items():assert sha(ROOT/f)==h
assert sha(ROOT/'web/build/moonstone-core.js')==runtime['wasm_core_sha256']
assert sha(ROOT/'Moonstonecd32-AMIGA.zip')==runtime['source_zip_sha256']
entries=[];midpoints=0
for c,p,g in zip(contracts,packing['assets'],generation):
 assert c['key']==p['key']==g['key'];png=HERE/'packed'/c['key'];raw=HERE/g['raw'];prompt=HERE/g['prompt']
 assert sha(raw)==g['raw_sha256']==p['raw_sha256'] and sha(prompt)==g['prompt_sha256']==p['prompt_sha256']
 assert sha(png)==p['candidate_sha256']==runtime['assets'][c['key']]
 assert next(r for r in independent['assets'] if r['key']==c['key'])['png_sha256']==sha(png)
 im=Image.open(png);assert im.mode=='RGBA' and im.size==(c['width']*4,c['height']*4)
 for q,index in enumerate(c['indices']):
  assert (im.getpixel((q%c['width']*4+2,q//c['width']*4+2))[3]>=128)==bool(index)
  midpoints+=1
 assert not (HERE/'packed'/c['key'].replace('.png','.mask.png')).exists()
 record={**g,**p,'packing_script_sha256':sha(HERE/'pack.cjs'),'geometry_sha256':sha(HERE/'geometries.json'),
  'method':packing['scope'],'visual_status':'reviewed_original_and_runtime' if args.visual_reviewed else 'pending_visual_review',
  'runtime_scope':'Natural original intro for000..006; explicit normal/mirrored frontend fixtures for all22. Routes007..021 not claimed naturally observed.'}
 record_path=HERE/f"records/{c['frame']:03}-final.json";record_path.parent.mkdir(exist_ok=True);record_path.write_text(json.dumps(record,indent=2,ensure_ascii=False)+'\n')
 entries.append(dict(key=c['key'],bank='ha1.cel',frame=c['frame'],source_bank_sha256=c['source_bank_sha256'],indices_sha256=c['indices_sha256'],
  png=rel(png),png_sha256=sha(png),raw=rel(raw),raw_sha256=sha(raw),prompt=rel(prompt),prompt_sha256=sha(prompt),generation_tool='builtin_image_gen',
  runtime_proof=rel(proof),runtime_asset_sha256=sha(png),art_record=rel(record_path),art_record_sha256=sha(record_path),
  qa=dict(source_centers_opaque=p['source_centers_opaque'],source_centers_empty=p['source_centers_empty'],source_midpoints_missing=0,source_transparent_midpoints_filled=0,
          original_hd_return='exact',emulated_state='unchanged',normal_and_mirror=True,unknown_foreground_rejected=True)))
companions=[HERE/'pack.cjs',HERE/'geometries-build.py',HERE/'geometries.json',HERE/'source-geometry-proof.json',HERE/'verification/packing-v1.json',HERE/'generation-records-v1.json',HERE/'runtime.cjs',HERE/'freeze.py',HERE/'check.py',HERE/'verification/packing-independent-v1.json',HERE.parent/'contours.py']
delivery=dict(schema=1,visual_status='reviewed_original_and_runtime' if args.visual_reviewed else 'pending_visual_review',
 source_zip_sha256=runtime['source_zip_sha256'],production_code_sha256=runtime['production_code_sha256'],wasm_core_sha256=runtime['wasm_core_sha256'],
 proofs=[dict(path=rel(proof),sha256=sha(proof),html_path=rel(proof.parent/'loaded.html'),html_sha256=runtime['html_sha256'])],
 companion_derivations=[dict(path=rel(p),sha256=sha(p)) for p in companions],scope=runtime['scope'],entries=entries)
(HERE/'activation-set-001.json').write_text(json.dumps(delivery,indent=2,ensure_ascii=False)+'\n')
(HERE/'verification/freeze-proof.json').write_text(json.dumps(dict(status='passed',frames=22,distinct_photographs=22,source_alpha_midpoints=midpoints,missing_source_midpoints=0,filled_transparent_source_midpoints=0,runtime_checks=len(runtime['checks']),natural_routes=7,normal_mirrored_fixtures=44,delivery_sha256=sha(HERE/'activation-set-001.json')),indent=2)+'\n')
print(json.dumps(dict(status='frozen',visual_reviewed=args.visual_reviewed,frames=22,midpoints=midpoints,delivery_sha256=sha(HERE/'activation-set-001.json'))))
