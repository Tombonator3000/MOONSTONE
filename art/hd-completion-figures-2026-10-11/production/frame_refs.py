#!/usr/bin/env python3
"""Eksporter farge- og formreferanse for én rute; dette er ikke nytegning."""
import argparse,hashlib,json
from pathlib import Path
from PIL import Image
ART=Path(__file__).resolve().parent
FIGURES=ART.parent

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('key');p.add_argument('--case',default='troll');a=p.parse_args()
 q=json.loads((FIGURES/'queue.json').read_text());r=next(r for r in q['entries'] if r['key']==a.key)
 contract=FIGURES/'palettes/cases'/f'{a.case}.json';c=json.loads(contract.read_text());ref=next(v for v in c['references'] if v['key']==a.key)
 assert ref['source_indices_sha256']==r['indices_sha256']
 original=Image.open(FIGURES/'palettes'/ref['original']).convert('RGBA');packed=Image.open(FIGURES/r['packed_original']['path']);bits=[1<<n for n in range(5) if r['plane_mask']&(1<<n)]
 ix=[sum(bit for n,bit in enumerate(bits) if v&(1<<n)) for v in packed.getdata()]
 body=original.copy();flat_shadow=[]
 # Indeks5 er en vanlig svart farge også inne i kroppen. Bare de fire
 # gangbenrutene og den separate fotruten008 har flat fotskygge her.
 if a.case=='troll' and a.key in {f'TROLL1.CEL/{n:03}.png' for n in [2,3,4,5,8,11,13,29]}:
  assert c['colors'][5]==[0,0,0]
  shadow_top=0 if a.key in {'TROLL1.CEL/008.png','TROLL1.CEL/029.png'} else original.height-(10 if a.key=='TROLL1.CEL/013.png' else 8)
  for y in range(original.height):
   for x in range(original.width):
    if ix[y*original.width+x]==5 and y>=shadow_top:
     body.putpixel((x,y),(0,0,0,0));flat_shadow.append([x,y])
  assert flat_shadow
 target=ART/'references'/a.key.replace('.png','');target.mkdir(parents=True,exist_ok=True)
 size=(original.width*20,original.height*20)
 white=Image.new('RGBA',body.size,'white');white.alpha_composite(body);white.convert('RGB').resize(size,Image.Resampling.NEAREST).save(target/'body-white.png')
 mask=Image.new('RGB',body.size,'white');mask.paste('black',(0,0,body.width,body.height),body.getchannel('A'));mask.resize(size,Image.Resampling.NEAREST).save(target/'body-silhouette.png')
 record=dict(key=a.key,source_indices_sha256=r['indices_sha256'],palette_contract_sha256=hashlib.sha256(contract.read_bytes()).hexdigest(),flat_shadow_source_pixels=len(flat_shadow),source_size=list(original.size),target_size=[r['target_width'],r['target_height']],status='original_reference_only_not_hd_redraw')
 (target/'source.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n');print(target)
if __name__=='__main__':main()
