#!/usr/bin/env python3
"""Tegn HD-glyfer fra lisensierte konturfonter med originalens mål og rutekart."""
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import moonfiles as mf

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / 'art/hd-text-2026-10-11'
SCALE = 6


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    game = mf.Spill(str(ROOT / 'Moonstonecd32-AMIGA.zip'))
    manifest = {'schema': 1, 'scale': SCALE, 'banks': {}, 'glyphs': []}
    characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!?.,#$% '
    characters += "'_"
    previews = []
    for name, face in [('bold.f', 'UncialAntiqua-Regular.ttf'), ('Small.font', 'IMFellEnglish-Regular.ttf')]:
        data = game.les(name)
        frames, _ = mf.cel_les(data)
        manifest['banks'][name.lower()] = sha(data)
        for i, g in enumerate(frames):
            if i >= len(characters):
                continue  # Logoen leveres separat; ukjente spesialbilder beholdes.
            char = characters[i]
            if name == 'Small.font' and 26 <= i < 52:
                char = char.upper()
            w, h = g['bredde'], g['hoyde']
            indices = mf.plan_til_indeks(g['data'], g['plan'], w, h)
            used = [p for p, v in enumerate(indices) if v and (name != 'bold.f' or v != 5)]
            if not used:
                continue  # Mellomrom og tomruter skal fortsatt være tomme.
            bounds = [min(p % w for p in used), min(p // w for p in used),
                      max(p % w for p in used) + 1, max(p // w for p in used) + 1]
            x0, y0, x1, y1 = (v * SCALE for v in bounds)
            font = ImageFont.truetype(str(ART / 'fonts' / face), h * SCALE * 3)
            box = font.getbbox(char)
            mask = Image.new('L', (box[2] - box[0] + 4, box[3] - box[1] + 4))
            ImageDraw.Draw(mask).text((2 - box[0], 2 - box[1]), char, font=font, fill=255)
            mask = mask.crop(mask.getbbox()).resize((x1 - x0, y1 - y0), Image.Resampling.LANCZOS)
            alpha = Image.new('L', (w * SCALE, h * SCALE))
            alpha.paste(mask, (x0, y0))
            image = Image.new('RGBA', alpha.size)
            colors = image.load()
            for y in range(image.height):
                t = min(1, max(0, (y - y0) / max(1, y1 - y0 - 1)))
                if name == 'bold.f':
                    rgb = tuple(round(a + (b - a) * t) for a, b in zip((255, 246, 211), (172, 112, 34)))
                else:
                    rgb = (255, 246, 216)
                for x in range(image.width):
                    colors[x, y] = (*rgb, alpha.getpixel((x, y)))
            rel = name.lower() + '/' + str(i).zfill(3) + '.png'
            target = ROOT / 'web/hd' / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            image.save(target)
            manifest['glyphs'].append({'file': name.lower(), 'frame': i, 'character': char,
                                      'width': w, 'height': h, 'path': rel,
                                      'sha256': sha(target.read_bytes()), 'source_ink_rect': bounds})
            previews.append((name, i, char, image))
    ART.mkdir(parents=True, exist_ok=True)
    logo = ART / 'candidates/logo-v2.png'
    if logo.is_file():
        import shutil
        target = ROOT / 'web/hd/bold.f/073.png'
        shutil.copyfile(logo, target)
        manifest['glyphs'].append({'file': 'bold.f', 'frame': 73,
            'character': 'Moonstone / A Hard Days Knight', 'width': 304, 'height': 52,
            'path': 'bold.f/073.png', 'raw_rect_px': [0, 172, 2172, 422],
            'alpha_cutoff': 0.15, 'sha256': sha(target.read_bytes()),
            # logo-v2 er 5,15:1, kilden 5,65:1. Fyll bredden uten aa strekke (render.js).
            'fit': 'width'})
    (ROOT / 'web/hd/text.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    (ART / 'glyphs.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    sheet = Image.new('RGB', (1080, ((len(previews) + 11) // 12) * 158), '#18232a')
    draw = ImageDraw.Draw(sheet)
    for n, (bank, index, char, image) in enumerate(previews):
        x, y = (n % 12) * 90, (n // 12) * 158
        draw.text((x + 3, y + 3), str(index) + ' ' + char, fill='white')
        image.thumbnail((84, 130))
        sheet.paste(image, (x + 3, y + 23), image)
    sheet.save(ART / 'glyph-preview.png')
    package_path = ROOT / 'web/hd/manifest.json'
    package = json.loads(package_path.read_text())
    new_paths = {g['path'] for g in manifest['glyphs']} | {'text.json'}
    package['files'] = [f for f in package['files'] if f['path'] not in new_paths]
    for rel in sorted(new_paths):
        p = ROOT / 'web/hd' / rel
        package['files'].append({'path': rel, 'sha256': sha(p.read_bytes()), 'bytes': p.stat().st_size, 'kind': 'base'})
    package['images'] = sum(f['path'].endswith('.png') for f in package['files'])
    package_path.write_text(json.dumps(package, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'glyphs': len(manifest['glyphs']), 'banks': manifest['banks']}))


if __name__ == '__main__':
    main()
