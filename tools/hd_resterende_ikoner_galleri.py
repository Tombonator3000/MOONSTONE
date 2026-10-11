#!/usr/bin/env python3
"""Lag diagnosegalleri fra ferdig pakkede ikoner. Endrer ingen spillbilder."""
import html
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / 'art/hd-remaining-icons-2026-10-11'
rows = json.loads((ART / 'packing-report.json').read_text())['assets']
out = ART / 'review'
out.mkdir(exist_ok=True)
font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 18)
for page in range((len(rows) + 7) // 8):
    sheet = Image.new('RGB', (1120, 1120), (27, 28, 28))
    draw = ImageDraw.Draw(sheet)
    for i, row in enumerate(rows[page * 8:page * 8 + 8]):
        x, y = i % 2 * 560, i // 2 * 280
        draw.text((x + 12, y + 8), row['key'] + ' ' + row['name'][:35], font=font, fill='white')
        for k, rel in enumerate([row['source'], 'packed/' + row['key'] + '.png']):
            im = Image.open(ART / rel).convert('RGBA')
            scale = min(250 / im.width, 210 / im.height)
            im = im.resize((round(im.width * scale), round(im.height * scale)),
                           Image.Resampling.NEAREST if k == 0 else Image.Resampling.LANCZOS)
            sheet.paste(im, (x + 10 + k * 275 + (250 - im.width) // 2,
                            y + 40 + (210 - im.height) // 2), im)
            draw.text((x + 10 + k * 275, y + 258), 'Original' if k == 0 else 'HD',
                      font=font, fill='#bcbcbc')
    sheet.save(out / f'contact-{page + 1:02}.png')

parts = ['<!doctype html><html lang="no"><meta charset="utf-8">',
         '<title>Moonstone: originale og HD-ikoner</title>',
         '<style>body{background:#1b1c1c;color:#eee;font:16px sans-serif;margin:2rem}',
         'section{display:inline-block;vertical-align:top;width:430px;padding:1rem;',
         'border:1px solid #555;margin:8px}img{object-fit:contain;width:200px;height:200px}',
         'a{color:#aaf}.source{image-rendering:pixelated}</style>',
         '<h1>Ikoner: original og HD</h1>',
         '<p>Kildebilder, urørt generering, prompt og pakkede spillbilder. ',
         'Figuranimasjon og tekst er egne arbeidsområder.</p>']
for row in rows:
    parts.append('<section><h2>' + html.escape(row['key'] + ' ' + row['name']) + '</h2>'
                 '<img class="source" src="' + row['source'] + '">'
                 '<img src="packed/' + row['key'] + '.png">'
                 '<p>Original til venstre, HD til høyre.</p>'
                 '<a href="' + row['raw'] + '">Urørt bilde</a> | '
                 '<a href="' + row['prompt'] + '">Prompt</a>')
    for variant in row.get('variants', []):
        parts.append('<p>' + html.escape(variant['id']) + '</p><img src="packed/' +
                     variant['key'] + '.png">')
    parts.append('</section>')
(ART / 'index.html').write_text(''.join(parts) + '</html>')
print(f'{len(rows)} kilde-/HD-par i {ART / "index.html"}')
