#!/usr/bin/env python3
"""Frys kildeformer til bakgrunnspakking; genererer ikke fotografisk grafikk."""
import hashlib
import json
from pathlib import Path
import sys

from PIL import Image

import moonfiles as mf
from hd_ui_bygg import ui_contours

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / 'art/hd-completion-backgrounds-2026-10-11'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    game = mf.Spill(str(ROOT / 'Moonstonecd32-AMIGA.zip'))
    output = {'schema': 1, 'entries': []}
    for key, name, mode in [
        ('94c7f163', 'hen1.p', 'full_frame'),
        ('c2501c17', 'bg3.PIV', 'full_frame'),
        ('a45a2508', 'bg2a.PIV', 'full_frame'),
        ('46963198', 'mindscape', 'source_gold'),
        ('d0f67acb', 'bg8.PIV', 'source_stars'),
    ]:
        bank = game.les('data/' + name)
        planes, rawpal, bits = mf.piv_alle(bank)[0][0]
        px = mf.plan_til_indeks(bits, planes, 320, 200)
        palette = [mf.amiga_rgb(c) for c in rawpal]
        row = dict(key='bg/' + key, source_file=name, source_sha256=sha(bank),
                   indices_sha256=sha(bytes(px)), width=320, height=200,
                   output_width=1280, output_height=800, mode=mode,
                   raw='raw/' + key + '-v1.png', reference='references/' + key + '.png',
                   palette=palette)
        if mode == 'source_gold':
            row['clip'] = ui_contours(px, 320, 200, lambda c: 0 < c < 16)
            row['text_clip'] = ui_contours(px, 320, 200, lambda c: c >= 16)
            row['text_paths'] = [dict(index=c, d=ui_contours(px, 320, 200, lambda v: v == c))
                                 for c in sorted(set(px)) if c >= 16]
            row['indices'] = list(px)
        if mode == 'source_stars':
            mask = [c if y < 126 and c in (1, 24, 25, 26, 27)
                    and not (x >= 230 and y >= 80) and not (x < 40 and y >= 115)
                    else 0 for y in range(200) for x in range(320)
                    for c in [px[y * 320 + x]]]
            row['star_pixels'] = sum(bool(c) for c in mask)
            row['star_mask_sha256'] = sha(bytes(mask))
            row['star_indices'] = mask
            row['star_paths'] = [dict(index=c, d=ui_contours(mask, 320, 200, lambda v: v == c))
                                 for c in sorted(set(mask)) if c]
        output['entries'].append(row)

    source = ROOT / 'art/hd-completion-runtime-2026-10-11/references/intro-scroll.png'
    im = Image.open(source).convert('RGB')
    assert im.size == (320, 1200)
    colors = sorted(set(im.get_flattened_data()))
    values = list(im.get_flattened_data())
    # Maaneomraadet skal bruke ny maanetekstur. Bare originale stjerner ellers.
    mask = [colors.index(rgb) + 1 if y < 450 and (rgb[0] > 0 or rgb[1] > 0)
            and not (103 <= x < 218 and 53 <= y < 147) else 0
            for y in range(1200) for x in range(320) for rgb in [values[y * 320 + x]]]
    output['entries'].append(dict(
        key='bg/6b258d27', mode='scroll_stars', width=320, height=1200,
        output_width=1280, output_height=4800, raw='raw/intro-scroll-v1.png',
        reference=str(source.relative_to(ART)) if source.is_relative_to(ART) else '../hd-completion-runtime-2026-10-11/references/intro-scroll.png',
        source_sha256=sha(source.read_bytes()), palette=[[0, 0, 0]] + [list(c) for c in colors],
        star_pixels=sum(bool(c) for c in mask), star_mask_sha256=sha(bytes(mask)),
        star_indices=mask,
        star_paths=[dict(index=c, d=ui_contours(mask, 320, 1200, lambda v: v == c))
                    for c in sorted(set(mask)) if c]))
    source = ROOT / 'art/hd-completion-runtime-2026-10-11/references/ending-scroll.png'
    im = Image.open(source).convert('RGB')
    assert im.size == (320, 1200)
    colors = sorted(set(im.get_flattened_data()))
    values = list(im.get_flattened_data())
    mask = [colors.index(rgb) + 1 if y < 1149 and any(rgb) else 0
            for y in range(1200) for x in range(320) for rgb in [values[y * 320 + x]]]
    output['entries'].append(dict(
        key='bg/0df34a83', mode='ending_scroll_stars', width=320, height=1200,
        output_width=1280, output_height=4800, raw='raw/ending-scroll-v1.png',
        reference='../hd-completion-runtime-2026-10-11/references/ending-scroll.png',
        source_sha256=sha(source.read_bytes()), palette=[[0, 0, 0]] + [list(c) for c in colors],
        star_pixels=sum(bool(c) for c in mask), star_mask_sha256=sha(bytes(mask)),
        star_indices=mask,
        star_paths=[dict(index=c, d=ui_contours(mask, 320, 1200, lambda v: v == c))
                    for c in sorted(set(mask)) if c]))
    (ART / 'source-contracts.json').write_text(json.dumps(output, ensure_ascii=False, separators=(',', ':')) + '\n')
    print(json.dumps([dict(key=r['key'], mode=r['mode'], star_pixels=r.get('star_pixels'))
                      for r in output['entries']]))


if __name__ == '__main__':
    main()
