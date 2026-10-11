#!/usr/bin/env python3
"""Ny konturtekst i de faste, kildevaliderte pergamentfeltene."""
from pathlib import Path
import json
import hashlib
from collections import Counter
from PIL import Image, ImageDraw, ImageFont
import moonfiles as mf

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / 'web/hd/manifest.json'

def main():
    m = json.loads(P.read_text())
    fontpath = ROOT / 'art/hd-text-2026-10-11/fonts/IMFellEnglish-Regular.ttf'
    panels = []
    game = mf.Spill(str(ROOT / 'Moonstonecd32-AMIGA.zip'))
    for scene in m['scenes']:
        name = scene['id']
        if name not in ('waterdeep', 'highwood', 'tavern'):
            continue
        scene['overlays'] = [o for o in scene.get('overlays', []) if not o['key'].startswith('scene-text/')]
        plan,pal,bp = mf.piv_alle(game.les(scene['file']))[0][scene['frame']]
        indices = mf.plan_til_indeks(bp,plan)
        if name == 'tavern':
            labels = [(str(i) + ' gold', [272, 51 + (i-1)*28, 309, 64 + (i-1)*28]) for i in range(1,6)]
            labels += [('Exit', [272,182,310,196])]
        else:
            x = 0 if name == 'waterdeep' else 256
            labels = [('Visit',[x+3,0,x+61,13]), ('Merchant',[x+2,28,x+62,43]),
                      ('Tavern',[x+4,63,x+62,78]),('Healer',[x+4,101,x+62,116]),
                      ('Mythral' if name=='waterdeep' else 'High',[x+4,135,x+62,148]),
                      ('Mystic' if name=='waterdeep' else 'Temple',[x+4,148,x+62,165]),
                      ('Exit',[x+4,182,x+62,196])]
        for text, rect in labels:
            w,h = rect[2]-rect[0],rect[3]-rect[1]
            color = Counter(indices[y*320+x] for y in range(rect[1],rect[3]) for x in range(rect[0],rect[2])).most_common(1)[0][0]
            c = pal[color]
            rgba = (((c>>8)&15)*17,((c>>4)&15)*17,(c&15)*17,255)
            im = Image.new('RGBA',(w*6,h*6),rgba)
            font = ImageFont.truetype(str(fontpath), h*6-12)
            box=font.getbbox(text)
            if box[2]-box[0] > w*6-8:
                font=ImageFont.truetype(str(fontpath),int((h*6-12)*(w*6-8)/(box[2]-box[0])))
                box=font.getbbox(text)
            ImageDraw.Draw(im).text(((w*6-(box[2]-box[0]))/2-box[0],(h*6-(box[3]-box[1]))/2-box[1]),text,font=font,fill=(28,17,10,255))
            rel=f'scene-text/{len(panels):03d}.png'
            target=ROOT/'web/hd'/rel;target.parent.mkdir(exist_ok=True);im.save(target)
            scene['overlays'].append({'key':rel[:-4],'rect':rect,'uv_rect':[0,0,1,1],'foreground':True})
            panels.append({'scene':name,'text':text,'rect':rect,'path':rel,'sha256':hashlib.sha256(target.read_bytes()).hexdigest()})
    m['files']=[f for f in m['files'] if not f['path'].startswith('scene-text/')]
    for row in panels:
        target=ROOT/'web/hd'/row['path']
        m['files'].append({'path':row['path'],'sha256':row['sha256'],'bytes':target.stat().st_size,'kind':'base'})
    m['images']=sum(f['path'].endswith('.png') for f in m['files'])
    P.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
    (ROOT/'art/hd-text-2026-10-11/panels.json').write_text(json.dumps(panels,ensure_ascii=False,indent=2)+'\n')
    print(len(panels),'faste tekstfelt')

if __name__=='__main__':main()
