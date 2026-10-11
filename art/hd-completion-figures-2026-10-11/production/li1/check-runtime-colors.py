"""Independent actual-pixel checks for LI1 white flash, black and original centers."""
from pathlib import Path
import argparse,hashlib,json
from PIL import Image
HERE=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
parser=argparse.ArgumentParser();parser.add_argument('reports',nargs='+',type=Path);parser.add_argument('--output',required=True,type=Path);args=parser.parse_args()
geometry={c['key']:c for c in json.loads((HERE/'geometries.json').read_text())}
source=json.loads((HERE/'source/natural-v1/test.json').read_text())
palettes={'normal':next(iter(geometry.values()))['palette'],'flash':next(p['palette'] for p in source['runtime']['palette_variants'] if p['first_frame']==4528),'black':next(p['palette'] for p in source['runtime']['palette_variants'] if p['first_frame']==4464)}
rows=[];seen=set();samples=0
for proof in args.reports:
 r=json.loads(proof.read_text());assert r['status']=='passed' and not r.get('errors')
 for f in r['fixtures']:
  key,mode,mirror=f['key'],f['mode'],f['mirror'];assert (key,mode,mirror) not in seen;seen.add((key,mode,mirror));c=geometry[key]
  prefix=f"{c['frame']:03}-{mode}"+('-mirror' if mirror else '')
  p=proof.parent/(prefix+'-hd.png');o=proof.parent/(prefix+'-original.png');assert sha(p)==f['hd_sha256'] and sha(o)==f['original_sha256']
  im,original=Image.open(p).convert('RGB'),Image.open(o).convert('RGB');assert im.size==original.size==(960,600)
  if mode=='black':assert im.tobytes()==original.tobytes() and im.getextrema()==((0,0),(0,0),(0,0))
  checked=0;white=0;black=0;max_neutral_error=0
  for q,index in enumerate(c['indices']):
   if not index:continue
   sx,sy=q%c['width'],q//c['width'];x=(148+(c['width']-1-sx if mirror else sx))*3+1;y=(min(90,200-c['height'])+sy)*3+1
   rgb=im.getpixel((x,y));ori=original.getpixel((x,y));ref=tuple(palettes[mode][index][:3]);assert ori==ref,(key,mode,mirror,index,ori,ref)
   if mode=='flash':
    if ref==(0,0,0):assert rgb==(0,0,0),(key,mirror,index,(x,y),rgb);black+=1
    elif ref==(255,255,255):
     error=max(rgb)-min(rgb);max_neutral_error=max(max_neutral_error,error);assert error<=1,(key,mirror,index,(x,y),rgb);white+=1
   checked+=1
  samples+=checked;rows.append(dict(key=key,mode=mode,mirror=mirror,hd_sha256=sha(p),original_sha256=sha(o),source_centers_checked=checked,neutral_flash_white_centers=white,exact_flash_black_centers=black,max_neutral_error=max_neutral_error))
assert len(seen)==180 and set(k for k,m,s in seen)==set(geometry)
report=dict(schema=1,status='passed',errors=[],scope='Pixel samples from actual960x600 runtime PNGs. Original source centers equal actual source palette; white flashes have neutral RGB, black source fields and all-black scans stay exactly black. No inference from captions or object labels.',script_sha256=sha(Path(__file__)),geometry_sha256=sha(HERE/'geometries.json'),proofs=[dict(path=str(p),sha256=sha(p))for p in args.reports],fixtures=len(rows),source_center_samples=samples,rows=rows)
args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(status='passed',fixtures=len(rows),source_center_samples=samples)))
