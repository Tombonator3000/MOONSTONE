#!/usr/bin/env python3
"""Bygg separat HD-fontkandidat fra originalens faktiske bokstavkonturer.

Ingen font erstattes med en annen skrifttype. Dette er kildebasert 8x
kantutjevning, ikke fotografisk nytegning. Kandidaten aktiveres ikke her.
"""
import hashlib
import json
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw
import hd_ikoner_bygg as kontur
from hd_ui_bygg import ui_contours
import moonfiles as mf

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT/'art/hd-faithful-text-2026-10-11'
SCALE = 8
CHARS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!?.,#$% '+"'_"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def rect(px, w, accept):
    points = [i for i, c in enumerate(px) if accept(c)]
    if not points:
        return None
    return [min(i % w for i in points), min(i // w for i in points),
            max(i % w for i in points)+1, max(i // w for i in points)+1]


def previews():
    data = json.loads((ART/'fragment-text.json').read_text())
    glyphs = {f'{g["file"]}/{g["frame"]:03}': g for g in data['glyphs']}
    char_index = {c: i for i, c in enumerate(CHARS)}

    def word(text, bank, kind, scale):
        parts, x = [], 0
        h = 19 if bank == 'bold.f' else 6
        for char in text:
            frame = char_index[char]
            meta = glyphs.get(f'{bank}/{frame:03}')
            w = meta['width'] if meta else (15 if bank == 'bold.f' else 5)
            if meta:
                image = Image.open(ART/kind/meta['path'])
                image = image.resize((w*scale, h*scale), Image.Resampling.LANCZOS if kind == 'packed' else Image.Resampling.NEAREST)
                parts.append((x, image))
            x += (w-3 if bank == 'bold.f' else w)*scale
        output = Image.new('RGBA', (max(x, max((xx+im.width for xx, im in parts), default=0)), h*scale))
        for xx, image in parts:
            output.alpha_composite(image, (xx, 0))
        return output

    samples = [('bold.f', 'Prepare yourself, for the'), ('bold.f', 'season of the Moonstones is'),
               ('bold.f', 'upon you!'), ('bold.f', 'Players 1   Gore On'),
               ('bold.f', 'Practice   Select Knight'), ('bold.f', 'Loading...'),
               ('small.font', 'SIR GODBER'), ('small.font', 'STR I  GOLD IO  HIT 20 20')]
    sheet = Image.new('RGB', (1500, 1900), '#171c25')
    draw, y = ImageDraw.Draw(sheet), 12
    for bank, line in samples:
        draw.text((12, y), bank+'  '+line+'  Original ovenfor / kandidat nedenfor', fill='white')
        y += 18
        for kind in ('references', 'packed'):
            image = word(line, bank, kind, 4 if bank == 'bold.f' else 7)
            sheet.paste(image, (12, y), image)
            y += image.height+7
        y += 16
    sheet.crop((0, 0, 1500, y)).save(ART/'comparison.png')
    for bank in ('bold.f', 'small.font'):
        selected = [g for g in data['glyphs'] if g['file'] == bank and g['frame'] < 73]
        columns, cell_width = 8, 255
        row_height = 200 if bank == 'bold.f' else 130
        image = Image.new('RGB', (columns*cell_width, math.ceil(len(selected)/columns)*row_height), '#171c25')
        draw = ImageDraw.Draw(image)
        for n, meta in enumerate(selected):
            x, y = (n % columns)*cell_width, (n // columns)*row_height
            draw.text((x+4, y+4), str(meta['frame'])+' '+meta['character']+'  Original | HD', fill='white')
            for j, kind in enumerate(('references', 'packed')):
                glyph = Image.open(ART/kind/meta['path'])
                scale = 5 if bank == 'bold.f' else 10
                glyph = glyph.resize((meta['width']*scale, meta['height']*scale), Image.Resampling.LANCZOS if kind == 'packed' else Image.Resampling.NEAREST)
                image.paste(glyph, (x+4+j*124, y+27), glyph)
        image.save(ART/(bank+'-comparison.png'))
    for frame in (74, 75):
        original = Image.open(ART/'references'/f'bold.f/{frame:03}.png')
        packed = Image.open(ART/'packed'/f'bold.f/{frame:03}.png')
        image = Image.new('RGB', (original.width+20, original.height*2+66), '#171c25')
        draw = ImageDraw.Draw(image)
        draw.text((10, 4), 'Original '+str(frame), fill='white')
        image.paste(original, (10, 23), original)
        draw.text((10, original.height+27), 'Kandidat '+str(frame), fill='white')
        image.paste(packed, (10, original.height+46), packed)
        image.save(ART/f'copyright-{frame:03}-comparison.png')


def main():
    ART.mkdir(parents=True, exist_ok=True)
    kontur.ART = ART
    kontur.contours = ui_contours
    game = mf.Spill(str(ROOT/'Moonstonecd32-AMIGA.zip'))
    _, rawpal, _ = mf.piv_alle(game.les('ch.piv'))[0][0]
    title_palette = [mf.amiga_rgb(c) for c in rawpal]
    entries, contracts, glyphs, banks = [], [], [], {}
    references = []
    for bank in ('bold.f', 'small.font'):
        raw = game.les(bank)
        banks[bank] = sha(raw)
        frames, _ = mf.cel_les(raw)
        for frame, source in enumerate(frames):
            if frame == 73 or frame > 75:
                continue  # Moonstone-logoen leveres av en egen arbeidspakke.
            w, h = source['bredde'], source['hoyde']
            packed = mf.plan_til_indeks(source['data'], source['plan'], w, h)
            bits = [1 << b for b in range(5) if source['maske'] & (1 << b)]
            px = [sum(bit for p, bit in enumerate(bits) if v & (1 << p)) for v in packed]
            if not any(px):
                continue  # Mellomrom og originalens tomruter forblir tomme.
            palette = [list(rgb) for rgb in title_palette]
            if bank == 'small.font':
                palette[1] = [255, 246, 216]
            key = f'{bank}/{frame:03}'
            identity = dict(file=bank, frame=frame, bank_sha256=banks[bank])
            entry = kontur.make_entry(key, px, w, h, palette, identity,
                                      plane_mask=source['maske'])
            if bank == 'bold.f':
                # Separate fargeflater maa ikke etterlate svarte soemmer mellom
                # gullnyansene. En sammenhengende gullbase ligger bare innenfor
                # den originale gullformen, over den originale svarte skyggen.
                face = ui_contours(px, w, h, lambda c: c not in (0, 5))
                colors = [c for c in sorted(set(px)) if c not in (0, 5)]
                base = max(colors, key=px.count)
                svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w*SCALE}" height="{h*SCALE}" viewBox="0 0 {w} {h}">',
                       '<defs><clipPath id="face"><path d="'+face+'" clip-rule="evenodd"/></clipPath></defs>',
                       '<path d="'+entry['clip']+'" fill="black" fill-rule="evenodd"/>',
                       '<g clip-path="url(#face)">',
                       '<path d="'+face+'" fill="rgb('+','.join(map(str, palette[base]))+')" fill-rule="evenodd"/>']
                for color in colors:
                    path = ui_contours(px, w, h, lambda c: c == color)
                    svg.append('<path d="'+path+'" fill="rgb('+','.join(map(str, palette[color]))+')" fill-rule="evenodd"/>')
                svg += ['</g></svg>']
                (ART/'svg'/f'{key}.svg').write_text('\n'.join(svg)+'\n')
            entries.append(entry)
            char = CHARS[frame] if frame < len(CHARS) else 'Originalt opphavsrettsfelt'
            if bank == 'small.font' and 26 <= frame < 52:
                char = char.upper()
            ink = rect(px, w, lambda c: c != 0 and (bank != 'bold.f' or c != 5))
            alpha_rect = rect(px, w, lambda c: c != 0)
            glyphs.append(dict(file=bank, frame=frame, character=char, width=w,
                               height=h, path=key+'.png', source_ink_rect=ink,
                               source_alpha_rect=alpha_rect,
                               method='original-source-contours', source_indices_sha256=sha(bytes(px))))
            contracts.append(dict(key=key, width=w, height=h, source=identity,
                                   plane_mask=source['maske'], expanded_plane_bits=bits,
                                   indices=px, indices_sha256=sha(bytes(px)), palette=palette,
                                   source_ink_rect=ink, source_alpha_rect=alpha_rect))
            original = Image.new('RGBA', (w, h))
            original.putdata([tuple(palette[c])+(255 if c else 0,) for c in px])
            target = ART/'references'/f'{key}.png'
            target.parent.mkdir(parents=True, exist_ok=True)
            original.resize((w*SCALE, h*SCALE), Image.Resampling.NEAREST).save(target)
            references.append((bank, frame, char, original))
    assert len(glyphs) == 144, f'Forventet 142 fontglyfer og to opphavsrettsfelt, fikk {len(glyphs)}'
    manifest = dict(schema=1, scale=SCALE, method='original-source-contours', banks=banks, glyphs=glyphs)
    (ART/'fragment-text.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n')
    (ART/'contours.json').write_text(json.dumps(dict(schema=1, entries=entries), ensure_ascii=False, indent=2)+'\n')
    contracts = dict(scope='Originale bokstavformer og gullflater. Kildebasert kantutjevning, ingen alternativ skrifttype eller fotografisk nytegning.',
                     original_zip_sha256=sha((ROOT/'Moonstonecd32-AMIGA.zip').read_bytes()),
                     banks=banks, scale=SCALE, entries=contracts,
                     color_policy=dict(bold='Originalpaletten i ch.piv, inkludert svarte skygger og gullindeksene 9..12.', small='Originalens monokrome form i kremfargen RGB255,246,216.'))
    (ART/'source-contracts.json').write_text(json.dumps(contracts, ensure_ascii=False, indent=2)+'\n')
    # Originalreferanser i full rutegeometri, uten trimming eller flyttede ankere.
    sheet = Image.new('RGB', (1200, 16*176), '#1b2228')
    draw = ImageDraw.Draw(sheet)
    for n, (bank, frame, char, image) in enumerate(references):
        if frame >= 74:
            continue
        x, y = (n % 12)*100, (n // 12)*176
        draw.text((x+2, y+2), f'{bank} {frame:03} {char}', fill='white')
        preview = image.resize((image.width*5, image.height*5), Image.Resampling.NEAREST)
        sheet.paste(preview, (x+2, y+24), preview)
    sheet.save(ART/'reference-sheet.png')
    print(json.dumps(dict(glyphs=len(glyphs), banks=banks, activation=False)))


if __name__ == '__main__':
    if '--preview-only' in sys.argv:
        previews()
    else:
        main()
