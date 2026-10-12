#!/usr/bin/env python3
"""Pakk separat generert blodoverflate innen én original effektkontur."""
import argparse
from collections import defaultdict, deque
import hashlib
import json
import os
from pathlib import Path
import subprocess

from PIL import Image, ImageDraw

ART = Path(__file__).resolve().parent
FIGURES = ART.parent
ROOT = FIGURES.parents[1]
sha = lambda data: hashlib.sha256(data).hexdigest()


def effect_contours(indices, width, height):
    """Foelg kildecellenes ytterkant med liten avrunding av hvert hjoerne."""
    edges = defaultdict(list)
    def opaque(x, y):
        return 0 <= x < width and 0 <= y < height and indices[y * width + x] == 15
    for y in range(height):
        for x in range(width):
            if not opaque(x, y):
                continue
            for neighbor, a, b in [((x, y - 1), (x, y), (x + 1, y)), ((x + 1, y), (x + 1, y), (x + 1, y + 1)), ((x, y + 1), (x + 1, y + 1), (x, y + 1)), ((x - 1, y), (x, y + 1), (x, y))]:
                if not opaque(*neighbor):
                    edges[a].append(b)
    paths = []
    while edges:
        start = point = next(iter(edges))
        points = []
        while True:
            points.append(point)
            following = edges[point].pop()
            if not edges[point]:
                del edges[point]
            point = following
            if point == start:
                break
        corners = []
        for i, b in enumerate(points):
            a, c = points[i - 1], points[(i + 1) % len(points)]
            if (b[0] - a[0]) * (c[1] - b[1]) != (b[1] - a[1]) * (c[0] - b[0]):
                corners.append(b)
        joins = []
        for i, b in enumerate(corners):
            def near(a):
                dx, dy = a[0] - b[0], a[1] - b[1]
                length = (dx * dx + dy * dy) ** .5
                fraction = min(.2, length * .45) / length
                return b[0] + dx * fraction, b[1] + dy * fraction
            joins.append((near(corners[i - 1]), b, near(corners[(i + 1) % len(corners)])))
        p = joins[-1][2]
        path = f'M{p[0]} {p[1]}'
        for a, b, c in joins:
            path += f'L{a[0]} {a[1]}Q{b[0]} {b[1]} {c[0]} {c[1]}'
        paths.append(path + 'Z')
    return ''.join(paths)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--key', required=True)
    parser.add_argument('--raw', type=Path, required=True)
    parser.add_argument('--prompt', type=Path, required=True)
    args = parser.parse_args()
    assert args.key.startswith('Balok3.CEL/') and 8 <= int(args.key[-7:-4]) < 60, 'Bare resterende Balok3-ruter; kildeindeks0/15 kontrolleres nedenfor'
    rejected = args.raw.with_name(args.raw.stem + '-rejected.json')
    assert not rejected.exists(), 'Avvist råbilde forblir negativt referansemateriale'
    raw_sha = sha(args.raw.read_bytes())
    for path in (ART / 'bound').glob('Balok*.CEL/*/*/source-bound-blood-surface-*/art-record.json'):
        previous = json.loads(path.read_text())
        assert previous['key'] == args.key or previous['raw_sha256'] != raw_sha, 'Hver effekt krever egen generering'
    queue_bytes = (FIGURES / 'queue.json').read_bytes()
    row = next(r for r in json.loads(queue_bytes)['entries'] if r['key'] == args.key)
    palette_path = FIGURES / 'palettes/cases/balok.json'
    palette = json.loads(palette_path.read_text())
    reference = next(r for r in palette['references'] if r['key'] == args.key)
    assert reference['source_indices_sha256'] == row['indices_sha256']
    assert palette['colors'][15] == [204, 0, 0]
    packed = Image.open(FIGURES / row['packed_original']['path'])
    bits = [1 << n for n in range(5) if row['plane_mask'] & (1 << n)]
    indices = [sum(bit for n, bit in enumerate(bits) if v & (1 << n)) for v in packed.getdata()]
    assert set(indices) == {0, 15}
    original = Image.open(FIGURES / 'palettes' / reference['original']).convert('RGBA')
    assert original.size == (row['width'], row['height'])
    raw = Image.open(args.raw).convert('RGBA')
    assert raw.width >= row['target_width'] and raw.height >= row['target_height']
    output = ART / 'bound' / row['bank'] / f"{row['frame']:03}" / sha(args.raw.read_bytes())[:16] / 'source-bound-blood-surface-v3'
    assert not output.exists(), 'Frosne kandidater overskrives ikke'
    output.mkdir(parents=True)
    target_size = row['target_width'], row['target_height']
    # Smale effekter kan komme med store transparente raabilderander.
    # Tilpass materialets faktiske utsnitt til kildens faktiske utsnitt,
    # uten rotasjon, ny form eller gjenbruk fra en annen effekt.
    raw_box = raw.getchannel('A').point(lambda v: 255 if v >= 128 else 0).getbbox()
    source_box = original.getchannel('A').getbbox()
    assert raw_box and source_box
    target_box = tuple(v * 4 for v in source_box)
    material = Image.new('RGBA', target_size)
    fitted = raw.crop(raw_box).resize((target_box[2] - target_box[0], target_box[3] - target_box[1]), Image.Resampling.LANCZOS)
    material.paste(fitted, target_box[:2])
    shape = effect_contours(indices, original.width, original.height)
    svg = output / 'alpha.svg'
    svg.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{target_size[0]}" height="{target_size[1]}" viewBox="0 0 {original.width} {original.height}"><path d="{shape}" fill="white" fill-rule="evenodd"/></svg>\n')
    node = '/home/tombonator3000t/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node'
    env = os.environ.copy()
    env.setdefault('NODE_PATH', '/home/tombonator3000t/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules')
    subprocess.run([node, str(ART / 'mask.cjs'), str(svg), str(output / 'alpha.png'), *map(str, target_size)], env=env, check=True)
    alpha = Image.open(output / 'alpha.png').getchannel('A')
    pixels, generated_alpha = material.load(), material.getchannel('A').load()
    nearest, distance, pending = {}, {}, deque()
    for y in range(material.height):
        for x in range(material.width):
            if generated_alpha[x, y] >= 128:
                nearest[x, y], distance[x, y] = (x, y), 0
                pending.append((x, y))
    assert pending, 'Råbildet mangler opakt fotomateriale'
    while pending:
        x, y = pending.popleft()
        for xx, yy in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if 0 <= xx < material.width and 0 <= yy < material.height and (xx, yy) not in nearest:
                nearest[xx, yy], distance[xx, yy] = nearest[x, y], distance[x, y] + 1
                pending.append((xx, yy))
    result, extensions = Image.new('RGBA', target_size), []
    red_dominant = total = retained = 0
    for y in range(result.height):
        for x in range(result.width):
            opacity = alpha.getpixel((x, y))
            if not opacity:
                continue
            u, v = nearest[x, y]
            rgb = pixels[u, v][:3]
            result.putpixel((x, y), rgb + (opacity,))
            retained += (u, v) == (x, y)
            if (u, v) != (x, y):
                extensions.append(dict(x=x, y=y, from_x=u, from_y=v, distance=distance[x, y]))
            if opacity >= 128:
                total += 1
                red_dominant += rgb[0] >= rgb[1] and rgb[0] > rgb[2]
    assert red_dominant / total >= .90, 'Fotomaterialet må være blodrødt'
    missing, filled = [], []
    for y in range(original.height):
        for x in range(original.width):
            source = indices[y * original.width + x] == 15
            target = result.getpixel((x * 4 + 2, y * 4 + 2))[3] >= 128
            if source and not target:
                missing.append([x, y])
            if target and not source:
                filled.append([x, y])
    assert not missing and not filled
    expected = original.getchannel('A').resize(target_size, Image.Resampling.NEAREST).tobytes()
    actual = result.getchannel('A').tobytes()
    intersection = sum(a >= 128 and b >= 128 for a, b in zip(actual, expected))
    union = sum(a >= 128 or b >= 128 for a, b in zip(actual, expected))
    silhouette_iou = intersection / union
    assert silhouette_iou >= .90, 'Effektkonturen maa ogsaa bestaa den generiske silhuettporten'
    candidate = output / 'candidate.png'
    result.save(candidate, optimize=True)
    record = dict(key=args.key, candidate_sha256=sha(candidate.read_bytes()), source_indices_sha256=row['indices_sha256'], authoring_method='individual_redraw', generator='built-in ChatGPT image generator; exact model version not exposed', raw_file=str(args.raw.resolve().relative_to(ROOT)), raw_sha256=sha(args.raw.read_bytes()), prompt=str(args.prompt.resolve().relative_to(ROOT)), prompt_sha256=sha(args.prompt.read_bytes()), palette_case='balok', palette_contract_sha256=sha(palette_path.read_bytes()), palette_reference_sha256=reference['sha256'], queue_sha256=sha(queue_bytes), geometry_gate_passed=True, silhouette_iou=silhouette_iou, alpha_method='Kildecellers ytterkontur med0.2kildepiksel hjoerneavrunding, ikke diagonal marching-squares som tynner smaa effekter.', missing_opaque_source_midpoints=missing, false_filled_transparent_source_midpoints=filled, source_pixel_midpoints_checked=original.width * original.height, status='source_guided_candidate_not_activated', retained_generated_rgb_pixels=retained, extended_edge_pixels=len(extensions), edge_extension_map=extensions, max_edge_extension_px=max((v['distance'] for v in extensions), default=0), material_canvas_mapping=dict(raw_opaque_bbox=list(raw_box),source_opaque_bbox=list(source_box),target_bbox=list(target_box),mapping='Eget raabildes opake utsnitt skaleres til originalens opake utsnitt uten rotasjon; full kildeform og tomme marger beholdes.'), packing='Egen separat generering av blodoverflate for denne effekten. Bare generert RGB brukes innen originalens eksakte 0/15-kontur med avrundet rand. Nærmeste opake genererte blodmateriale fyller små manglende kantfelt. Kilden gir plassering og form, ingen original RGB kopieres. Ingen anatomisk nytegning påstås for ensfarget effekt; dette er fotografisk overflate i kildeform. Råsilhuettens anatomiske IoU-port brukes ikke for ensfargede væskeeffekter. Alle originale pikselmidtpunkter kontrolleres.', effect_source_contract=dict(source_indices=[0, 15], fixed_palette_index=15, fixed_palette_word='c00', original_bank_sha256=row['source_bank']['sha256'], independent_generated_surface=True, original_contour_only=True, anatomical_redraw_claimed=False, reused_texture=False, raw_shape_is_qa_gate=False), visual_checks={k:'pending' for k in ['pose','crop','equipment','source_colors','anatomy','material','runtime_overlap','original_hd_return']})
    (output / 'art-record.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
    sheet = Image.new('RGB', (780, 350), '#ddd')
    draw = ImageDraw.Draw(sheet)
    for x, title, image in [(10, 'Original', original), (270, 'Eget generert materiale', raw), (530, 'Kildebundet effekt', result)]:
        draw.text((x, 8), title, fill='black')
        factor = min(240 / image.width, 310 / image.height)
        image = image.resize((max(1, round(image.width * factor)), max(1, round(image.height * factor))), Image.Resampling.NEAREST if x == 10 else Image.Resampling.LANCZOS)
        sheet.paste(image, (x, 30), image)
    sheet.save(output / 'comparison.png')
    print(json.dumps(dict(key=args.key, path=str(output.relative_to(ROOT)), sha256=record['candidate_sha256'], source_midpoint_errors=0, red_dominant_fraction=red_dominant / total, status=record['status'])))


if __name__ == '__main__':
    main()
