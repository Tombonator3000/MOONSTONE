#!/usr/bin/env python3
"""Originalankret innebygd TAV-spiller med separat levende kappemaskefelt."""
import hashlib, json, sys
from collections import Counter, deque
from pathlib import Path
from PIL import Image
ART = Path(__file__).resolve().parent
ROOT = ART.parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import moonfiles as mf
from hd_ui_bygg import ui_contours
sha = lambda b: hashlib.sha256(b).hexdigest()
game = mf.Spill(ROOT / 'Moonstonecd32-AMIGA.zip')
data = game.les('tav.piv')
planes, raw, bank = mf.piv_alle(data)[0][0]
full = mf.plan_til_indeks(bank, planes)
rect = [90, 65, 225, 188]
x0, y0, x1, y1 = rect
w, h = x1 - x0, y1 - y0
mask, idx = [], []
steel = (1, 3, 4, 5, 17)
for y in range(y0, y1):
    for x in range(x0, x1):
        c = full[y * 320 + x]
        cape = 131 <= x < 223 and 67 <= y < 174 and 6 <= c <= 11
        helmet = 157 <= x < 209 and 78 <= y < 135 and c in steel
        arm = 92 <= x < 160 and 121 <= y < 178 and c in steel
        lower = 111 <= x < 160 and 168 <= y < 186 and c in steel
        foam = 103 <= x < 124 and 119 <= y < 129 and c in (1, 12, 13, 27, 28)
        mask.append(int(cape or helmet or arm or lower or foam))
        idx.append(c)
# PIV har ugjennomsiktige svarte skygger. Fyll bare lukkede nullfelt helt
# omgitt av den kildevalgte spilleren, aldri bord eller nabopersoner.
outside = set()
q = deque()
for y in range(h):
    for x in range(w):
        n = y * w + x
        if (x in (0, w - 1) or y in (0, h - 1)) and not mask[n]:
            outside.add(n)
            q.append(n)
while q:
    n = q.popleft()
    x, y = n % w, n // w
    for v in (n - 1 if x else -1, n + 1 if x + 1 < w else -1,
              n - w if y else -1, n + w if y + 1 < h else -1):
        if v >= 0 and not mask[v] and v not in outside:
            outside.add(v)
            q.append(v)
black = [n for n, c in enumerate(idx) if c == 0 and not mask[n] and n not in outside]
for n in black:
    mask[n] = 1
# Originalen dithrer nedre albuens svarte staalskygge med indeks0/5.
# Nullene mellom to staalankre paa samme kilderad er ugjennomsiktig figur,
# selv om den aapne dithringen har forbindelse til bakgrunnen. Bordindekser
# og nuller utenfor de dokumenterte staalankrene velges aldri.
dither_black = []
for y in range(168, 183):
    steel_x = [x for x in range(111, 160) if full[y * 320 + x] in steel]
    if not steel_x:
        continue
    for x in range(min(steel_x), max(steel_x) + 1):
        n = (y - y0) * w + x - x0
        if idx[n] == 0 and not mask[n]:
            mask[n] = 1
            dither_black.append(n)
assert sum(c in range(6, 11) and mask[n] for n, c in enumerate(idx)) == 3682
assert sum(c in range(6, 11) for c in full) - 3682 == 16
assert all(y0 + n // w >= 65 for n, v in enumerate(mask) if v)
palette = [[*mf.amiga_rgb(c), 255] for c in raw]
# Kildebevis: $08a3b2-$08a3be bruker $08a9b6 paa TAV-palett6..10.
# De fire originalpalettene er kontrollert i Math og i disassemblyen.
for i, c in enumerate((0x05d, 0x03b, 0x028, 0x016, 0x003), 6):
    palette[i] = [*mf.amiga_rgb(c), 255]
for folder in ('references', 'source', 'raw', 'prompts', 'verification'):
    (ART / folder).mkdir(exist_ok=True)
(ART / 'source/player-indices.bin').write_bytes(bytes(idx))
(ART / 'source/player-mask.bin').write_bytes(bytes(mask))
im = Image.new('RGBA', (w, h))
im.putdata([tuple(palette[c]) if mask[n] else (0, 0, 0, 0) for n, c in enumerate(idx)])
ref = ART / 'references/player-original-blue.png'
im.resize((w * 4, h * 4), Image.Resampling.NEAREST).save(ref)
row = dict(frame=0, width=w, height=h, target_width=w * 4, target_height=h * 4,
    source_bank='data/tav.piv', source_bank_sha256=sha(data),
    indices_file='source/player-indices.bin', indices_sha256=sha(bytes(idx)),
    alpha_indices_file='source/player-mask.bin', alpha_indices_sha256=sha(bytes(mask)),
    reference='references/player-original-blue.png', reference_sha256=sha(ref.read_bytes()),
    target='embedded/tav-player.png', scene='tavern',
    alpha_path=ui_contours(mask, w, h, lambda c: bool(c)),
    live_palette_mask_indices=[6, 7, 8, 9, 10],
    fill_missing_by_material=True)
record = dict(schema=1, kind='embedded-tavern-player',
    scope='Ekstra innebygd figur utenfor1779CEL-mastere. Original hjelm, hanske, arm, kappe/fjaer og eget oelkrus. DICE006..009 ligger over slik originalen gjoer.',
    source_file_sha256=sha(data), source_zip_sha256=sha((ROOT / 'Moonstonecd32-AMIGA.zip').read_bytes()),
    rect=rect, source_live_pixels=3682, excluded_bar_maid_live_pixels=16,
    selected_pixels=sum(mask), selected_indices=dict(Counter(c for n, c in enumerate(idx) if mask[n])),
    enclosed_original_black_positions=black,
    original_elbow_dither_shadow={'rect':[111,168,160,183],
        'indices':[0], 'row_anchor_indices':list(steel),
        'local_positions':dither_black,
        'method':'Only original0 positions between first/last original steel anchors on the same row; no table indices or positions outside the arm row silhouette.'},
    original_selection={'cape':[131,67,223,174], 'helmet':[157,78,209,135],
        'arm_and_mug':[92,121,160,178], 'lower_arm':[111,168,160,186],
        'mug_foam':[103,119,124,129]},
    source_evidence=['$08a224-$08a242: TAV.PIV og palett til08ceaa',
        '$08a3b2-$08a3be: palett6..10 gjennom08a9b6',
        '$08a9b6-$08aa42: aktiv_ridder+0x36 velger original draktpalett'],
    runtime_palette_status='Blue source palette derived from verified original routine; TAV current runtime must verify all four colors before activation',
    routes=[row], palettes={'tavern':{'rgba':palette}})
(ART / 'player-source-contract.json').write_text(json.dumps(record, indent=2) + '\n')
print(sum(mask), 'originalbundne figurpiksler;', len(black), 'lukkede svarte originalskygger;16barmaid-piksler utelatt')
