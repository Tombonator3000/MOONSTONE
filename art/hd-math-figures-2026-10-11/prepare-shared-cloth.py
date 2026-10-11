#!/usr/bin/env python3
"""Del bare kildeidentisk kappemateriale mellom to selvstendige haarruter."""
import hashlib, json, sys
from pathlib import Path
ART = Path(__file__).resolve().parent
ROOT = ART.parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from hd_ui_bygg import ui_contours
sha = lambda b: hashlib.sha256(b).hexdigest()
a = (ART / 'source/indices/005.bin').read_bytes()
b = (ART / 'source/indices/010.bin').read_bytes()
assert len(a) == len(b) == 46 * 48
mask = bytes(int(x == y and x in range(6, 11)) for x, y in zip(a, b))
assert sum(mask) == 309
(ART / 'source/shared-cloth-005-010.bin').write_bytes(mask)
donor = ART / 'raw/math-static-v1.png'
record = {
    'schema': 1,
    'kind': 'deling-av-uendret-kappemateriale',
    'scope': 'Kun 309 kildeidentiske kappematerialpiksler. Hver bevegelige haar- og ansiktsrute har egen generert master. Ingen nytegning av hele kappen.',
    'frames': [5, 10], 'width': 46, 'height': 48,
    'source_indices': {'005': sha(a), '010': sha(b)},
    'allowed_indices': [6, 7, 8, 9, 10],
    'mask': 'source/shared-cloth-005-010.bin', 'mask_sha256': sha(mask),
    'mask_pixels': sum(mask),
    'alpha_path': ui_contours(mask, 46, 48, lambda c: bool(c)),
    'donor': 'raw/math-static-v1.png', 'donor_sha256': sha(donor.read_bytes()),
    'original_rect': [98, 49, 144, 97],
    'donor_original_rect': [20, 32, 270, 166],
    'donor_crop_normalized': [78 / 250, 17 / 134, 46 / 250, 48 / 134],
}
(ART / 'shared-cloth.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
print('309 uendrede kappematerialpiksler registrert')

# Wi1.P er den faste originalen under oeyeanimasjonen. Uendrede hudpiksler
# faar det samme allerede genererte materialet paa eksakt samme plassering.
import moonfiles as mf
game = mf.Spill(ROOT / 'Moonstonecd32-AMIGA.zip')
piv = game.les('WI1.P')
planes, palette, data = mf.piv_alle(piv)[0][0]
source = mf.plan_til_indeks(data, planes)
eye = bytes(source[y * 320 + x] for y in range(53, 66) for x in range(141, 179))
(ART / 'source/static-eye-indices.bin').write_bytes(eye)
for frame, count in ((3, 390), (4, 297)):
    name = f'{frame:03}'
    idx = (ART / f'source/indices/{name}.bin').read_bytes()
    mask = bytes(int(x == y and x != 0) for x, y in zip(idx, eye))
    assert sum(mask) == count
    index_identical_pixels = sum(mask)
    if frame == 4:
        # Samme originalindeks er ikke et anatomisk posebevis i fotomaterialet.
        # Hele det lukkede oeye-/brynfeltet bruker derfor egen nye master.
        mask = bytes(int(v and i // 38 < 2) for i, v in enumerate(mask))
    mask_file = f'source/shared-skin-{name}.bin'
    (ART / mask_file).write_bytes(mask)
    row = dict(record)
    row.update(kind='deling-av-uendret-hudmateriale',
        scope='Bare originale hud- og skyggepiksler som er identiske i CEL og WI1.P. Endrede oeyelokk har rutens egen genererte master.',
        frames=[frame], width=38, height=13,
        source_indices={name: sha(idx)}, allowed_indices=list(range(1, 32)),
        comparison_indices_file='source/static-eye-indices.bin',
        comparison_indices_sha256=sha(eye), comparison_piv_sha256=sha(piv),
        mask=mask_file, mask_sha256=sha(mask), mask_pixels=sum(mask),
        index_identical_pixels=index_identical_pixels,
        excluded_animated_anatomy_local_rect=[0, 2, 38, 13] if frame == 4 else None,
        alpha_path=ui_contours(mask, 38, 13, lambda c: bool(c)),
        original_rect=[141, 53, 179, 66],
        donor_crop_normalized=[121 / 250, 21 / 134, 38 / 250, 13 / 134])
    (ART / f'shared-skin-{name}.json').write_text(json.dumps(row, ensure_ascii=False, indent=2) + '\n')
    print(count, 'uendrede hudmaterialpiksler registrert for', name)
