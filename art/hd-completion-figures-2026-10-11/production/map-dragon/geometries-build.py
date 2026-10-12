"""Kildekonturer for aatte separat genererte kartdrager; ingen nytegning i dette steget."""
import json
import sys
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'art/hd-completion-figures-2026-10-11/production'))
from contours import source_contours

ART = ROOT / 'art/hd-completion-figures-2026-10-11'
palette = json.loads((ART / 'source/palettes/map-runtime.json').read_text())['colors']
rows = []
for number in range(34, 42):
    route = json.loads((ART / f'routes/mi.c/{number:03}.json').read_text())
    image = Image.open(ART / route['packed_original']['path'])
    indices = list(image.get_flattened_data())
    groups = {'red': {28}, 'wing': {16, 17, 18, 19}, 'pale': {1, 2, 3, 4, 5, 6}}
    assert set(indices) <= {0}.union(*groups.values())
    rows.append(dict(key=route['key'], number=f'{number:03}', width=image.width,
                     height=image.height, indices=indices, palette=palette,
                     indices_sha256=route['indices_sha256'],
                     alpha_path=source_contours(indices,image.width,image.height,lambda value:value!=0),
                     materials={name: source_contours(indices, image.width, image.height,
                                                  lambda value, allowed=allowed: value in allowed)
                                for name, allowed in groups.items()}))
(Path(__file__).parent / 'geometries.json').write_text(json.dumps(rows, separators=(',', ':')) + '\n')
