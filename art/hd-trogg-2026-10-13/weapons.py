#!/usr/bin/env python3
"""Bind tre genererte materialmastere til originale vaapenruter, uten ny anatomi."""
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
from PIL import Image, ImageDraw
ART=Path(__file__).resolve().parent
ROOT=ART.parents[1]
OLD=ROOT/'art/hd-completion-figures-2026-10-11/production'
sys.path.insert(0,str(OLD))
from contours import source_contours
sys.path.insert(0,str(ROOT/'tools'))
import moonfiles as mf
import hd_bestilling as bestilling
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def texture(name,box):
    im=Image.open(ART/'raw'/name).convert('RGBA')
    box=tuple(round(v*(im.width if i%2==0 else im.height)) for i,v in enumerate(box))
    tex=im.crop(box)
    assert min(tex.getchannel('A').getextrema())>=240,(name,box,'Gjennomsiktig felt i materialutvalg')
    return tex.convert('RGB'),box


def main():
    materials={
        'iron':('TROGGAxe2.CEL-055.png',(.58,.27,.83,.43)),
        'wood':('TROGGAxe2.CEL-066.png',(.405,.23,.447,.49)),
        'skin':('TROGGAxe2.CEL-066.png',(.356,.584,.470,.638)),
        'hammer':('TROGGAxe2.CEL-069.png',(.20,.18,.72,.34)),
    }
    textures={};material_records={}
    for label,(name,box) in materials.items():
        tex,b=texture(name,box);textures[label]=tex
        material_records[label]=dict(raw='raw/'+name,raw_sha256=sha(ART/'raw'/name),pixel_box=b,prompt='prompts/'+name.replace('.png','.txt'),prompt_sha256=sha(ART/'prompts'/name.replace('.png','.txt')))
    records=[]
    source=json.loads((ART/'source/contracts.json').read_text())
    assert sha(ROOT/'Moonstonecd32-AMIGA.zip')==source['source_zip_sha256']
    game=mf.Spill(str(ROOT/'Moonstonecd32-AMIGA.zip'))
    bank=game.les('data/TROGGAxe2.CEL');frames=mf.cel_les(bank)[0]
    for r in sorted(source['entries'],key=lambda r:r['frame']):
        if r['bank']!='TROGGAxe2.CEL':continue
        n,w,h=r['frame'],r['width'],r['height'];ix=r['indices'];size=w*4,h*4
        assert hashlib.sha256(bank).hexdigest()==r['source_bank_sha256']
        b=frames[n];assert (b['bredde'],b['hoyde'],b['maske'])==(w,h,r['plane_mask'])
        original=bestilling.utvid_indekser(mf.plan_til_indeks(b['data'],b['plan'],w,h),b['maske'])
        assert bytes(ix)==original and hashlib.sha256(original).hexdigest()==r['indices_sha256']
        path=ART/f'weapons-packing/{n:03}';path.mkdir(parents=True,exist_ok=True)
        svg=path/'alpha.svg'
        svg.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{size[0]}" height="{size[1]}" viewBox="0 0 {w} {h}"><path d="{source_contours(ix,w,h,lambda a:a>0)}" fill="white" fill-rule="evenodd"/></svg>\n')
        node=os.environ.get('NODE','/home/tombonator3000t/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node');env=os.environ.copy();env.setdefault('NODE_PATH',str(Path(node).parents[1]/'node_modules'))
        subprocess.run([node,str(OLD/'mask.cjs'),str(svg),str(path/'alpha.png'),*map(str,size)],check=True,env=env,stdout=subprocess.DEVNULL)
        alpha=Image.open(path/'alpha.png').getchannel('A')
        label_for=lambda v:'wood' if v==5 else 'skin' if v in {12,13,14} else 'cloth' if v in {9,10,11} else 'hammer' if n>=69 else 'iron'
        # Materialgrupper kommer fra dokumenterte indekser, ikke gamle RGB-piksler.
        bounds={}
        for y in range(h):
            for x in range(w):
                v=ix[y*w+x]
                if not v:continue
                label=label_for(v)
                old=bounds.get(label,(x,y,x+1,y+1));bounds[label]=(min(old[0],x),min(old[1],y),max(old[2],x+1),max(old[3],y+1))
        scaled={}
        for label,b in bounds.items():
            if label=='cloth':continue
            tex=textures[label]
            # Skaftets trestruktur foelger faktisk retning, ogsaa i svingrutene.
            if label=='wood':
                points=[(x,y) for y in range(h) for x in range(w) if ix[y*w+x]==5]
                mx=sum(x for x,y in points)/len(points);my=sum(y for x,y in points)/len(points)
                xx=sum((x-mx)**2 for x,y in points);yy=sum((y-my)**2 for x,y in points);xy=sum((x-mx)*(y-my) for x,y in points)
                angle=.5*math.atan2(2*xy,xx-yy)
                tex=tex.rotate(math.degrees(angle)-90,resample=Image.Resampling.BICUBIC,expand=True)
            scaled[label]=tex.resize(((b[2]-b[0])*4,(b[3]-b[1])*4),Image.Resampling.LANCZOS)
        result=Image.new('RGBA',size);mask=Image.new('RGBA',size,(0,128,0,255))
        for y in range(size[1]):
            for x in range(size[0]):
                v=ix[y//4*w+x//4]
                if v in r['live_indices']:mask.putpixel((x,y),(v+1,128,255,255))
        for y in range(size[1]):
            for x in range(size[0]):
                a=alpha.getpixel((x,y))
                if not a:continue
                sx,sy=x//4,y//4;v=ix[sy*w+sx]
                # Rundet alfakant kan ligge utenfor sin gamle opake celle.
                if v==0:
                    near=[(abs(xx-sx)+abs(yy-sy),ix[yy*w+xx]) for yy in range(max(0,sy-1),min(h,sy+2)) for xx in range(max(0,sx-1),min(w,sx+2)) if ix[yy*w+xx]]
                    assert near;v=min(near)[1]
                label=label_for(v);b=bounds[label]
                if label=='cloth':rgb=(3,8,25)
                else:
                    tex=scaled[label];u=max(0,min(tex.width-1,x-b[0]*4));z=max(0,min(tex.height-1,y-b[1]*4));rgb=tex.getpixel((u,z))
                    if label=='wood':rgb=tuple(round(c*.45) for c in rgb)
                result.putpixel((x,y),rgb+(a,))
                original_v=ix[sy*w+sx]
                if original_v in r['live_indices']:
                    # Samme fotografiske lysdetalj paa originalens levende hud/ermfelt.
                    lum=.2126*rgb[0]+.7152*rgb[1]+.0722*rgb[2]
                    base=78 if label=='skin' else 8
                    g=max(32,min(255,round(128*lum/base)))
                    mask.putpixel((x,y),(original_v+1,g,255,255))
        errors=[(x,y) for y in range(h) for x in range(w) if (result.getpixel((4*x+2,4*y+2))[3]>=128)!=(ix[y*w+x]!=0)]
        assert not errors
        target=ART/f'weapons/TROGGAxe2.CEL/{n:03}.png';target.parent.mkdir(parents=True,exist_ok=True);result.save(target,optimize=True)
        rec={k:v for k,v in r.items() if k not in {'indices','palette_words'}}
        rec.update(png=str(target.relative_to(ROOT)),png_sha256=sha(target),candidate_sha256=sha(target),material_master_count=3,materials=material_records,source_midpoints_checked=w*h,source_midpoint_errors=errors,method='Felles genererte metall/tre/hudmaterialer, originale del-/materialindekser og avrundet kildekontur. 30 kildebundne ruter, ikke 30 uavhengige AI-tegninger. Ingen original RGB er oppskalert.',runtime_status='pending')
        if r['live_indices']:
            m=target.with_suffix('.mask.png');mask.save(m,optimize=True);rec.update(mask=str(m.relative_to(ROOT)),mask_sha256=sha(m))
        (path/'record.json').write_text(json.dumps(rec,ensure_ascii=False,indent=2)+'\n');records.append(rec)
    contact=Image.new('RGB',(1200,math.ceil(len(records)/6)*215),'#262626');d=ImageDraw.Draw(contact)
    for i,r in enumerate(records):
        x=i%6*200;y=i//6*215;d.text((x+6,y+4),f"{r['frame']:03} original / HD",fill='white')
        for k,im in enumerate([Image.open(ART/r['reference']).convert('RGBA'),Image.open(ROOT/r['png']).convert('RGBA')]):
            scale=min(90/im.width,180/im.height);im=im.resize((max(1,round(im.width*scale)),max(1,round(im.height*scale))),Image.Resampling.NEAREST if k==0 else Image.Resampling.LANCZOS);contact.paste(im,(x+5+k*98,y+25),im)
    contact.save(ART/'weapon-comparison.png')
    (ART/'weapons.json').write_text(json.dumps(dict(schema=1,status='candidate_runtime_pending',source_zip_sha256=source['source_zip_sha256'],method='30 original-constrained material sprites from three generated masters',entries=records),ensure_ascii=False,indent=2)+'\n')
    print('Pakket',len(records),'ruter og',sum(bool(r.get('mask')) for r in records),'terrengmasker')


if __name__=='__main__':main()
