"""Eksporter originalruter012..014 og egne kildebundne materialomraader."""
from pathlib import Path
import json,hashlib,sys
from PIL import Image
H=Path(__file__).resolve().parent;B=H.parent;R=B.parents[3];sys.path[:0]=[str(R/'tools'),str(B.parent)]
import moonfiles as m
from hd_bestilling import utvid_indekser
from contours import source_contours
sha=lambda b:hashlib.sha256(b).hexdigest();bank=m.Spill(R/'Moonstonecd32-AMIGA.zip').les('be1.c');rows=m.cel_les(bank)[0];pal=json.loads((B/'geometries-six-v3.json').read_text())[0]['palette'];contracts=[]
for i in [12,13,14,16]:
 s=rows[i];w,h=s['bredde'],s['hoyde'];ind=utvid_indekser(m.plan_til_indeks(s['data'],s['plan'],w,h),s['maske']);labels=[0 if not j else 7 if i==12 and j in [9,10] else 2 if j==13 else 1 for j in ind]
 im=Image.new('RGBA',(w,h));im.putdata([tuple(pal[j])if j else(0,0,0,0)for j in ind]);bounds=im.getbbox();white=Image.new('RGBA',im.size,'white');white.alpha_composite(im);p=H/'references'/f'{i:03}-original20x.png';p.parent.mkdir(exist_ok=True);white.convert('RGB').resize((w*20,h*20),Image.Resampling.NEAREST).save(p)
 contracts.append(dict(key=f'be1.c/{i:03}.png',frame=i,number=f'{i:03}',width=w,height=h,indices=list(ind),indices_sha256=sha(ind),source_bank_sha256=sha(bank),source_palette_contract=str((R/'art/hd-completion-figures-2026-10-11/palettes/cases/beast.json').relative_to(R)),source_palette_contract_sha256=sha((R/'art/hd-completion-figures-2026-10-11/palettes/cases/beast.json').read_bytes()),palette=pal,source_alpha_bounds=list(bounds),alpha_path=source_contours(ind,w,h,lambda j:j!=0),material_labels=labels,materials={name:source_contours(labels,w,h,lambda j,jj=jj:j==jj)for jj,name in [(1,'fur'),(2,'hide'),(7,'muzzle')]if jj in labels},flat_shadow=[],flat_shadow_top=None,reference=str(p.relative_to(H)),reference_sha256=sha(p.read_bytes()),scope='Hver fotomaster fra sin egen originalrute. Ingen uavklarte kroppsformer fullfoeres.'))
(H/'geometries-v2.json').write_text(json.dumps(contracts,indent=2)+'\n')
print('Fire originalkontrakter klare.')
