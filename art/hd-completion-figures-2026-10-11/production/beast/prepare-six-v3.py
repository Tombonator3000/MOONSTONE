"""Bevar kildegeometrien og skill beistets pels fra munnpartiet etter originalen."""
from pathlib import Path
import json,sys
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H.parent))
from contours import source_contours
cs=json.loads((H/'geometries-first3-v1.json').read_text())+json.loads((H/'geometries-003-005-v1.json').read_text())
muzzles={0:(43,23),1:(99,99),2:(0,0),3:(99,99),4:(46,15),5:(49,24)}
for c in cs:
 mx,my=muzzles[c['frame']]
 c['material_labels']=[0 if not i else 5 if q in c['flat_shadow']else 4 if i==15 else 3 if i in [1,2,3]or(i in [9,10]and q%c['width']>=mx and q//c['width']>=my)else 2 if i in [11,12,13]else 1 for q,i in enumerate(c['indices'])]
 c['materials']={name:source_contours(c['material_labels'],c['width'],c['height'],lambda x,i=i:x==i)for i,name in [(1,'fur'),(2,'hide'),(3,'bone'),(4,'eye')]if i in c['material_labels']}
 c['material_review']='Originalen deler graaindeks9/10 mellom pels og munnparti. Bare det visuelt kontrollerte nedre ansiktsfeltet faar munnmateriale. Graa pelsflekker bruker fotografiets svarte pels. Originalform og alle gjennomsiktige aapninger beholdes.'
 c['reviewed_muzzle_min_xy']=[mx,my]
p=H/'geometries-six-v3.json';b=json.dumps(cs,indent=2)+'\n'
if p.exists():assert p.read_text()==b,'Ikke overskriv en endret frosset geometri'
else:p.write_text(b)
print('Seks originalbundne materialfordelinger stemmer.')
