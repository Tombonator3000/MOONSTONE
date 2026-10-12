#!/usr/bin/env python3
"""Pakk generert blodmateriale i TROLL2/015s fire eksakte kildepiksler."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

from PIL import Image
from contours import source_contours

ART = Path(__file__).resolve().parent
FIGURES = ART.parent
ROOT = FIGURES.parents[1]
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('record', type=Path)
    a = p.parse_args()
    a.record = a.record.resolve()
    old = json.loads(a.record.read_text())
    assert old['key'] == 'TROLL2.CEL/015.png'
    base = a.record.parent / 'candidate.png'
    assert sha(base) == old['candidate_sha256']
    im = Image.open(base).convert('RGBA')
    before = im.copy()
    q = json.loads((FIGURES / 'queue.json').read_text())
    route = next(r for r in q['entries'] if r['key'] == old['key'])
    packed = Image.open(FIGURES / route['packed_original']['path'])
    bits = [1 << n for n in range(5) if route['plane_mask'] & (1 << n)]
    ix = [sum(bit for n, bit in enumerate(bits) if v & (1 << n)) for v in packed.get_flattened_data()]
    points = [(x, y) for y in range(packed.height) for x in range(packed.width) if ix[y * packed.width + x] == 14]
    assert points == [(24, 8), (24, 9), (27, 10), (28, 10)]

    is_red = lambda c: c[0] > 10 and c[0] > c[1] * 1.3 and c[0] > c[2] * 1.15 and c[3] > 128
    red = [(x, y) for y in range(im.height) for x in range(im.width) if is_red(im.getpixel((x, y)))]
    assert red
    box = (min(x for x, y in red), min(y for x, y in red), max(x for x, y in red) + 1, max(y for x, y in red) + 1)
    assert box[0] >= 20 * 4 and box[2] <= 33 * 4 and box[1] >= 6 * 4 and box[3] <= 14 * 4, box
    material = im.crop(box).resize((5 * 4, 3 * 4), Image.Resampling.LANCZOS)
    red_material = [(x, y) for y in range(material.height) for x in range(material.width) if is_red(material.getpixel((x, y)))]
    assert red_material
    fill_box = (box[0] - 3, box[1] - 3, box[2] + 3, box[3] + 3)
    patch = old['eye_source_binding']['generated_eyeless_skin_patch']
    skin_path = ROOT / patch['raw']
    assert sha(skin_path) == patch['raw_sha256']
    assert sha(ROOT / patch['prompt']) == patch['prompt_sha256']
    skin = Image.open(skin_path).convert('RGBA').resize(im.size, Image.Resampling.LANCZOS)
    aff = old['global_affine']
    sx, sy, dx, dy = [aff[k] for k in ['scale_x', 'scale_y', 'translate_x_px', 'translate_y_px']]
    skin = skin.transform(im.size, Image.Transform.AFFINE, (1 / sx, 0, -dx / sx, 0, 1 / sy, -dy / sy), Image.Resampling.BICUBIC)
    for y in range(fill_box[1], fill_box[3]):
        for x in range(fill_box[0], fill_box[2]):
            weight = min(1, min(x - fill_box[0] + 1, fill_box[2] - x, y - fill_box[1] + 1, fill_box[3] - y) / 2)
            a0, b0 = before.getpixel((x, y)), skin.getpixel((x, y))
            im.putpixel((x, y), tuple(round(a0[k] * (1 - weight) + b0[k] * weight) for k in range(3)) + (a0[3],))

    out = a.record.parent / 'source-blood-v1-photo-skin'
    out.mkdir(exist_ok=True)
    source_bits = [255 if (x, y) in points else 0 for y in range(packed.height) for x in range(packed.width)]
    shape = source_contours(source_bits, packed.width, packed.height, lambda v: v > 0)
    svg = out / 'blood.svg'
    svg.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{im.width}" height="{im.height}" viewBox="0 0 {packed.width} {packed.height}"><path d="{shape}" fill="white"/></svg>\n')
    node = os.environ.get('NODE', '/home/tombonator3000t/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node')
    env = os.environ.copy()
    env.setdefault('NODE_PATH', '/home/tombonator3000t/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules')
    subprocess.run([node, str(ART / 'mask.cjs'), str(svg), str(out / 'blood-mask.png'), str(im.width), str(im.height)], env=env, check=True)
    mask = Image.open(out / 'blood-mask.png').getchannel('A')
    mapping = []
    for x, y in points:
        for dy in range(4):
            for dx in range(4):
                xx, yy = x * 4 + dx, y * 4 + dy
                weight = mask.getpixel((xx, yy)) / 255
                if weight:
                    u, v = (x - 24) * 4 + dx, (y - 8) * 4 + dy
                    # Kantens blaa blandingspiksler erstattes med naermeste
                    # faktiske genererte roede fotomateriale, aldri kilde-RGB.
                    if not is_red(material.getpixel((u, v))):
                        u, v = min(red_material, key=lambda xy: (xy[0] - u) ** 2 + (xy[1] - v) ** 2)
                    a0, b0 = im.getpixel((xx, yy)), material.getpixel((u, v))
                    im.putpixel((xx, yy), tuple(round(a0[k] * (1 - weight) + b0[k] * weight) for k in range(3)) + (a0[3],))
                    mapping.append([xx, yy, u, v])
    assert im.getchannel('A').tobytes() == before.getchannel('A').tobytes()
    outside = [(x, y) for y in range(im.height) for x in range(im.width) if is_red(im.getpixel((x, y))) and mask.getpixel((x, y)) == 0]
    assert not outside, outside
    assert all(is_red(im.getpixel((x * 4 + 2, y * 4 + 2))) for x, y in points)
    target = out / 'candidate.png'
    im.save(target, optimize=True)
    record = dict(old)
    record['candidate_sha256'] = sha(target)
    record['packing'] += ' Generert blodfotomateriale pakkes bare i originalens fire indeks14-piksler. Utenfor denne kildekonturen fylles det gamle genererte blodfeltet med den separat genererte blaa hudlappen. Alfa og oevrige piksler beholdes.'
    record['blood_source_binding'] = dict(source_index=14, source_pixels=points, generated_material_crop=list(box), source_contour_mask_sha256=sha(out / 'blood-mask.png'), material_map=mapping, old_blood_skin_fill_box=list(fill_box), red_pixels_outside_source_contour=outside, alpha_unchanged=True)
    record['source_blood_material'] = dict(patch, used_region=list(fill_box), method='Separat generert blaa hud fyller bare det gamle blodfeltet; generert roedt fotomateriale brukes bare inne i originalens fire kildepiksler.')
    (out / 'art-record.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(dict(path=str(out.relative_to(ROOT)), sha256=sha(target), source_blood_pixels=points)))


if __name__ == '__main__':
    main()
