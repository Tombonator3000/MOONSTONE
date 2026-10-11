#!/usr/bin/env python3
"""Pakk én faktisk generert rute med kildeform og dokumenterte RGB-kart."""
import argparse
from collections import deque
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

from PIL import Image, ImageDraw
from contours import source_contours

ART=Path(__file__).resolve().parent
FIGURES=ART.parent
ROOT=FIGURES.parents[1]
sys.path.insert(0,str(ROOT/'tools'))


def sha(b):return hashlib.sha256(b).hexdigest()


def main():
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument('--key',required=True);ap.add_argument('--raw',required=True,type=Path)
 ap.add_argument('--prompt',required=True,type=Path);ap.add_argument('--palette-case',default='troll')
 ap.add_argument('--fit-generated-vertical-padding',action='store_true',help='Tilpass generatorens loddrette marg; ingen piksler med alfa over7 kan fjernes')
 ap.add_argument('--fit-generated-horizontal-padding',action='store_true',help='Tilpass generatorens vannrette marg; ingen piksler med alfa over7 kan fjernes')
 ap.add_argument('--diagnostic',action='store_true',help='Inspect failed raw geometry without approval or packing')
 ap.add_argument('--separate-shadow',action='store_true',help='TROLL source index5 stays a separate fixed black footshadow')
 ap.add_argument('--exact-flat-shadow',action='store_true',help='Bevar opprinnelig svart fotskygge med eksakt naermeste4x-alfa i ny pakkeversjon')
 args=ap.parse_args()
 assert not args.exact_flat_shadow or (args.separate_shadow and args.key in {'TROLL1.CEL/002.png','TROLL1.CEL/004.png','TROLL1.CEL/005.png'})
 args.raw=args.raw.resolve();args.prompt=args.prompt.resolve()
 q=json.loads((FIGURES/'queue.json').read_text());r=next(r for r in q['entries'] if r['key']==args.key)
 assert r['role']=='redraw'
 pal_path=FIGURES/'palettes/cases'/f'{args.palette_case}.json';pal=json.loads(pal_path.read_text())
 source_record=next(x for x in pal['references'] if x['key']==args.key)
 assert source_record['source_indices_sha256']==r['indices_sha256']
 original=Image.open(FIGURES/'palettes'/source_record['original']).convert('RGBA')
 original4x=original.resize((r['target_width'],r['target_height']),Image.Resampling.NEAREST)
 body_original=original.copy();shadow_positions=[]
 if args.separate_shadow:
  assert args.palette_case=='troll' and pal['colors'][5]==[0,0,0]
  troll2_shadow={'TROLL2.CEL/000.png':0,'TROLL2.CEL/001.png':38,'TROLL2.CEL/002.png':0,'TROLL2.CEL/006.png':0,'TROLL2.CEL/010.png':0,'TROLL2.CEL/011.png':0,'TROLL2.CEL/012.png':39,'TROLL2.CEL/014.png':0}
  assert args.key in {f'TROLL1.CEL/{n:03}.png' for n in [2,3,4,5,8,11,13,19,29,34,40]} or args.key in troll2_shadow,'Indeks5 er ikke generelt en fotskygge'
  packed=Image.open(FIGURES/r['packed_original']['path'])
  bits=[1<<n for n in range(5) if r['plane_mask']&(1<<n)]
  source_indices=[sum(bit for n,bit in enumerate(bits) if v&(1<<n)) for v in packed.getdata()]
  shadow_top=troll2_shadow[args.key] if args.key in troll2_shadow else 0 if args.key.startswith('TROLL2.CEL/') or args.key in {'TROLL1.CEL/008.png','TROLL1.CEL/019.png','TROLL1.CEL/029.png','TROLL1.CEL/034.png','TROLL1.CEL/040.png'} else original.height-(10 if args.key=='TROLL1.CEL/013.png' else 9 if args.key=='TROLL1.CEL/002.png' else 8)
  for y in range(original.height):
   for x in range(original.width):
    if source_indices[y*original.width+x]==5 and y>=shadow_top:
     shadow_positions.append((x,y));body_original.putpixel((x,y),(0,0,0,0))
  assert shadow_positions,'Separate-shadow requested without original index5'
  assert min(y for x,y in shadow_positions)>=shadow_top,'Svart kroppsmateriale må ikke fjernes som fotskygge'
 raw=Image.open(args.raw);assert raw.mode=='RGBA'
 assert not(args.fit_generated_vertical_padding and args.fit_generated_horizontal_padding),'Bare én teknisk margretning om gangen'
 raw_window=None;raw_margin_proof=None
 if args.fit_generated_vertical_padding:
  target_height=round(raw.width*original.height/original.width)
  bounds=raw.getchannel('A').point(lambda v:255 if v>=8 else 0).getbbox();assert bounds
  source_top=body_original.getchannel('A').getbbox()[1]
  # Bevar ogsaa den opprinnelige transparente toppmargen ved teknisk pakking.
  top=max(0,bounds[1]-round(source_top*target_height/original.height));window_height=max(target_height,bounds[3]-top)
  # Brede genereringer kan ha en liten sideforholdsavrunding. Bevar alle
  # synlige piksler, og tillat høyst to prosent ekstra helbildehøyde her.
  assert window_height<=target_height*1.02
  assert window_height<raw.height and bounds[3]<=top+window_height<=raw.height
  raw_window=[0,top,raw.width,top+window_height]
  # Ingen synlig form kuttes. Svak generatoralfa i tommargen dokumenteres.
  outside=[raw.getpixel((x,y))[3] for y in range(raw.height) for x in range(raw.width) if y<top or y>=top+window_height]
  assert max(outside,default=0)<=7,'Synlig kunst kan ikke fjernes som marg'
  raw_margin_proof=dict(removed_pixels=len(outside),nonzero_alpha_pixels=sum(v>0 for v in outside),max_alpha=max(outside,default=0),visible_content_clipped=False,target_aspect_height=target_height,preserved_window_height=window_height)
  raw=raw.crop(raw_window)
 if args.fit_generated_horizontal_padding:
  target_width=round(raw.height*original.width/original.height)
  bounds=raw.getchannel('A').point(lambda v:255 if v>=8 else 0).getbbox();assert bounds
  assert body_original.getchannel('A').getbbox()[0]==0,'Automatisk margfjerning krever kildeinnhold ved venstrekanten'
  left=bounds[0];window_width=max(target_width,bounds[2]-left)
  assert window_width<=target_width*1.02
  assert window_width<raw.width and bounds[2]<=left+window_width<=raw.width
  raw_window=[left,0,left+window_width,raw.height]
  outside=[raw.getpixel((x,y))[3] for y in range(raw.height) for x in range(raw.width) if x<left or x>=left+window_width]
  assert max(outside,default=0)<=7,'Synlig kunst kan ikke fjernes som marg'
  raw_margin_proof=dict(removed_pixels=len(outside),nonzero_alpha_pixels=sum(v>0 for v in outside),max_alpha=max(outside,default=0),visible_content_clipped=False,target_aspect_width=target_width,preserved_window_width=window_width)
  raw=raw.crop(raw_window)
 assert raw.size[0]>=r['target_width'] and raw.size[1]>=r['target_height']
 # Only generated pixels supply RGB. Original supplies geometry, never texture.
 generated=raw.resize(original4x.size,Image.Resampling.LANCZOS)
 source_alpha=body_original.getchannel('A').resize(original4x.size,Image.Resampling.NEAREST)
 raw_alpha=generated.getchannel('A')
 aa,bb=source_alpha.tobytes(),raw_alpha.tobytes()
 raw_iou=sum(a>=128 and b>=128 for a,b in zip(aa,bb))/sum(a>=128 or b>=128 for a,b in zip(aa,bb))
 assert raw_iou>=.80 or args.diagnostic,'Genereringens form avviker for mye for kildepakking'
 bank,frame=args.key.split('/')
 path=ART/'bound'/bank/frame.replace('.png','')/sha(args.raw.read_bytes())[:16]/('diagnostic-unapproved' if args.diagnostic else ('separate-shadow-troll2-v1-original-flat' if args.key.startswith('TROLL2.CEL/') else 'separate-shadow-feet-v23-original-flat' if args.key=='TROLL1.CEL/040.png' else 'separate-shadow-feet-v21-original-flat' if args.key=='TROLL1.CEL/034.png' else 'separate-shadow-feet-v18-original-flat' if args.key=='TROLL1.CEL/029.png' else 'separate-shadow-bottom10-v13' if args.key=='TROLL1.CEL/013.png' else 'separate-shadow-feet-v12-original-flat' if args.key=='TROLL1.CEL/011.png' else 'separate-shadow-feet-v9-original-flat' if args.key=='TROLL1.CEL/008.png' else 'separate-shadow-bottom8-v7') if args.separate_shadow else 'rounded-source-edge-v5')
 if args.exact_flat_shadow and not args.diagnostic:path=path.parent/'separate-shadow-walk-v8-original-flat'
 path.mkdir(parents=True,exist_ok=True)
 # Only a small whole-fragment placement correction is allowed. It preserves
 # generated anatomy and natural alpha edges; no per-row body deformation and
 # no source RGB is introduced. Source shape is the independent scoring guide.
 source_set={n for n,v in enumerate(source_alpha.tobytes()) if v>=128}
 best=(-1,None,None)
 for sx in (.96,.98,1,1.02,1.04):
  for sy in (.98,1,1.02):
   for dx in range(-4,5):
    for dy in range(-2,3):
     im=generated.transform(generated.size,Image.Transform.AFFINE,(1/sx,0,-dx/sx,0,1/sy,-dy/sy),Image.Resampling.BICUBIC)
     hit={n for n,v in enumerate(im.getchannel('A').tobytes()) if v>=128}
     iou=len(source_set&hit)/len(source_set|hit)
     if iou>best[0]:best=iou,(sx,sy,dx,dy),im
 # Very shallow fragments have a disproportionate IoU penalty from subpixel
 # antialiasing. Their edge repair is separately bounded below to one source
 # pixel, and the same mandatory source-midpoint tests still apply.
 shallow_fragment=original.height<=10
 alignment_gate=.85 if shallow_fragment else .90
 geometry_gate_passed=raw_iou>=.80 and best[0]>=alignment_gate
 assert geometry_gate_passed or args.diagnostic,'Genereringen krever nytegning; små globale korreksjoner er ikke nok'
 aligned_iou,affine,result=best
 aligned=result
 shape=source_contours(list(body_original.getchannel('A').getdata()),original.width,original.height,lambda a:a>0)
 svg=path/'alpha.svg';svg.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{r["target_width"]}" height="{r["target_height"]}" viewBox="0 0 {r["width"]} {r["height"]}"><path d="{shape}" fill="white" fill-rule="evenodd"/></svg>\n')
 node=os.environ.get('NODE','/home/tombonator3000t/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node')
 env=os.environ.copy();env.setdefault('NODE_PATH','/home/tombonator3000t/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules')
 subprocess.run([node,str(ART/'mask.cjs'),str(svg),str(path/'alpha.png'),str(r['target_width']),str(r['target_height'])],env=env,check=True)
 alpha=Image.open(path/'alpha.png').getchannel('A')
 generated_pixels=aligned.load();generated_alpha=aligned.getchannel('A').load();source_pixels=alpha.load()
 nearest={};distance={};pending=deque()
 for y in range(aligned.height):
  for x in range(aligned.width):
   if generated_alpha[x,y]>=128:
    nearest[(x,y)]=(x,y);distance[(x,y)]=0;pending.append((x,y))
 while pending:
  x,y=pending.popleft()
  for xx,yy in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
   if 0<=xx<aligned.width and 0<=yy<aligned.height and (xx,yy) not in nearest:
    nearest[(xx,yy)]=nearest[(x,y)];distance[(xx,yy)]=distance[(x,y)]+1;pending.append((xx,yy))
 result=Image.new('RGBA',aligned.size);out=result.load();extended=[];retained=0
 for y in range(aligned.height):
  for x in range(aligned.width):
   if not source_pixels[x,y]:continue
   if generated_alpha[x,y]>=128:u,v=x,y;retained+=1
   else:
    u,v=nearest[(x,y)];extended.append(dict(x=x,y=y,from_x=u,from_y=v,distance=distance[(x,y)]))
   out[x,y]=generated_pixels[u,v][:3]+(source_pixels[x,y],)
 if shadow_positions:
  shadow_set=set(shadow_positions)
  shadow_bits=[255 if (x,y) in shadow_set else 0 for y in range(original.height) for x in range(original.width)]
  shadow_shape=source_contours(shadow_bits,original.width,original.height,lambda a:a>0)
  shadow_svg=path/'shadow.svg';shadow_svg.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{r["target_width"]}" height="{r["target_height"]}" viewBox="0 0 {r["width"]} {r["height"]}"><path d="{shadow_shape}" fill="black" fill-rule="evenodd"/></svg>\n')
  subprocess.run([node,str(ART/'mask.cjs'),str(shadow_svg),str(path/'shadow.png'),str(r['target_width']),str(r['target_height'])],env=env,check=True)
  if args.exact_flat_shadow or args.key.startswith('TROLL2.CEL/') or args.key in {'TROLL1.CEL/008.png','TROLL1.CEL/019.png','TROLL1.CEL/011.png','TROLL1.CEL/013.png','TROLL1.CEL/029.png','TROLL1.CEL/034.png','TROLL1.CEL/040.png'}:
   # Spredte opprinnelige skyggeprikker beholdes eksakt, ikke nytegnet.
   original_shadow=Image.new('RGBA',original.size);original_shadow.putdata([(0,0,0,v) for v in shadow_bits]);original_shadow.resize(result.size,Image.Resampling.NEAREST).save(path/'shadow.png')
  result=Image.alpha_composite(Image.open(path/'shadow.png').convert('RGBA'),result)
 missing=[];false_filled=[]
 for y in range(original.height):
  for x in range(original.width):
   source_opaque=original.getpixel((x,y))[3]>0
   target_opaque=result.getpixel((4*x+2,4*y+2))[3]>=128
   if source_opaque and not target_opaque:missing.append([x,y])
   if target_opaque and not source_opaque:false_filled.append([x,y])
 assert not missing and not false_filled,(missing,false_filled)
 opaque_extension=max((p['distance'] for p in extended if source_pixels[p['x'],p['y']]>=128),default=0)
 if shallow_fragment and not args.diagnostic:assert opaque_extension<=4,'Grunt fragment krever mer enn én kildepiksel nytt randmateriale'
 target=path/'candidate.png';result.save(target,optimize=True)
 review=dict(key=args.key,candidate_sha256=sha(target.read_bytes()),source_indices_sha256=r['indices_sha256'],
  authoring_method='individual_redraw',generator='built-in ChatGPT image generator; exact model version not exposed',
  raw_sha256=sha(args.raw.read_bytes()),raw_file=str(args.raw.relative_to(ROOT)),raw_padding_window=raw_window,raw_margin_proof=raw_margin_proof,prompt=str(args.prompt.relative_to(ROOT)),
  prompt_sha256=sha(args.prompt.read_bytes()),palette_case=args.palette_case,palette_contract_sha256=sha(pal_path.read_bytes()),
  palette_reference_sha256=source_record['sha256'],
  packing='Generated RGBA resized to source4x and minimally globally aligned. Original alpha via marching-squares contours with <=.4sourcepx rounded corners; every original pixel midpoint preserved. Aligned generated interior RGB unchanged, missing edge RGB extended from nearest generated material. No original RGB, per-row anatomy warp, or raster replacement.',
  raw_silhouette_iou=raw_iou,aligned_silhouette_iou=aligned_iou,
  alignment_gate=alignment_gate,max_opaque_edge_extension_px=opaque_extension,
  geometry_gate_passed=geometry_gate_passed and not args.diagnostic,
  original_flat_shadow_packing=dict(indices=[5],source_rect=[0,shadow_top,original.width,original.height],source_pixels=len(shadow_positions),method='Originalt flatt svart indeks5-fotskyggefelt bevares med eksakt naermeste4x-alfa i sitt kildebekreftede rektangel. Generert foto brukes bare i kropp/fot; ingen nytegning av skyggen paastaas.' if args.key.startswith('TROLL2.CEL/') else 'Originalt konstant svart indeks5-skyggemoenster i rute040 beholdes med eksakt naermeste4x-alfa. Bare foten inneholder generert fotomateriale; ingen nytegning av skyggen paastaas.' if args.key=='TROLL1.CEL/040.png' else 'Originalt konstant svart indeks5-skyggemoenster i rute034 beholdes med eksakt naermeste4x-alfa. Bare foten inneholder generert fotomateriale; ingen nytegning av skyggen paastaas.' if args.key=='TROLL1.CEL/034.png' else 'Original constant-black index5 within known footshadow region is antialiased separately. Frame008 contains only cropped feet and shadow; frames002..005 restrict this to bottom8 rows. Black index5 above that region remains generated body material. Frame008, Frame011, Frame013 and Frame029 preserve sparse flat source shadow with exact nearest4x alpha; other footshadows use rounded contours. Not claimed as a new shadow redraw') if shadow_positions else None,
  source_pixel_midpoints_checked=original.width*original.height,missing_opaque_source_midpoints=missing,false_filled_transparent_source_midpoints=false_filled,
  retained_generated_rgb_pixels=retained,extended_edge_pixels=len(extended),max_edge_extension_px=max((p['distance'] for p in extended),default=0),edge_extension_map=extended,
  global_affine=dict(scale_x=affine[0],scale_y=affine[1],translate_x_px=affine[2],translate_y_px=affine[3]),
  visual_checks={k:'pending' for k in ['pose','crop','equipment','source_colors','anatomy','material','runtime_overlap','original_hd_return']},
  status='unapproved_geometry_diagnostic' if args.diagnostic else 'source_guided_candidate_not_activated')
 if args.exact_flat_shadow or args.key=='TROLL1.CEL/019.png':
  review['original_flat_shadow_packing']['method']='Originalt flatt svart indeks5-fotskyggefelt bevares med eksakt naermeste4x-alfa i sitt kildebekreftede rektangel. Bare kropp/fot inneholder separat generert fotomateriale. Ingen nytegning av skyggen paastaas.'
 (path/'art-record.json').write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n')
 sheet=Image.new('RGB',(900,580),'#222222');draw=ImageDraw.Draw(sheet)
 for x,title,im in [(15,'Original correct palette',original4x),(310,'Generated before packing',generated),(605,'Aligned candidate',result)]:
  draw.text((x,8),title,fill='white');factor=min(264/im.width,416/im.height)
  im=im.resize((max(1,round(im.width*factor)),max(1,round(im.height*factor))),Image.Resampling.NEAREST if x==15 else Image.Resampling.LANCZOS);sheet.paste(im,(x,32),im)
 sheet.save(path/'comparison.png')
 print(json.dumps(dict(key=args.key,path=str(path.relative_to(ROOT)),sha256=review['candidate_sha256'],raw_iou=raw_iou,aligned_iou=aligned_iou,status=review['status'])))
 return


if __name__=='__main__':main()
