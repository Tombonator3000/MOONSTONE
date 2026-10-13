#!/usr/bin/env python3
"""Pakk hele Trogg-serien med felles nye materialer og originale delkontrakter."""
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
from PIL import Image, ImageDraw, ImageFilter, ImageStat

ART = Path(__file__).resolve().parent
ROOT = ART.parents[1]
OLD = ROOT / 'art/hd-completion-figures-2026-10-11/production'
sys.path.insert(0, str(OLD))
from contours import source_contours
sys.path.insert(0, str(ROOT / 'tools'))
import moonfiles as mf
import hd_bestilling as bestilling
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
rel = lambda p: str(p.relative_to(ROOT))


def material(name, box):
    im = Image.open(ART / 'raw' / name).convert('RGB')
    box = tuple(round(v * (im.width if i % 2 == 0 else im.height)) for i, v in enumerate(box))
    return im.crop(box), box


def main():
    source = json.loads((ART / 'source/contracts.json').read_text())
    before = {r['path']:r for r in json.loads((ART/'source/manifest-before.json').read_text())['files']}
    for r in source['entries']:
        r['previous'] = before.get(r['key'])
    assert sha(ROOT / 'Moonstonecd32-AMIGA.zip') == source['source_zip_sha256']
    game = mf.Spill(str(ROOT / 'Moonstonecd32-AMIGA.zip'))
    specs = {'skin': ('materials.png', (.03,.03,.47,.47)),
             'cloth': ('materials.png', (.53,.03,.97,.47)),
             'hair': ('materials.png', (.03,.53,.47,.97)),
             'leather': ('materials.png', (.53,.53,.97,.97)),
             'steel': ('equipment.png', (.03,.03,.30,.97)),
             'wood': ('equipment.png', (.36,.03,.63,.97)),
             'blood': ('equipment.png', (.70,.03,.97,.97))}
    textures = {}; materials = {}
    for label, (name, box) in specs.items():
        tex, pixels = material(name, box); textures[label] = tex
        prompt = ART / 'prompts' / ('materials.txt' if name == 'materials.png' else 'equipment.txt')
        materials[label] = dict(raw=rel(ART/'raw'/name), raw_sha256=sha(ART/'raw'/name),
                                prompt=rel(prompt), prompt_sha256=sha(prompt), pixel_box=pixels)
    node = '/home/tombonator3000t/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node'
    env = os.environ.copy(); env['NODE_PATH'] = str(Path(node).parents[1] / 'node_modules')
    entries = []; masters = {}; banks = {}
    for r in source['entries']:
        key, w, h, ix = r['key'], r['width'], r['height'], r['indices']
        if r['bank'] not in banks:
            data=game.les('data/'+r['bank']);banks[r['bank']]=(data,mf.cel_les(data)[0])
        bank,frames=banks[r['bank']];frame=frames[r['frame']]
        assert hashlib.sha256(bank).hexdigest() == r['source_bank_sha256']
        actual = bestilling.utvid_indekser(mf.plan_til_indeks(frame['data'],frame['plan'],w,h),frame['maske'])
        assert bytes(ix) == actual
        target = ART / 'sprites' / key; target.parent.mkdir(parents=True,exist_ok=True)
        ref = ART / 'source' / key; ref.parent.mkdir(parents=True,exist_ok=True)
        pal = [tuple(((v>>s)&15)*17 for s in (8,4,0)) for v in r['palette_words']]
        im = Image.new('RGBA',(w,h)); im.putdata([pal[v]+(255 if v else 0,) for v in ix]); im.save(ref)
        live = bestilling.maskefarger(r['bank'],r['frame']).intersection(ix)
        r['live_indices'] = sorted(live)
        rec = {k:v for k,v in r.items() if k not in {'indices','palette_words','index_counts'}}
        rec['reference'] = rel(ref)
        record = ART / 'packing' / key.replace('.png','') / 'record.json';record.parent.mkdir(parents=True,exist_ok=True)
        pure = set(ix) <= {0,5}
        if r['previous']:
            shutil.copy2(ROOT/'web/hd'/key,target)
            if live:
                mask = target.with_suffix('.mask.png');shutil.copy2(ROOT/'web/hd'/key.replace('.png','.mask.png'),mask)
            rec['method'] = 'Bevart tidligere kontrollert vaapenleveranse byteidentisk'
            rec['existing_master'] = True
        elif r['master_key'] != key:
            master = masters[r['master_key']];shutil.copy2(ROOT/master['png'],target)
            if live:
                mask=target.with_suffix('.mask.png');shutil.copy2(ROOT/master['mask'],mask)
            rec['method']='Eksakt originalindeksalias til '+r['master_key']
            rec['alias_of']=r['master_key']
        elif pure:
            # Disse svarte originalformene er skygger og rette skaft, ikke hud.
            im=Image.new('RGBA',(w,h));im.putdata([(0,0,0,255 if v else 0) for v in ix])
            im.resize((w*4,h*4),Image.Resampling.NEAREST).save(target)
            rec['method']='Bevart original svart skygge/skaftform, uten falsk fototekstur'
            rec['pure_black_source']=True
            (record.parent/'source.png').write_bytes(target.read_bytes())
        else:
            size=(w*4,h*4)
            alpha_svg=record.parent/'alpha.svg'
            alpha_svg.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{size[0]}" height="{size[1]}" viewBox="0 0 {w} {h}"><path d="{source_contours(ix,w,h,lambda a:a>0)}" fill="white" fill-rule="evenodd"/></svg>\n')
            if not (record.parent/'alpha.png').exists():
                subprocess.run([node,str(OLD/'mask.cjs'),str(alpha_svg),str(record.parent/'alpha.png'),*map(str,size)],env=env,check=True,stdout=subprocess.DEVNULL)
            alpha=Image.open(record.parent/'alpha.png').getchannel('A')
            weapon=r['bank']=='TROGGSpear2.CEL' and r['frame'] in {52,53,56,57,60,62,63,65,66}
            victim=bool(set(ix)&{6,7,8})
            cap_y=next((y for y in range(h) if sum(1<=v<=4 for v in ix[y*w:(y+1)*w])>=4),0)
            legs=(r['bank']=='TROGGAxe1.CEL' and r['frame'] in {1,3,5,7,11,13,14,16,19,20,24,28}) or (r['bank']=='TROGGAxe2.CEL' and r['frame']==22) or (r['bank']=='TROGGSpear1.CEL' and r['frame'] in {3,13,23}) or (r['bank']=='TROGGSpear2.CEL' and r['frame'] in {22,51,61})
            def label(v,y):
                if v==15:return 'blood'
                if 12<=v<=14:return 'skin'
                if 6<=v<=11:return 'cloth'
                if v==5:return 'wood' if weapon else 'hair'
                if legs:return 'leather'
                if not weapon and not victim and y>cap_y+9:
                    return 'leather' if y>h*.72 else 'hair'
                return 'steel'
            # Lysnivaaene definerer originalens fold/ansiktsform. RGB er nytt materiale.
            factors={1:1.2,2:.78,3:.53,4:.28,5:.08,6:1,7:.62,8:.28,9:1,10:.53,11:.22,12:1,13:.38,14:1.42,15:1}
            bounds={}
            for y in range(h):
                for x in range(w):
                    v=ix[y*w+x]
                    if not v:continue
                    lab=label(v,y);b=bounds.get(lab,(x,y,x+1,y+1));bounds[lab]=(min(b[0],x),min(b[1],y),max(b[2],x+1),max(b[3],y+1))
            scaled={};light={};means={}
            for lab,b in bounds.items():
                tex=textures[lab]
                if lab=='wood' and w>h:tex=tex.rotate(90,expand=True)
                scaled[lab]=tex.resize(((b[2]-b[0])*4,(b[3]-b[1])*4),Image.Resampling.LANCZOS)
                means[lab]=max(1,ImageStat.Stat(tex.convert('L')).mean[0])
                field=Image.new('L',(w,h),128)
                field.putdata([min(255,round(128*factors[v])) if v and label(v,i//w)==lab else 128 for i,v in enumerate(ix)])
                light[lab]=field.resize(size,Image.Resampling.BICUBIC).filter(ImageFilter.GaussianBlur(.65))
            bases={'skin':(145,64,18),'cloth':(4,13,49),'hair':(12,11,9),'leather':(38,34,25),'steel':(177,179,164),'wood':(24,18,10),'blood':(170,4,5)}
            result=Image.new('RGBA',size);mask=Image.new('RGBA',size,(0,128,0,255))
            for y in range(size[1]):
                for x in range(size[0]):
                    sx,sy=x//4,y//4;ov=ix[sy*w+sx];v=ov;material_y=sy
                    if ov in live:mask.putpixel((x,y),(ov+1,128,255,255))
                    a=alpha.getpixel((x,y))
                    if not a:continue
                    if v==0:
                        near=[(abs(xx-sx)+abs(yy-sy),ix[yy*w+xx],yy) for yy in range(max(0,sy-1),min(h,sy+2)) for xx in range(max(0,sx-1),min(w,sx+2)) if ix[yy*w+xx]]
                        assert near;_,v,material_y=min(near)
                    lab=label(v,material_y);b=bounds[lab];tex=scaled[lab];rgb=tex.getpixel((max(0,min(tex.width-1,x-4*b[0])),max(0,min(tex.height-1,y-4*b[1]))))
                    lum=.2126*rgb[0]+.7152*rgb[1]+.0722*rgb[2]
                    detail=max(.60,min(1.55,lum/means[lab]));f=light[lab].getpixel((x,y))/128
                    if v==5 and not weapon:
                        # Originalens svarte konturer og bakkeskygge skal ikke bli brunt haar.
                        rgb=(0,0,0) if sy>=h*.84 else tuple(round(c*detail) for c in (5,5,4))
                    else:rgb=tuple(max(0,min(255,round(c*detail*f))) for c in bases[lab])
                    if v in {6,7,8}:rgb=(0,0,round(min(255,100*detail*f)))
                    result.putpixel((x,y),rgb+(a,))
                    if ov in live:
                        pl=sum(pal[ov]);g=max(0,min(255,round(128*sum(rgb)/max(1,pl))))
                        # NN-indeksen bevares; fotoets detaljer ligger i lyskanalen.
                        mask.putpixel((x,y),(ov+1,g,255,255))
            result.save(target,optimize=True)
            if live:maskpath=target.with_suffix('.mask.png');mask.save(maskpath,optimize=True)
            rec['method']='To nye genererte materialatlas, avrundet kildekontur og originale material-/lysindekser; ingen original RGB-oppskalering'
        result=Image.open(target).convert('RGBA')
        errors=[(x,y) for y in range(h) for x in range(w) if (result.getpixel((4*x+2,4*y+2))[3]>=128)!=(ix[y*w+x]!=0)]
        assert not errors,(key,errors)
        rec.update(png=rel(target),png_sha256=sha(target),candidate_sha256=sha(target),source_midpoints_checked=w*h,source_midpoint_errors=errors,materials=materials,live_indices=sorted(live))
        if r['previous']:
            prior=ROOT/f'art/hd-trogg-2026-10-13/weapons-packing/{r["frame"]:03}/record.json'
            rec.update(materials={},previous_provenance=rel(prior),previous_provenance_sha256=sha(prior))
        if live:
            mp=target.with_suffix('.mask.png');rec.update(mask=rel(mp),mask_sha256=sha(mp))
        record.write_text(json.dumps(rec,ensure_ascii=False,indent=2)+'\n');rec['art_record']=rel(record);rec['art_record_sha256']=sha(record)
        entries.append(rec);masters[key]=rec
    for bank in dict.fromkeys(r['bank'] for r in entries):
        rr=[r for r in entries if r['bank']==bank];contact=Image.new('RGB',(1440,math.ceil(len(rr)/8)*230),'#262626');d=ImageDraw.Draw(contact)
        for i,r in enumerate(rr):
            x=i%8*180;y=i//8*230;d.text((x+4,y+3),f"{r['frame']:03} Original / HD",fill='white')
            for side,p in enumerate([ROOT/r['reference'],ROOT/r['png']]):
                im=Image.open(p).convert('RGBA');scale=min(84/im.width,200/im.height);im=im.resize((max(1,round(im.width*scale)),max(1,round(im.height*scale))),Image.Resampling.NEAREST if side==0 else Image.Resampling.LANCZOS);contact.paste(im,(x+4+side*88,y+24),im)
        contact.save(ART/(bank+'.comparison.png'))
    (ART/'source/contracts.json').write_text(json.dumps(source,indent=2)+'\n')
    (ART/'sprites.json').write_text(json.dumps(dict(schema=1,source_zip_sha256=source['source_zip_sha256'],entries=entries),ensure_ascii=False,indent=2)+'\n')
    print('Pakket',len(entries),'ruter;',sum(not r.get('previous') for r in entries),'nye;',sum(bool(r.get('mask')) for r in entries),'masker')


if __name__=='__main__':main()
