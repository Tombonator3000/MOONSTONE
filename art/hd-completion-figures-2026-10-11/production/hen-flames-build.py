#!/usr/bin/env python3
"""Eksporter bare kildegeometrien for individuelt nytegnede flammer."""
import json
import sys
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
from hd_ui_bygg import ui_contours

ART = Path(__file__).resolve().parent.parent
rows = []
for n in range(7, 25):
    key = f'hen1.c/{n:03d}.png'
    row = json.loads((ART / 'routes' / key.replace('.png', '.json')).read_text())
    alpha = Image.open(ART / row['silhouette']['path']).convert('L')
    indices = list(alpha.get_flattened_data())
    packed = Image.open(ART / row['packed_original']['path'])
    original_indices = list(packed.get_flattened_data())
    palette = Image.open(ART / row['original']['path']).convert('RGB')
    base_regions = []
    for color in (19, 20, 21):
        if color in original_indices:
            first = original_indices.index(color)
            base_regions.append(dict(index=color, rgb=list(palette.getpixel((first % row['width'], first // row['width']))),
                clip=ui_contours(original_indices, row['width'], row['height'], lambda c, color=color: c == color)))
    rows.append(dict(key=key, n=f'{n:03d}', width=row['width'], height=row['height'],
                     alpha=indices, clip=ui_contours(indices, row['width'], row['height'], lambda c: c > 0),
                     preserved_dark_base=base_regions,
                     indices_sha256=row['indices_sha256']))
(ART / 'production/hen-flames-geometries.json').write_text(json.dumps(rows, separators=(',', ':')) + '\n')
