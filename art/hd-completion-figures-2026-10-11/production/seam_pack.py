#!/usr/bin/env python3
"""Pakk en separat generert hudovergang mellom to originale trollfragmenter."""
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--raw', required=True, type=Path)
    parser.add_argument('--prompt', required=True, type=Path)
    parser.add_argument('--pair', choices=['027-028', '031-032'], default='027-028')
    args = parser.parse_args()
    wrist = args.pair == '031-032'
    group = '006' if wrist else '005'
    seam_dir = ART / ('seam-' + args.pair + '-v1')
    size = (136, 216) if wrist else (172, 188)
    band = [68, 88, 112, 104] if wrist else [64, 36, 88, 112]
    index = json.loads((ART / ('candidates-troll-' + group + '.json')).read_text())
    raw, prompt = args.raw.resolve(), args.prompt.resolve()
    photo = Image.open(raw).convert('RGBA').resize(size, Image.Resampling.LANCZOS)
    input_photo = seam_dir / 'source-positions-photo-original4x.png'
    before_composite = Image.open(input_photo).convert('RGBA')
    after_composite = Image.new('RGBA', before_composite.size)
    # Originalkallet plasserer 027 ved 0,0 og 028 ved 19,10, før speiling.
    placements = {'TROLL1.CEL/031.png': (24, 0), 'TROLL1.CEL/032.png': (0, 96)} if wrist else {'TROLL1.CEL/027.png': (0, 0), 'TROLL1.CEL/028.png': (76, 40)}
    proof = dict(raw=str(raw.relative_to(ROOT)), raw_sha256=sha(raw),
                 prompt=str(prompt.relative_to(ROOT)), prompt_sha256=sha(prompt),
                 input_composite=str(input_photo.relative_to(ROOT)), input_composite_sha256=sha(input_photo),
                 source_positions_4x=placements, source_composite_size=list(size),
                 used_region=band,
                 source_drawlist_proof='art/hd-completion-figures-2026-10-11/production/verification/' + ('runtime-425b773f9848363e-59dfcb6c/test.json' if wrist else 'runtime-fea2f344dd4f95de-59dfcb6c/test.json'),
                 method='Separat generert fotohud pakkes i en 16 HD-piksler hoey stripe over armskjoeten. Lineaer innfasing ved stripekanten. Alle originale alpha-verdier og alt RGB utenfor stripen beholdes; ingen originaltekstur brukes.' if wrist else 'Separat generert fotohud pakkes i en 24 HD-piksler bred stripe over skulderskjoeten. Lineaer innfasing ved stripekanten. Alle originale alpha-verdier og alt RGB utenfor stripen beholdes; ingen originaltekstur brukes.')
    for entry in index['entries']:
        key = entry['key']
        if key not in placements:
            continue
        candidate, record_path = ROOT / entry['candidate'], ROOT / entry['art_record']
        assert sha(candidate) == entry['candidate_sha256'] and sha(record_path) == entry['art_record_sha256']
        old = json.loads(record_path.read_text())
        image = Image.open(candidate).convert('RGBA')
        before = image.copy()
        ox, oy = placements[key]
        changed, retained_edge = [], []
        for y in range(image.height):
            for x in range(image.width):
                xx, yy = ox + x, oy + y
                if not (band[0] <= xx < band[2] and band[1] <= yy < band[3]) or not before.getpixel((x, y))[3]:
                    continue
                weight = min(1, (xx - band[0] + 1) / 8, (band[2] - xx) / 8, (yy - band[1] + 1) / 4, (band[3] - yy) / 4)
                color, original = photo.getpixel((xx, yy)), before.getpixel((x, y))
                if color[3] < 128:
                    retained_edge.append([x, y, xx, yy])
                    continue
                packed = tuple(round(color[k] * weight + original[k] * (1 - weight)) for k in range(3)) + (original[3],)
                image.putpixel((x, y), packed)
                changed.append([x, y, xx, yy, weight])
        assert image.getchannel('A').tobytes() == before.getchannel('A').tobytes()
        # Oyedetaljen paa 028 ligger langt utenfor skulderstripen.
        if key.endswith('/028.png'):
            assert image.crop((32, 0, 76, 40)).tobytes() == before.crop((32, 0, 76, 40)).tobytes()
        if key.endswith('/032.png'):
            assert image.crop((0, 0, 68, 40)).tobytes() == before.crop((0, 0, 68, 40)).tobytes()
        output = candidate.parent / ('source-wrist-join-v1' if wrist else 'source-shoulder-join-v1')
        output.mkdir(exist_ok=True)
        target = output / 'candidate.png'
        image.save(target, optimize=True)
        record = dict(old)
        record['candidate_sha256'] = sha(target)
        record['packing'] += ' Separat fotohud for armskjoeten pakkes ved originalens faktiske fragmentplassering, med uendret alpha og uendret oyedetalj.' if wrist else ' Separat fotohud for skulderskjoeten pakkes ved originalens faktiske fragmentplassering, med uendret alpha og uendret oyedetalj.'
        record['wrist_join_material' if wrist else 'shoulder_join_material'] = dict(proof, previous_candidate=str(candidate.relative_to(ROOT)), previous_candidate_sha256=sha(candidate), alpha_unchanged=True, changed_rgb_pixels=len(changed), retained_original_candidate_at_photo_edge=retained_edge, packing_map=changed)
        record['visual_checks'] = dict(old['visual_checks'], runtime_overlap='pending_repaired_shoulder_runtime', original_hd_return='pending_repaired_shoulder_runtime')
        freeze(output / 'art-record.json', record)
        entry.update(candidate=str(target.relative_to(ROOT)), candidate_sha256=sha(target), art_record=str((output / 'art-record.json').relative_to(ROOT)), art_record_sha256=sha(output / 'art-record.json'))
        after_composite.alpha_composite(image, placements[key])
    # Diagnosebildet bruker bare pakking og skal aldri telles som en nytegning.
    after_composite.save(seam_dir / 'packed-join-v1.png', optimize=True)
    preview = Image.new('RGB', (size[0] * 5, size[1] * 5), 'white')
    enlarged = after_composite.resize(preview.size, Image.Resampling.NEAREST)
    preview.paste(enlarged, (0, 0), enlarged)
    preview.save(seam_dir / 'packed-join-v1-preview.png')
    output_index = ART / ('candidates-troll-' + group + '-join-v1.json')
    freeze(output_index, index)
    print(json.dumps(dict(index=str(output_index.relative_to(ROOT)), sha256=sha(output_index))))


if __name__ == '__main__':
    main()
