"""Strenge original-NN-masker for tre innbakte ridderfragmenter."""
from pathlib import Path
import hashlib,json
from PIL import Image
HERE=Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rows=[]
for c in json.loads((HERE/'geometries-knights-v1.json').read_text()):
 png=HERE/'packed'/c['key'];im=Image.open(png);assert im.mode=='RGBA'and im.size==(c['width']*4,c['height']*4)
 mask=Image.new('RGBA',im.size,(0,0,0,255));live=0
 for y in range(im.height):
  for x in range(im.width):
   index=c['indices'][y//4*c['width']+x//4]
   if index in[6,7,8]:
    reference=sum(v*k for v,k in zip(c['palette'][index][:3],[.2126,.7152,.0722]));light=sum(v*k for v,k in zip(im.getpixel((x,y))[:3],[.2126,.7152,.0722]));assert reference>0
    mask.putpixel((x,y),(index+1,max(0,min(255,round(light*128/reference))),255,255));live+=1
 dest=png.with_suffix('.mask.png');mask.save(dest)
 rows.append(dict(key=c['key'],source_bank_sha256=c['source_bank_sha256'],source_indices_sha256=c['indices_sha256'],photo_sha256=sha(png),mask_sha256=sha(dest),live_source_cells=live//16,live_HD_pixels=live))
out=HERE/'verification/mask-knights-v1.json';out.write_text(json.dumps(dict(schema=1,status='passed',script_sha256=sha(Path(__file__)),source_contracts_sha256=sha(HERE/'source-contracts.json'),assets=rows,contract='R=source NN index+1 for6..8 and B=255 otherwise R/B=0, independent of alpha. G=photographic luminance/reference*128. A=255.'),indent=2)+'\n')
print(json.dumps(dict(status='passed',routes=len(rows),live_source_cells=sum(r['live_source_cells']for r in rows))))
