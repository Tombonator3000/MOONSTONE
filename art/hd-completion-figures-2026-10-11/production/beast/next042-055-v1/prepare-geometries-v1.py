"""Bind ti fotomastere og en originalskygge til uendrede kilderuter."""
from pathlib import Path
import json,hashlib,sys
H=Path(__file__).resolve().parent;B=H.parent;R=B.parents[3];sys.path.insert(0,str(B.parent));sys.path.insert(0,str(R/'tools'))
from contours import source_contours
from hd_bestilling import maskefarger
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();palette=R/'art/hd-completion-figures-2026-10-11/palettes/cases/beast.json'
selected={42,43,*range(46,55)};rows=[];records=[]
for source in json.loads((H/'sources-v1.json').read_text()):
 n=source['frame']
 if n not in selected:continue
 w,h=source['width'],source['height'];indices=source['indices'];black=set(indices)<={0,5};live=maskefarger('be1.c',n)&set(indices)
 labels=[0 if not i else 9 if i in live else 11 if i==15 else 2 if i in (11,12,13) else 8 for i in indices]
 cells=[(q%w,q//w)for q,i in enumerate(indices)if i];bounds=[min(x for x,y in cells),min(y for x,y in cells),max(x for x,y in cells)+1,max(y for x,y in cells)+1]
 rows.append({**source,'bank':'be1.c','source_palette_contract':str(palette.relative_to(R)),'source_palette_contract_sha256':sha(palette),'source_alpha_bounds':bounds,'alpha_path':source_contours(indices,w,h,lambda i:i!=0),'material_labels':labels,'materials':{name:source_contours(labels,w,h,lambda i,j=j:i==j)for j,name in [(2,'hide'),(8,'metal'),(9,'cloth'),(11,'blood')]if j in labels},'original_motion_cells':[],'fixed_black_cells':[q for q,i in enumerate(indices)if i==5],'preserved_original_black_shadow':black,'needs_mask':bool(live),'mask_indices':sorted(live),'neutral_template':{'6':128,'7':96,'8':64}if live else None,'scope':'Originalens kontur, hull, utsnitt og materialfelt er laast.6..8 er levende spillerdrakt;1..5 staal/skygge;11..13 fast brunt laer;15 blodroedt. Ingen anatomisk nytolkning.054 er ren originalsvart skygge uten fotomaster.'})
 if not black:
  version=2 if n in (49,50)else 1;record=json.loads((H/f'generation-{n:03}-v{version}.json').read_text())
  record={**record,'key':source['key'],'source_generation_record':f'generation-{n:03}-v{version}.json','source_generation_record_sha256':sha(H/f'generation-{n:03}-v{version}.json')}
  for field in ('raw','prompt','reference'):
   if Path(record[field]).is_absolute():record[field]=str(Path(record[field]).relative_to(H))
  if 'generation_call_id'not in record:record['generation_call_id']=Path(record['original_generated_path']).stem
  assert record['generation_tool']=='builtin_image_gen'
  for field in ('raw','prompt','reference'):assert sha(H/record[field])==record[field+'_sha256']
  records.append(record)
assert len(rows)==11 and len(records)==10 and sum(r['needs_mask']for r in rows)==5
for name,value in [('geometries-v1.json',rows),('generation-records-v1.json',records)]:
 p=H/name;text=json.dumps(value,indent=2)+'\n'
 if p.exists():assert p.read_text()==text
 else:p.write_text(text)
print('11 kildekontrakter,10 egne foto og5 levende masker klare')
