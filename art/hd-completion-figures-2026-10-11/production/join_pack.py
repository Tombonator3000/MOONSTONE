#!/usr/bin/env python3
"""Forbered og pakk fotomateriale i kildebekreftede fragmentskjoeter."""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image

ART = Path(__file__).resolve().parent
ROOT = ART.parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def freeze(path, value):
    data = (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()
    if path.exists():
        assert path.read_bytes() == data, path
    else:
        path.write_bytes(data)


def preview(image, path):
    enlarged = image.resize((image.width * 3, image.height * 3), Image.Resampling.NEAREST)
    white = Image.new('RGB', enlarged.size, 'white')
    white.paste(enlarged, (0, 0), enlarged)
    white.save(path)


def prepare(args):
    index = json.loads(args.index.read_text())
    report = json.loads(args.runtime.read_text())
    assert report['status'] == 'passed' and not report['errors']
    assert report['index_sha256'] == sha(args.index)
    sample = report['runtime']['samples'][args.sample.lower().removesuffix('.png')]
    selected = [e for e in index['entries'] if e['key'] in args.keys]
    assert len(selected) == len(set(args.keys))
    draws = {}
    for e in selected:
        bank, name = e['key'].split('/')
        found = [d for d in sample['visible'] if d['hd'] and d['fil'].lower() == bank.lower() and d['bilde'] == int(name[:3])]
        assert len(found) == 1, e['key']
        draws[e['key']] = found[0]
    assert len({d['speilet'] for d in draws.values()}) == 1
    mirrored = next(iter(draws.values()))['speilet']
    left = min(d['x'] for d in draws.values())
    right = max(d['x'] + d['w'] for d in draws.values())
    top = min(d['y'] for d in draws.values())
    bottom = max(d['y'] + d['h'] for d in draws.values())
    size = [(right - left) * 4, (bottom - top) * 4]
    placements = {key: [(right - d['x'] - d['w'] if mirrored else d['x'] - left) * 4, (d['y'] - top) * 4] for key, d in draws.items()}
    image = Image.new('RGBA', size)
    for e in selected:
        assert sha(ROOT / e['candidate']) == e['candidate_sha256']
        assert sha(ROOT / e['art_record']) == e['art_record_sha256']
        im = Image.open(ROOT / e['candidate']).convert('RGBA')
        d = draws[e['key']]
        assert im.size == (d['w'] * 4, d['h'] * 4)
        image.alpha_composite(im, placements[e['key']])
    output = ART / args.name
    output.mkdir(exist_ok=True)
    image.save(output / 'source-composite4x.png', optimize=True)
    preview(image, output / 'source-composite-preview.png')
    contract = dict(schema=1, status='source_positioned_material_patch_not_new_pose',
                    input_index=str(args.index.resolve().relative_to(ROOT)), input_index_sha256=sha(args.index),
                    runtime=str(args.runtime.resolve().relative_to(ROOT)), runtime_sha256=sha(args.runtime),
                    frame=sample['frame'], mirrored=mirrored, original_draws=draws,
                    placements4x=placements, size4x=size, band4x=args.band,
                    source_composite_sha256=sha(output / 'source-composite4x.png'), entries=selected)
    freeze(output / 'join-contract.json', contract)
    print(output / 'join-contract.json')


def pack(args):
    contract = json.loads(args.contract.read_text())
    output = args.contract.parent
    assert sha(ROOT / contract['input_index']) == contract['input_index_sha256']
    assert sha(ROOT / contract['runtime']) == contract['runtime_sha256']
    assert sha(output / 'source-composite4x.png') == contract['source_composite_sha256']
    band = contract['band4x']
    photo = Image.open(args.raw).convert('RGBA')
    if args.raw_is_band:
        patch = photo.resize((band[2] - band[0], band[3] - band[1]), Image.Resampling.LANCZOS)
        photo = Image.new('RGBA', contract['size4x'])
        photo.alpha_composite(patch, band[:2])
    else:
        photo = photo.resize(contract['size4x'], Image.Resampling.LANCZOS)
    result = Image.new('RGBA', contract['size4x'])
    index = json.loads((ROOT / contract['input_index']).read_text())
    assert 0 <= band[0] < band[2] <= photo.width and 0 <= band[1] < band[3] <= photo.height
    for e in contract['entries']:
        candidate, record_path = ROOT / e['candidate'], ROOT / e['art_record']
        assert sha(candidate) == e['candidate_sha256'] and sha(record_path) == e['art_record_sha256']
        old = json.loads(record_path.read_text())
        before = Image.open(candidate).convert('RGBA')
        image = before.copy()
        # Originale flate skygger skal aldri faa generert hudmateriale.
        shadow = set()
        indices = None
        if old.get('original_flat_shadow_packing') or args.source_blue_only:
            queue = json.loads((ART.parent / 'queue.json').read_text())
            route = next(r for r in queue['entries'] if r['key'] == e['key'])
            packed = Image.open(ART.parent / route['packed_original']['path'])
            bits = [1 << n for n in range(5) if route['plane_mask'] & (1 << n)]
            indices = [sum(bit for n, bit in enumerate(bits) if v & (1 << n)) for v in packed.getdata()]
            if old.get('original_flat_shadow_packing'):
                rect = old['original_flat_shadow_packing']['source_rect']
                allowed = old['original_flat_shadow_packing']['indices']
                for sy in range(rect[1], rect[3]):
                    for sx in range(rect[0], rect[2]):
                        if indices[sy * packed.width + sx] in allowed:
                            shadow.update((sx * 4 + dx, sy * 4 + dy) for dy in range(4) for dx in range(4))
        ox, oy = contract['placements4x'][e['key']]
        changed, retained_edge = [], []
        for y in range(image.height):
            for x in range(image.width):
                xx, yy = ox + x, oy + y
                if not (band[0] <= xx < band[2] and band[1] <= yy < band[3]) or not before.getpixel((x, y))[3]:
                    continue
                if (x, y) in shadow:
                    continue
                if args.source_blue_only and indices[(y // 4) * packed.width + x // 4] not in [9, 10, 11, 12]:
                    continue
                p = photo.getpixel((xx, yy))
                if p[3] < 128:
                    retained_edge.append([x, y])
                    continue
                weight = min(1, (xx - band[0] + 1) / 8, (band[2] - xx) / 8, (yy - band[1] + 1) / 8, (band[3] - yy) / 8)
                original = before.getpixel((x, y))
                image.putpixel((x, y), tuple(round(p[k] * weight + original[k] * (1 - weight)) for k in range(3)) + (original[3],))
                changed.append([x, y, xx, yy, weight])
        assert image.getchannel('A').tobytes() == before.getchannel('A').tobytes()
        assert all(image.getpixel(p) == before.getpixel(p) for p in shadow)
        assert changed
        folder = candidate.parent / ('source-join-' + sha(args.contract)[:8] + '-' + sha(args.raw)[:8])
        folder.mkdir(exist_ok=True)
        target = folder / 'candidate.png'
        image.save(target, optimize=True)
        material = dict(raw=str(args.raw.resolve().relative_to(ROOT)), raw_sha256=sha(args.raw), prompt=str(args.prompt.resolve().relative_to(ROOT)), prompt_sha256=sha(args.prompt), contract=str(args.contract.resolve().relative_to(ROOT)), contract_sha256=sha(args.contract), previous_candidate=str(candidate.relative_to(ROOT)), previous_candidate_sha256=sha(candidate), alpha_unchanged=True, band4x=band, changed_rgb_pixels=len(changed), retained_original_candidate_at_photo_edge=retained_edge, packing_map=changed, method='Separat generert fotohud pakkes bare i kildebekreftet fragmentskjoet, med aatte HD-piksler innfasing. Alfa og alt RGB utenfor stripe beholdes eksakt. Ingen originaltekstur brukes.')
        if args.raw_is_band or args.source_blue_only:
            material.update(raw_is_band=args.raw_is_band, source_blue_indices_only=[9, 10, 11, 12] if args.source_blue_only else None, retained_flat_shadow_hd_pixels=len(shadow))
        record = dict(old, candidate_sha256=sha(target), source_join_material=material)
        record['packing'] += ' Separat generert lokal hudovergang er pakket etter originalkallets eksakte plasseringer, med uendret alfa.'
        record['visual_checks'] = dict(old['visual_checks'], runtime_overlap='pending_new_join_runtime', original_hd_return='pending_new_join_runtime')
        freeze(folder / 'art-record.json', record)
        entry = next(i for i in index['entries'] if i['key'] == e['key'])
        entry.update(candidate=str(target.relative_to(ROOT)), candidate_sha256=sha(target), art_record=str((folder / 'art-record.json').relative_to(ROOT)), art_record_sha256=sha(folder / 'art-record.json'))
        result.alpha_composite(image, [ox, oy])
    result.save(output / ('packed-' + sha(args.raw)[:8] + '.png'), optimize=True)
    preview(result, output / ('packed-' + sha(args.raw)[:8] + '-preview.png'))
    freeze(args.output_index, index)
    print(args.output_index, sha(args.output_index))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    p = commands.add_parser('prepare')
    p.add_argument('--index', type=Path, required=True)
    p.add_argument('--runtime', type=Path, required=True)
    p.add_argument('--sample', required=True)
    p.add_argument('--keys', nargs='+', required=True)
    p.add_argument('--band', nargs=4, type=int, required=True)
    p.add_argument('--name', required=True)
    p = commands.add_parser('pack')
    p.add_argument('--contract', type=Path, required=True)
    p.add_argument('--raw', type=Path, required=True)
    p.add_argument('--prompt', type=Path, required=True)
    p.add_argument('--output-index', type=Path, required=True)
    p.add_argument('--raw-is-band', action='store_true', help='Raabildet dekker bare kontraktens materialstripe.')
    p.add_argument('--source-blue-only', action='store_true', help='Behold brune foetter og andre kildefarger uendret; bruk bare TROLL-blaa9..12.')
    args = parser.parse_args()
    (prepare if args.command == 'prepare' else pack)(args)


if __name__ == '__main__':
    main()
