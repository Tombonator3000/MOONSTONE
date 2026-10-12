"""Uavhengig originalalfa, hull og kildefarger, uten endring av kandidatene."""
from pathlib import Path
from collections import deque
import hashlib,json,os
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
contracts=json.loads((HERE/'source-contracts.json').read_text())
for c in contracts:
 p=HERE/'packed'/c['key']
 if not p.exists():continue
 im=Image.open(p);w,h=c['width'],c['height'];assert im.mode=='RGBA' and im.size==(w*4,h*4)
 alpha=list(im.getchannel('A').get_flattened_data());source=[bool(i) for i in c['indices']];packed=[a>=128 for a in alpha]
 for y in range(h):
  for x in range(w):assert source[y*w+x]==packed[(y*4+2)*w*4+x*4+2]
 fg=components(source,w,h,8);hd_fg=components(packed,w*4,h*4,4);holes=components([not p for p in source],w,h,4,True);hd_holes=components([not p for p in packed],w*4,h*4,4,True)
 assert fg==hd_fg,(c['key'],'foreground',fg,hd_fg)
 assert holes==hd_holes,(c['key'],'holes',holes,hd_holes)
 samples=0
 for q,index in enumerate(c['indices']):
  if not index:continue
  r,g,b,a=im.getpixel((q%w*4+2,q//w*4+2));assert a>=128
  # All opaque Guardian source indices are pale cyan/slate-blue in this bank.
  if index in [9,10,11,12,13,14,21,22,23,28,29,30,31]:assert b>=g>=r,(c['key'],q,'warm drift',r,g,b)
  elif index==5:assert r==g==b==0,(c['key'],q,'black source changed')
  elif index==15:assert r>g and r>b,(c['key'],q,'red source detail lost')
  elif index in [1,2]:assert r>=g>=b,(c['key'],q,'cream source highlight changed')
  samples+=1
 maskpath=p.with_suffix('.mask.png')
 if c['frame']==60:
  mask=Image.open(maskpath);assert mask.mode=='RGBA' and mask.size==im.size
  live=0
  for y in range(im.height):
   for x in range(im.width):
    index=c['indices'][y//4*w+x//4];r,g,b,a=mask.getpixel((x,y));expected=index+1 if index in[6,7,8]else 0
    assert r==expected and b==(255 if expected else 0)and a==255,(c['key'],x,y,'strict original NN mask')
    if expected:
     live+=1
     if im.getpixel((x,y))[3]>=128:assert g>0,(x,y,'black photographic live edge')
  assert live==sum(i in[6,7,8]for i in c['indices'])*16
 else:assert not maskpath.exists(),('Unexpected mask',c['key'])
 rows.append(dict(key=c['key'],png_sha256=sha(p),source_alpha_midpoints=w*h,source_foreground8=fg,packed_foreground4=hd_fg,source_holes4=holes,packed_holes4=hd_holes,cyan_slate_centers=samples))
assert rows
report=dict(schema=1,status='passed',source_contracts_sha256=sha(HERE/'source-contracts.json'),geometry_sha256=sha(HERE/'geometries.json'),script_sha256=sha(Path(__file__)),assets=rows,source_alpha_midpoints=sum(r['source_alpha_midpoints'] for r in rows))
out=HERE/os.environ.get('MOONSTONE_GUARDIAN_CHECK_OUTPUT','verification/packing-independent-first3-v1.json');out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(status='passed',assets=len(rows),midpoints=report['source_alpha_midpoints'])))
