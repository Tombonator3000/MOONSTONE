"""Bind de ti separate fotomasterene til originalens materialeomraader."""
from pathlib import Path
import hashlib,json,sys
H=Path(__file__).resolve().parent;B=H.parent;R=B.parents[3];sys.path.insert(0,str(B.parent))
from contours import source_contours
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();source=H/'sources-v1.json';palette=R/'art/hd-completion-figures-2026-10-11/palettes/cases/beast.json';rows=[]
# Konservative svarte gulvceller bevares eksakt, uten foto eller ny anatomi.
shadow_tops={20:35,23:0,26:20,27:34,28:27,29:32}
for s in json.loads(source.read_text()):
 n=s['frame']
 if n==19:continue
 w,h=s['width'],s['height'];ind=s['indices'];top=shadow_tops.get(n,999)
 shadow=[q for q,j in enumerate(ind)if j==5 and q//w>=top and(n!=28 or q%w<57)]
 labels=[0 if not j else 1 if n==18 else 5 if q in shadow else 4 if j==15 else 6 if j==14 else 3 if j in [1,2,3] else 7 if j in [9,10] else 2 if j in [11,12,13] else 1 for q,j in enumerate(ind)]
 body=[(q%w,q//w)for q,j in enumerate(ind)if j and q not in shadow];bounds=[min(x for x,y in body),min(y for x,y in body),max(x for x,y in body)+1,max(y for x,y in body)+1]
 rows.append({**s,'source_palette_contract':str(palette.relative_to(R)),'source_palette_contract_sha256':sha(palette),'source_alpha_bounds':bounds,'alpha_path':source_contours(ind,w,h,lambda j:j!=0),'material_labels':labels,'materials':{name:source_contours(labels,w,h,lambda j,jj=jj:j==jj)for jj,name in [(1,'fur'),(2,'hide'),(3,'bone'),(4,'eye'),(6,'mouth'),(7,'muzzle')]if jj in labels},'flat_shadow':shadow,'flat_shadow_top':top if shadow else None,'scope':'Eget foto per kildeframe. Originalkontur, utsnitt, hull og materialegrenser bevares. Navngitte svarte gulvceller beholdes konservativt byteeksakt; dette er ikke fri nytegning av geometri.'})
p=H/'geometries-v3.json';b=json.dumps(rows,indent=2)+'\n'
if p.exists():assert p.read_text()==b,'Bevar tidligere geometri'
else:p.write_text(b)
print('Elleve kildebundne kandidatkontrakter klare.')
