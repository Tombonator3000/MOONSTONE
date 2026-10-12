"""Freeze seven separately generated source-bound Beast candidates with honest fixture scope."""
from pathlib import Path
import json,hashlib
H=Path(__file__).resolve().parent;R=H.parents[4];F=H.parents[2]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:str(p.relative_to(R))
def frozen(p,data):
 text=json.dumps(data,ensure_ascii=False,indent=2)+'\n';p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():assert p.read_text()==text,'Do not overwrite frozen evidence'
 else:p.write_text(text)
geometry=json.loads((H/'runtime-geometries-v1.json').read_text());generation=json.loads((H/'generation-records-v1.json').read_text());packing=json.loads((H/'verification/packing-v1.json').read_text());independent=json.loads((H/'verification/packing-independent-v1.json').read_text());proof_path=H/'verification/runtime-frontend008-v1/test.json';proof=json.loads(proof_path.read_text())
assert len(geometry)==len(generation)==7 and len({g['raw_sha256']for g in generation})==7
assert proof['status']=='passed'and not proof['errors']and len(proof['checks'])==246
assert len(proof['fixtures'])==14 and len(proof['negative'])==70 and len(proof['palette_variants'])==3 and not proof['runtime']['seen']
assert proof['test_sha256']==sha(H/'runtime-fixtures-008-v1.cjs')
assert proof['geometry_sha256']==sha(H/'runtime-geometries-v1.json')
assert proof['html_sha256']==sha(proof_path.parent/'loaded.html')
assert independent['status']=='passed'and independent['source_alpha_midpoints']==11011
for name,digest in proof['production_code_sha256'].items():assert sha(R/name)==digest
screenfiles=[H/'comparison-v1.png']+[proof_path.parent/f for f in ['006-hd.png','060-hd.png','061-orange-hd.png']]
review_path=H/'root-review-seven-v1.json';frozen(review_path,dict(status='approved',reviewer='root',keys=[c['key']for c in geometry],actual_runtime_observed=False,notes='All seven source/HD pairs visually compared, then selected008 GPU fixtures and orange live knight palette. Source silhouette, holes and original material regions are retained. This is not natural combat observation.',screenshots=[dict(path=rel(p),sha256=sha(p))for p in screenfiles]))
files={H/n for n in ['freeze-seven-008-v1.py','prepare-references-v1.py','prepare-seven-v1.py','pack-v1.cjs','check-seven-v1.py','runtime-fixtures-008-v1.cjs','sources-v1.json','geometries-v1.json','runtime-geometries-v1.json','generation-records-v1.json','verification/packing-v1.json','verification/packing-independent-v1.json','comparison-v1.png','root-review-seven-v1.json']}
files.update([proof_path,F/'production/contours.py',F/'production/beast/next006-011-v1/geometries-v3.json',F/'palettes/cases/beast.json',R/'tools/hd_resterende_ikoner_fixture.cjs',F/'figures/ratmen-production/runtime-proof.cjs',F/'figures/kn3-production/runtime-host.cjs'])
entries=[]
for c,g in zip(geometry,generation):
 assert c['key']==g['key'];png=R/c['packed_candidate_path'];assert sha(png)==c['candidate_png_sha256']==proof['assets'][c['key']]
 for field in ['raw','prompt','reference']:assert sha(H/g[field])==g[field+'_sha256']
 gen=H/g['source_generation_record'];assert sha(gen)==g['source_generation_record_sha256'];files.add(gen)
 raw,prompt=H/g['raw'],H/g['prompt'];record_path=H/f"records/{c['number']}-final-seven-v1.json"
 packed=next(r for r in packing['assets']if r['key']==c['key'])
 frozen(record_path,dict(key=c['key'],generation=g,packed=packed,source_bank_sha256=c['source_bank_sha256'],indices_sha256=c['indices_sha256'],candidate_sha256=sha(png),generation_tool='builtin_image_gen',actual_runtime_observed=False,runtime_scope='source_exact_fixture_only',source_size=[c['width'],c['height']],target_size=[c['width']*4,c['height']*4]))
 entry=dict(key=c['key'],bank='be1.c',frame=c['frame'],source_bank_sha256=c['source_bank_sha256'],indices_sha256=c['indices_sha256'],png=rel(png),png_sha256=sha(png),raw=rel(raw),raw_sha256=sha(raw),prompt=rel(prompt),prompt_sha256=sha(prompt),generation_tool='builtin_image_gen',runtime_proof=rel(proof_path),runtime_asset_sha256=sha(png),art_record=rel(record_path),art_record_sha256=sha(record_path),actual_runtime_observed=False,runtime_scope='source_exact_fixture_only')
 files.update([raw,prompt,png,record_path])
 if c['needs_mask']:
  mask=R/c['mask_path'];assert sha(mask)==proof['mask_sha256'][c['key'].replace('.png','.mask.png')];entry.update(mask=rel(mask),mask_sha256=sha(mask));files.add(mask)
 entries.append(entry)
companions=[p for p in files if p.suffix in ['.py','.cjs','.json']and p!=proof_path]
contract=dict(schema=1,visual_status='reviewed_original_and_runtime',source_zip_sha256=proof['source_zip_sha256'],production_code_sha256=proof['production_code_sha256'],wasm_core_sha256=proof['wasm_core_sha256'],proofs=[dict(path=rel(proof_path),sha256=sha(proof_path),html_path=rel(proof_path.parent/'loaded.html'),html_sha256=proof['html_sha256'])],companion_derivations=[dict(path=rel(p),sha256=sha(p))for p in sorted(companions)],entries=entries,fixture_only=[c['key']for c in geometry],actual_runtime_observed=False,scope='Seven own photographic figure fragments, three exact live6..8 masks, source contour and material registration. Fourteen normal/mirror,70 negative source/owner and15 palette samples. Actual HD combat observation is not claimed.')
out=H/'activation-set-seven-008-v1.json';frozen(out,contract);files.add(out);files.update(screenfiles)
for number in ['011','060']:
 for n in [f'generation-{number}-v1.json',f'generation-{number}-v1-rejected.json',f'raw/{number}-v1.png',f'prompts/{number}-v1.txt']:files.add(H/n)
(H/'delivery-seven-008-files.txt').write_text('\n'.join(sorted(rel(p)for p in files))+'\n')
print(json.dumps(dict(status='frozen_not_activated',routes=7,png_files=10,photographic_masters=7,runtime_checks=246,contract_sha256=sha(out))))
