"""Add source-index masks for two already shipped embedded-knight routes; photographs stay unchanged."""
from pathlib import Path
import hashlib,json,sys,shutil
from PIL import Image
H=Path(__file__).resolve().parent;R=H.parents[3];sys.path.insert(0,str(R/'tools'))
import moonfiles as mf
from hd_bestilling import utvid_indekser,maskefarger
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:str(p.relative_to(R))
game=mf.Spill(R/'Moonstonecd32-AMIGA.zip');rows=[]
for bank,frame,case in [('Balok1.CEL',10,'balok'),('RATMEN2.CEL',58,'ratmen')]:
 raw=game.les('data/'+bank);source=mf.cel_les(raw)[0][frame];w,h=source['bredde'],source['hoyde'];ind=utvid_indekser(mf.plan_til_indeks(source['data'],source['plan'],w,h),source['maske']);key=f'{bank}/{frame:03}.png';png=R/'web/hd'/key;mask=H/'packed'/key.replace('.png','.mask.png');mask.parent.mkdir(parents=True,exist_ok=True)
 live=maskefarger(bank,frame);assert live=={6,7,8}
 if bank.startswith('RATMEN'):
  master=mf.cel_les(game.les('KN3.ob'))[0][12];mi=utvid_indekser(mf.plan_til_indeks(master['data'],master['plan'],master['bredde'],master['hoyde']),master['maske']);assert mi==ind and (master['bredde'],master['hoyde'])==(w,h)
  assert png.read_bytes()==(R/'web/hd/KN3.ob/012.png').read_bytes();shutil.copyfile(R/'web/hd/KN3.ob/012.mask.png',mask)
 else:
  assert [(q%w,q//w)for q,i in enumerate(ind)if i in live]==[(14,20),(15,20),(16,20)]
  m=Image.new('RGBA',(w*4,h*4),(0,0,0,255))
  for y in range(h*4):
   for x in range(w*4):
    i=ind[(y//4)*w+x//4]
    if i in live:m.putpixel((x,y),(i+1,128,255,255))
  m.save(mask)
 im=Image.open(mask);assert im.mode=='RGBA' and im.size==(w*4,h*4)
 for y in range(h*4):
  for x in range(w*4):
   i=ind[y//4*w+x//4];r,g,b,a=im.getpixel((x,y));assert r==(i+1 if i in live else 0) and b==(255 if r else 0) and a==255
 palette=R/f'art/hd-completion-figures-2026-10-11/palettes/cases/{case}.json';colors=json.loads(palette.read_text())['colors']
 rows.append(dict(key=key,bank=bank,frame=frame,width=w,height=h,indices=list(ind),indices_sha256=hashlib.sha256(ind).hexdigest(),source_bank_sha256=hashlib.sha256(raw).hexdigest(),png=rel(png),png_sha256=sha(png),mask=rel(mask),mask_sha256=sha(mask),palette_case=rel(palette),palette_sha256=sha(palette),colors=colors,live_source_cells=sum(i in live for i in ind),method='Exact source identical KN3/012 mask copy, existing photograph unchanged'if bank.startswith('RATMEN')else'Only three original index8 cells,48 exact4x maskpixels; G128 because original index8 blue luminance is below8; existing photograph unchanged'))
report=dict(schema=1,status='prepared_not_activated',source_zip_sha256=sha(R/'Moonstonecd32-AMIGA.zip'),prepare_sha256=sha(Path(__file__)),rows=rows);p=H/'source-contracts-v1.json';p.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(status=report['status'],routes=len(rows),live_source_cells=[r['live_source_cells']for r in rows],photographs_unchanged=True)))
