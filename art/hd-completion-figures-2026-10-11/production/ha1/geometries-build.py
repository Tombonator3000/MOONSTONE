"""HA1: originaleksakte former og runtimebekreftet intro-palett, ingen aktivering."""
from pathlib import Path
from collections import deque
import hashlib,json,sys
from PIL import Image
ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'tools'))
import moonfiles as mf
import hd_bestilling as order
sys.path.insert(0,str(HERE.parent))
from contours import source_contours
sha=lambda b:hashlib.sha256(b).hexdigest()
contracts=json.loads((HERE/'source-contracts.json').read_text())
proof_path=HERE.parent/'intro/source/intro-runtime-catalog-v1.json'
proof=json.loads(proof_path.read_text());assert proof['status']=='passed'
runtime=next(r for r in proof['runtime']['records'] if r['key']=='ha1.cel/000.png')
assert runtime['frame']==4912 and runtime['scan_valid']
palette=runtime['palette']
game=mf.Spill(str(ROOT/'Moonstonecd32-AMIGA.zip'));bank=game.les('data/ha1.cel');frames=mf.cel_les(bank)[0]
assert len(contracts)==len(frames)==22
rows=[]
for c,frame in zip(contracts,frames):
 w,h=c['width'],c['height'];px=c['indices'];number=c['frame']
 original=order.utvid_indekser(mf.plan_til_indeks(frame['data'],frame['plan'],w,h),frame['maske'])
 assert list(original)==px and sha(original)==c['indices_sha256'] and sha(bank)==c['source_bank_sha256']
 assert c['palette']==palette
 # Highlight index1 is moonstone only if it belongs to a white component
 # adjacent to the source's purple stone; ordinary steel highlights stay steel.
 gem={q for q,i in enumerate(px) if i in (12,15,23)}
 seen=set();highlights=set()
 for q,i in enumerate(px):
  if i!=1 or q in seen:continue
  queue=deque([q]);seen.add(q);component=[];touches=False
  while queue:
   j=queue.popleft();component.append(j);x,y=j%w,j//w
   for yy in range(max(0,y-1),min(h,y+2)):
    for xx in range(max(0,x-1),min(w,x+2)):
     k=yy*w+xx
     if k in gem:touches=True
     if px[k]==1 and k not in seen:seen.add(k);queue.append(k)
  if touches:highlights.update(component)
 gem|=highlights
 assert bool(gem)==(number in (12,19))
 allowed={0,1,2,3,4,5,6,7,12,15,18,19,23,24,27};assert set(px)<=allowed
 labels=[0 if i==0 else 2 if q in gem else 1 for q,i in enumerate(px)]
 alpha=Image.new('L',(w,h));alpha.putdata([255 if i else 0 for i in px])
 row=dict(key=c['key'],number=f'{number:03}',frame=number,width=w,height=h,indices=px,palette=palette,
  indices_sha256=c['indices_sha256'],source_bank_sha256=c['source_bank_sha256'],source_alpha_bounds=alpha.getbbox(),
  material_labels=labels,alpha_path=source_contours(px,w,h,lambda i:i!=0),
  materials={name:source_contours(labels,w,h,lambda v,ix=ix:v==ix) for name,ix in [('steel',1),('moonstone',2)] if ix in labels},
  moonstone_source_pixels=len(gem),moonstone_highlight_pixels=len(highlights))
 rows.append(row)
(HERE/'geometries.json').write_text(json.dumps(rows,separators=(',',':'))+'\n')
(HERE/'source-geometry-proof.json').write_text(json.dumps(dict(schema=1,status='passed',source_contract_sha256=sha((HERE/'source-contracts.json').read_bytes()),source_bank_sha256=sha(bank),palette_proof=str(proof_path.relative_to(ROOT)),palette_proof_sha256=sha(proof_path.read_bytes()),palette_frame=4912,assets=[{k:r[k] for k in ('key','width','height','indices_sha256','moonstone_source_pixels','moonstone_highlight_pixels')} for r in rows]),indent=2)+'\n')
print('22 originalbundne geometrikontrakter')
