#!/usr/bin/env python3
"""Pakk separate genererte blodmaterialer i blo.cel sine originale konturer."""
import argparse
from collections import deque
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from PIL import Image, ImageDraw
import moonfiles as mf
ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/'art/hd-blood-wounds-2026-10-12'
OLD=ROOT/'art/hd-completion-figures-2026-10-11/production'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
spec=importlib.util.spec_from_file_location('blood_contours',OLD/'effect_pack_balok3.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--frames',default='0:41',help='Halvaapent fra:til-interval')
    args=parser.parse_args();start,end=map(int,args.frames.split(':'))
    game=mf.Spill(str(ROOT/'Moonstonecd32-AMIGA.zip'));bank=game.les('data/blo.cel')
    assert hashlib.sha256(bank).hexdigest()=='d83857454db7f5113598c6a41a46e45f62ecb4936637372b4807e22125bf699e'
    frames=mf.cel_les(bank)[0];contracts=json.loads((ART/'source/contracts.json').read_text())
    seen={};records=[]
    for n in range(start,end):
        r=contracts['frames'][n];b=frames[n];w,h=b['bredde'],b['hoyde']
        ix=mf.plan_til_indeks(b['data'],b['plan'],w,h)
        assert set(ix)=={0,15} and b['maske']==15
        assert hashlib.sha256(bytes(ix)).hexdigest()==r['indices_sha256']
        rawfile=ART/f'raw/{n:03}.png';prompt=ART/f'prompts/{n:03}.txt'
        digest=sha(rawfile);assert digest not in seen;seen[digest]=n
        raw=Image.open(rawfile).convert('RGBA');rb=raw.getchannel('A').point(lambda v:255 if v>=128 else 0).getbbox();assert rb
        original=Image.open(ART/f'source/{n:03}.png').convert('RGBA');sb=original.getchannel('A').getbbox();tb=tuple(v*4 for v in sb)
        size=(w*4,h*4);material=Image.new('RGBA',size)
        material.paste(raw.crop(rb).resize((tb[2]-tb[0],tb[3]-tb[1]),Image.Resampling.LANCZOS),tb[:2])
        out=ART/f'packing/{n:03}';out.mkdir(parents=True,exist_ok=True)
        svg=out/'alpha.svg';svg.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{size[0]}" height="{size[1]}" viewBox="0 0 {w} {h}"><path d="{module.effect_contours(ix,w,h)}" fill="white" fill-rule="evenodd"/></svg>\n')
        node=os.environ.get('NODE','/home/tombonator3000t/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node')
        env=os.environ.copy();env.setdefault('NODE_PATH','/home/tombonator3000t/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules')
        subprocess.run([node,str(OLD/'mask.cjs'),str(svg),str(out/'alpha.png'),*map(str,size)],check=True,env=env,stdout=subprocess.DEVNULL)
        alpha=Image.open(out/'alpha.png').getchannel('A');nearest={};dist={};pending=deque()
        for y in range(size[1]):
            for x in range(size[0]):
                if material.getpixel((x,y))[3]>=128:nearest[x,y]=(x,y);dist[x,y]=0;pending.append((x,y))
        assert pending
        while pending:
            x,y=pending.popleft()
            for xx,yy in [(x-1,y),(x+1,y),(x,y-1),(x,y+1)]:
                if 0<=xx<size[0] and 0<=yy<size[1] and (xx,yy) not in nearest:
                    nearest[xx,yy]=nearest[x,y];dist[xx,yy]=dist[x,y]+1;pending.append((xx,yy))
        result=Image.new('RGBA',size);red=total=retained=0;extended=[]
        for y in range(size[1]):
            for x in range(size[0]):
                a=alpha.getpixel((x,y))
                if not a:continue
                p=nearest[x,y];rgb=material.getpixel(p)[:3];result.putpixel((x,y),rgb+(a,))
                if p==(x,y):retained+=1
                else:extended.append(dist[x,y])
                if a>=128:total+=1;red+=rgb[0]>=rgb[1] and rgb[0]>rgb[2]
        assert red/total>=.90,(n,'not red',red/total)
        errors=[(x,y) for y in range(h) for x in range(w) if (result.getpixel((x*4+2,y*4+2))[3]>=128)!=(ix[y*w+x]==15)]
        assert not errors
        nearest_alpha=original.getchannel('A').resize(size,Image.Resampling.NEAREST)
        a,b=alpha.tobytes(),nearest_alpha.tobytes();iou=sum(v>=128 and z>=128 for v,z in zip(a,b))/sum(v>=128 or z>=128 for v,z in zip(a,b));assert iou>=.90
        target=ART/f'packed/blo.cel/{n:03}.png';target.parent.mkdir(parents=True,exist_ok=True);result.save(target,optimize=True)
        rec=dict(key=f'blo.cel/{n:03}.png',source_bank_sha256=contracts['bank_sha256'],source_indices_sha256=r['indices_sha256'],source_size=[w,h],texture_size=list(size),plane_mask=15,source_indices=[0,15],fixed_palette_word='c00',candidate_sha256=sha(target),raw_sha256=digest,prompt_sha256=sha(prompt),raw_file=str(rawfile.relative_to(ROOT)),prompt=str(prompt.relative_to(ROOT)),generator='Built-in ChatGPT image generator; exact model version not exposed',authoring_method='independent_generated_fluid_surface_in_original_contour',source_midpoints_checked=w*h,source_midpoint_errors=errors,silhouette_iou=iou,red_dominant_fraction=red/total,generated_rgb_retained_pixels=retained,nearest_surface_extended_pixels=len(extended),max_surface_extension_px=max(extended,default=0),raw_opaque_bbox=rb,target_opaque_bbox=tb,alpha_sha256=hashlib.sha256(a).hexdigest(),status='packed_runtime_pending')
        (out/'record.json').write_text(json.dumps(rec,ensure_ascii=False,indent=2)+'\n');records.append(rec)
        sheet=Image.new('RGB',(600,230),'#222');d=ImageDraw.Draw(sheet)
        for x,title,img in [(8,'Original',original),(208,'Nytt materiale',raw),(408,'Pakket',result)]:
            d.text((x,8),title,fill='white');s=min(180/img.width,190/img.height);im=img.resize((max(1,round(img.width*s)),max(1,round(img.height*s))),Image.Resampling.NEAREST if x==8 else Image.Resampling.LANCZOS);sheet.paste(im,(x,28),im)
        sheet.save(out/'comparison.png')
    print(json.dumps(dict(packed=len(records),frames=[r['key'] for r in records],status='runtime_pending')))
if __name__=='__main__':main()
