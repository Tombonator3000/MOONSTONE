"""Kildebundet rituallys fra separate generatorkall; ingen aktivering."""
from pathlib import Path
import json,hashlib,sys
from PIL import Image
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from contours import source_contours
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
contracts=json.loads((HERE/'source-contracts.json').read_text())
records=[json.loads(p.read_text()) for p in sorted((HERE/'generation-calls').glob('*.json'))]
records=[r for r in records if 25<=int(r['key'].split('/')[1][:3])<=39]
rows=[]
for g in records:
 c=next(c for c in contracts if c['key']==g['key']);n=c['frame'];w=c['width'];h=c['height'];px=c['indices']
 assert sha(HERE/g['raw'])==g['raw_sha256'] and sha(HERE/g['prompt'])==g['prompt_sha256']
 labels=[1 if i else 0 for i in px];alpha=Image.new('L',(w,h));alpha.putdata([255 if i else 0 for i in px]);shape=source_contours(px,w,h,lambda i:i!=0)
 rows.append(dict(**c,number=f'{n:03}',source_alpha_bounds=alpha.getbbox(),material_labels=labels,alpha_path=shape,materials={'light':shape},moonstone_source_pixels=0,moonstone_highlight_pixels=0))
assert len({g['raw_sha256'] for g in records})==len(records)
(HERE/'geometries-effects.json').write_text(json.dumps(rows,separators=(',',':'))+'\n')
(HERE/'generation-records-effects-v1.json').write_text(json.dumps(records,indent=2)+'\n')
print(len(rows),'separate kildebundne ritualeffekter')
