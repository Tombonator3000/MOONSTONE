#!/usr/bin/env python3
"""Separate healer/mystic eye references with original scene palettes."""
import json,hashlib,sys
from pathlib import Path
from PIL import Image
ART=Path(__file__).resolve().parent;ROOT=ART.parents[1];sys.path.insert(0,str(ROOT/'tools'))
import moonfiles as mf
from hd_ui_bygg import ui_contours
sha=lambda b:hashlib.sha256(b).hexdigest()
game=mf.Spill(ROOT/'Moonstonecd32-AMIGA.zip');bank=game.les('mys.cel');frames=mf.cel_les(bank)[0]
routes=[];palettes={}
for nr,piv,scene in [(6,'hea.piv','healer'),(7,'mys.piv','mystic')]:
 data=game.les(piv);p,raw,planes=mf.piv_alle(data)[0][0];pal=[[*mf.amiga_rgb(c),255] for c in raw];palettes[scene]={'rgba':pal,'source':piv,'sha256':sha(data),'status':'original_source_palette_runtime_pending'}
 f=frames[nr];w,h=f['bredde'],f['hoyde'];idx=mf.plan_til_indeks(f['data'],f['plan'],w,h);assert f['maske']==31
 (ART/'source/indices').mkdir(parents=True,exist_ok=True);(ART/'source/indices'/f'{nr:03}.bin').write_bytes(idx)
 im=Image.new('RGBA',(w,h));im.putdata([tuple(pal[c]) if c else (0,0,0,0) for c in idx]);im.resize((w*4,h*4),Image.Resampling.NEAREST).save(ART/'references'/f'{nr:03}.png')
 routes.append({'frame':nr,'width':w,'height':h,'target_width':w*4,'target_height':h*4,'plane_mask':31,'alpha_path':ui_contours(idx,w,h,lambda c:c!=0),'indices_sha256':sha(idx),'reference_sha256':sha((ART/'references'/f'{nr:03}.png').read_bytes()),'scene':scene,'live_palette_mask_indices':[],'target':f'mys.cel/{nr:03}.png','source_bank':'data/mys.cel','source_bank_sha256':sha(bank)})
 (ART/'source-contract.json').write_text(json.dumps({'bank_sha256':sha(bank),'source_zip_sha256':sha((ROOT/'Moonstonecd32-AMIGA.zip').read_bytes()),'palettes':palettes,'routes':routes,'evidence':['disasm/mog.s:089a56..089a68 loads MYS.piv and mys.cel','disasm/mog.s:089cc6..089cd8 loads HEA.piv and mys.cel']},indent=2)+'\n')
