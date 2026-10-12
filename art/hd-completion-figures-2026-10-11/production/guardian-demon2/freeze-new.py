"""Frys selvstendige Guardian-mastere og faktisk runtimebevis, aldri aktiver."""
from pathlib import Path
import argparse,hashlib,json,shutil
from PIL import Image
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rel=lambda p:str(p.relative_to(ROOT))
parser=argparse.ArgumentParser();parser.add_argument('--runtime-script',default='runtime-v1.cjs');parser.add_argument('--first-new-frame',type=int,default=0);parser.add_argument('--set',required=True);parser.add_argument('--runtime',required=True);parser.add_argument('--independent',required=True);parser.add_argument('--packing',required=True);parser.add_argument('--visual-reviewed',action='store_true');args=parser.parse_args()
proof=HERE/args.runtime;runtime=json.loads(proof.read_text());assert runtime['status']=='passed' and not runtime['errors']
folder=HERE/args.set;assert not (folder/'activation-set-001.json').exists(),'Bevar eksisterende frosset leveranse';folder.mkdir(exist_ok=True)
def frozen_copy(src,dest):
 if dest.exists():assert src.read_bytes()==dest.read_bytes(),('Frozen bytes changed',dest)
 else:shutil.copyfile(src,dest)
for src,dest in [(HERE/'geometries.json',folder/'geometries.json'),(HERE/args.packing,folder/'packing-v1.json'),(HERE/'pack.cjs',folder/'pack.cjs'),(HERE/args.runtime_script,folder/'runtime.cjs'),(HERE/'check.py',folder/'check.py')]:frozen_copy(src,dest)
selected_generation=[g for g in json.loads((HERE/'generation-records-v1.json').read_text()) if g['key'] in runtime['assets']]
generation_bytes=(json.dumps(selected_generation,indent=2)+'\n').encode();generation_dest=folder/'generation-records-v1.json'
if generation_dest.exists():assert generation_dest.read_bytes()==generation_bytes
else:generation_dest.write_bytes(generation_bytes)
geometry=json.loads((folder/'geometries.json').read_text());packing=json.loads((folder/'packing-v1.json').read_text());generation=json.loads((folder/'generation-records-v1.json').read_text());independent=json.loads((HERE/args.independent).read_text())
keys=set(runtime['assets']);assert keys and keys=={p['key']for p in packing['assets']}
geometry=[c for c in geometry if c['key'] in keys];generation=[g for g in generation if g['key'] in keys]
assert keys=={c['key']for c in geometry}=={g['key']for g in generation}
assert len(runtime['fixtures'])==len(keys)*2 and len(runtime['negative'])==len(keys)*10
assert set(runtime['runtime']['seen'])=={k.lower().replace('.png','')for k in keys}
assert runtime['geometry_sha256']==sha(folder/'geometries.json') and runtime['test_sha256']==sha(folder/'runtime.cjs')
assert packing['packing_script_sha256']==sha(folder/'pack.cjs') and packing['geometry_sha256']==sha(folder/'geometries.json') and packing['generation_records_sha256']==sha(folder/'generation-records-v1.json')
assert independent['status']=='passed' and independent['geometry_sha256']==sha(folder/'geometries.json') and independent['script_sha256']==sha(folder/'check.py')
assert len({g['raw_sha256']for g in generation})==len({g['tool_call_id']for g in generation})==len(keys)
assert sha(proof.parent/'loaded.html')==runtime['html_sha256']
for f,h in runtime['production_code_sha256'].items():assert sha(ROOT/f)==h
assert sha(ROOT/'web/build/moonstone-core.js')==runtime['wasm_core_sha256'] and sha(ROOT/'Moonstonecd32-AMIGA.zip')==runtime['source_zip_sha256']
entries=[];midpoints=0;calls=[]
for c in geometry:
 if c['frame']<args.first_new_frame:
  active=ROOT/'web/hd'/c['key'];assert active.exists() and sha(active)==runtime['assets'][c['key']],('Existing context changed',c['key'])
  continue
 p=next(p for p in packing['assets']if p['key']==c['key']);g=next(g for g in generation if g['key']==c['key']);png=HERE/'packed'/c['key'];raw=HERE/g['raw'];prompt=HERE/g['prompt'];reference=HERE/g['source_reference'];call=HERE/f"generation-calls/{c['frame']:03}-v1.json"
 assert g==json.loads(call.read_text()) and g['generation_tool']=='builtin_image_gen';calls.append(call)
 assert sha(raw)==g['raw_sha256']==p['raw_sha256'] and sha(prompt)==g['prompt_sha256']==p['prompt_sha256'] and sha(reference)==g['source_reference_sha256']
 assert sha(png)==p['candidate_sha256']==runtime['assets'][c['key']]==next(r for r in independent['assets']if r['key']==c['key'])['png_sha256']
 assert c['source_palette_contract_sha256']==sha(ROOT/c['source_palette_contract'])==runtime['palette_case_sha256']
 im=Image.open(png);assert im.mode=='RGBA' and im.size==(c['width']*4,c['height']*4)
 for q,index in enumerate(c['indices']):assert (im.getpixel((q%c['width']*4+2,q//c['width']*4+2))[3]>=128)==bool(index);midpoints+=1
 assert not (HERE/'packed'/c['key'].replace('.png','.mask.png')).exists()
 record={**g,**p,'packing_script_sha256':sha(folder/'pack.cjs'),'packing_script_path':rel(folder/'pack.cjs'),'geometry_sha256':sha(folder/'geometries.json'),'method':packing['scope'],'visual_status':'reviewed_original_and_runtime' if args.visual_reviewed else 'pending_visual_review','runtime_scope':runtime['scope']}
 rp=folder/f"{c['frame']:03}-record.json";rp.write_text(json.dumps(record,indent=2)+'\n')
 entries.append(dict(key=c['key'],bank='Demon2.CEL',frame=c['frame'],source_bank_sha256=c['source_bank_sha256'],indices_sha256=c['indices_sha256'],png=rel(png),png_sha256=sha(png),raw=rel(raw),raw_sha256=sha(raw),prompt=rel(prompt),prompt_sha256=sha(prompt),generation_tool='builtin_image_gen',runtime_proof=rel(proof),runtime_asset_sha256=sha(png),art_record=rel(rp),art_record_sha256=sha(rp),qa=dict(source_alpha_midpoints=c['width']*c['height'],source_midpoints_missing=0,source_transparent_midpoints_filled=0,normal_and_mirror=True,unknown_foreground_rejected=True,original_hd_return='exact',emulated_state='unchanged')))
companions=[folder/f for f in ['geometries.json','generation-records-v1.json','packing-v1.json','pack.cjs','runtime.cjs','check.py']]+[HERE/'source-contracts.json',HERE/'prepare.py',HERE/'prepare-prompts.py',HERE/'record-generated.py',HERE/'freeze-new.py',HERE/'compare.py',HERE/'verification/comparison-first15-v1.png',HERE/args.independent,HERE.parent/'contours.py',ROOT/'tools/hd_resterende_ikoner_fixture.cjs',ROOT/geometry[0]['source_palette_contract']]+calls
index=dict(schema=1,visual_status='reviewed_original_and_runtime' if args.visual_reviewed else 'pending_visual_review',source_zip_sha256=runtime['source_zip_sha256'],production_code_sha256=runtime['production_code_sha256'],wasm_core_sha256=runtime['wasm_core_sha256'],proofs=[dict(path=rel(proof),sha256=sha(proof),html_path=rel(proof.parent/'loaded.html'),html_sha256=runtime['html_sha256'])],companion_derivations=[dict(path=rel(p),sha256=sha(p))for p in companions],scope=runtime['scope'],entries=entries)
dest=folder/'activation-set-001.json';dest.write_text(json.dumps(index,indent=2)+'\n');(folder/'freeze-proof.json').write_text(json.dumps(dict(status='passed',routes=len(entries),distinct_photographs=len(entries),source_alpha_midpoints=midpoints,runtime_checks=len(runtime['checks']),actual_original_combat_routes=len(runtime['runtime']['seen']),normal_mirrored_fixtures=len(runtime['fixtures']),negative_source_fixtures=len(runtime['negative']),delivery_sha256=sha(dest),visual_status=index['visual_status']),indent=2)+'\n')
print(json.dumps(dict(status='frozen_not_activated',routes=len(entries),source_alpha_midpoints=midpoints,index=rel(dest),sha256=sha(dest),visual_status=index['visual_status'])))
