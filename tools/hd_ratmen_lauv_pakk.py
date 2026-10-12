#!/usr/bin/env python3
"""Pakk eksisterende Ratmen-lauvfoto uten intern kildepikselkvantisering.

Bare RGB-materialet moderniseres. Originalrute, maal, plassering og den allerede
kildebundne alfakonturen beholdes. Kjor uten argument for kandidat/kvittering;
--activate oppdaterer bare RATMEN1.CEL/063.png og dens manifestoppfoering.
"""
import argparse
from collections import Counter, deque
import hashlib
import io
import json
from pathlib import Path
import struct
import sys

from PIL import Image, ImageFilter

import moonfiles as mf

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / 'art/hd-ratmen-foliage-2026-10-12'
OLD_ART = ROOT / 'art/hd-completion-figures-2026-10-11/figures/ratmen-production'
KEY = 'RATMEN1.CEL/063.png'
RAW_SHA = 'c4dc1d3c4ba00bcb4d61858bb1a47b4a0d319fe01bc6810d1014037bbeaa200f'
OLD_SHA = '1957438f9c8970778fd1254be948148a7a2aacb44439d1883051dfafffa86ede'
BANK_SHA = '6b59eb2aee821f94e9f5ce0fbea17eba0239ce4759a54e7dc2c057c69865f6ab'
INDEX_SHA = '52b5a933dd9bc0b295ca6decdc7cc219613254ccdcf7f7658b44457fd267c378'
SHADOW_FILL = .08
sha = lambda b: hashlib.sha256(b).hexdigest()


def atomic(path, data):
    temporary = path.with_name(path.name + '.ratmen-tmp')
    temporary.write_bytes(data)
    temporary.replace(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--activate', action='store_true')
    parser.add_argument('--native-chip', type=Path,
                        help='Valgfri lokal original-CPU-probe; gjenskapes som beskrevet i source/native-proof.json')
    args = parser.parse_args()
    (ART / 'packed/RATMEN1.CEL').mkdir(parents=True, exist_ok=True)
    (ART / 'source').mkdir(exist_ok=True)
    game = mf.Spill(str(ROOT / 'Moonstonecd32-AMIGA.zip'))
    bank = game.les('data/RATMEN1.CEL')
    assert sha(bank) == BANK_SHA
    g = mf.cel_les(bank)[0][63]
    indices = bytes(mf.plan_til_indeks(g['data'], g['plan'], g['bredde'], g['hoyde']))
    assert (g['bredde'], g['hoyde'], g['maske']) == (44, 35, 31)
    assert sha(indices) == INDEX_SHA
    palette_source = OLD_ART / 'identity/source-color-contract.json'
    colors = json.loads(palette_source.read_bytes())['palette_words']
    palette = [mf.amiga_rgb(c) for c in colors]
    # Den tidligere kontrakten binder dagpaletten til kildekoden. Raa minnedump
    # er lokal etterproevbar QA, ikke en obligatorisk innsporet byggeavhengighet.
    native_proof = json.loads((ART / 'source/native-proof.json').read_bytes())
    native_sha = next(e['sha256'] for e in native_proof['artifacts'] if e['file'] == 'chip1400.bin')
    if args.native_chip:
        chip = args.native_chip.read_bytes()
        words = struct.pack('>32H', *colors)
        assert sha(chip) == native_sha
        assert chip[0x960e0:0x96120] == words and chip[0x961a0:0x961e0] == words
    original = Image.new('RGBA', (44, 35))
    original.putdata([tuple(palette[c]) + (255 if c else 0,) for c in indices])
    original.save(ART / 'source/original063-day.png')
    raw_bytes = (OLD_ART / 'raw' / KEY).read_bytes()
    assert sha(raw_bytes) == RAW_SHA
    old_path = ART / 'source/previous-active063.png'
    if not old_path.exists():
        previous = (ROOT / 'web/hd' / KEY).read_bytes()
        assert sha(previous) == OLD_SHA
        old_path.write_bytes(previous)
    previous = old_path.read_bytes()
    assert sha(previous) == OLD_SHA
    alpha = Image.open(io.BytesIO(previous)).convert('RGBA').getchannel('A')
    assert alpha.size == (176, 140)
    raw = Image.open(io.BytesIO(raw_bytes)).convert('RGBA')
    # Samme originale hele44x35-anker som den tidligere pakken. Raa RGB fra
    # fotografiet er eneste materiale; den gamle PNG-en bidrar bare med alfa.
    resized = raw.crop(raw.getchannel('A').getbbox()).resize(alpha.size, Image.Resampling.LANCZOS)
    pixels = list(resized.getdata())
    w, h = resized.size
    near = [-1] * (w * h)
    queue = deque()
    for n, p in enumerate(pixels):
        if p[3] >= 160:
            near[n] = n
            queue.append(n)
    assert queue
    while queue:
        n = queue.popleft()
        x, y = n % w, n // w
        for q in (n-1 if x else -1, n+1 if x+1 < w else -1,
                  n-w if y else -1, n+w if y+1 < h else -1):
            if q >= 0 and near[q] < 0:
                near[q] = near[n]
                queue.append(q)
    # Ett globalt fargeforhold fra dagpalettens bladmateriale. Ingen oppslag paa
    # x//4,y//4 eller per-kildecellefarge brukes ved RGB-produksjonen.
    counts = Counter(indices)
    leaf_indices = (22, 24, 25, 28)
    count = sum(counts[c] for c in leaf_indices)
    target_mean = [sum(palette[c][k] * counts[c] for c in leaf_indices) / count for k in range(3)]
    core = [p for p in pixels if p[3] >= 160]
    source_mean = [sum(p[k] for p in core) / len(core) for k in range(3)]
    gain = [target_mean[k] / source_mean[k] for k in range(3)]
    # Normalisert foto-uskarphet fyller bare materialets indre mellomrom.
    # Det unngaar diamant-/Voronoi-kanter fra en naermeste-nabo-fargefylling.
    blur_alpha = list(resized.getchannel('A').filter(ImageFilter.GaussianBlur(4)).getdata())
    blur_rgb = []
    for k in range(3):
        channel = Image.new('L', (w, h))
        channel.putdata([round(p[k] * p[3] / 255) for p in pixels])
        blur_rgb.append(list(channel.filter(ImageFilter.GaussianBlur(4)).getdata()))
    rgb = []
    for n, p in enumerate(pixels):
        coverage = p[3] / 255
        fill = [blur_rgb[k][n] * 255 / blur_alpha[n] if blur_alpha[n] else pixels[near[n]][k] for k in range(3)]
        # Fotoflaten beholder sine egne blader og ribber. Gjennomsiktige
        # fotomellomrom blir myk plantenselvskygge innen den opake kildeformen.
        rgb.append(tuple(max(0, min(255, round((p[k] * coverage + fill[k] * (1-coverage) * SHADOW_FILL) * gain[k]))) for k in range(3)))
    out = Image.new('RGBA', (w, h))
    out.putdata([p + (a,) for p, a in zip(rgb, alpha.getdata())])
    buf = io.BytesIO()
    out.save(buf, format='PNG', optimize=True)
    png = buf.getvalue()
    assert out.getchannel('A').tobytes() == alpha.tobytes()
    for y in range(35):
        for x in range(44):
            assert (alpha.getpixel((x*4+2, y*4+2)) >= 250) == bool(indices[y*44+x])
    candidate = ART / 'packed' / KEY
    candidate.write_bytes(png)
    manifest_path = ROOT / 'web/hd/manifest.json'
    raw_manifest = manifest_path.read_bytes()
    manifest = json.loads(raw_manifest)
    before = {e['path']: e['sha256'] for e in manifest['files']}
    assert len(before) == 1970 and manifest['images'] == 1964
    for e in manifest['files']:
        b = (ROOT / 'web/hd' / e['path']).read_bytes()
        assert len(b) == e['bytes'] and sha(b) == e['sha256'], e['path']
    report = dict(schema=1, key=KEY, method='continuous_existing_photo_global_day_palette_v3',
                  raw_sha256=RAW_SHA, original_bank_sha256=BANK_SHA,
                  original_indices_sha256=INDEX_SHA, original_size=[44, 35], target_size=[w, h],
                  previous_png_sha256=OLD_SHA, candidate_sha256=sha(png),
                  alpha_sha256=sha(alpha.tobytes()), alpha_exact_unchanged=True,
                  palette_source_sha256=sha(palette_source.read_bytes()),
                  native_chip_sha256=native_sha, native_chip_rechecked=bool(args.native_chip),
                  native_proof='source/native-proof.json', native_palette_addresses=['0x960e0', '0x961a0'],
                  source_leaf_palette={str(c): palette[c] for c in leaf_indices},
                  target_mean_rgb=target_mean, photograph_mean_rgb=source_mean, global_rgb_gain=gain,
                  source_index_counts=dict(counts), original_placements=[[137, 20], [155, 23], [173, 16]],
                  role='Static opaque foliage foreground, repeatedly drawn before and over descending Ratmen parts; source-zero holes remain transparent.',
                  source_5_policy='Natural continuous photographic self-shadow; source opacity and holes retained, no per-cell darkening.',
                  photograph_shadow_fill=SHADOW_FILL,
                  before_manifest_sha256=sha(raw_manifest), activated=args.activate)
    if args.activate:
        entry = next(e for e in manifest['files'] if e['path'] == KEY)
        assert entry['sha256'] in (OLD_SHA, sha(png))
        entry.update(bytes=len(png), sha256=sha(png))
        updated = (json.dumps(manifest, ensure_ascii=False, indent=2) + '\n').encode()
        atomic(ROOT / 'web/hd' / KEY, png)
        atomic(manifest_path, updated)
        report['manifest_sha256'] = sha(updated)
        assert [e['path'] for e in manifest['files'] if before[e['path']] != e['sha256']] in ([KEY], [])
    (ART / 'packing.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: report[k] for k in ('key', 'candidate_sha256', 'alpha_exact_unchanged', 'activated')}))


if __name__ == '__main__':
    main()
