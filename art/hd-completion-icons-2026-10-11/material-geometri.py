"""Frys motivets materialregioner direkte fra de originale CEL-indeksene."""
import json
import sys
from pathlib import Path

ART = Path(__file__).resolve().parent
ROOT = ART.parent.parent
sys.path.insert(0, str(ROOT/'tools'))
from hd_ui_bygg import ui_contours


def material(c, index):
    r, g, b = c['palette'][index][:3]
    if c['source']['file'] == 'ki.cel':
        return 'leaf' if g > r*1.1 and g > b*1.05 else 'bark'
    if c['source']['file'] == 'dice.cel':
        return 'light' if (index != 15 if c['source']['frame'] == 1 else index == 3) else 'field'
    return 'photo'


def main():
    contracts = json.loads((ART/'source-contracts.json').read_text())
    entries = []
    for c in contracts['entries']:
        groups = {}
        for index in c['source_colors']:
            groups.setdefault(material(c, index), []).append(index)
        entries.append({'key': c['key'], 'groups': [
            {'material': name, 'source_indices': colors,
             'd': ui_contours(c['indices'], c['width'], c['height'], lambda i: i in colors)}
            for name, colors in groups.items()]})
    (ART/'material-geometries.json').write_text(json.dumps({'schema': 1, 'entries': entries}, indent=2)+'\n')


if __name__ == '__main__':
    main()
