"""Gjenskap de tretten bestilte Troll-referansene fra originalZIP."""
from pathlib import Path
import csv,hashlib,json,sys
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;F=H.parents[1];R=F.parents[1];sys.path.insert(0,str(R/'tools'))
import moonfiles as mf
from hd_bestilling import utvid_indekser
sha=lambda b:hashlib.sha256(b).hexdigest();case=F/'palettes/cases/troll.json';palette=json.loads(case.read_text())['colors'];game=mf.Spill(R/'Moonstonecd32-AMIGA.zip');rows=[];(H/'references').mkdir(exist_ok=True)
contact=Image.new('RGB',(1200,1100),'#ddd');d=ImageDraw.Draw(contact)
for pos,r in enumerate([dict(fil=b,bilde=n,hd_fil=f'{b}/{n:03}.png') for b,n in [('TROLL1.CEL',n)for n in[12,16,18,19,36,41,42,43,44,45,46,47]]+[('TROLL2.CEL',10)]]):
 bank=r['fil'];n=int(r['bilde']);blob=game.les(bank);s=mf.cel_les(blob)[0][n];w,h=s['bredde'],s['hoyde'];idx=utvid_indekser(mf.plan_til_indeks(s['data'],s['plan'],w,h),s['maske']);im=Image.new('RGBA',(w,h));im.putdata([tuple(palette[i])+((255,)if i else(0,))for i in idx]);white=Image.new('RGBA',im.size,'white');white.alpha_composite(im);ref=white.convert('RGB').resize((w*16,h*16),Image.Resampling.NEAREST);p=H/'references'/f'{bank}-{n:03}-original16x.png';ref.save(p)
 rows.append(dict(key=r['hd_fil'],bank=bank,frame=n,width=w,height=h,indices=list(idx),indices_sha256=sha(idx),source_bank_sha256=sha(blob),palette=[c+[255]for c in palette],reference=str(p.relative_to(H)),reference_sha256=sha(p.read_bytes()),source_palette_contract=str(case.relative_to(R)),source_palette_contract_sha256=sha(case.read_bytes())))
 tile=ref.copy();tile.thumbnail((280,220),Image.Resampling.NEAREST);x=pos%4*300;y=pos//4*270;contact.paste(tile,(x+(300-tile.width)//2,y+32));d.text((x+8,y+8),f'{bank}/{n:03} {w}x{h} idx{sorted(set(idx))}',fill='black')
assert len(rows)==13
(H/'sources-v1.json').write_text(json.dumps(rows,indent=2)+'\n');contact.save(H/'references/contact-remaining13-v1.png');print('13 source references exported')
