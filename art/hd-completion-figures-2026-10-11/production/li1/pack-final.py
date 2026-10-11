"""Bind 30 selvstendige fotografier og avgrensede kildeankrede materialrevisjoner."""
from pathlib import Path
import hashlib,json,shutil
from PIL import Image
HERE=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
geometry=json.loads((HERE/'geometries.json').read_text());generation=json.loads((HERE/'generation-records-v1.json').read_text())
baseline=json.loads((HERE/'verification/packing-30.json').read_text())
lights=json.loads((HERE/'iterations/lights-v2/verification/packing-11.json').read_text())
cloth=json.loads((HERE/'iterations/cloth-v4/material-proof.json').read_text())
assert len(geometry)==len(generation)==len(baseline['assets'])==30
assert len(lights['assets'])==11 and len(cloth['entries'])==8
assert baseline['script_sha256']==sha(HERE/'pack.cjs') and lights['script_sha256']==sha(HERE/'pack-lights-v2.cjs')
assert cloth['script_sha256']==sha(HERE/'material-demo-v4.py') and cloth['geometries_sha256']==sha(HERE/'geometries.json')
assert len({r['raw_sha256'] for r in generation})==len({r['generated_output'] for r in generation})==30
out=HERE/'packed-final-v1';out.mkdir(exist_ok=True);entries=[]
for c in geometry:
 n=c['frame'];r=next(r for r in generation if r['key']==c['key']);b=next(r for r in baseline['assets'] if r['key']==c['key'])
 assert sha(HERE/r['raw'])==r['raw_sha256']==b['raw_sha256'] and sha(HERE/r['prompt'])==r['prompt_sha256']==b['prompt_sha256']
 if n<=10:
  source=HERE/'iterations/lights-v2/packed';p=next(r for r in lights['assets'] if r['key']==c['key']);assert p['png_sha256']==sha(source/c['key'])
  method='Own independent electrical photograph supplies high-frequency light material. Smoothed original colors define exact lightning branches, white core positions and blue glow. Original-contour4x alpha is unchanged.'
 elif n in [12,13,14,15,19,20,21,22]:
  source=HERE/'iterations/cloth-v4/packed';p=next(r for r in cloth['entries'] if r['frame']==n);assert p['output_png_sha256']==sha(source/c['key']) and p['input_png_sha256']==sha(HERE/'packed'/c['key'])
  method='Own independent photograph supplies all figure identity and wool material. Original4502 gray fields supply common matte lighting only near fragment joins, feathered into this photograph; source anchors and alpha are unchanged. No extra photo or whole-pose redraw claim.'
 else:
  source=HERE/'packed';assert b['png_sha256']==sha(source/c['key'])
  method='Own independent photograph registered to the original-contour4x alpha; original frame anchors and holes are preserved.'
 key=c['key'];dest=out/key;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source/key,dest);mk=key.replace('.png','.mask.png');shutil.copyfile(source/mk,out/mk)
 im=Image.open(dest);mask=Image.open(out/mk);assert im.mode==mask.mode=='RGBA' and im.size==mask.size==(c['width']*4,c['height']*4)
 for q,index in enumerate(c['indices']):assert (im.getpixel((q%c['width']*4+2,q//c['width']*4+2))[3]>=128)==bool(index)
 for y in range(im.height):
  for x in range(im.width):
   index=c['indices'][(y//4)*c['width']+x//4];R,G,B,A=mask.getpixel((x,y));assert R==(index+1 if index else 0) and B==(255 if index else 0) and A==255
 entries.append(dict(key=key,source_path=str((source/key).relative_to(HERE)),png_sha256=sha(dest),mask_sha256=sha(out/mk),raw=r['raw'],raw_sha256=r['raw_sha256'],prompt=r['prompt'],prompt_sha256=r['prompt_sha256'],source_bank_sha256=c['source_bank_sha256'],indices_sha256=c['indices_sha256'],method=method))
report=dict(schema=1,status='candidate_not_activated',frames=30,pngs=60,packing_script_sha256=sha(Path(__file__)),geometry_sha256=sha(HERE/'geometries.json'),generation_records_sha256=sha(HERE/'generation-records-v1.json'),derivations=[dict(path=str(p.relative_to(HERE)),sha256=sha(p))for p in [HERE/'verification/packing-30.json',HERE/'iterations/lights-v2/verification/packing-11.json',HERE/'iterations/cloth-v4/material-proof.json',HERE/'pack.cjs',HERE/'pack-lights-v2.cjs',HERE/'material-demo-v4.py']],entries=entries)
(HERE/'verification/packing-final-v1.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n');print(json.dumps(dict(status=report['status'],frames=30,pngs=60)))
