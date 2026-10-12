import sys,json,re
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'tools'))
from hd_ui_bygg import ui_contours
art=ROOT/'art/hd-completion-figures-2026-10-11';rows=[]
positions={6:[119,102],7:[119,102],8:[118,93],9:[122,90],10:[121,91],11:[116,88],12:[108,87],13:[105,92],14:[103,87],15:[99,84],16:[95,84],17:[92,86],18:[88,82],19:[85,82],20:[86,81],21:[82,82],22:[81,83]}
for n in range(6,23):
 r=json.loads((art/f'routes/dice.cel/{n:03}.json').read_text());im=Image.open(art/r['packed_original']['path']);idx=list(im.get_flattened_data());src=Image.open(art/r['original']['path']).convert('RGB');pal={v:list(src.getpixel((idx.index(v)%im.width,idx.index(v)//im.width))) for v in set(idx)}
 rows.append(dict(key=r['key'],n=f'{n:03}',width=im.width,height=im.height,indices=idx,palette=pal,source_indices_sha256=r['indices_sha256'],regions=[dict(index=v,clip=ui_contours(idx,im.width,im.height,lambda x,v=v:x==v)) for v in set(idx) if v],clip=ui_contours(idx,im.width,im.height,lambda x:x!=0),steel_clip=ui_contours(idx,im.width,im.height,lambda x:x in ((3,4,5,17) if n<8 else (3,4,5,9))),cloth_clip=ui_contours(idx,im.width,im.height,lambda x:n<8 and 6<=x<=10),has_cloth=n<8,background_xy=positions[n],position_authority='original0ad75e/0ad76e; actual dice-runtime.json trace'))
(art/'production/dice/geometries.json').write_text(json.dumps(rows,separators=(',',':'))+'\n')
