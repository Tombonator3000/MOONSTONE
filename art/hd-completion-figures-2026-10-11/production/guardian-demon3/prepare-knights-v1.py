"""Avgrens bare kildeidentiske materialer i Demon3/015,020,021."""
from pathlib import Path
import json,sys,hashlib
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent));from contours import source_contours
geometry=json.loads((HERE/'geometries.json').read_text());rows=[]
for n in [15,20,21]:
 c=geometry[n];assert c['frame']==n and c['live_palette_indices']==[6,7,8]
 c['material_labels']=[0 if i==0 else 5 if i==5 else 7 if i in[6,7,8] else 11 if i in[1,2] else 10 if i in[3,4] else 12 for i in c['indices']]
 groups=[('cloth',[6,7,8]),('pale',[1,2]),('steel',[3,4]),('black',[5]),('light',list(range(9,32)))]
 c['materials']={name:source_contours(c['indices'],c['width'],c['height'],lambda i,values=values:i in values)for name,values in groups if set(values).intersection(c['indices'])}
 c['material_method']='Only original index regions: cloth6..8, pale steel1..2, grey steel3..4, opaque black5 and cyan energy9..31. Each route has its own photograph; no change to source contour, crop or holes.'
 rows.append(c)
for name,value in [('geometries-knights-v1.json',rows),('generation-records-knights-v1.json',[r for r in json.loads((HERE/'generation-records-v1.json').read_text())if r['key']in{c['key']for c in rows}])]:
 p=HERE/name;b=(json.dumps(value,separators=(',',':'))+'\n').encode()
 if p.exists()and name.startswith('geometries'):assert json.loads(p.read_bytes())==value
 p.write_bytes(b)
print(hashlib.sha256((HERE/'geometries-knights-v1.json').read_bytes()).hexdigest())
