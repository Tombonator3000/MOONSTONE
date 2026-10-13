#!/usr/bin/env python3
"""Pakk separat Trogg-foto i originalrute; avvis store formavvik."""
import argparse
from collections import deque
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from PIL import Image, ImageDraw

ART = Path(__file__).resolve().parent
ROOT = ART.parents[1]
OLD = ROOT / 'art/hd-completion-figures-2026-10-11/production'
sys.path.insert(0, str(OLD))
from contours import source_contours
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def pack(r):
    bank, n, w, h = r['bank'], r['frame'], r['width'], r['height']
    name = f'{bank}-{n:03}'
    rawfile, prompt = ART / f'raw/{name}.png', ART / f'prompts/{name}.txt'
    raw = Image.open(rawfile).convert('RGBA')
    original = Image.open(ART / r['reference']).convert('RGBA')
    ix = r['indices']
    # Nederste svarte fotkontakt er kildeform, ikke generert stoff eller haar.
    shadow_top = {0: h-2, 1: h-3, 25: h-3, 26: h-3, 27: h, 28: h-3}.get(n, h) if bank == 'TROGGAxe1.CEL' else h
    shadow = {(x,y) for y in range(shadow_top,h) for x in range(w) if ix[y*w+x] == 5}
    body = original.copy()
    for x,y in shadow: body.putpixel((x,y),(0,0,0,0))
    size = w*4,h*4
    sb, rb = body.getchannel('A').getbbox(), raw.getchannel('A').point(lambda a: 255 if a>=128 else 0).getbbox()
    material = Image.new('RGBA',size)
    tb = tuple(v*4 for v in sb)
    material.paste(raw.crop(rb).resize((tb[2]-tb[0],tb[3]-tb[1]),Image.Resampling.LANCZOS),tb[:2])
    source_alpha = body.getchannel('A').resize(size,Image.Resampling.NEAREST)
    def iou(a,b):
        a,b=a.tobytes(),b.tobytes()
        return sum(x>=128 and y>=128 for x,y in zip(a,b))/sum(x>=128 or y>=128 for x,y in zip(a,b))
    raw_iou = iou(source_alpha,material.getchannel('A'))
    outdir = ART / f'packing/{name}';outdir.mkdir(parents=True,exist_ok=True)
    bits = list(body.getchannel('A').getdata())
    svg = outdir/'alpha.svg'
    svg.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{size[0]}" height="{size[1]}" viewBox="0 0 {w} {h}"><path d="{source_contours(bits,w,h,lambda a:a>0)}" fill="white" fill-rule="evenodd"/></svg>\n')
    node = os.environ.get('NODE','/home/tombonator3000t/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node')
    env = os.environ.copy();env.setdefault('NODE_PATH',str(Path(node).parents[1]/'node_modules'))
    subprocess.run([node,str(OLD/'mask.cjs'),str(svg),str(outdir/'alpha.png'),*map(str,size)],env=env,check=True,stdout=subprocess.DEVNULL)
    alpha = Image.open(outdir/'alpha.png').getchannel('A')
    nearest = {};dist = {};pending = deque()
    for y in range(size[1]):
        for x in range(size[0]):
            if material.getpixel((x,y))[3]>=128:nearest[x,y]=(x,y);dist[x,y]=0;pending.append((x,y))
    while pending:
        x,y=pending.popleft()
        for xx,yy in [(x-1,y),(x+1,y),(x,y-1),(x,y+1)]:
            if 0<=xx<size[0] and 0<=yy<size[1] and (xx,yy) not in nearest:
                nearest[xx,yy]=nearest[x,y];dist[xx,yy]=dist[x,y]+1;pending.append((xx,yy))
    result=Image.new('RGBA',size);mask=Image.new('RGBA',size,(0,128,0,255));extensions=[]
    for y in range(size[1]):
        for x in range(size[0]):
            a=alpha.getpixel((x,y));idx=ix[y//4*w+x//4]
            if not a:continue
            p=nearest[x,y];rgb=material.getpixel(p)[:3]
            if a>=128 and p!=(x,y):extensions.append(dist[x,y])
            result.putpixel((x,y),rgb+(a,))
            if idx in r['live_indices']:
                # Fotoets lokale luminans bevares som lysdetalj; faktisk palett styrer terrengfargen.
                word=r['palette_words'][idx];ref=tuple(((word>>k)&15)*17 for k in [8,4,0])
                lum=lambda v:.2126*v[0]+.7152*v[1]+.0722*v[2]
                g=max(32,min(255,round(128*lum(rgb)/max(1,lum(ref)))))
                mask.putpixel((x,y),(idx+1,g,255,255))
    for x,y in shadow:
        for yy in range(y*4,y*4+4):
            for xx in range(x*4,x*4+4):result.putpixel((xx,yy),(0,0,0,255))
    errors=[(x,y) for y in range(h) for x in range(w) if (result.getpixel((x*4+2,y*4+2))[3]>=128)!=(ix[y*w+x]!=0)]
    assert not errors,errors
    target=ART/f'packed/{bank}/{n:03}.png';target.parent.mkdir(parents=True,exist_ok=True)
    result.save(target,optimize=True)
    if r['live_indices']:mask.save(target.with_suffix('.mask.png'),optimize=True)
    sheet=Image.new('RGB',(900,560),'#242424');d=ImageDraw.Draw(sheet)
    for x,label,im in [(10,'Original',original),(310,'Generert materiale',raw),(610,'Pakket kandidat',result)]:
        d.text((x,8),label,fill='white');s=min(275/im.width,500/im.height);im=im.resize((round(im.width*s),round(im.height*s)),Image.Resampling.NEAREST if x==10 else Image.Resampling.LANCZOS);sheet.paste(im,(x,30),im)
    sheet.save(outdir/'comparison.png')
    record={**{k:v for k,v in r.items() if k not in ['indices','palette_words']},'raw_sha256':sha(rawfile),'prompt_sha256':sha(prompt),'candidate_sha256':sha(target),'raw_silhouette_iou':raw_iou,'max_opaque_extension_px':max(extensions,default=0),'source_midpoint_errors':errors,'original_shadow_pixels':len(shadow),'method':'Separat generert foto tilpasset originalboks. Originalen bestemmer alfa og flate fotskygger; foto gir RGB og lysdetaljer. Ingen per-rad formkriging. Terrengindekser9..14 har palettmaske.','geometry_status':'passed' if raw_iou>=.85 and max(extensions,default=0)<=8 else 'requires_redraw','runtime_status':'pending'}
    if r['live_indices']:record['mask_sha256']=sha(target.with_suffix('.mask.png'))
    (outdir/'record.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
    print(name,record['geometry_status'],round(raw_iou,3),record['max_opaque_extension_px'])


if __name__ == '__main__':
    ap=argparse.ArgumentParser();ap.add_argument('key',nargs='?');a=ap.parse_args()
    entries=json.loads((ART/'source/contracts.json').read_text())['entries']
    for r in entries:
        if (not a.key or r['key']==a.key) and (ART/f'raw/{r["bank"]}-{r["frame"]:03}.png').exists():pack(r)
