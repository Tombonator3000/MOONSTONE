#!/usr/bin/env python3
"""Pakk levende draktfarge i et separat nytegnet Balok-fragment."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
from PIL import Image
ART = Path(__file__).resolve().parent
FIGURES = ART.parent
ROOT = FIGURES.parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import hd_bestilling as order
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('record', type=Path)
    args = parser.parse_args()
    art = json.loads(args.record.read_text())
    queue = json.loads((FIGURES / 'queue.json').read_text())
    row = next(r for r in queue['entries'] if r['key'] == art['key'])
    assert row['bank'] in ['Balok2.CEL', 'Balok3.CEL']
    source = FIGURES / row['packed_original']['path']
    packed = Image.open(source)
    indices = order.utvid_indekser(packed.tobytes(), row['plane_mask'])
    assert hashlib.sha256(indices).hexdigest() == row['indices_sha256'] == art['source_indices_sha256']
    live = order.maskefarger(row['bank'], row['frame']).intersection(indices)
    assert live and live.issubset({6, 7, 8})
    original = args.record.parent / 'candidate.png'
    assert sha(original) == art['candidate_sha256']
    photo = Image.open(original).convert('RGBA')
    assert photo.size == (row['width'] * 4, row['height'] * 4)
    changed = 0
    for y in range(photo.height):
        for x in range(photo.width):
            if indices[(y // 4) * row['width'] + x // 4] in live:
                red, green, blue, alpha = photo.getpixel((x, y))
                grey = round(order.lys(red, green, blue))
                changed += red != grey or green != grey or blue != grey
                photo.putpixel((x, y), (grey, grey, grey, alpha))
    out = args.record.parent / 'live-knight-6-8-v1'
    assert not out.exists(), 'Bevar eldre pakking'
    out.mkdir()
    candidate = out / 'candidate.png'
    photo.save(candidate, optimize=True)
    mask = out / 'candidate.mask.png'
    order.lag_maske(str(source), str(mask), str(candidate), str(ROOT / 'Moonstonecd32-AMIGA.zip'), 128)
    assert Image.open(original).getchannel('A').tobytes() == photo.getchannel('A').tobytes()
    art['candidate_sha256'] = sha(candidate)
    art['live_knight_packing'] = dict(input_record=str(args.record.relative_to(ROOT)) if args.record.is_absolute() else str(args.record), input_record_sha256=sha(args.record), input_candidate_sha256=sha(original), source_bank_sha256=row['source_bank']['sha256'], source_indices_sha256=row['indices_sha256'], live_indices=sorted(live), source_cells=sum(i in live for i in indices), grey_reference=128, grey_normalized_target_pixels=changed, mask=str(mask.relative_to(ROOT)) if mask.is_absolute() else str(mask), mask_sha256=sha(mask), tool_sha256=sha(Path(__file__)), method='Bare eget generert draktmateriale normaliseres til graatt innen kildeindeks6..8. Masken bruker opprinnelig indeks og fotomaterialets lysnivaa; rustning og øvrig generert materiale er uendret.')
    (out / 'art-record.json').write_text(json.dumps(art, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(dict(key=art['key'], path=str(out), candidate_sha256=sha(candidate), mask_sha256=sha(mask), live_indices=sorted(live), source_cells=sum(i in live for i in indices))))

if __name__ == '__main__':
    main()
