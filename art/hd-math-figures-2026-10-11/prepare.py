#!/usr/bin/env python3
"""Math-referanser fra originale indeksformer og faktisk maalt scenepalett."""
import hashlib,json,sys
from pathlib import Path
from PIL import Image,ImageDraw
ART=Path(__file__).resolve().parent;ROOT=ART.parents[1];sys.path.insert(0,str(ROOT/'tools'))
import moonfiles as mf
import hd_bestilling as order
from hd_ui_bygg import ui_contours
sha=lambda b:hashlib.sha256(b).hexdigest()
report=json.loads((ART/'verification/palette/math-figure-palette-test.json').read_text())
assert report['status']=='passed'
scene_pal={}
for scene in ('math-tower','math-balcony'):
 samples=[s for s in report['visit']['samples'] if s['scene']==scene]
 s=max(samples,key=lambda s:sum(s['palettes'][1]))
 assert all(p==s['palettes'][0] for p in s['palettes']), 'Paletten maa vaere lik paa alle maalte linjer'
 scene_pal[scene]={'frame':s['frame'],'state':s['state'],'rgba':[s['palettes'][0][i:i+4] for i in range(0,128,4)]}
game=mf.Spill(ROOT/'Moonstonecd32-AMIGA.zip');data=game.les('Wi1.C');frames=mf.cel_les(data)[0]
records=[];empties=[]
for nr,f in enumerate(frames):
 if not f['plan']:empties.append(nr);continue
 w,h=f['bredde'],f['hoyde'];idx=order.utvid_indekser(mf.plan_til_indeks(f['data'],f['plan'],w,h),f['maske']);scene='math-tower' if nr>=15 else 'math-balcony';p=scene_pal[scene]
 im=Image.new('RGBA',(w,h));im.putdata([tuple(p['rgba'][c]) if c else (0,0,0,0) for c in idx])
 rel=f'references/Wi1.C/{nr:03}.png';out=ART/rel;out.parent.mkdir(parents=True,exist_ok=True);im.resize((w*4,h*4),Image.Resampling.NEAREST).save(out)
 ids=ART/'source/indices'/f'{nr:03}.bin';ids.parent.mkdir(parents=True,exist_ok=True);ids.write_bytes(bytes(idx))
 records.append({'alpha_path':ui_contours(idx,w,h,lambda c:c!=0),'frame':nr,'width':w,'height':h,'target_width':w*4,'target_height':h*4,'plane_mask':f['maske'],'indices_sha256':sha(bytes(idx)),'reference':rel,'reference_sha256':sha(out.read_bytes()),'scene':scene,'palette_frame':p['frame'],'live_palette_mask_indices':list(range(6,11)) if nr>=15 else [],'source_bank_sha256':sha(data),'source_bank':'data/Wi1.C','target':f'Wi1.C/{nr:03}.png'})
assert empties==[8,9,13,14] and len(records)==17
contract={'kind':'verified-Math-palettes','source_zip_sha256':sha((ROOT/'Moonstonecd32-AMIGA.zip').read_bytes()),'bank_sha256':sha(data),'empty_frames':empties,'masters':17,'palettes':scene_pal,'runtime_report_sha256':sha((ART/'verification/palette/math-figure-palette-test.json').read_bytes()),'source_evidence':['$082f3a: WI2.P loads Math tower','$082f6a: WI1.P loads balcony','$089478-$089484: WI2 palette+12 passed to $08a9b6','$08a9b6: active_ridder+0x36 chooses blue/yellow/red/green for indices6..10'],'routes':records}
(ART/'source-contract.json').write_text(json.dumps(contract,ensure_ascii=False,indent=2)+'\n')
print('17 originalruter eksportert med faktisk Math-palett; 4 tomme beholdes tomme')
