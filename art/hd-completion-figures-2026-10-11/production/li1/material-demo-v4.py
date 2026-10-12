"""Avgrenset LI1-ullmaterialprøve, hver råmaster beholdes separat."""
from pathlib import Path
import json,hashlib
from PIL import Image,ImageFilter
HERE=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rows=json.loads((HERE/'geometries.json').read_text())
proof=HERE/'verification/natural-mode3-v2/test.json'
natural=json.loads(proof.read_text());assert natural['status']=='passed'
placed={d['bilde']:(d['x'],d['y']) for d in natural['runtime']['shots']['4502']['figures'] if d['fil'].lower()=='li1.cel'}
frames=[12,13,14,15,19,20,21,22];gray={1,2,3,4,5,6,7,23}
def cloth(n,x,y):
 return n in frames and (n!=15 or y>=29) and rows[n]['indices'][y*rows[n]['width']+x] in gray
# The low-frequency lighting field is source-exact at its input, including
# cross-fragment positions from the actual4502 draw list. Photograph residuals
# supply wool detail; no image is treated as a newly drawn pose or new geometry.
field=Image.new('RGB',(320,200));weight=Image.new('L',(320,200))
for n in frames:
 c=rows[n];ox,oy=placed[n]
 for y in range(c['height']):
  for x in range(c['width']):
   if cloth(n,x,y):
    v=c['indices'][y*c['width']+x];field.putpixel((ox+x,oy+y),tuple(c['palette'][v][:3]));weight.putpixel((ox+x,oy+y),255)
field=field.resize((1280,800),Image.Resampling.NEAREST).filter(ImageFilter.GaussianBlur(2.2))
weight=weight.resize((1280,800),Image.Resampling.NEAREST).filter(ImageFilter.GaussianBlur(2.2))
out=HERE/'iterations/cloth-v4';(out/'packed/li1.cel').mkdir(parents=True,exist_ok=True);records=[]
for n in frames:
 c=rows[n];ox,oy=placed[n];src=HERE/f'packed/li1.cel/{n:03}.png';im=Image.open(src).copy();low=im.convert('RGB').filter(ImageFilter.GaussianBlur(7));count=0
 for y in range(im.height):
  for x in range(im.width):
   sx,sy=x//4,y//4
   if not cloth(n,sx,sy):continue
   rgb=im.getpixel((x,y));local=low.getpixel((x,y));L=sum(rgb[k]*w for k,w in enumerate((.2126,.7152,.0722)));mean=sum(local[k]*w for k,w in enumerate((.2126,.7152,.0722)));detail=max(.75,min(1.25,L/max(1,mean)))
   gx,gy=ox*4+x,oy*4+y;w=weight.getpixel((gx,gy));base=field.getpixel((gx,gy));edge=min(x,y,im.width-1-x,im.height-1-y);blend=max(0,min(.85,edge/20));common=[(.75*v*255/max(1,w)+32)*(1+min(1,edge/20)*(detail-1)) for v in base];result=tuple(min(255,round(common[k]*(1-blend)+rgb[k]*blend)) for k in range(3))
   im.putpixel((x,y),result+(rgb[3],));count+=1
 dest=out/f'packed/li1.cel/{n:03}.png';im.save(dest)
 mask=Image.open(HERE/f'packed/li1.cel/{n:03}.mask.png').copy()
 for y in range(im.height):
  for x in range(im.width):
   index=c['indices'][(y//4)*c['width']+x//4];rgb=im.getpixel((x,y));ref=c['palette'][index];L=sum(rgb[k]*w for k,w in enumerate((.2126,.7152,.0722)));rL=sum(ref[k]*w for k,w in enumerate((.2126,.7152,.0722)))
   mask.putpixel((x,y),(index+1 if index else 0,min(255,round(L/rL*128)) if rL and index else 128 if index else 0,255 if index else 0,255))
 mask.save(out/f'packed/li1.cel/{n:03}.mask.png');records.append(dict(frame=n,input_png_sha256=sha(src),output_png_sha256=sha(dest),cloth_pixels=count,source_position=[ox,oy]))
(out/'material-proof.json').write_text(json.dumps(dict(schema=1,status='visual_demo_not_activated',scope='Each independent photograph supplies registered high-frequency wool detail. Original4502 gray fields supply common matte lighting at rectangular fragment joins, feathered into each independent photograph inside the frame. Geometry/alpha and all non-cloth RGB remain unchanged. No whole figure redraw or shared new photo claim.',source_4502_proof_sha256=sha(proof),geometries_sha256=sha(HERE/'geometries.json'),script_sha256=sha(Path(__file__)),entries=records),indent=2)+'\n')
print('separate wool candidates',len(records))
