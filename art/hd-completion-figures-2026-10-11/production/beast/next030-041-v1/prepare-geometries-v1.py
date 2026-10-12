"""Bind tolv separate fotomastere til eksakte kildeomraader og bevegelige draktfelt."""
from pathlib import Path
import hashlib,json,sys
H=Path(__file__).resolve().parent;B=H.parent;R=B.parents[3];sys.path.insert(0,str(B.parent))
from contours import source_contours
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();palette=R/'art/hd-completion-figures-2026-10-11/palettes/cases/beast.json';rows=[]
for s in json.loads((H/'sources-v1.json').read_text()):
 n=s['frame'];w,h=s['width'],s['height'];ind=s['indices'];motion=[];components=[]
 if n in (40,41):
  remaining={q for q,j in enumerate(ind)if j}
  while remaining:
   stack=[remaining.pop()];cc=[]
   while stack:
    q=stack.pop();cc.append(q);x,y=q%w,q//w
    for dy in (-1,0,1):
     for dx in (-1,0,1):
      if not(dx or dy)or not(0<=x+dx<w and 0<=y+dy<h):continue
      j=(y+dy)*w+x+dx
      if j in remaining:remaining.remove(j);stack.append(j)
   components.append(sorted(cc))
  main=max(components,key=len)
  motion=sorted(q for cc in components if cc is not main and len(cc)<=20 and all(ind[q]==3 for q in cc)for q in cc)
 labels=[0 if not j else 10 if q in motion else 9 if n>=34 and j in (6,7,8) else 8 if n>=34 else 6 if j==14 else 3 if j in (1,2) else 7 if j in (9,10) else 1 for q,j in enumerate(ind)]
 body=[(q%w,q//w)for q,j in enumerate(ind)if j and q not in motion];bounds=[min(x for x,y in body),min(y for x,y in body),max(x for x,y in body)+1,max(y for x,y in body)+1]
 row={**s,'bank':'be1.c','source_palette_contract':str(palette.relative_to(R)),'source_palette_contract_sha256':sha(palette),'source_alpha_bounds':bounds,'alpha_path':source_contours(ind,w,h,lambda j:j!=0),'material_labels':labels,'materials':{name:source_contours(labels,w,h,lambda j,jj=jj:j==jj)for jj,name in [(1,'fur'),(3,'bone'),(6,'mouth'),(7,'muzzle'),(8,'metal'),(9,'cloth')]if jj in labels},'original_motion_cells':motion,'alpha_connected_components':components,'alpha_component_connectivity':8,'needs_mask':n>=34,'mask_indices':[6,7,8]if n>=34 else [],'neutral_template':{'6':128,'7':96,'8':64}if n>=34 else None,'scope':'Eget foto per originalrute. Originalkontur, utsnitt, hull og materialegrenser bevares. Bare sma ikke-hoved alfa-komponenter med utelukkende indeks3 og hoyst20 celler i040/041 beholdes eksakt. Ingen helhetlig fri nytegning av geometri.'}
 rows.append(row)
p=H/'geometries-v1.json';b=json.dumps(rows,indent=2)+'\n'
if p.exists():assert p.read_text()==b,'Bevar tidligere geometri'
else:p.write_text(b)
print('12 kildebundne kontrakter klare; originale bevegelsesceller',[(r['frame'],len(r['original_motion_cells']))for r in rows if r['original_motion_cells']])
