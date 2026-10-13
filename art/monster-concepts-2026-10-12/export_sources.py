#!/usr/bin/env python3
"""Lag bare originalreferanser med kildepaletter, aldri HD-nytegning."""
import sys,json,hashlib,math
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
import moonfiles as mf
OUT=Path(__file__).resolve().parent
OLD=ROOT/'art/hd-completion-figures-2026-10-11'
game=mf.Spill(ROOT/'Moonstonecd32-AMIGA.zip')
base=json.loads((OLD/'palettes/cases/beast.json').read_text())['words']
kn5=json.loads((OLD/'figures/kn5-production/identity/source-color-contract.json').read_text())
items=[
('balok',['Balok1.CEL','Balok2.CEL','Balok3.CEL'],'balok',None),
('war-beast',['be1.c','be2.c'],'beast',None),
('guardian',['Demon1.CEL','Demon2.CEL','Demon3.CEL','Demon4.CEL'],'guardian',None),
('troll',['TROLL1.CEL','TROLL2.CEL'],'troll',None),
('ratman',['RATMEN1.CEL','RATMEN2.CEL'],None,[0x653,0x942,0x720,0x500,0xa96,0x875,0xc00]),
('mudman',['Mudmen1.CEL','Mudmen2.CEL'],None,[0x332,0xccb,0xb81,0x851,0x630,0xf52,0xc00]),
('trogg-axe-hammer',['TROGGAxe1.CEL','TROGGAxe2.CEL'],None,[0x025,0x004,0x001,0x830,0x400,0xf80,0xc00]),
('trogg-spear',['TROGGSpear1.CEL','TROGGSpear2.CEL'],None,[0x025,0x004,0x001,0x830,0x400,0xf80,0xc00]),
('dragon',['DRAGON1.CEL','DRAGON2.CEL','DRAGON5.CEL'],None,None),
('black-knight',['HE1.ob','HE2.ob','HE3.ob'],None,[0x206,0x103,0x001,0x830,0x400,0xf80,0xc00]),
]
records=[]
for slug,banks,case,override in items:
 words=base.copy()
 provenance='Original kode 088a4e..088d14; terreng0c'
 if case:
  c=json.loads((OLD/f'palettes/cases/{case}.json').read_text());words=c['words'];provenance=f'../hd-completion-figures-2026-10-11/palettes/cases/{case}.json'
 elif slug=='dragon': words=kn5['cases'][0]['samples'][0]['palette_words'];provenance='../hd-completion-figures-2026-10-11/figures/kn5-production/identity/source-color-contract.json'
 elif override:words[9:16]=override
 rgb=[mf.amiga_rgb(w) for w in words]
 for bank in banks:
  data=game.les(bank);frames,mem=mf.cel_les(data);cols=8;cw=165;ch=165
  sheet=Image.new('RGB',(cols*cw,math.ceil(len(frames)/cols)*ch),(232,230,224));d=ImageDraw.Draw(sheet);rows=[]
  for i,b in enumerate(frames):
   ix=mf.plan_til_indeks(b['data'],b['plan'],b['bredde'],b['hoyde'])
   bits=[1<<n for n in range(5) if b['maske']&(1<<n)]
   ix=bytes(sum(bit for n,bit in enumerate(bits) if v&(1<<n)) for v in ix)
   im=Image.new('RGBA',(b['bredde'],b['hoyde']));im.putdata([(*rgb[v],255 if v else 0) for v in ix])
   s=min(3,(cw-10)/im.width,(ch-30)/im.height);shown=im.resize((int(im.width*s),int(im.height*s)),Image.Resampling.NEAREST)
   x=(i%cols)*cw;y=(i//cols)*ch;sheet.paste(shown,(x+(cw-shown.width)//2,y+22+(ch-25-shown.height)//2),shown)
   d.text((x+4,y+3),f'{i:03} {b["bredde"]}x{b["hoyde"]}',fill=(20,20,20))
   rows.append(dict(frame=i,width=b['bredde'],height=b['hoyde'],flag=b['flagg'],plane_mask=b['maske'],offset=b['offset'],indices_sha256=hashlib.sha256(ix).hexdigest()))
  name=bank.lower().replace('.','-')+'.png';sheet.save(OUT/'source'/name)
  records.append(dict(monster=slug,bank=bank,source_sha256=hashlib.sha256(data).hexdigest(),palette_words=words,palette_provenance=provenance,contact='source/'+name,frames=rows))
(OUT/'source/inventory.json').write_text(json.dumps(dict(status='original_references_only_not_HD',source_zip_sha256=hashlib.sha256((ROOT/'Moonstonecd32-AMIGA.zip').read_bytes()).hexdigest(),banks=records),ensure_ascii=False,indent=2)+'\n')
print('Eksportert',len(records),'originalbanker,',sum(len(r['frames']) for r in records),'ruter')
