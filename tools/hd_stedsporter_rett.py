#!/usr/bin/env python3
"""Koble Math og 23 Stonehenge-porter til uendrede kildemoenstre."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT/'art/faithful-hd-icons-2026-10-11'


def main():
    icons = json.loads((ART/'raster-icons.json').read_text())
    active = json.loads((ROOT/'web/hd/icons.json').read_text())
    assets = json.loads((ART/'assets.json').read_text())
    sample = json.loads((ROOT/'art/hd-icons-2026-10-11/source/map-frame2000.json').read_text())
    tower = next(a for a in assets['assets'] if a['key'] == 'map-landmarks/001')
    tower.update(raw='place-correction/tower.png',
                 review_note='Brukerretting: rundt tårn med loddrette vegger, balkong og lav brystning. Erstatter avvist kjegle.')
    for n in range(23):
        key = f'map-icons/{n:03}'
        meta = next(m.copy() for m in active['entries'] if m['key'] == key)
        assert (meta['width'], meta['height']) == (9, 5) and len(meta['expected']) == 45
        meta.pop('draw_rect', None)
        meta.update(render_mode='raster',
                    reference_palette={str(c): sample['palette'][c][:3]
                                       for c in {meta['base_index'], *(p['index'] for p in meta['paths'])}})
        icons['entries'] = [m for m in icons['entries'] if m['key'] != key] + [meta]
        assets['assets'] = [a for a in assets['assets'] if a['key'] != key] + [dict(
            id=f'stedsport-{n:03}', key=key, raw='place-correction/trilithon.png',
            source='place-correction/original-place-marker.png', placement='contain',
            review_status='reviewed_for_runtime',
            review_note='Brukerens foto: én Stonehenge-port med to oppreiste steiner og én overligger. Proporsjonal skalering innen originalens 9x5 kartpiksler, sentrert med samme fotpunkt. Åpen passasje og uendret kildemønster.')]
    icons['entries'].sort(key=lambda m:m['key'])
    assets['assets'].sort(key=lambda a:a['key'])
    (ART/'raster-icons.json').write_text(json.dumps(icons, ensure_ascii=False, separators=(',', ':'))+'\n')
    (ART/'assets.json').write_text(json.dumps(assets, ensure_ascii=False, indent=2)+'\n')
    print('Math og 23 Stonehenge-porter klargjort, kilderektangler og forventede originalpiksler bevart.')


if __name__ == '__main__':
    main()
