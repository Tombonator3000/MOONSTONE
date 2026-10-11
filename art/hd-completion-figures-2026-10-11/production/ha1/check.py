"""Independent binary-alpha/topology and semantic material checks, no mutations."""
from pathlib import Path
from collections import deque
import hashlib,json
from PIL import Image
HERE=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def components(mask,w,h,neighbors=4,holes=False):
 seen=set();count=0
 for q,on in enumerate(mask):
  if not on or q in seen:continue
  todo=deque([q]);seen.add(q);edge=False
  while todo:
   i=todo.popleft();x,y=i%w,i//w;edge|=x==0 or y==0 or x==w-1 or y==h-1
   for dy in (-1,0,1):
    for dx in (-1,0,1):
     if not (dx or dy) or (neighbors==4 and dx and dy):continue
     xx,yy=x+dx,y+dy
     if 0<=xx<w and 0<=yy<h:
      k=yy*w+xx
      if mask[k] and k not in seen:seen.add(k);todo.append(k)
  if not holes or not edge:count+=1
 return count
rows=[]
for c in json.loads((HERE/'geometries.json').read_text()):
 p=HERE/'packed'/c['key'];im=Image.open(p);w,h=c['width'],c['height'];assert im.mode=='RGBA' and im.size==(w*4,h*4)
 alpha=list(im.getchannel('A').get_flattened_data());source=[bool(i) for i in c['indices']];packed=[a>=128 for a in alpha]
 for y in range(h):
  for x in range(w):assert source[y*w+x]==packed[(y*4+2)*w*4+x*4+2]
 fg=components(source,w,h,8);hd_fg=components(packed,w*4,h*4,4);holes=components([not p for p in source],w,h,4,True);hd_holes=components([not p for p in packed],w*4,h*4,4,True)
 assert fg==hd_fg,(c['key'],'foreground',fg,hd_fg)
 assert holes==hd_holes,(c['key'],'holes',holes,hd_holes)
 gem=[];highlights=[]
 for q,material in enumerate(c['material_labels']):
  if material==2:
   r,g,b,a=im.getpixel((q%w*4+2,q//w*4+2));assert a>=128
   if c['indices'][q]!=1:assert r>g and b>g;gem.append(g)
   else:highlights.append(g)
 if gem:assert highlights and sum(highlights)/len(highlights)>sum(gem)/len(gem)
 rows.append(dict(key=c['key'],png_sha256=sha(p),source_alpha_midpoints=w*h,source_foreground8=fg,packed_foreground4=hd_fg,source_holes4=holes,packed_holes4=hd_holes,moonstone_pixels=len(gem),white_highlight_pixels=len(highlights)))
report=dict(schema=1,status='passed',geometry_sha256=sha(HERE/'geometries.json'),script_sha256=sha(Path(__file__)),assets=rows,source_alpha_midpoints=sum(r['source_alpha_midpoints'] for r in rows))
(HERE/'verification/packing-independent-v1.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(status='passed',assets=len(rows),midpoints=report['source_alpha_midpoints'])))
