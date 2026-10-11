#!/usr/bin/env python3
"""Koble tre motivrettede landemerker til hele originalutsnittet."""
import json
from pathlib import Path
import moonfiles as mf
import hd_ikoner_bygg as kontur

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT/'art/faithful-hd-icons-2026-10-11'


def main():
    game = mf.Spill(str(ROOT/'Moonstonecd32-AMIGA.zip'))
    data = game.les('test')
    planes, pal, bp = mf.piv_alle(data)[0][8]
    pixels = mf.plan_til_indeks(bp, planes)
    palette = [mf.amiga_rgb(c) for c in pal]
    icons = json.loads((ART/'raster-icons.json').read_text())
    assets = json.loads((ART/'assets.json').read_text())
    kontur.ART = ART
    for ident, number, rect, source_name in [
        ('tower', 1, [215, 8, 225, 36], 'tower1'),
        ('valley', 2, [140, 84, 180, 119], 'valley'),
        ('stonehenge', 3, [84, 146, 113, 173], 'stonehenge'),
    ]:
        x0, y0, x1, y1 = rect
        w, h = x1-x0, y1-y0
        px = [pixels[y*320+x] for y in range(y0,y1) for x in range(x0,x1)]
        key = f'map-landmarks/{number:03}'
        meta = kontur.make_entry(key, px, w, h, palette,
            dict(file='test', frame=8, bank_sha256=kontur.sha(data), rect=rect),
            scene='world-map', rect=rect, opaque=True)
        meta['render_mode'] = 'raster'
        meta['reference_palette'] = {str(c): palette[c] for c in set(px)}
        if ident == 'valley':
            meta['reference_palette_cycles'] = [[21,22,23,24]]
            for c in [21,22,23,24]:
                meta['reference_palette'][str(c)] = palette[c]
        if ident != 'tower':
            meta['edge_feather'] = [3/w, 3/h]
        icons['entries'] = [m for m in icons['entries'] if m['key'] != key] + [meta]
        a = next(a for a in assets['assets'] if a['key'] == key)
        a.update(raw=f'semantic-correction/{ident}.png',
                 source=f'references/landmark-crops/{source_name}.png',
                 placement='full_rect', review_status='reviewed_for_runtime',
                 review_note='Motiv kontrollert mot brukerens retting, hele originalutsnitt og manual. Troskap i plassering og motiv; ikke pikselidentisk.')
    icons['entries'].sort(key=lambda m:m['key'])
    (ART/'raster-icons.json').write_text(json.dumps(icons,separators=(',',':'))+'\n')
    (ART/'assets.json').write_text(json.dumps(assets,indent=2,ensure_ascii=False)+'\n')
    print('Tre motivrettede landemerker klargjort.')


if __name__ == '__main__':
    main()
