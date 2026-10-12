"""Pakk aatte egne genererte bevegelsesmaterialer i originalens separate kildefelt."""
from pathlib import Path
from collections import deque
import hashlib
import json
import os
import statistics
import subprocess
import sys
from PIL import Image, ImageDraw

H = Path(__file__).resolve().parent
P = H.parent
R = H.parents[4]
sys.path.insert(0, str(P.parent))
from effect_pack import effect_contours

sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
rows = [r for r in json.loads((P / 'sources-v1.json').read_text()) if r['bank'] == 'TROLL1.CEL' and r['frame'] in [36, 41, 42, 43, 44, 45, 46, 47]]
palette = rows[0]['palette']
result, qa = [], []
contact = Image.new('RGB', (1080, 800), '#ddd')
draw = ImageDraw.Draw(contact)
for n, row in enumerate(rows):
    number = '%03d' % row['frame']
    version = 'v2' if row['frame'] in [44, 45] else 'v1'
    generation_path = H / ('generation-' + number + '-' + version + '.json')
    generation = json.loads(generation_path.read_text())
    raw_path = P / generation['raw']
    assert sha(raw_path) == generation['raw_sha256']
    assert sha(P / generation['prompt']) == generation['prompt_sha256']
    raw = Image.open(raw_path).convert('RGBA')
    box = raw.getchannel('A').point(lambda a: 255 if a >= 128 else 0).getbbox()
    assert box
    w, h = row['width'], row['height']
    size = (w * 4, h * 4)
    material = raw.crop(box).resize(size, Image.Resampling.LANCZOS)
    target_dir = H / 'packed-v1' / number
    target_dir.mkdir(parents=True, exist_ok=True)
    # Hvert originalt ditherhull beholdes. Bare den skarpe cellekanten avrundes0.2kildepiksel.
    shape = effect_contours([15 if i else 0 for i in row['indices']], w, h)
    svg = target_dir / 'alpha.svg'
    svg.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{size[0]}" height="{size[1]}" viewBox="0 0 {w} {h}"><path d="{shape}" fill="white" fill-rule="evenodd"/></svg>\n')
    env = os.environ.copy()
    env.setdefault('NODE_PATH', '/home/tombonator3000t/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules')
    subprocess.run(['/home/tombonator3000t/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node', str(P.parent / 'mask.cjs'), str(svg), str(target_dir / 'alpha.png'), str(size[0]), str(size[1])], env=env, check=True, capture_output=True)
    alpha = Image.open(target_dir / 'alpha.png').getchannel('A')
    nearest, pending = {}, deque()
    for y in range(size[1]):
        for x in range(size[0]):
            if material.getpixel((x, y))[3] >= 128:
                nearest[x, y] = (x, y)
                pending.append((x, y))
    assert pending
    while pending:
        x, y = pending.popleft()
        for xx, yy in [(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)]:
            if 0 <= xx < size[0] and 0 <= yy < size[1] and (xx, yy) not in nearest:
                nearest[xx, yy] = nearest[x, y]
                pending.append((xx, yy))
    # Fast palett er fargefasit. Det nye bildet leverer optisk/trebasert lysvariasjon,
    # ikke en erstatning av den originale brune makrofargen med lysere honningtre.
    luminance = lambda rgb: .2126 * rgb[0] + .7152 * rgb[1] + .0722 * rgb[2]
    median = statistics.median(luminance(material.getpixel(xy)) for xy in set(nearest.values()))
    assert median > 0
    image = Image.new('RGBA', size)
    mapping = []
    for y in range(size[1]):
        for x in range(size[0]):
            a = alpha.getpixel((x, y))
            if not a:
                continue
            i = row['indices'][y // 4 * w + x // 4]
            if not i:
                # Avrundingen fyller aldri et originalt hull.
                continue
            u, v = nearest[x, y]
            gain = max(.80, min(1.20, luminance(material.getpixel((u, v))) / median))
            rgb = tuple(min(255, round(c * gain)) for c in palette[i][:3])
            image.putpixel((x, y), rgb + (a,))
            mapping.append([x, y, u, v, gain])
    for y in range(h):
        for x in range(w):
            assert (image.getpixel((x * 4 + 2, y * 4 + 2))[3] >= 128) == bool(row['indices'][y * w + x])
    target = target_dir / 'candidate.png'
    image.save(target, optimize=True)
    record = dict(key=row['key'], candidate_sha256=sha(target), source_indices_sha256=row['indices_sha256'], source_bank_sha256=row['source_bank_sha256'], authoring_method='individual_generated_photographic_motion_material', generator='builtin_image_gen', model='not_exposed_by_tool', raw_file=str(raw_path.relative_to(R)), raw_sha256=sha(raw_path), prompt=str((P / generation['prompt']).relative_to(R)), prompt_sha256=generation['prompt_sha256'], generation_record=str(generation_path.relative_to(R)), generation_record_sha256=sha(generation_path), source_palette_contract=row['source_palette_contract'], source_palette_contract_sha256=row['source_palette_contract_sha256'], geometry_gate_passed=True, source_pixel_midpoints_checked=w * h, missing_opaque_source_midpoints=[], false_filled_transparent_source_midpoints=[], original_indices=sorted(set(row['indices'])), original_dither_holes_retained=True, photographic_surface_only=True, anatomy_redraw_claimed=False, reused_texture=False, packing='Egen separat generering per originalt klubbebevegelsesspor. Generert opakt utsnitt skaleres til originalrutens utsnitt. Narmeste genererte optiske tremateriale gir lokal lysvariasjon; statisk original brun makropalett styrer fargen, med dokumentert0.80..1.20luminansgradering. Originalens alle ditherhull og midtpunkter beholdes. Ingen ny klubb eller anatomisk figur er laget.', raw_opaque_bbox=list(box), material_median_luminance=median, photographic_luminance_gain_limits=[.8, 1.2], material_map=mapping, status='source_guided_candidate_not_activated')
    art_path = target_dir / 'art-record.json'
    art_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
    row.update(number=number, needs_mask=False, packed_candidate_path=str(target.relative_to(R)))
    result.append(dict(key=row['key'], candidate=str(target.relative_to(R)), candidate_sha256=sha(target), art_record=str(art_path.relative_to(R)), art_record_sha256=sha(art_path), generation_record=str(generation_path.relative_to(R))))
    qa.append(dict(key=row['key'], source_midpoints=w * h, missing=0, falsely_filled_holes=0, separate_raw_sha256=sha(raw_path)))
    source = Image.new('RGBA', (w, h))
    source.putdata([tuple(palette[i][:3]) + (255 if i else 0,) for i in row['indices']])
    source = source.resize(size, Image.Resampling.NEAREST)
    x = (n % 2) * 540
    y = n // 2 * 200
    draw.text((x + 8, y + 4), row['key'] + ' original / eget materiale', fill='black')
    scale = min(1, 240 / image.width, 170 / image.height)
    tile_size = (max(1, round(image.width * scale)), max(1, round(image.height * scale)))
    for dx, tile in [(8, source), (278, image)]:
        tile = tile.resize(tile_size, Image.Resampling.LANCZOS)
        contact.paste(tile, (x + dx, y + 24), tile)
assert len({r['separate_raw_sha256'] for r in qa}) == 8
(H / 'geometries-v1.json').write_text(json.dumps(rows, indent=2) + '\n')
(H / 'candidates-v1.json').write_text(json.dumps(result, indent=2) + '\n')
(H / 'source-qa-v1.json').write_text(json.dumps(dict(status='passed', checks=sum(r['source_midpoints'] for r in qa), entries=qa), indent=2) + '\n')
contact.save(H / 'comparison-v1.png')
print(json.dumps(dict(routes=len(result), checks=sum(r['source_midpoints'] for r in qa), raw_reuse=False, activated=False)))
