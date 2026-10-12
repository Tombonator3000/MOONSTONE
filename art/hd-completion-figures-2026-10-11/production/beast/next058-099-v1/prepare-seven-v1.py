"""Bind seven independent figure photographs to their original source fields."""
from pathlib import Path
import hashlib,json,sys
H=Path(__file__).resolve().parent;B=H.parent;R=B.parents[3]
sys.path[:0]=[str(R/'tools'),str(B.parent)]
from contours import source_contours
from hd_bestilling import maskefarger
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
prior={r['frame']:r for r in json.loads((B/'next006-011-v1/geometries-v3.json').read_text())}
rows=[];records=[];palette=R/'art/hd-completion-figures-2026-10-11/palettes/cases/beast.json'
for s in json.loads((H/'sources-v1.json').read_text()):
 n=s['frame']
 if n not in [6,10,11,58,59,60,61]:continue
 w,h=s['width'],s['height'];ind=s['indices'];live=maskefarger('be1.c',n)&set(ind)
 if n in [6,10,11]:labels=prior[n]['material_labels']
 else:
  labels=[]
  for q,j in enumerate(ind):
   x,y=q%w,q//w
   furpart=n==59 or n in [60,61] and x<(12 if n==60 else 16) and y>20
   labels.append(0 if not j else 9 if j in live else 11 if j==15 else 2 if j in [11,12,13] else 1 if furpart else 8)
 materials={name:source_contours(labels,w,h,lambda j,jj=jj:j==jj)for jj,name in [(1,'fur'),(2,'hide'),(3,'bone'),(4,'eye'),(6,'mouth'),(7,'muzzle'),(8,'metal'),(9,'cloth'),(11,'blood')]if jj in labels}
 row={**s,'bank':'be1.c','source_palette_contract':str(palette.relative_to(R)),'source_palette_contract_sha256':sha(palette),'alpha_path':source_contours(ind,w,h,lambda j:j!=0),'material_labels':labels,'materials':materials,'original_motion_cells':[],'fixed_black_cells':[q for q,j in enumerate(ind)if j==5 and labels[q]==8],'needs_mask':bool(live),'mask_indices':sorted(live),'neutral_template':{'6':128,'7':96,'8':64}if live else None,'scope':'Own photographic master for each original frame. Source silhouette, holes, crop and source material colors are retained. Brown11..13 is organic creature fur/hide, never leather. Original3/4/5 dark creature fragment is photographic fur only in the reviewed left area.6..8 is live knight cloth, never fixed creature colors.'}
 rows.append(row);v=2 if n in [11,60]else 1;p=H/f'generation-{n:03}-v{v}.json';record=json.loads(p.read_text());assert record['generation_tool']=='builtin_image_gen'
 for field in ['raw','prompt','reference']:assert sha(H/record[field])==record[field+'_sha256']
 records.append({**record,'source_generation_record':p.name,'source_generation_record_sha256':sha(p)})
for name,data in [('geometries-v1.json',rows),('generation-records-v1.json',records)]:
 p=H/name;text=json.dumps(data,indent=2)+'\n'
 if p.exists():assert p.read_text()==text
 else:p.write_text(text)
print('7 source-bound photographs;',sum(r['needs_mask']for r in rows),'live cloth masks')
