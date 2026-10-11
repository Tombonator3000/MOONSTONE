"""Kontroller nye kandidatfiler mot originalbildene og lag lik visningsstoerrelse."""
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw
import sys

ART = Path(__file__).resolve().parent
FIGURES = ART.parents[1]
ROOT = ART.parents[3]
sys.path.insert(0,str(ROOT/'tools'))
import moonfiles as mf
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
sources = json.loads((ART/'source-contracts.json').read_text())
records = json.loads((ART/'generation-records.json').read_text())['assets']
assets = []
checks = 0
for c in sources['entries']:
    final = ART/'packed'/c['key']
    if not final.exists():
        continue
    source = FIGURES/c['original']['path']
    assert sha(source) == c['original']['sha256']; checks += 1
    original = Image.open(source).convert('RGBA')
    new = Image.open(final)
    assert new.mode == 'RGBA' and new.size == (c['target_width'], c['target_height']); checks += 1
    record = next(r for r in records if r['key'] == c['key'])
    assert sha(ART/'raw'/c['key']) == record['raw_sha256']; checks += 1
    covered = empty = 0
    for y in range(original.height):
        for x in range(original.width):
            opaque = original.getpixel((x, y))[3] > 0
            a = new.getpixel((x*4+2, y*4+2))[3]
            assert (a >= 250 if opaque else a == 0), (c['key'], x, y, opaque, a)
            checks += 1
            if opaque: covered += 1
            else: empty += 1
    colors = {pixel[:3] for pixel in new.get_flattened_data() if pixel[3] > 220}
    assert len(colors) > 8, c['key']; checks += 1
    source_alpha = original.resize(new.size, Image.Resampling.NEAREST)
    pairs = [(a[3] > 127, b[3] > 127) for a,b in zip(source_alpha.get_flattened_data(),new.get_flattened_data())]
    iou = sum(a and b for a,b in pairs) / sum(a or b for a,b in pairs)
    assert iou >= .90, (c['key'], iou); checks += 1
    dark = 0
    for n,i in enumerate(c['indices']):
        if i not in (4,5): continue
        rgb = new.getpixel(((n%c['width'])*4+2,(n//c['width'])*4+2))[:3]
        assert max(rgb) <= (90 if i == 4 else 12), (c['key'],n,i,rgb)
        dark += 1; checks += 1
    mask_record = None
    if c['needs_mask']:
        mask_path = final.with_name(final.stem+'.mask.png')
        mask = Image.open(mask_path).convert('RGBA')
        assert mask.size == new.size; checks += 1
        live = {6,7,8,9,10,11}
        expected = Image.frombytes('L', original.size,bytes(c['indices'])).resize(new.size,Image.Resampling.NEAREST)
        active = 0
        for i,m in zip(expected.get_flattened_data(),mask.get_flattened_data()):
            assert m[0] == (i+1 if i in live else 0) and m[2] == (255 if i in live else 0) and m[3] == 255
            active += i in live; checks += 1
        mask_record = dict(sha256=sha(mask_path), live_indices=sorted(set(c['indices'])&live),colored_pixels=active)
    assets.append(dict(key=c['key'], png_sha256=sha(final), covered_source_centers=covered,
                       transparent_source_centers=empty, material_colors=len(colors),final_alpha_iou=iou,
                       preserved_dark_centers=dark,mask=mask_record))

aliases = []
game = mf.Spill(str(ROOT/'Moonstonecd32-AMIGA.zip'))
game_files = {k.lower():v for k,v in game.filer.items()}
for a in json.loads((ART/'queue-subset.json').read_text())['aliases']:
    master = ART/'packed'/a['master_key']; target = ART/'packed'/a['key']
    original = next(c for c in sources['entries'] if c['key'] == a['master_key'])
    assert a['indices_sha256'] == original['indices_sha256']; checks += 1
    bank = game_files[a['source_bank']['path'].lower()]
    assert hashlib.sha256(bank).hexdigest() == a['source_bank']['sha256']; checks += 1
    frames,_ = mf.cel_les(bank); frame=frames[a['frame']]
    packed = mf.plan_til_indeks(frame['data'],frame['plan'],a['width'],a['height'])
    expanded = bytes(a['index_remap'][str(v)] for v in packed)
    assert hashlib.sha256(expanded).hexdigest() == a['indices_sha256']; checks += 1
    assert (a['width'],a['height']) == (original['width'],original['height']); checks += 1
    assert target.exists(), a['key']; checks += 1
    assert sha(target) == sha(master); checks += 1
    aliases.append(dict(key=a['key'],master_key=a['master_key'],sha256=sha(target),source_bank_sha256=a['source_bank']['sha256']))

sheet = Image.new('RGB', (1500, ((len(assets)+2)//3)*220), (29, 29, 29))
draw = ImageDraw.Draw(sheet)
for n, a in enumerate(assets):
    c = next(c for c in sources['entries'] if c['key'] == a['key'])
    x, y = (n % 3)*500, (n//3)*220
    draw.text((x+8, y+5), a['key']+'  original | HD (begge 4x)', fill='white')
    source_path = ART/'references/KN4.ob/025-live-blue.png' if c['frame']==25 else FIGURES/c['original']['path']
    source = Image.open(source_path).convert('RGBA').resize((c['target_width'], c['target_height']), Image.Resampling.NEAREST)
    new = Image.open(ART/'packed'/a['key'])
    sheet.paste(source, (x+10, y+32), source)
    sheet.paste(new, (x+260, y+32), new)
sheet.save(ART/'comparison.png')
report = dict(schema=1, status='passed', checks=checks, assets=assets,
              aliases=aliases,
              source_contracts_sha256=sha(ART/'source-contracts.json'),
              scope='Original-PNG-SHA, rawkvittering, 4xmaal, alle kildepikselmidtpunkter, sluttalfa-IoU >= 0.90, moerke4/5-felt, palettmaske og eksakte kopier. Visuell kontroll og faktisk runtime kreves separat.')
(ART/'verification/packing-test.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(dict(status=report['status'], checks=checks, assets=len(assets))))
