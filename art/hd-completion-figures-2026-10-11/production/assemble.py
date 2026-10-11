#!/usr/bin/env python3
"""Compose an original figure from consecutive, source-verified CPU draw calls.

This is an art contact proof, not a claim that the HD candidate was activated.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
from PIL import Image, ImageDraw, ImageOps

ART=Path(__file__).resolve().parent
FIGURES=ART.parent
ROOT=FIGURES.parents[1]
def sha(b):return hashlib.sha256(b).hexdigest()

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--case',default='troll');p.add_argument('--frame',type=int,required=True)
 p.add_argument('--key',required=True);p.add_argument('--candidate',type=Path,required=True)
 p.add_argument('--other',action='append',default=[],help='Additional KEY=PNG replacement')
 a=p.parse_args();a.candidate=a.candidate.resolve()
 replacements={a.key:a.candidate}
 for value in a.other:
  key,path=value.split('=',1);replacements[key]=Path(path).resolve()
 case_path=FIGURES/'palettes/cases'/f'{a.case}.json';case=json.loads(case_path.read_text())
 trace_path=FIGURES/'palettes/runtime'/a.case/'trace.txt';trace=trace_path.read_text()
 pattern=re.compile(r'  (.*?) bilde (\d+) x (-?\d+) y (-?\d+) \((\d+)x(\d+), xoff (-?\d+)(, speilet)?\) buffer ([0-9a-f]+) fra ([0-9a-f]+)')
 lookup={r['key'].lower():r for r in case['references']};draws=[];frame=-1
 for line in trace.splitlines():
  if line.startswith('tegneliste bilde '):frame=int(line.split()[2])
  m=pattern.fullmatch(line)
  if not m or not a.frame-1<=frame<=a.frame:continue
  bank,n,x,y,w,h,xoff,mirror,buffer,caller=m.groups();key=f'{bank}/{int(n):03}.png'
  if key.lower() not in lookup:continue
  assert int(xoff)==0,'Nonzero source offsets need an explicit placement contract'
  ref=lookup[key.lower()]
  draws.append(dict(frame=frame,key=ref['key'],x=int(x),y=int(y),width=int(w),height=int(h),mirror=bool(mirror),buffer=buffer,caller=caller))
 assert any(d['key']==a.key for d in draws),draws
 assert len({d['buffer'] for d in draws})==1,'Cannot combine independent buffers'
 original=Image.new('RGBA',(1280,800));candidate=original.copy()
 for d in draws:
  ref=lookup[d['key'].lower()];image=Image.open(FIGURES/'palettes'/ref['original']).convert('RGBA')
  assert image.size==(d['width'],d['height'])
  source=image.resize((image.width*4,image.height*4),Image.Resampling.NEAREST)
  hd=Image.open(replacements[d['key']]) if d['key'] in replacements else source
  assert hd.mode=='RGBA' and hd.size==source.size
  if d['mirror']:source=ImageOps.mirror(source);hd=ImageOps.mirror(hd)
  original.alpha_composite(source,(d['x']*4,d['y']*4));candidate.alpha_composite(hd,(d['x']*4,d['y']*4))
 roi=(min(d['x'] for d in draws)*4,min(d['y'] for d in draws)*4,
      max(d['x']+d['width'] for d in draws)*4,max(d['y']+d['height'] for d in draws)*4)
 missing=[];false_filled=[]
 for y in range(200):
  for x in range(320):
   aa=original.getpixel((x*4+2,y*4+2))[3]>=128;bb=candidate.getpixel((x*4+2,y*4+2))[3]>=128
   if aa and not bb:missing.append([x,y])
   if bb and not aa:false_filled.append([x,y])
 assert not missing and not false_filled
 out=ART/'assembly'/a.key.replace('.png','')/f'{a.frame}-{sha(a.candidate.read_bytes())[:16]}';out.mkdir(parents=True,exist_ok=True)
 original.save(out/'original-full.png');candidate.save(out/'candidate-full.png')
 left=original.crop(roi);right=candidate.crop(roi)
 sheet=Image.new('RGB',(left.width*2+60,left.height+60),'#242424');pen=ImageDraw.Draw(sheet)
 pen.text((15,8),'Original: verified palette + actual draw positions',fill='white')
 pen.text((left.width+40,8),'Only selected frame replaced; remaining art original',fill='white')
 sheet.paste(left,(15,32),left);sheet.paste(right,(left.width+40,32),right);sheet.save(out/'comparison.png')
 report=dict(status='source_drawlist_composition_checked_not_hd_runtime',frame=a.frame,key=a.key,
  source_zip_sha256=case['source_zip_sha256'],palette_contract_sha256=sha(case_path.read_bytes()),
  trace_sha256=sha(trace_path.read_bytes()),candidate_sha256=sha(a.candidate.read_bytes()),
  replacements={k:dict(path=str(v.relative_to(ROOT)),sha256=sha(v.read_bytes())) for k,v in replacements.items()},
  source_banks=case['source_banks'],draws=draws,roi=roi,
  missing_opaque_source_midpoints=missing,false_filled_transparent_source_midpoints=false_filled,
  limitation='Two consecutive original CPU draw batches in the same buffer. Art contact assembly only; original background, copper display, animation and HD runtime still require their own checks.')
 (out/'assembly.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 print(out.relative_to(ROOT))

if __name__=='__main__':main()
