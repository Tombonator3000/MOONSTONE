#!/usr/bin/env python3
"""Kildeport for innebygd TAV-figur, alfa og NN-palettmaske."""
import hashlib
import json
import math
import sys
from pathlib import Path
from PIL import Image

ART = Path(__file__).resolve().parent
ROOT = ART.parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import moonfiles as mf

sha = lambda b: hashlib.sha256(b).hexdigest()
contract_path = ART / 'player-source-contract.json'
contract = json.loads(contract_path.read_text())
source = mf.Spill(ROOT / 'Moonstonecd32-AMIGA.zip').les('tav.piv')
assert sha(source) == contract['source_file_sha256']
assert sha((ROOT / 'Moonstonecd32-AMIGA.zip').read_bytes()) == contract['source_zip_sha256']
planes, palette, bank = mf.piv_alle(source)[0][0]
full = mf.plan_til_indeks(bank, planes)
x0, y0, x1, y1 = contract['rect']
w, h = x1 - x0, y1 - y0
indices = (ART / 'source/player-indices.bin').read_bytes()
selected = (ART / 'source/player-mask.bin').read_bytes()
assert len(indices) == len(selected) == w * h
assert indices == bytes(full[y * 320 + x] for y in range(y0, y1) for x in range(x0, x1))
row = contract['routes'][0]
assert sha(indices) == row['indices_sha256']
assert sha(selected) == row['alpha_indices_sha256']
assert sum(selected) == contract['selected_pixels'] == 7431
assert sum(6 <= c <= 10 for c in full) == 3698
assert sum(bool(v) and 6 <= indices[i] <= 10 for i, v in enumerate(selected)) == 3682
assert sum(6 <= c <= 10 for c in full[:65 * 320]) == contract['excluded_bar_maid_live_pixels'] == 16
png_path = ART / 'packed/embedded/tav-player.png'
mask_path = ART / 'packed/embedded/tav-player.mask.png'
photo = Image.open(png_path).convert('RGBA')
mask = Image.open(mask_path).convert('RGBA')
assert photo.size == mask.size == (w * 4, h * 4)
px, mp = photo.load(), mask.load()
checks = {'source_indices': w * h, 'source_alpha_centers': 0, 'nn_mask_pixels': 0, 'photo_live_luminance': 0, 'photo_black_live_pixels': 0}
red = {}
for y in range(h):
    for x in range(w):
        i = y * w + x
        assert (px[x * 4 + 2, y * 4 + 2][3] >= 128) == bool(selected[i]), (x, y, 'alfa')
        checks['source_alpha_centers'] += 1
for y in range(h * 4):
    for x in range(w * 4):
        i = (y // 4) * w + x // 4
        c = indices[i]
        live = bool(selected[i]) and 6 <= c <= 10
        r, g, b, a = mp[x, y]
        assert r == (c + 1 if live else 0), (x, y, c, r)
        assert b == (255 if live else 0), (x, y, c, b)
        checks['nn_mask_pixels'] += 1
        pr, pg, pb, pa = px[x, y]
        if live:
            luminance = pr * .299 + pg * .587 + pb * .114
            rr, rg, rb = contract['palettes']['tavern']['rgba'][c][:3]
            reference = rr * .299 + rg * .587 + rb * .114
            expected_g = min(255, max(0, math.floor(128 * luminance / reference + .5)))
            assert g == expected_g, (x, y, g, expected_g)
            checks['photo_live_luminance'] += 1
            checks['photo_black_live_pixels'] += int(g == 0)
        if pa >= 128 and pr > pg * 1.5 and pr > pb * 1.5:
            red[str(c)] = red.get(str(c), 0) + 1
assert checks['photo_live_luminance'] == 3682 * 16
# En NN-feil paa en levende kildepiksel skal avvises selv om alfa er avrundet.
live_i = next(i for i, c in enumerate(indices) if selected[i] and 6 <= c <= 10)
live_x, live_y = live_i % w * 4, live_i // w * 4
original_r = mp[live_x, live_y][0]
assert original_r == indices[live_i] + 1
def require_nn(actual_r, source_index):
    assert actual_r == source_index + 1

rejected = False
try:
    require_nn(0, indices[live_i])
except AssertionError:
    rejected = True
assert rejected
checks['negative_wrong_live_R_rejected'] = rejected
before_path = ART / 'verification/frozen-player-before-fixed/tav-player.png'
normalization = None
if before_path.exists():
    before = Image.open(before_path).convert('RGBA').load()
    live_changed = alpha_changed = 0
    for y in range(h * 4):
        for x in range(w * 4):
            i = y // 4 * w + x // 4
            old, new = before[x, y], px[x, y]
            alpha_changed += old[3] != new[3]
            live_changed += 6 <= indices[i] <= 10 and old != new
            if new[3] and indices[i] == 11:
                assert new[0] <= 64 and new[1] == new[2] == 0
            if new[3] and indices[i] == 0:
                assert not (new[2] > new[0] * 1.35 + 1 and new[2] > new[1] * 1.1 + 1)
    remaining_blue = 0
    for y in range(h * 4):
        for x in range(w * 4):
            c = indices[y // 4 * w + x // 4]
            r, g, b, a = px[x, y]
            remaining_blue += bool(a and not 6 <= c <= 10 and b > r * 1.35 + 1 and b > g * 1.1 + 1)
    assert remaining_blue == 0
    assert live_changed == alpha_changed == 0
    normalization = dict(remaining_blue_outside_live=remaining_blue, before_sha256=sha(before_path.read_bytes()), live_RGBA_changed=live_changed, alpha_changed=alpha_changed, fixed_red_and_neutral_shadows_preserved=True)
report = dict(schema=1, status='passed', checks=checks,
    source_contract_sha256=sha(contract_path.read_bytes()),
    source_zip_sha256=contract['source_zip_sha256'],
    source_file_sha256=sha(source), original_rect=contract['rect'],
    selected_pixels=sum(selected), preserved_other_live_pixels=16,
    photo={'path':str(png_path.relative_to(ROOT)), 'sha256':sha(png_path.read_bytes())},
    mask={'path':str(mask_path.relative_to(ROOT)), 'sha256':sha(mask_path.read_bytes())},
    red_dominant_photo_pixels_by_original_index=red, fixed_material_normalization=normalization,
    interpretation='Varmt staal kan ha roed refleks. Dette er diagnostikk, ikke visuell godkjenning eller bevis for riktig scene. Alle levende maskepiksler er eksakte NN-indekser uavhengig av alfa.')
(ART / 'verification/packing-v1.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'status': 'passed', 'checks': checks}))
