"""Frys alle50 Demon3-ruter med separat master og eksplisitt fixture-forbehold."""
from pathlib import Path
import argparse, hashlib, json, shutil
from PIL import Image

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rel=lambda p:str(p.relative_to(ROOT))
ap=argparse.ArgumentParser();ap.add_argument('--runtime',required=True);ap.add_argument('--set',required=True);ap.add_argument('--visual-reviewed',action='store_true');a=ap.parse_args()
proof=HERE/a.runtime;rt=json.loads(proof.read_text());assert rt['status']=='passed' and not rt['errors']
folder=HERE/a.set;assert not (folder/'activation-set-001.json').exists();folder.mkdir(exist_ok=True)
def copy(p,name=None):
 dest=folder/(name or p.name)
 if dest.exists():assert dest.read_bytes()==p.read_bytes()
 else:shutil.copyfile(p,dest)
 return dest

geometry=json.loads((HERE/'geometries.json').read_text());assert len(geometry)==50
keys={c['key']for c in geometry};masks={c['key'].replace('.png','.mask.png')for c in geometry if c['live_palette_indices']}
assert len(masks)==3 and set(rt['assets'])==keys|masks
assert not rt['runtime']['seen'] and set(rt['unobserved_routes'])==keys
assert len(rt['fixtures'])==100 and len(rt['negative'])==500
assert len(rt['knight_palette_variants'])==6 and all(len(x['samples'])==5 for x in rt['knight_palette_variants'])
assert rt['test_sha256']==sha(HERE/'runtime-v1.cjs') and rt['geometry_sha256']==sha(HERE/'geometries.json')
assert sha(proof.parent/'loaded.html')==rt['html_sha256']
source_root=Path(rt['source_freeze']);assert rt['source_freeze_explicit']
for f,h in rt['production_code_sha256'].items():assert sha(source_root/f)==h
assert sha(ROOT/'web/build/moonstone-core.js')==rt['wasm_core_sha256'] and sha(ROOT/'Moonstonecd32-AMIGA.zip')==rt['source_zip_sha256']
independent_path=HERE/'verification/packing-independent-all50-v1.json';ind=json.loads(independent_path.read_text())
assert ind['status']=='passed' and len(ind['assets'])==50 and ind['script_sha256']==sha(HERE/'check-v1.py')
generation=json.loads((HERE/'generation-records-v1.json').read_text());assert len(generation)==50
companions=[copy(HERE/'geometries.json'),copy(HERE/'generation-records-v1.json'),copy(HERE/'runtime-v1.cjs','runtime.cjs')]
rows={}
ledgers=['packing-first3-v1.json','packing-003-011-v1.json','packing-012-014-v1.json','packing-016-019-v1.json','packing-knights-v1.json','packing-022-029-v1.json','packing-030-035-v1.json','packing-036-041-v1.json','packing-042-047-v1.json','packing-048-049-v1.json']
for name in ledgers:
 p=HERE/'verification'/name;data=json.loads(p.read_text());companions.append(copy(p))
 knight=name=='packing-knights-v1.json';script=HERE/('pack-knights-v1.cjs'if knight else'pack.cjs');geo=HERE/('geometries-knights-v1.json'if knight else'geometries.json')
 assert sha(script)==data['packing_script_sha256'] and sha(geo)==data['geometry_sha256']
 if knight:
  gp=copy(HERE/'generation-records-knights-v1.json');assert sha(gp)==data['generation_records_sha256'];companions.append(gp)
 else:
  matches=[n for n in range(1,51)if hashlib.sha256((json.dumps(generation[:n],indent=2)+'\n').encode()).hexdigest()==data['generation_records_sha256']]
  assert len(matches)==1;count=matches[0];gp=folder/f'generation-records-through-{count-1:03}.json';gb=(json.dumps(generation[:count],indent=2)+'\n').encode()
  if gp.exists():assert gp.read_bytes()==gb
  else:gp.write_bytes(gb)
  companions.append(gp)
 for row in data['assets']:
  assert row['key']not in rows;rows[row['key']]=(row,data,script,geo)
assert set(rows)==keys
reviews=[]
for name in ['comparison-000-014-v1.png','comparison-015-021-v1.png','comparison-022-035-v1.png','comparison-036-049-v1.png']:
 p=HERE/'verification'/name;reviews.append(dict(path=rel(p),sha256=sha(p),reviewer='root',approval='visual_review_confirmed_in_agent_message',scope='Exact original contours, openings, source colors and partial crop. Three embedded knight fragments keep source pose/steel/cloth. No natural combat claim.'));companions.append(p)
review=folder/'visual-review.json';review.write_text(json.dumps(dict(schema=1,status='reviewed'if a.visual_reviewed else'pending',images=reviews),indent=2)+'\n');companions.append(review)
entries=[];midpoints=0
for c in geometry:
 row,packing,script,geo=rows[c['key']];g=next(g for g in generation if g['key']==c['key']);call=HERE/f"generation-calls/{c['frame']:03}-v1.json"
 assert json.loads(call.read_text())==g and g['generation_tool']=='builtin_image_gen'
 png=HERE/'packed'/c['key'];raw=HERE/g['raw'];prompt=HERE/g['prompt'];ref=HERE/g['source_reference'];im=Image.open(png)
 assert sha(png)==row['candidate_sha256']==rt['assets'][c['key']]==next(x['png_sha256']for x in ind['assets']if x['key']==c['key'])
 assert sha(raw)==g['raw_sha256']==row['raw_sha256'] and sha(prompt)==g['prompt_sha256']==row['prompt_sha256'] and sha(ref)==g['source_reference_sha256']
 assert c['source_palette_contract_sha256']==sha(ROOT/c['source_palette_contract'])==rt['palette_case_sha256']
 assert im.mode=='RGBA' and im.size==(c['width']*4,c['height']*4)
 for q,index in enumerate(c['indices']):
  assert (im.getpixel((q%c['width']*4+2,q//c['width']*4+2))[3]>=128)==bool(index);midpoints+=1
 record={**g,**row,'packing_script_path':rel(script),'packing_script_sha256':sha(script),'geometry_path':rel(geo),'geometry_sha256':sha(geo),'method':packing['scope'],'visual_status':'reviewed_original_and_runtime'if a.visual_reviewed else'pending_visual_review','actual_runtime_observed':False,'runtime_scope':rt['scope']}
 rp=folder/f"{c['frame']:03}-record.json";rp.write_text(json.dumps(record,indent=2)+'\n')
 entry=dict(key=c['key'],bank='Demon3.CEL',frame=c['frame'],source_bank_sha256=c['source_bank_sha256'],indices_sha256=c['indices_sha256'],png=rel(png),png_sha256=sha(png),raw=rel(raw),raw_sha256=sha(raw),prompt=rel(prompt),prompt_sha256=sha(prompt),generation_tool='builtin_image_gen',runtime_proof=rel(proof),runtime_asset_sha256=sha(png),art_record=rel(rp),art_record_sha256=sha(rp),actual_runtime_observed=False,qa=dict(source_alpha_midpoints=c['width']*c['height'],source_midpoints_missing=0,source_transparent_midpoints_filled=0,normal_and_mirror=True,unknown_foreground_rejected=True,original_hd_return='exact',emulated_state='unchanged',source_usage='bank_and_expanded_indices_verified_no_sequence_claim',runtime_qualification='source_exact_frontend_fixture_only'))
 if c['live_palette_indices']:
  assert c['frame']in[15,20,21];mask=png.with_suffix('.mask.png');m=Image.open(mask);assert m.mode=='RGBA'and m.size==im.size and sha(mask)==rt['assets'][c['key'].replace('.png','.mask.png')]
  for y in range(m.height):
   for x in range(m.width):
    index=c['indices'][y//4*c['width']+x//4];r,g_,b,alpha=m.getpixel((x,y));expected=index+1 if index in[6,7,8]else 0
    assert r==expected and b==(255 if expected else 0)and alpha==255
    if expected and im.getpixel((x,y))[3]>=128:assert g_>0
  entry.update(mask=rel(mask),mask_sha256=sha(mask));entry['qa']['five_original_knight_palettes_both_mirrors']=True
 else:assert not png.with_suffix('.mask.png').exists()
 entries.append(entry);companions.append(call)
assert len({e['raw_sha256']for e in entries})==50
companions += [HERE/name for name in ['pack.cjs','pack-knights-v1.cjs','prepare.py','prepare-prompts.py','record-generated.py','check-v1.py','compare.py','freeze-delivery.py','prepare-knights-v1.py','geometries-knights-v1.json','mask-knights-v1.py']]
companions += [independent_path,HERE/'verification/mask-knights-v1.json',HERE.parent/'contours.py',ROOT/'tools/hd_resterende_ikoner_fixture.cjs',ROOT/geometry[0]['source_palette_contract'],source_root/'source-map.json',*[source_root/f for f in rt['production_code_sha256']]]
companions=list(dict.fromkeys(companions))
index=dict(schema=1,visual_status='reviewed_original_and_runtime'if a.visual_reviewed else'pending_visual_review',source_zip_sha256=rt['source_zip_sha256'],production_code_sha256=rt['production_code_sha256'],wasm_core_sha256=rt['wasm_core_sha256'],proofs=[dict(path=rel(proof),sha256=sha(proof),html_path=rel(proof.parent/'loaded.html'),html_sha256=rt['html_sha256'])],companion_derivations=[dict(path=rel(p),sha256=sha(p))for p in companions],scope=rt['scope'],visual_reviews=reviews,entries=entries)
dest=folder/'activation-set-001.json';dest.write_text(json.dumps(index,indent=2)+'\n')
receipt=folder/'freeze-proof.json';receipt.write_text(json.dumps(dict(status='passed',routes=50,png_files=53,distinct_generated_masters=50,source_alpha_midpoints=midpoints,actual_original_combat_routes=0,fixture_only_routes=50,normal_mirrored_fixtures=100,negative_source_fixtures=500,runtime_checks=len(rt['checks']),delivery_sha256=sha(dest)),indent=2)+'\n')
paths={dest,receipt,*companions,proof}
for e in entries:
 paths.update(ROOT/e[f]for f in ['png','raw','prompt','art_record'])
 if e.get('mask'):paths.add(ROOT/e['mask'])
for frame in [0,15,19,20,21,38,43,47,48,49]:
 for mode in ['original','hd']:paths.add(proof.parent/f'{frame:03}-{mode}.png')
for frame in [15,20,21]:
 for color in ['blue','orange','green','red','purple']:paths.add(proof.parent/f'{frame:03}-{color}-hd.png')
filelist=HERE/'delivery-demon3-000-049-files.txt';filelist.write_text(''.join(rel(p)+'\n'for p in sorted(paths)))
print(json.dumps(dict(status='frozen_not_activated',routes=50,png_files=53,index=rel(dest),sha256=sha(dest),filelist=rel(filelist))))
