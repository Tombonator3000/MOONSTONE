"""Skill kjente terrengbilder fra senere originale endringer i kampbakgrunnen."""
from pathlib import Path
from collections import Counter
import hashlib,json,sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];sys.path.insert(0,str(ROOT/'tools'));import moonfiles as mf
sha=lambda b:hashlib.sha256(b).hexdigest()
folder=HERE/'verification/test-background-audit-v1';audit_bytes=(folder/'audit.json').read_bytes();audit=json.loads(audit_bytes);assert audit['status']=='passed'and len(audit['original_composites'])==32
target=folder/'later-runtime-deltas.json';assert not target.exists(),'Bevar tidligere bevis'
references=[(r,(ROOT/r['png']).parent.joinpath('indices.bin').read_bytes())for r in audit['original_composites']]
rows=[]
for case in audit['historical_original_cases']:
 chip=(ROOT/case['chip_path']).read_bytes();assert sha(chip)==case['chip_sha256'];ptr=int(case['background_pointer'],16);indices=bytes(mf.plan_til_indeks(chip[ptr:ptr+40000],5))
 choices=[(sum(a!=b for a,b in zip(indices,ref)),r,ref)for r,ref in references if r['terrain']==case['actual_terrain']];count,nearest,ref=min(choices,key=lambda x:x[0]);changes=[(q,a,b)for q,(a,b)in enumerate(zip(ref,indices))if a!=b];new=Counter(b for _,_,b in changes);pairs=Counter((a,b)for _,a,b in changes)
 if case['case']=='guardian':classification='exact raw Test005, separate source reset; nearest decorated layout is not its identity'
 elif count==0:classification='exact existing terrain layout'
 elif set(new)=={15}:classification='later original change consists exclusively of source index15, red in this combat palette; no new terrain drawing'
 else:classification='later original runtime change; source mechanism not fully attributed, no separate art job inferred'
 coords=[(q%320,q//320)for q,_,_ in changes];bounds=[min(x for x,y in coords),min(y for x,y in coords),max(x for x,y in coords)+1,max(y for x,y in coords)+1]if coords else None
 rows.append(dict(case=case['case'],frame=case['frame'],actual_terrain=case['actual_terrain'],historical_background_fnv1a=case['background_fnv1a'],nearest_original_layout=nearest['source_file'],nearest_layout_fnv1a=nearest['background_fnv1a'],nearest_layout_has_hd=nearest['direct_hd'],different_source_pixels=count,difference_bounds=bounds,new_indices=dict(new),index_pairs=[dict(before=a,after=b,pixels=n)for(a,b),n in pairs.most_common()],index15_rgb=case['palette_rgb'][15],classification=classification))
game=mf.Spill(ROOT/'Moonstonecd32-AMIGA.zip');mog=game.les('mog');assert sha(mog)==audit['mog_sha256'];memory,_,_=mf.legg_ut(mog);snippet=memory[0x7ae0:0x7b46]
# Originalens flagg4-gren velger bakgrunnsbufferen og tegner CEL direkte dit.
assert memory[0x7b18:0x7b24]==bytes.fromhex('20390008cde84eb900088f42')
assert memory[0x7b2e:0x7b34]==bytes.fromhex('4eb90009dcec')
(folder/'original-background-CEL-write.bin').write_bytes(snippet)
result=dict(schema=1,status='passed',script_sha256=sha(Path(__file__).read_bytes()),audit_sha256=sha(audit_bytes),scope='Exact historical background comparison, no new runtime or art generation.',rows=rows,all32_clean_layouts_have_direct_hd=all(r['direct_hd']for r in audit['original_composites']),source_background_write=dict(start='0x087ae0',end_exclusive='0x087b46',sha256=sha(snippet),proof='flag4 branch at087b0a selects08cde8 via088f42, draws CEL at087b2e, then restores0aa948; this proves original combat can mutate clean background'),limitations=['Red-only changes are mathematically established; attribution to a particular CEL or action requires its exact draw trace.','Mudmen and ratmen later deltas include additional indices, so they are not called simple blood-only changes.','Existing HD image coverage is complete for these32 source layouts. Dynamic changed hashes can still cause Original fallback; no presentation fix is implemented here.'])
target.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n');print(json.dumps(dict(status='passed',rows=len(rows),red_only_cases=[r['case']for r in rows if r['new_indices']and set(r['new_indices'])=={15}],sha256=sha(target.read_bytes()))))
