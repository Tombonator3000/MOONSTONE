#!/usr/bin/env python3
"""Les originalindekser og pakket alfa uten bildeendring; kontroller hvert kildepiksel."""
from pathlib import Path
import hashlib,json
from PIL import Image
ART=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
source=json.loads((ART/'source-contract.json').read_text());entries=[]
for row in source['routes']:
    frame=row['frame'];indices=(ART/f'source/indices/{frame:03}.bin').read_bytes()
    assert sha(indices)==row['indices_sha256'];png=ART/'packed'/row['target'];im=Image.open(png).convert('RGBA')
    assert im.size==(row['width']*4,row['height']*4)
    assert all((im.getpixel((x*4+2,y*4+2))[3]>=128)==(indices[y*row['width']+x]!=0) for y in range(row['height']) for x in range(row['width'])),frame
    entries.append({'frame':frame,'source_pixels':len(indices),'source_hash':row['indices_sha256'],'packed_sha256':sha(png.read_bytes())})
static=json.loads((ART/'static-source-contract.json').read_text());mask=(ART/'source/math-static-mask.bin').read_bytes();im=Image.open(ART/'packed/embedded/math-static.png').convert('RGBA')
assert sha(mask)==static['mask_sha256'] and sum(bool(v) for v in mask)==9758
assert im.size==(1000,536) and all((im.getpixel((x*4+2,y*4+2))[3]>=128)==bool(mask[y*250+x]) for y in range(134) for x in range(250))
report={'status':'passed','scope':'All original source pixel centers match transparency; source rectangles, index hashes and9758-pixel embedded mask unchanged.','entries':entries,'static':{'mask_sha256':sha(mask),'png_sha256':sha((ART/'packed/embedded/math-static.png').read_bytes()),'source_pixels':len(mask)}}
(ART/'verification/alpha-v21.json').write_text(json.dumps(report,indent=2)+'\n');print('passed17frames+static',len(entries))
