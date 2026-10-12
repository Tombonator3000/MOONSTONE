"""Eksporter seks nye originalruter og referanser uten aa nytegne dem."""
from pathlib import Path
import hashlib,json,sys
from PIL import Image
H=Path(__file__).resolve().parent;B=H.parent;R=B.parents[3];sys.path[:0]=[str(R/'tools'),str(B.parent)]
import moonfiles as m
from hd_bestilling import utvid_indekser
from contours import source_contours
sha=lambda b:hashlib.sha256(b).hexdigest();bank=m.Spill(R/'Moonstonecd32-AMIGA.zip').les('be1.c');rows=m.cel_les(bank)[0];pal=json.loads((B/'geometries-six-v3.json').read_text())[0]['palette'];contracts=[]
# Bare den visuelt avklarte nederste skyggen i007/008 tas ut av fotoreferansen.
shadow_top={7:23,8:34};muzzle={6:(37,13),9:(10,12),10:(31,10)}
for i in range(6,12):
 s=rows[i];w,h=s['bredde'],s['hoyde'];ind=utvid_indekser(m.plan_til_indeks(s['data'],s['plan'],w,h),s['maske']);shadow=[q for q,j in enumerate(ind)if j==5 and q//w>=shadow_top.get(i,999)];mx,my=muzzle.get(i,(999,999));labels=[0 if not j else 5 if q in shadow else 4 if j==15 else 6 if j==14 else 3 if j in [1,2,3]or(j in [9,10]and q%w>=mx and q//w>=my and(i!=9 or q//w<=23))else 2 if j in [11,12,13]else 1 for q,j in enumerate(ind)]
 
 if i==7:labels=[0 if not j else 5 if q in shadow else 2 for q,j in enumerate(ind)]
 
 for q,j in enumerate(ind):
  if labels[q]==3 and j in [9,10]:labels[q]=7
 im=Image.new('RGBA',(w,h));im.putdata([tuple(pal[j])if j and q not in shadow else(0,0,0,0)for q,j in enumerate(ind)]);bounds=im.getbbox();bg=Image.new('RGBA',im.size,'white');bg.alpha_composite(im);ref=bg.convert('RGB').resize((w*20,h*20),Image.Resampling.NEAREST);p=H/'references'/f'{i:03}-original20x.png';p.parent.mkdir(exist_ok=True);ref.save(p)
 contracts.append(dict(key=f'be1.c/{i:03}.png',frame=i,number=f'{i:03}',width=w,height=h,indices=list(ind),indices_sha256=sha(ind),source_bank_sha256=sha(bank),source_palette_contract=str((R/'art/hd-completion-figures-2026-10-11/palettes/cases/beast.json').relative_to(R)),source_palette_contract_sha256=sha((R/'art/hd-completion-figures-2026-10-11/palettes/cases/beast.json').read_bytes()),palette=pal,source_alpha_bounds=list(bounds),alpha_path=source_contours(ind,w,h,lambda j:j!=0),material_labels=labels,materials={name:source_contours(labels,w,h,lambda j,jj=jj:j==jj)for jj,name in [(1,'fur'),(2,'hide'),(3,'bone'),(4,'eye'),(6,'mouth'),(7,'muzzle')]if jj in labels},flat_shadow=shadow,flat_shadow_top=shadow_top.get(i),reviewed_muzzle_min_xy=[mx,my],reference=str(p.relative_to(H)),reference_sha256=sha(p.read_bytes()),scope='En egen generering per originalrute. Originalkontur, tomrom, materialeomraader og kildefarger beholdes. Ingen manglende anatomi fullfoeres.'))
p=H/'geometries-v3.json';b=json.dumps(contracts,indent=2)+'\n'
if p.exists():assert p.read_text()==b
else:p.write_text(b)
print('Seks kildekontrakter og originalreferanser klare.')
