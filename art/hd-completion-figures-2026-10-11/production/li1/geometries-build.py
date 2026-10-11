from pathlib import Path
import json,sys
from PIL import Image
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent))
from contours import source_contours
rows=[]
for c in json.loads((HERE/'source-contracts.json').read_text()):
 px=c['indices'];w,h=c['width'],c['height'];im=Image.new('L',(w,h));im.putdata([255 if i else 0 for i in px])
 rows.append({**c,'number':f"{c['frame']:03}",'source_alpha_bounds':im.getbbox(),'alpha_path':source_contours(px,w,h,lambda i:i!=0)})
(HERE/'geometries.json').write_text(json.dumps(rows,separators=(',',':'))+'\n')
