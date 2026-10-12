"""Originalbundne Demon2-referanser og former, ingen aktivering."""
from pathlib import Path
import hashlib,json,sys
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];FIGURES=HERE.parents[1]
sys.path.insert(0,str(ROOT/'tools'));sys.path.insert(0,str(HERE.parent))
import moonfiles as mf
from hd_bestilling import utvid_indekser,maskefarger
from contours import source_contours
sha=lambda b:hashlib.sha256(b).hexdigest()
case_path=FIGURES/'palettes/cases/guardian.json';case_bytes=case_path.read_bytes();case=json.loads(case_bytes)
assert case['status']=='original_palette_branch_and_controlled_runtime_verified'and'demon2.cel'in case['drawn_banks']
game=mf.Spill(ROOT/'Moonstonecd32-AMIGA.zip');bank=game.les('data/Demon2.CEL');assert sha(bank)==case['source_banks']['Demon2.CEL']
queue=json.loads((FIGURES/'queue.json').read_text());rows=[];sheet=Image.new('RGB',(1200,1100),(28,28,28));pen=ImageDraw.Draw(sheet)
for n,c in enumerate(mf.cel_les(bank)[0]):
 w,h=c['bredde'],c['hoyde'];key=f'Demon2.CEL/{n:03}.png';q=next(q for q in queue['entries']if q['key']==key)
 indices=utvid_indekser(mf.plan_til_indeks(c['data'],c['plan'],w,h),c['maske']);assert sha(indices)==q['indices_sha256']
 palette=[rgb+[255]for rgb in case['colors']];im=Image.new('RGBA',(w,h));im.putdata([tuple(palette[i][:3])+((255 if i else 0),)for i in indices]);ref=HERE/f'references/{n:03}-original.png';ref.parent.mkdir(exist_ok=True);im.save(ref)
 white=Image.new('RGBA',(w,h),'white');white.alpha_composite(im);white.convert('RGB').resize((w*20,h*20),Image.Resampling.NEAREST).save(HERE/f'references/{n:03}-nearest20x.png')
 x=n%10*120;y=n//10*110;fit=im.resize((max(1,int(w*min(110/w,85/h))),max(1,int(h*min(110/w,85/h)))),Image.Resampling.NEAREST);sheet.paste(fit,(x,y+20),fit);pen.text((x+3,y+3),f'{n:03} {w}x{h}',fill='white')
 shape=source_contours(list(indices),w,h,bool);live=sorted(maskefarger('Demon2.CEL',n)&set(indices))
 rows.append(dict(key=key,frame=n,number=f'{n:03}',width=w,height=h,indices=list(indices),indices_sha256=sha(indices),source_bank_sha256=sha(bank),source_palette_contract=str(case_path.relative_to(ROOT)),source_palette_contract_sha256=sha(case_bytes),palette=palette,source_alpha_bounds=im.getbbox(),material_labels=[0 if i==0 else 5 if i==5 else 7 if i in live else 3 if 9<=i<=12 else 4 if i==15 else 6 if i in[1,2,3,4]else 1 for i in indices],alpha_path=shape,materials={'light':shape},moonstone_source_pixels=0,moonstone_highlight_pixels=0,live_palette_indices=live,identity='original Guardian Demon2 fragment; per-frame action is not inferred from file order'))
assert len(rows)==99 and [r['frame']for r in rows if r['live_palette_indices']]==[60]
for name in ['source-contracts.json','geometries.json']:
 target=HERE/name;data=(json.dumps(rows,separators=(',',':'))+'\n').encode()
 if target.exists():assert target.read_bytes()==data
 else:target.write_bytes(data)
sheet.save(HERE/'references/all99-original.png')
print(json.dumps(dict(status='source_prepared_not_generated',routes=99,bank_sha256=sha(bank),live_palette_frames=[60],source_contracts_sha256=sha((HERE/'source-contracts.json').read_bytes()))))
