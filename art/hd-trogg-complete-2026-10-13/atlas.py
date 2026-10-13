#!/usr/bin/env python3
"""Eksporter urørte ruteutsnitt og et samlet sammenligningsgalleri."""
import hashlib
import html
import json
from pathlib import Path
from PIL import Image

ART=Path(__file__).resolve().parent
ROOT=ART.parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rows=json.loads((ART/'sprites.json').read_text())['entries']
out=ART/'atlas';out.mkdir(exist_ok=True)
checks=[];cards=[];sheets=[]
for bank in dict.fromkeys(r['bank'] for r in rows):
    rr=[r for r in rows if r['bank']==bank]
    rects=[];x=y=rowh=2
    for r in rr:
        w,h=r['width']*4,r['height']*4
        if x+w+2>2048:x=2;y+=rowh+2;rowh=2
        rects.append(dict(key=r['key'],frame=r['frame'],x=x,y=y,width=w,height=h,source_width=r['width'],source_height=r['height'],png_sha256=r['png_sha256'],mask_sha256=r.get('mask_sha256')))
        x+=w+2;rowh=max(rowh,h)
    image=Image.new('RGBA',(2048,y+rowh+2));mask=Image.new('RGBA',image.size,(0,128,0,255))
    for r,b in zip(rr,rects):
        im=Image.open(ROOT/r['png']).convert('RGBA');image.paste(im,(b['x'],b['y']))
        if r.get('mask'):mask.paste(Image.open(ROOT/r['mask']),(b['x'],b['y']))
    p=out/(bank+'.png');m=out/(bank+'.mask.png');image.save(p,optimize=True);mask.save(m,optimize=True)
    for r,b in zip(rr,rects):
        box=(b['x'],b['y'],b['x']+b['width'],b['y']+b['height'])
        assert image.crop(box).tobytes()==Image.open(ROOT/r['png']).convert('RGBA').tobytes()
        if r.get('mask'):assert mask.crop(box).tobytes()==Image.open(ROOT/r['mask']).convert('RGBA').tobytes()
        checks.append(r['key'])
        ref=Path(r['reference']).relative_to(ART.relative_to(ROOT));png=Path(r['png']).relative_to(ART.relative_to(ROOT))
        cards.append(f'<article data-bank="{bank}"><h3>{html.escape(r["key"])}</h3><div class="pair"><figure><img class="source" loading="lazy" src="{ref}"><figcaption>Original</figcaption></figure><figure><img loading="lazy" src="{png}"><figcaption>{"Bevart svart form" if set(json.loads((ART/"source/contracts.json").read_text())["entries"][len(checks)-1]["indices"])<={0,5} else "HD-materiale"}</figcaption></figure></div><p>{html.escape(r["method"])}</p></article>')
    data=dict(bank=bank,image=p.name,mask=m.name,image_sha256=sha(p),mask_sha256=sha(m),rectangles=rects,role='Eksport og inspeksjon. Spillet bruker individuelle PNG-er og originalens ankere.')
    (out/(bank+'.json')).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n');sheets.append(data)
(ART/'index.html').write_text('''<!doctype html><html lang="no"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Hele Trogg-serien</title><style>body{margin:0;background:#171a1f;color:#e6e4db;font:16px system-ui}header{padding:24px;max-width:1000px}h1{margin:0 0 14px}a{color:#c9aa66}select{padding:10px;background:#252a32;color:inherit}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,300px),1fr));gap:14px;padding:16px}article{background:#24282e;padding:12px;min-width:0}h3{font-size:14px;overflow-wrap:anywhere}.pair{display:grid;grid-template-columns:1fr 1fr;gap:6px}figure{margin:0;background:#383b3e;text-align:center}img{width:100%;height:240px;object-fit:contain}.source{image-rendering:pixelated}figcaption{padding:8px;font-size:13px}p{line-height:1.5}article p{font-size:12px}article[hidden]{display:none}</style><header><h1>Hele Trogg-serien</h1><p>225 ruter i fire banker.195 nye ruter og30 tidligere leverte våpenruter. Nye genererte materialer er bundet til originalens konturer og fragmentdeling. Dette er materialkonvertering, ikke225 separat nytegnede poser. Rene svarte skygger og skaft er bevart. Spiller- og terrengfarger styres av egne masker i spillet.</p><label>Bank <select id="bank"><option value="">Alle225</option>'''+''.join('<option>'+s['bank']+'</option>' for s in sheets)+'''</select></label><p>'''+ ' | '.join(f'<a href="atlas/{s["bank"]}.png">{s["bank"]} atlas</a>' for s in sheets)+'''</p><p><a href="README.md">Produksjonsgrunnlag og kontrollomfang</a></p></header><main>'''+''.join(cards)+'''</main><script>document.getElementById('bank').onchange=e=>document.querySelectorAll('article').forEach(c=>c.hidden=!!e.target.value&&c.dataset.bank!==e.target.value);</script></html>''')
(ART/'verification').mkdir(exist_ok=True)
(ART/'verification/atlas.json').write_text(json.dumps(dict(status='passed',routes=len(checks),masks=sum(bool(r.get('mask')) for r in rows),sheets=[dict(bank=s['bank'],image_sha256=s['image_sha256'],mask_sha256=s['mask_sha256']) for s in sheets],all_crops_byte_exact=True),indent=2)+'\n')
print('225 eksakte atlasutsnitt og',sum(bool(r.get('mask')) for r in rows),'masker')
