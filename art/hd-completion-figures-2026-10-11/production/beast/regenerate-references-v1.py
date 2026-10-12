"""Lag de seks regenererbare originalreferansene direkte fra spillarkivet."""
from pathlib import Path
import hashlib,json,sys,io
from PIL import Image
H=Path(__file__).resolve().parent;R=H.parents[3];sys.path.insert(0,str(R/'tools'))
import moonfiles as mf
from hd_bestilling import utvid_indekser
sha=lambda b:hashlib.sha256(b).hexdigest();game=mf.Spill(R/'Moonstonecd32-AMIGA.zip');original=mf.cel_les(game.les('be1.c'))[0];cs=json.loads((H/'geometries-six-v3.json').read_text());gs=json.loads((H/'generation-records-six-v1.json').read_text())
for c in cs:
 s=original[c['frame']];ind=utvid_indekser(mf.plan_til_indeks(s['data'],s['plan'],s['bredde'],s['hoyde']),s['maske']);assert sha(ind)==c['indices_sha256'];im=Image.new('RGBA',(c['width'],c['height']))
 for q,i in enumerate(ind):
  im.putpixel((q%c['width'],q//c['width']),tuple(c['palette'][i])if i and q not in c['flat_shadow']else(0,0,0,0))
 bg=Image.new('RGBA',im.size,'white');bg.alpha_composite(im);result=bg.convert('RGB').resize((im.width*20,im.height*20),Image.Resampling.NEAREST);buf=io.BytesIO();result.save(buf,format='PNG');b=buf.getvalue();g=next(g for g in gs if g['key']==c['key']);assert sha(b)==g['reference_sha256'],c['key'];p=H/g['reference'];p.parent.mkdir(exist_ok=True)
 if p.exists():assert p.read_bytes()==b
 else:p.write_bytes(b)
print('Seks originalreferanser er SHA-identiske med genereringsgrunnlaget.')
