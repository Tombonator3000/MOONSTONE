"""LI1: normal original-intropalett skilt fra faktisk lynblink, ingen kamp-preview."""
from pathlib import Path
import hashlib,json,sys
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'tools'))
import moonfiles as mf
import hd_bestilling as order
sha=lambda b:hashlib.sha256(b).hexdigest()
proof_path=HERE.parent/'intro/source/intro-runtime-catalog-v1.json';proof=json.loads(proof_path.read_text());assert proof['status']=='passed'
normal=next(r for r in proof['runtime']['records'] if r['key']=='li1.cel/000.png');flash=next(r for r in proof['runtime']['records'] if r['key']=='li1.cel/011.png')
assert normal['frame']==4502 and flash['frame']==4552 and normal['scan_valid'] and flash['scan_valid']
palette=normal['palette'];game=mf.Spill(str(ROOT/'Moonstonecd32-AMIGA.zip'));bank=game.les('data/li1.cel');rows=[]
for n,c in enumerate(mf.cel_les(bank)[0]):
 w,h=c['bredde'],c['hoyde'];idx=order.utvid_indekser(mf.plan_til_indeks(c['data'],c['plan'],w,h),c['maske'])
 im=Image.new('RGBA',(w,h));im.putdata([tuple(palette[i][:3])+((255 if i else 0),) for i in idx]);im.save(HERE/f'source/{n:03}-original.png');im.resize((w*4,h*4),Image.Resampling.NEAREST).save(HERE/f'source/{n:03}-nearest4x.png')
 rows.append(dict(key=f'li1.cel/{n:03}.png',frame=n,width=w,height=h,indices_sha256=sha(idx),source_bank_sha256=sha(bank),indices=list(idx),palette=palette))
assert len(rows)==30
(HERE/'source-contracts.json').write_text(json.dumps(rows,separators=(',',':'))+'\n')
(HERE/'source-palette-evidence.json').write_text(json.dumps(dict(schema=1,source_bank_sha256=sha(bank),catalog_path=str(proof_path.relative_to(ROOT)),catalog_sha256=sha(proof_path.read_bytes()),normal=normal,flash=flash,natural_observed_frames=sorted(int(r['key'].split('/')[1][:-4]) for r in proof['runtime']['records'] if r['key'].startswith('li1.cel/')),scope='Normal frame4502 palette for identity references. Actual flash4552 is separately preserved as source evidence; global max-light is not a material color reference. Routes023..029 not naturally observed in this catalog.'),indent=2)+'\n')
out=Image.new('RGB',(1200,1400),(28,28,28));draw=ImageDraw.Draw(out)
for c in rows:
 n=c['frame'];im=Image.open(HERE/f'source/{n:03}-nearest4x.png');im.thumbnail((185,235));x=n%6*200;y=n//6*280;out.paste(im,(x+8,y+25),im);draw.text((x+8,y+7),f'{n:03} {c["width"]}x{c["height"]}',fill='white')
out.save(HERE/'source/all-original-normal.png')
print(json.dumps(dict(frames=len(rows),bank_sha256=sha(bank),indices=[dict(frame=r['frame'],used=sorted(set(r['indices']))) for r in rows])))
