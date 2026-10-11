"""Freeze 30 distinct LI1 photos, source contours, mode3 masks and actual runtime."""
from pathlib import Path
import argparse,hashlib,json
from PIL import Image
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rel=lambda p:str(p.resolve().relative_to(ROOT))
parser=argparse.ArgumentParser();parser.add_argument('--visual-reviewed',action='store_true');parser.add_argument('--routes',required=True,nargs='+',type=Path);parser.add_argument('--natural',required=True,type=Path);parser.add_argument('--negative',required=True,type=Path);parser.add_argument('--mode2',required=True,type=Path);parser.add_argument('--tavern',required=True,type=Path);parser.add_argument('--colors',required=True,type=Path);args=parser.parse_args()
contracts=json.loads((HERE/'source-contracts.json').read_text());packing=json.loads((HERE/'verification/packing-final-v1.json').read_text());generation=json.loads((HERE/'generation-records-v1.json').read_text());independent=json.loads((HERE/'verification/packing-independent-final-v1.json').read_text())
assert len(contracts)==len(packing['entries'])==len(generation)==30 and independent['status']=='passed' and len(independent['assets'])==30
assert packing['packing_script_sha256']==sha(HERE/'pack-final.py') and packing['geometry_sha256']==sha(HERE/'geometries.json') and packing['generation_records_sha256']==sha(HERE/'generation-records-v1.json')
assert independent['script_sha256']==sha(HERE/'check-final.py') and independent['geometry_sha256']==sha(HERE/'geometries.json')
assert len({g['generated_output'] for g in generation})==len({g['raw_sha256'] for g in generation})==30
for d in packing['derivations']:assert sha(HERE/d['path'])==d['sha256']
proof_paths=[*args.routes,args.natural,args.negative,args.mode2,args.tavern];reports={p:json.loads(p.read_text())for p in proof_paths}
natural,negative,regr2,tav=[reports[p]for p in [args.natural,args.negative,args.mode2,args.tavern]]
frontend=natural['production_code_sha256'];wasm=natural['wasm_core_sha256'];zip_sha=natural['source_zip_sha256'];html_sha=natural['html_sha256']
for p,r in reports.items():
 assert r['status']=='passed' and not r.get('errors'),p
 assert r['production_code_sha256']==frontend and r['wasm_core_sha256']==wasm and r['source_zip_sha256']==zip_sha and r['html_sha256']==html_sha,p
 assert sha(p.parent/'loaded.html')==html_sha,p
for f,h in frontend.items():assert sha(ROOT/f)==h,f
assert sha(ROOT/'web/build/moonstone-core.js')==wasm and sha(ROOT/'Moonstonecd32-AMIGA.zip')==zip_sha
scripts={args.natural:'runtime-final-natural.cjs',args.negative:'runtime-negative.cjs',args.mode2:'runtime-mode2.cjs',args.tavern:'runtime-tav-regression.cjs',**{p:'runtime-routes.cjs'for p in args.routes}}
for p,s in scripts.items():assert reports[p].get('test_sha256',reports[p].get('script_sha256'))==sha(HERE/s),(p,s)
assert len(natural['observed'])==23 and natural['observed']==list(range(23))
assert set(natural['runtime']['shots'])==set(map(str,[4474,4502,4506,4512,4528,4552,5704]))
assert {'4502_all12_body_routes_HD','4512_all12_body_routes_HD','5704_departed_LI1_source_tracks_removed'}<=set(natural['checks'])
assert {'transparent_unknown_retained_source_track','transparent_unknown_HD_rejected','transparent_unknown_Original_exact','transparent_unknown_strict_rectangle_gate','transparent_unknown_cleared_without_CEL_source_mask_ready','transparent_unknown_Original_return'}<=set(negative['checks'])
assert len(negative['normal_photo_exact'])==30 and all(x['mode3_sha256']==x['mode0_sha256'] for x in negative['normal_photo_exact'])
assert 'actual_practice_pose_mode2' in regr2['checks'] and tav['status']=='passed'
fixtures={};runtime_for={}
for p in args.routes:
 for f in reports[p]['fixtures']:
  k=(f['key'],f['mode'],f['mirror']);assert k not in fixtures;fixtures[k]=f;runtime_for[f['key']]=p
assert len(fixtures)==180
for c in contracts:
 for mode in ['normal','flash','black']:
  for mirror in [False,True]:assert (c['key'],mode,mirror) in fixtures
colors=json.loads(args.colors.read_text());assert colors['status']=='passed' and colors['fixtures']==180 and colors['script_sha256']==sha(HERE/'check-runtime-colors.py')
assert len(args.routes)==len(colors['proofs'])
for p,d in zip(args.routes,colors['proofs']):assert str(p)==d['path'] and sha(p)==d['sha256']
entries=[];midpoints=0;visual='reviewed_original_and_runtime' if args.visual_reviewed else 'pending_visual_review'
for c,p,g in zip(contracts,packing['entries'],generation):
 assert c['key']==p['key']==g['key'];key=c['key'];png=HERE/'packed-final-v1'/key;mask=png.with_name(png.stem+'.mask.png');raw=HERE/g['raw'];prompt=HERE/g['prompt'];proof=runtime_for[key]
 assert sha(raw)==g['raw_sha256']==p['raw_sha256'] and sha(prompt)==g['prompt_sha256']==p['prompt_sha256'] and sha(HERE/g['reference'])==g['reference_sha256']
 assert sha(png)==p['png_sha256']==reports[proof]['assets'][key] and sha(mask)==p['mask_sha256']==reports[proof]['assets'][key.replace('.png','.mask.png')]
 assert sha(png)==natural['assets'][key]==negative['assets'][key] and sha(mask)==natural['assets'][key.replace('.png','.mask.png')]==negative['assets'][key.replace('.png','.mask.png')]
 qa=next(r for r in independent['assets']if r['key']==key);assert qa['png_sha256']==sha(png) and qa['mask_sha256']==sha(mask)
 im,m=Image.open(png),Image.open(mask);assert im.mode==m.mode=='RGBA' and im.size==m.size==(c['width']*4,c['height']*4)
 for q,index in enumerate(c['indices']):assert (im.getpixel((q%c['width']*4+2,q//c['width']*4+2))[3]>=128)==bool(index);midpoints+=1
 for y in range(m.height):
  for x in range(m.width):
   index=c['indices'][(y//4)*c['width']+x//4];R,G,B,A=m.getpixel((x,y));assert R==(index+1 if index else 0) and B==(255 if index else 0) and A==255
 record={**g,**p,'candidate_sha256':sha(png),'mask_sha256':sha(mask),'packing_script_sha256':sha(HERE/'pack-final.py'),'visual_status':visual,'runtime_scope':'Unchanged original intro observes000..022. All30 have normal/mirrored fixtures in actual normal, flash and black source palettes. No natural use or unused claim for023..029. Photographic RGB preserved exactly in normal palette.'}
 rp=HERE/f"records/{c['frame']:03}-final.json";rp.parent.mkdir(exist_ok=True);rp.write_text(json.dumps(record,indent=2,ensure_ascii=False)+'\n')
 entries.append(dict(key=key,bank='li1.cel',frame=c['frame'],source_bank_sha256=c['source_bank_sha256'],indices_sha256=c['indices_sha256'],png=rel(png),png_sha256=sha(png),mask=rel(mask),mask_sha256=sha(mask),raw=rel(raw),raw_sha256=sha(raw),prompt=rel(prompt),prompt_sha256=sha(prompt),generation_tool='builtin_image_gen',runtime_proof=rel(proof),runtime_asset_sha256=sha(png),art_record=rel(rp),art_record_sha256=sha(rp),qa=dict(source_alpha_midpoints=c['width']*c['height'],source_midpoints_missing=0,source_transparent_midpoints_filled=0,strict_NN_mask=True,original_hd_return='exact',emulated_state='unchanged',normal_and_mirror=True,white_flash_and_black=True,normal_photo_RGB_exact=True,unknown_foreground_rejected=True)))
companions=[HERE/n for n in ['pack.cjs','pack-final.py','pack-lights-v2.cjs','material-demo-v4.py','geometries-build.py','geometries.json','source-contracts.json','source-palette-evidence.json','generation-records-v1.json','verification/packing-30.json','verification/packing-final-v1.json','iterations/lights-v2/verification/packing-11.json','iterations/cloth-v4/material-proof.json','check-final.py','verification/packing-independent-final-v1.json','runtime-routes.cjs','runtime-final-natural.cjs','runtime-negative.cjs','runtime-mode2.cjs','runtime-tav-regression.cjs','source-runtime-extra.cjs','source/natural-v1/test.json','source/natural-v2/test.json','runtime-hand-trace.cjs','runtime-hand-trace-v2.cjs','verification/hand-trace-v1/test.json','verification/hand-trace-v2/test.json','verification/hand-retention-source-v1.json','check-runtime-colors.py','freeze.py']]+[args.colors,HERE.parent/'contours.py']
delivery=dict(schema=1,visual_status=visual,source_zip_sha256=zip_sha,production_code_sha256=frontend,wasm_core_sha256=wasm,proofs=[dict(path=rel(p),sha256=sha(p),html_path=rel(p.parent/'loaded.html'),html_sha256=html_sha)for p in proof_paths],companion_derivations=[dict(path=rel(p),sha256=sha(p))for p in companions],scope=record['runtime_scope'],entries=entries)
(HERE/'activation-set-001.json').write_text(json.dumps(delivery,indent=2,ensure_ascii=False)+'\n')
summary=dict(status='passed',visual_reviewed=args.visual_reviewed,frames=30,distinct_photographs=30,pngs=60,source_alpha_midpoints=midpoints,runtime_fixtures=180,runtime_checks=sum(len(r['checks'])for r in reports.values()),source_center_samples=colors['source_center_samples'],delivery_sha256=sha(HERE/'activation-set-001.json'))
(HERE/'verification/freeze-proof.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary))
