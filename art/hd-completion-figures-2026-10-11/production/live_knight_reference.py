#!/usr/bin/env python3
"""Eksporter nøytral draktreferanse for en kildebevist innbakt ridder."""
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

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('key')
    args = parser.parse_args()
    queue = json.loads((FIGURES / 'queue.json').read_text())
    row = next(r for r in queue['entries'] if r['key'] == args.key)
    assert row['bank'] in ['Balok2.CEL', 'Balok3.CEL']
    contract = FIGURES / 'palettes/cases/balok.json'
    palette = json.loads(contract.read_text())
    ref = next(r for r in palette['references'] if r['key'] == args.key)
    assert ref['source_indices_sha256'] == row['indices_sha256']
    packed = Image.open(FIGURES / row['packed_original']['path'])
    indices = order.utvid_indekser(packed.tobytes(), row['plane_mask'])
    assert hashlib.sha256(indices).hexdigest() == row['indices_sha256']
    live = order.maskefarger(row['bank'], row['frame']).intersection(indices)
    assert live and live.issubset({6, 7, 8})
    original = Image.open(FIGURES / 'palettes' / ref['original']).convert('RGBA')
    neutral = original.copy()
    levels = {6: 128, 7: 96, 8: 64}
    for y in range(original.height):
        for x in range(original.width):
            index = indices[y * original.width + x]
            if index in live:
                level = levels[index]
                neutral.putpixel((x, y), (level, level, level, 255))
    out = ART / 'references' / args.key.removesuffix('.png') / 'neutral-live-v1'
    assert not out.exists(), 'Bevar eldre referanser'
    out.mkdir(parents=True)
    neutral.save(out / 'original-neutral.png')
    white = Image.new('RGBA', neutral.size, 'white')
    white.alpha_composite(neutral)
    white.convert('RGB').resize((neutral.width * 20, neutral.height * 20), Image.Resampling.NEAREST).save(out / 'body-white.png')
    mask = Image.new('RGB', neutral.size, 'white')
    mask.paste('black', (0, 0, neutral.width, neutral.height), neutral.getchannel('A'))
    mask.resize((neutral.width * 20, neutral.height * 20), Image.Resampling.NEAREST).save(out / 'body-silhouette.png')
    (out / 'source.json').write_text(json.dumps(dict(key=args.key, source_bank_sha256=row['source_bank']['sha256'], source_indices_sha256=row['indices_sha256'], palette_contract_sha256=hashlib.sha256(contract.read_bytes()).hexdigest(), live_indices=sorted(live), preview_neutral_levels=levels, mask_grey_reference=128, scope='Kun kildereferanse for generering. Originalens blå ridderfarger er byttet til tydelig grå drakt; silhuett, rustning og øvrige materialer er uendret. Ingen HD-nytegning.'), ensure_ascii=False, indent=2) + '\n')
    print(out)

if __name__ == '__main__':
    main()
