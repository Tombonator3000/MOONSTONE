"""Separat materialavgrensning for original ridder i Demon2/060, uten ny geometri."""
from pathlib import Path
import json,sys,hashlib
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent));from contours import source_contours
c=json.loads((HERE/'geometries.json').read_text())[60]
assert c['frame']==60 and c['live_palette_indices']==[6,7,8]
c['material_labels']=[0 if i==0 else 5 if i==5 else 7 if i in[6,7,8] else 11 if i in[1,2] else 10 for i in c['indices']]
c['materials']={name:source_contours(c['indices'],c['width'],c['height'],lambda i,values=values:i in values) for name,values in [('cloth',[6,7,8]),('sword',[1,2]),('steel',[3,4]),('black',[5])]}
c['material_method']='Only source-identical original index regions: cloth6..8, pale sword1..2, grey steel3..4, exact opaque black5. Own generated photograph supplies material light and grain; no change to original geometry.'
for name,value in [('geometry-knight-v2.json',[c]),('generation-records-knight-v2.json',[r for r in json.loads((HERE/'generation-records-v1.json').read_text())if r['key']==c['key']])]:
 b=(json.dumps(value,separators=(',',':'))+'\n').encode();p=HERE/name
 if p.exists() and name.startswith('geometry'):assert json.loads(p.read_bytes())==value
 p.write_bytes(b)
print(hashlib.sha256((HERE/'geometry-knight-v2.json').read_bytes()).hexdigest())
