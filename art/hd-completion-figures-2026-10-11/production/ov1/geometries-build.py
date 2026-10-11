"""Kildeformer og bekreftet nattpalett for fire separate introforgrunner."""
from pathlib import Path
import json
import sys
from PIL import Image

ROOT = Path(__file__).resolve().parents[4]
ART = ROOT/'art/hd-completion-figures-2026-10-11'
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ART/'production'))
from contours import source_contours

proof = json.loads((HERE/'source/actual-intro-palette.json').read_text())
assert proof['status'] == 'passed' and proof['scan_valid']
assert len({json.dumps(p) for p in proof['palettes']}) == 1
palette = proof['palettes'][100]
rows = []
for number in range(4):
    route = json.loads((ART/f'routes/ov1.cel/{number:03}.json').read_text())
    image = Image.open(ART/route['packed_original']['path'])
    indices = list(image.get_flattened_data())
    available = {'stone': {19,20,21,22}, 'grass': {4,5,6,7}, 'ivy': {24,25,26,27}}
    assert set(indices) <= {0}.union(*available.values())
    groups = {name: allowed for name, allowed in available.items() if allowed.intersection(indices)}
    alpha = Image.new('L', image.size)
    alpha.putdata([255 if i else 0 for i in indices])
    rows.append(dict(key=route['key'], number=f'{number:03}', width=image.width, height=image.height,
                     indices=indices, palette=palette, indices_sha256=route['indices_sha256'],
                     source_alpha_bounds=alpha.getbbox(),
                     alpha_path=source_contours(indices,image.width,image.height,lambda value:value!=0),
                     materials={name: source_contours(indices,image.width,image.height,
                                                       lambda value,allowed=allowed:value in allowed)
                                for name,allowed in groups.items()}))
(HERE/'geometries.json').write_text(json.dumps(rows,separators=(',',':'))+'\n')
