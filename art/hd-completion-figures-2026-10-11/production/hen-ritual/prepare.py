"""Kildeformer og faktiske avslutningsfarger til ridder og ritualeffekter."""
from pathlib import Path
import sys,json,hashlib
from PIL import Image
R=Path(__file__).resolve().parents[4];H=Path(__file__).resolve().parent;sys.path.insert(0,str(R/'tools'))
import moonfiles as mf
import hd_bestilling as order
s=mf.Spill(R/'Moonstonecd32-AMIGA.zip');b=s.les('data/hen1.c');k=s.les('data/Klift1.CEL');assert b==k
D=json.loads((H/'source/ending-runtime-catalog-v1.json').read_text());assert D['status']=='passed'
r=next(r for r in D['runtime']['records'] if r['key']=='Klift1.CEL/000.png');pal=next(v['palette'] for v in r['variants'] if v['palette'][1][:3]==[204,238,255]);rows=[]
# Rapporten feilet sin gamle lilla forventning, men inneholder uendret originalskanout.
# Beviset er derfor fargekilde, aldri et bestatt HD-runtimebevis.
proof=H/'verification/ascending-all-v1/test.json';proof_sha=hashlib.sha256(proof.read_bytes()).hexdigest()
assert proof_sha=='167b7d8b2dfdc8e8c4a0e61b26048907010a9f29c70099172acb91d81daba78f'
scan=json.loads(proof.read_text())['runtime']['seen']
for n,c in enumerate(mf.cel_les(b)[0]):
 if 7<=n<=24:continue
 w,h=c['bredde'],c['hoyde'];idx=order.utvid_indekser(mf.plan_til_indeks(c['data'],c['plan'],w,h),c['maske'])
 p=scan[str(n)]['palette'] if n>=40 else pal
 im=Image.new('RGBA',(w,h));im.putdata([tuple(p[i][:3])+((255 if i else 0),) for i in idx])
 if n>=40:
  # Gamle lilla generatorreferanser bevares med sine opprinnelige SHA-er.
  im.save(H/f'source/{n:03}-scanout-original.png')
 else:
  im.save(H/f'source/{n:03}-original.png');im.resize((w*20,h*20),Image.Resampling.NEAREST).save(H/f'source/{n:03}-nearest20x.png')
 rows.append(dict(key=f'hen1.c/{n:03}.png',alias=f'Klift1.CEL/{n:03}.png',frame=n,width=w,height=h,source_bank_sha256=hashlib.sha256(b).hexdigest(),indices_sha256=hashlib.sha256(idx).hexdigest(),indices=list(idx),palette=p,identity='fixed red knight fragment' if n<7 else 'electrical arc from sky' if n<=27 else 'source electrical knight or attached arc fragment' if n<40 else 'luminous knight ascending and shrinking'))
 if n>=40:rows[-1].update(palette_source='actual_original_scanout',palette_proof_frame=scan[str(n)]['frame'],palette_proof=str(proof.relative_to(R)),palette_proof_sha256=proof_sha)
(H/'source-contracts.json').write_text(json.dumps(rows,separators=(',',':'))+'\n')
print(len(rows),'source identities exported; not HD art')
