"""Frys revidert008-binding for Demon2/048..098 uten aa endre v1-bevis eller aktivere."""
from pathlib import Path
import argparse, hashlib, json, shutil
from PIL import Image
HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[3]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rel=lambda p:str(p.relative_to(ROOT))
ap=argparse.ArgumentParser();ap.add_argument('--runtime',required=True);ap.add_argument('--set',required=True);ap.add_argument('--visual-reviewed',action='store_true');args=ap.parse_args()
proof=HERE/args.runtime;runtime=json.loads(proof.read_text());assert runtime['status']=='passed' and not runtime['errors']
folder=HERE/args.set;assert not (folder/'activation-set-002.json').exists(),'Bevar frosset leveranse';folder.mkdir(exist_ok=True)
def copy(src,name=None):
 dest=folder/(name or src.name)
 if dest.exists():assert dest.read_bytes()==src.read_bytes()
 else:shutil.copyfile(src,dest)
 return dest
geometry=json.loads((HERE/'geometries.json').read_text());selected=[c for c in geometry if 48<=c['frame']<=98]
assert len(selected)==51 and not runtime['runtime']['seen']
keys={c['key']for c in selected};maskkey='Demon2.CEL/060.mask.png'
assert set(runtime['assets'])==keys|{maskkey}
assert set(runtime['unobserved_routes'])==keys and len(runtime['fixtures'])==102 and len(runtime['negative'])==510
assert len(runtime['knight_palette_variants'])==2 and all(len(r['samples'])==5 for r in runtime['knight_palette_variants'])
assert runtime['test_sha256']==sha(HERE/'runtime-remainder-v4.cjs') and runtime['geometry_sha256']==sha(HERE/'geometries.json')
assert sha(proof.parent/'loaded.html')==runtime['html_sha256']
source_root=Path(runtime['source_freeze']);assert runtime['source_freeze_explicit']
for f,h in runtime['production_code_sha256'].items():assert sha(source_root/f)==h
assert sha(ROOT/'web/build/moonstone-core.js')==runtime['wasm_core_sha256'] and sha(ROOT/'Moonstonecd32-AMIGA.zip')==runtime['source_zip_sha256']
independent_path=HERE/'verification/packing-independent-all99-v3.json';independent=json.loads(independent_path.read_text())
assert independent['status']=='passed' and len(independent['assets'])==99 and independent['script_sha256']==sha(HERE/'check-v2.py')
generation=json.loads((HERE/'generation-records-v1.json').read_text());assert len(generation)==99
companions=[copy(HERE/'geometries.json'),copy(HERE/'generation-records-v1.json'),copy(HERE/'runtime-remainder-v4.cjs','runtime.cjs')]
packed_rows={}
for name,count in [('packing-048-059-v1.json',60),('packing-knight-v2.json',None),('packing-061-074-v1.json',75),('packing-075-098-v1.json',99)]:
 p=HERE/'verification'/name;data=json.loads(p.read_text());companions.append(copy(p))
 script=HERE/('pack-knight-v2.cjs'if count is None else 'pack.cjs');geometries=HERE/('geometry-knight-v2.json'if count is None else 'geometries.json')
 assert sha(script)==data['packing_script_sha256'] and sha(geometries)==data['geometry_sha256']
 if count is None:companions.append(copy(HERE/'generation-records-knight-v2.json'));assert sha(companions[-1])==data['generation_records_sha256']
 else:
  dest=folder/f'generation-records-through-{count-1:03}.json';bytes_=(json.dumps(generation[:count],indent=2)+'\n').encode()
  if dest.exists():assert dest.read_bytes()==bytes_
  else:dest.write_bytes(bytes_)
  assert sha(dest)==data['generation_records_sha256'];companions.append(dest)
 for row in data['assets']:
  assert row['key']not in packed_rows;packed_rows[row['key']]=(row,data,script,geometries)
assert set(packed_rows)==keys
usage_path=HERE/'verification/source-usage-remainder-v1.json';usage=json.loads(usage_path.read_text());assert usage['status']=='source_group_usage_verified_not_runtime_observed'
reviews=[]
for name in ['comparison-048-059-v1.png','comparison-knight060-v2.png','comparison-061-074-v1.png','comparison-075-098-v1.png']:
 p=HERE/'verification'/name;reviews.append(dict(path=rel(p),sha256=sha(p),reviewer='root',approval='visual_review_confirmed_in_agent_message',scope='Original contour, crop, openings and source color. Route060 steel/cloth/pose approved; black fields remain source display surfaces. No actual-runtime-observed claim.'));companions.append(p)
review=folder/'visual-review.json';review.write_text(json.dumps(dict(schema=1,status='reviewed'if args.visual_reviewed else'pending',images=reviews),indent=2)+'\n');companions.append(review)
entries=[];midpoints=0
for c in selected:
 row,packing,script,geometries=packed_rows[c['key']];g=next(g for g in generation if g['key']==c['key']);call=HERE/f"generation-calls/{c['frame']:03}-v1.json"
 assert json.loads(call.read_text())==g and g['generation_tool']=='builtin_image_gen'
 png=HERE/'packed'/c['key'];raw=HERE/g['raw'];prompt=HERE/g['prompt'];ref=HERE/g['source_reference'];im=Image.open(png)
 assert sha(png)==row['candidate_sha256']==runtime['assets'][c['key']]==next(r['png_sha256']for r in independent['assets']if r['key']==c['key'])
 assert sha(raw)==g['raw_sha256']==row['raw_sha256'] and sha(prompt)==g['prompt_sha256']==row['prompt_sha256'] and sha(ref)==g['source_reference_sha256']
 assert c['source_palette_contract_sha256']==sha(ROOT/c['source_palette_contract'])==runtime['palette_case_sha256']
 assert im.mode=='RGBA'and im.size==(c['width']*4,c['height']*4)
 for q,index in enumerate(c['indices']):assert(im.getpixel((q%c['width']*4+2,q//c['width']*4+2))[3]>=128)==bool(index);midpoints+=1
 record={**g,**row,'packing_script_path':rel(script),'packing_script_sha256':sha(script),'geometry_path':rel(geometries),'geometry_sha256':sha(geometries),'method':packing['scope'],'visual_status':'reviewed_original_and_runtime'if args.visual_reviewed else'pending_visual_review','actual_runtime_observed':False,'runtime_scope':runtime['scope']}
 rp=folder/f"{c['frame']:03}-record.json";rp.write_text(json.dumps(record,indent=2)+'\n')
 entry=dict(key=c['key'],bank='Demon2.CEL',frame=c['frame'],source_bank_sha256=c['source_bank_sha256'],indices_sha256=c['indices_sha256'],png=rel(png),png_sha256=sha(png),raw=rel(raw),raw_sha256=sha(raw),prompt=rel(prompt),prompt_sha256=sha(prompt),generation_tool='builtin_image_gen',runtime_proof=rel(proof),runtime_asset_sha256=sha(png),art_record=rel(rp),art_record_sha256=sha(rp),actual_runtime_observed=False,qa=dict(source_alpha_midpoints=c['width']*c['height'],source_midpoints_missing=0,source_transparent_midpoints_filled=0,normal_and_mirror=True,unknown_foreground_rejected=True,original_hd_return='exact',emulated_state='unchanged',source_usage='original_animation_tables_confirmed',runtime_qualification='source_exact_frontend_fixture_only'))
 if c['live_palette_indices']:
  assert c['frame']==60;mask=png.with_suffix('.mask.png');m=Image.open(mask);assert m.mode=='RGBA'and m.size==im.size and sha(mask)==runtime['assets'][maskkey]
  for y in range(m.height):
   for x in range(m.width):
    index=c['indices'][y//4*c['width']+x//4];r,g_,b,a=m.getpixel((x,y));expected=index+1 if index in[6,7,8]else 0
    assert r==expected and b==(255 if expected else 0)and a==255
    if expected and im.getpixel((x,y))[3]>=128:assert g_>0
  entry.update(mask=rel(mask),mask_sha256=sha(mask));entry['qa']['five_original_knight_palettes_both_mirrors']=True
 else:assert not png.with_suffix('.mask.png').exists()
 entries.append(entry);companions.append(call)
assert len({e['raw_sha256']for e in entries})==51
for c in geometry[:48]:assert sha(ROOT/'web/hd'/c['key'])==sha(HERE/'packed'/c['key']),('Active context changed',c['key'])
companions += [HERE/name for name in ['pack.cjs','pack-knight-v2.cjs','prepare.py','prepare-prompts.py','record-generated.py','check-v2.py','compare.py','freeze-remainder-v2.py','prepare-knight-v2.py','geometry-knight-v2.json','mask-knight-v2.py','source-usage-audit.py']]
companions += [independent_path,usage_path,HERE/'verification/mask-knight-v2.json',HERE.parent/'contours.py',ROOT/'tools/hd_resterende_ikoner_fixture.cjs',ROOT/selected[0]['source_palette_contract']]
companions += [source_root/'source-map.json',*[source_root/f for f in runtime['production_code_sha256']]]
companions=list(dict.fromkeys(companions))
index=dict(schema=1,visual_status='reviewed_original_and_runtime'if args.visual_reviewed else'pending_visual_review',source_zip_sha256=runtime['source_zip_sha256'],production_code_sha256=runtime['production_code_sha256'],wasm_core_sha256=runtime['wasm_core_sha256'],proofs=[dict(path=rel(proof),sha256=sha(proof),html_path=rel(proof.parent/'loaded.html'),html_sha256=runtime['html_sha256'])],companion_derivations=[dict(path=rel(p),sha256=sha(p))for p in companions],scope=runtime['scope'],original_usage_proof=rel(usage_path),visual_reviews=reviews,entries=entries)
dest=folder/'activation-set-002.json';dest.write_text(json.dumps(index,indent=2)+'\n')
receipt=folder/'freeze-proof.json';receipt.write_text(json.dumps(dict(status='passed',routes=51,png_files=52,distinct_photographs=51,source_alpha_midpoints=midpoints,actual_original_combat_routes=0,fixture_only_routes=51,normal_mirrored_fixtures=102,negative_source_fixtures=510,runtime_checks=len(runtime['checks']),delivery_sha256=sha(dest)),indent=2)+'\n')
paths={dest,receipt,*companions,proof}
for e in entries:
 paths.update(ROOT/e[f]for f in ['png','raw','prompt','art_record'])
 if e.get('mask'):paths.add(ROOT/e['mask'])
for frame in [48,60,67,98]:
 for mode in ['original','hd']:paths.add(proof.parent/f'{frame:03}-{mode}.png')
for color in ['blue','orange','green','red','purple']:paths.add(proof.parent/f'060-{color}-hd.png')
filelist=HERE/'delivery-demon2-048-098-v2-files.txt';filelist.write_text(''.join(rel(p)+'\n'for p in sorted(paths)))
print(json.dumps(dict(status='frozen_not_activated',routes=51,png_files=52,index=rel(dest),sha256=sha(dest),filelist=rel(filelist))))
