"""Eksporter beistets originale18..29 til separate, regenererbare referanser."""
from pathlib import Path
import json,hashlib,sys
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;B=H.parent;R=B.parents[3];sys.path[:0]=[str(R/'tools'),str(B.parent)]
import moonfiles as mf
from hd_bestilling import utvid_indekser
sha=lambda b:hashlib.sha256(b).hexdigest();bank=mf.Spill(R/'Moonstonecd32-AMIGA.zip').les('be1.c');original=mf.cel_les(bank)[0];palette=json.loads((B/'geometries-six-v3.json').read_text())[0]['palette'];rows=[]
(H/'references').mkdir(exist_ok=True)
contact=Image.new('RGB',(1200,960),'#ddd');draw=ImageDraw.Draw(contact)
for position,number in enumerate(range(18,30)):
 s=original[number];w,h=s['bredde'],s['hoyde'];indices=utvid_indekser(mf.plan_til_indeks(s['data'],s['plan'],w,h),s['maske']);im=Image.new('RGBA',(w,h));im.putdata([tuple(palette[i])if i else(0,0,0,0)for i in indices]);white=Image.new('RGBA',im.size,'white');white.alpha_composite(im);ref=white.convert('RGB').resize((w*20,h*20),Image.Resampling.NEAREST);p=H/'references'/f'{number:03}-original20x.png';ref.save(p)
 rows.append(dict(key=f'be1.c/{number:03}.png',frame=number,number=f'{number:03}',width=w,height=h,indices=list(indices),indices_sha256=sha(indices),source_bank_sha256=sha(bank),palette=palette,reference=str(p.relative_to(H)),reference_sha256=sha(p.read_bytes()),source_alpha_bounds=list(im.getbbox())if im.getbbox()else None,scope='Originaleksport. Ingen nytegning eller aktivering.'))
 tile=ref.copy();tile.thumbnail((270,205),Image.Resampling.NEAREST);x=position%4*300;y=position//4*320;contact.paste(tile,(x+(300-tile.width)//2,y+35));draw.text((x+8,y+8),f'{number:03} {w}x{h} idx'+str(sorted(set(indices))),fill='black')
(H/'sources-v1.json').write_text(json.dumps(rows,indent=2)+'\n');contact.save(H/'references/contact-original18-29.png');print('Tolv separate originalreferanser klare.')
