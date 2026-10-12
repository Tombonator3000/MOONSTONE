# Registrer fotoets bladfarger til originalens faste kildeindekser.
from pathlib import Path
import json,hashlib
from PIL import Image
b=Path(__file__).resolve().parent
sha=lambda x:hashlib.sha256(x).hexdigest()
c=next(c for c in json.loads((b/'source-contracts.json').read_text())['entries'] if c['key']=='RATMEN1.CEL/063.png')
source=b/'revisions/063-packed-v1/063.png'
assert sha(source.read_bytes())=='a21d2f82128650205526a1073abb7a85a7d2de17b2fe493db327d33411b6fe7b'
colors=json.loads((b/'identity/source-color-contract.json').read_text())['palette_words']
im=Image.open(source).convert('RGBA');out=im.copy();pix=im.load();dst=out.load()
assert im.size==(176,140) and set(c['indices'])=={0,5,22,24,25,28}
# Fotoets lokale lysvariasjon beholdes innen hver originale bladfarge.
# Alfa og svart kildeindeks5 endres ikke. Ingen ny form eller nye blad tegnes.
means={}
for index in [22,24,25,28]:
 values=[max(pix[x,y][:3]) for y in range(im.height) for x in range(im.width) if c['indices'][(y//4)*44+x//4]==index and pix[x,y][3]]
 means[index]=sum(values)/len(values)
for y in range(im.height):
 for x in range(im.width):
  index=c['indices'][(y//4)*44+x//4]
  if index not in means:continue
  r,g,blue,a=pix[x,y]
  if not a:continue
  word=colors[index];base=[((word>>8)&15)*17,((word>>4)&15)*17,(word&15)*17]
  light=max(.55,min(1.6,max(r,g,blue)/means[index]))
  dst[x,y]=tuple(min(255,round(v*light)) for v in base)+(a,)
assert im.getchannel('A').tobytes()==out.getchannel('A').tobytes()
target=b/'packed/RATMEN1.CEL/063.png';out.save(target)
report={'schema':1,'source_contracts_sha256':sha((b/'source-contracts.json').read_bytes()),'source_color_contract_sha256':sha((b/'identity/source-color-contract.json').read_bytes()),'key':c['key'],'indices_sha256':c['indices_sha256'],'input_packed_sha256':sha(source.read_bytes()),'output_packed_sha256':sha(target.read_bytes()),'source_palette_words':{str(i):colors[i] for i in means},'method':'source_index_bound_photo_color_registration','alpha_exact_unchanged':True,'raw_photo_unchanged':True,'scope':'Fast bladfarge22/24/25/28 fra observert originalpalett. Lokalt fotolys beholdt, klipp/ankre/svart5 uendret. V1 har for gulgronne blad, beholdt som avvist fargeregistrering.'}
(b/'verification/foliage063-color-v2.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report))
