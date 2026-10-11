"""Frys nye tavernabordpakker og NN-masker med faktisk maalt blaapalett."""
from pathlib import Path
import hashlib,json,shutil
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent;ART=HERE.parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rows=json.loads((HERE/'verification/packing.json').read_text())['assets']
proof=HERE/'verification/runtime-0/dice-runtime.json';palette=json.loads(proof.read_text())['runtime']['seen']['6']['palette']
old=HERE/'records/preclean-v1';old.mkdir(exist_ok=True)
for row in rows:
 n=Path(row['key']).stem;record=HERE/f'records/dice-{n}-final.json'
 if record.exists() and not (old/record.name).exists():shutil.copy2(record,old/record.name)
 png=HERE/'packed'/row['key'];assert sha(png)==row['candidate_sha256']
 dest=ART/f'packs/dice.cel/{n}/{sha(png)[:16]}';hd=dest/'hd/dice.cel';hd.mkdir(parents=True,exist_ok=True);shutil.copy2(png,hd/f'{n}.png')
 row.update(status='packed_runtime_pending',tool='builtin_image_gen',authoring_method='individual_redraw',
   prompt_sha256=sha(HERE/row['prompt']),packing_script_sha256=sha(HERE/'pack.cjs'),
   method='Eget generert fotomateriale per rute, originalens kontur og ankre. Bordet hentes fra den samme rene HD-bakgrunnen. Ingen frie terningsymboler eller nye objektplasseringer.')
 if int(n)<8:
  geom=next(g for g in json.loads((HERE/'geometries.json').read_text()) if g['n']==n);im=Image.open(png).convert('RGBA');mask=Image.new('RGBA',im.size,(0,0,0,255));ip=im.load();mp=mask.load()
  for y in range(im.height):
   for x in range(im.width):
    idx=geom['indices'][y//4*geom['width']+x//4]
    if idx in range(6,11):
     color=palette[idx*4:idx*4+3];ref=sum(a*b for a,b in zip(color,[.2126,.7152,.0722]));light=sum(a*b for a,b in zip(ip[x,y][:3],[.2126,.7152,.0722]));mp[x,y]=(idx+1,max(0,min(255,round(light*128/ref))) if ref>8 else 128,255,255)
  if row.get('stationary_cloth_join'):
   joined=Image.open(ROOT/row['stationary_cloth_join']['mask']).convert('RGBA');jp=joined.load()
   assert sha(ROOT/row['stationary_cloth_join']['mask'])==row['stationary_cloth_join']['mask_sha256']
   for y in range(im.height):
    for x in range(im.width):
     if geom['indices'][y//4*geom['width']+x//4] in range(6,11):
      value=jp[(119-90)*4+x,(102-65)*4+y];assert value[0]==geom['indices'][y//4*geom['width']+x//4]+1;mp[x,y]=value
  mask.save(hd/f'{n}.mask.png');row['mask_sha256']=sha(hd/f'{n}.mask.png');row['mask_reference_palette']=palette;row['mask_reference_proof']=str(proof.relative_to(ROOT));row['mask_reference_proof_sha256']=sha(proof)
 record.write_text(json.dumps(row,ensure_ascii=False,indent=2)+'\n');(dest/'art-record.json').write_text(record.read_text())
print('Frosset17 nye bordpakker,2NN-masker; gamle kandidater bevart')
