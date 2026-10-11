"""Originale ha1-referanser med maalt palett fra naturlig intro4912."""
from pathlib import Path
import hashlib,json,sys
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'tools'))
import moonfiles as mf
import hd_bestilling as order
r=json.loads((HERE.parent/'intro/source/intro-runtime-catalog-v1.json').read_text());assert r['status']=='passed'
palette=next(x['palette'] for x in r['runtime']['records'] if x['key']=='ha1.cel/000.png')
game=mf.Spill(str(ROOT/'Moonstonecd32-AMIGA.zip'));bank=game.les('data/ha1.cel');rows=[]
for n,c in enumerate(mf.cel_les(bank)[0]):
 w,h=c['bredde'],c['hoyde'];idx=order.utvid_indekser(mf.plan_til_indeks(c['data'],c['plan'],w,h),c['maske'])
 im=Image.new('RGBA',(w,h));im.putdata([tuple(palette[i][:3])+((255 if i else 0),) for i in idx]);im.save(HERE/f'source/{n:03}-original.png');im.resize((w*4,h*4),Image.Resampling.NEAREST).save(HERE/f'source/{n:03}-nearest4x.png')
 rows.append(dict(key=f'ha1.cel/{n:03}.png',frame=n,width=w,height=h,indices_sha256=hashlib.sha256(idx).hexdigest(),source_bank_sha256=hashlib.sha256(bank).hexdigest(),indices=list(idx),palette=palette))
(HERE/'source-contracts.json').write_text(json.dumps(rows,separators=(',',':'))+'\n')
print(len(rows),palette[:8])
