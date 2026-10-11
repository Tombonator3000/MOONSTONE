#!/usr/bin/env python3
"""Originalens faste Math-figur i den eksisterende preserve-masken."""
import json,hashlib,sys
from pathlib import Path
from PIL import Image
ART=Path(__file__).resolve().parent;ROOT=ART.parents[1];sys.path.insert(0,str(ROOT/'tools'))
import moonfiles as mf
from hd_ui_bygg import ui_contours
sha=lambda b:hashlib.sha256(b).hexdigest()
game=mf.Spill(ROOT/'Moonstonecd32-AMIGA.zip');data=game.les('WI1.P');p,raw,planes=mf.piv_alle(data)[0][0];idx=mf.plan_til_indeks(planes,p);palette=[[*mf.amiga_rgb(c),255] for c in raw]
scene=next(s for s in json.loads((ROOT/'web/hd/manifest.json').read_text())['scenes'] if s['id']=='math-balcony')
regions=scene['preserve_regions'];rect=[20,32,270,166];x0,y0,x1,y1=rect;w,h=x1-x0,y1-y0;mask=[];pixels=[];colors=[]
for y in range(y0,y1):
 for x in range(x0,x1):
  c=idx[y*320+x];keep=any(r['rect'][0]<=x<r['rect'][2] and r['rect'][1]<=y<r['rect'][3] and c in r['indices'] for r in regions);mask.append(int(keep));colors.append(c);pixels.append(tuple(palette[c]) if keep else (0,0,0,0))
preserve_mask=mask[:];seen=set();components=[]
for i,v in enumerate(mask):
 if not v or i in seen:continue
 q=[i];seen.add(i)
 for at in q:
  x,y=at%w,at//w
  for dy in (-1,0,1):
   for dx in (-1,0,1):
    xx,yy=x+dx,y+dy
    if 0<=xx<w and 0<=yy<h:
     n=yy*w+xx
     if mask[n] and n not in seen:seen.add(n);q.append(n)
 components.append(q)
large=sorted(components,key=len,reverse=True)[:3];assert sorted(map(len,large))==[769,2858,5916]
keep=set(n for c in large for n in c)
detail_fields=[[120,6,158,42],[18,110,56,132],[217,110,250,132]]
for i,v in enumerate(mask):
 if v and any(a<=i%w<c and b<=i//w<d for a,b,c,d in detail_fields):keep.add(i)
mask=[int(i in keep) for i in range(w*h)];pixels=[tuple(palette[c]) if mask[i] else (0,0,0,0) for i,c in enumerate(colors)]
# Indeks5 er originalens ugjennomsiktige svarte ansiktsskygge, ikke et hull.
# Avgrensningen er kun originalens hodefelt; arkitektur og animerte slots roeres ikke.
shadow_added=[]
for i,c in enumerate(colors):
 if 120<=i%w<158 and 6<=i//w<42 and c in (2,3,4,5) and not mask[i]:mask[i]=1;shadow_added.append(i)
pixels=[tuple(palette[c]) if mask[i] else (0,0,0,0) for i,c in enumerate(colors)]
im=Image.new('RGBA',(w,h));im.putdata(pixels);im.resize((w*4,h*4),Image.Resampling.NEAREST).save(ART/'references/math-static.png');(ART/'source/math-static-mask.bin').write_bytes(bytes(mask));(ART/'source/math-static-indices.bin').write_bytes(bytes(colors))
record={'kind':'embedded-Math-figure','source_file':'data/WI1.P','source_file_sha256':sha(data),'source_indices_sha256':sha(idx),'rect':rect,'width':w,'height':h,'target_width':w*4,'target_height':h*4,'preserve_regions':regions,'mask_sha256':sha(bytes(mask)),'mask_pixels':sum(mask),'alpha_path':ui_contours(mask,w,h,lambda c:bool(c)),'palette':palette,'reference':'references/math-static.png','reference_sha256':sha((ART/'references/math-static.png').read_bytes()),'target':'embedded/math-static.png','activation_requires':'Combined actual Math runtime with17 fragments, eyes, mouth, wind, dialogue and Original return'}
record['original_preserve_pixels']=sum(preserve_mask);record['figure_components']=[len(c) for c in large];record['detail_fields_local']=detail_fields;record['static_mask_is_preserve_subset']=all(not a or b for a,b in zip(mask,preserve_mask))
assert all(57<=i//w+y0<=62 for i in shadow_added if colors[i] in (2,3))
record['additional_original_head_shadow']={'indices':[2,3,4,5],'rect':[140,38,178,74],'pixels':len(shadow_added),'local_positions':shadow_added,'reason':'Original WI1.P opaque eyebrow, iris and head shading inside the source head. Indices2/3 occur only in the original eye/eyebrow rows57..62 here. No architectural pixel or transparent animation slot.'}
(ART/'static-source-contract.json').write_text(json.dumps(record,indent=2)+'\n')
pack_row={k:record[k] for k in ['width','height','target_width','target_height','reference_sha256','target','alpha_path']}
pack_row.update(frame=0,indices_file='source/math-static-mask.bin',indices_sha256=record['mask_sha256'],live_palette_mask_indices=[],scene='math-balcony')
(ART/'static-pack-contract.json').write_text(json.dumps({'routes':[pack_row],'palettes':{'math-balcony':{'rgba':palette}}},indent=2)+'\n')
print(sum(mask),'original static figure pixels')
