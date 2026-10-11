"""Strenge NN-indeksmasker til originalens15 oppstigningsruter."""
from pathlib import Path
import sys,json
from PIL import Image
H=Path(__file__).resolve().parent;R=H.parents[3];sys.path.insert(0,str(R/'tools'))
import hd_bestilling as order,moonfiles as mf
s=mf.Spill(R/'Moonstonecd32-AMIGA.zip');bank=mf.cel_les(s.les('data/hen1.c'))[0]
for c in json.loads((H/'source-contracts.json').read_text()):
 if c['frame']<40:continue
 b=bank[c['frame']];px=mf.plan_til_indeks(b['data'],b['plan'],b['bredde'],b['hoyde']);assert list(order.utvid_indekser(px,b['maske']))==c['indices']
 src=H/'source/masks/hen1.c'/f"{c['frame']:03}.png";src.parent.mkdir(parents=True,exist_ok=True)
 im=Image.frombytes('P',(c['width'],c['height']),px);im.putpalette(sum([p[:3]for p in c['palette']],[])+[0]*672);im.save(src)
 order.lag_maske(str(src),str(H/'packed'/c['key'].replace('.png','.mask.png')))
