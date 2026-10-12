"""Kontroller ferdige beistfragmenter direkte mot originalbanken og fotokildene."""
from pathlib import Path
import hashlib, json, sys
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT / 'tools'))
import moonfiles as mf
from hd_bestilling import utvid_indekser

sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
geometry_path = HERE / 'geometries-v3.json'
geometry = json.loads(geometry_path.read_text())
generation_path = HERE / 'generation-records-v1.json'
generation = json.loads(generation_path.read_text())
palette_path = HERE.parents[2] / 'palettes/cases/beast.json'
palette = json.loads(palette_path.read_text())
game = mf.Spill(ROOT / 'Moonstonecd32-AMIGA.zip')
bank = game.les('be1.c')
assert hashlib.sha256(bank).hexdigest() == palette['source_banks']['be1.c']
assert len({g['raw_sha256'] for g in generation}) == len(generation) == 6
assert len({g['call_id'] for g in generation}) == 6
originals = mf.cel_les(bank)[0]
rows = []
for c in geometry:
    source = originals[c['frame']]
    w, h = source['bredde'], source['hoyde']
    indices = utvid_indekser(mf.plan_til_indeks(source['data'], source['plan'], w, h), source['maske'])
    assert list(indices) == c['indices']
    assert hashlib.sha256(indices).hexdigest() == c['indices_sha256']
    assert c['source_palette_contract_sha256'] == sha(palette_path)
    photo = next(g for g in generation if g['key'] == c['key'])
    for name in ['raw', 'prompt', 'reference']:
        assert sha(HERE / photo[name]) == photo[name + '_sha256']
    path = HERE / 'packed-v3' / c['key']
    image = Image.open(path)
    assert image.mode == 'RGBA' and image.size == (w * 4, h * 4)
    shadow_checks = 0
    for q, index in enumerate(indices):
        x, y = q % w, q // w
        r, g, b, a = image.getpixel((x * 4 + 2, y * 4 + 2))
        assert (a >= 128) == bool(index), (c['key'], q, 'source alpha')
        if not index:
            continue
        material = c['material_labels'][q]
        if material == 4:
            assert r > g * 2 and r > b * 2, (c['key'], q, 'red eye')
        if material == 2:
            assert r >= g >= b, (c['key'], q, 'brown hide')
        if material == 1:
            assert max(r, g, b) <= 90, (c['key'], q, 'dark mane')
        if material == 5:
            assert index == 5 and y >= c['flat_shadow_top']
            for dy in range(4):
                for dx in range(4):
                    assert image.getpixel((x * 4 + dx, y * 4 + dy)) == (0, 0, 0, 255)
                    shadow_checks += 1
    rows.append(dict(key=c['key'], png_sha256=sha(path), raw_sha256=photo['raw_sha256'], source_alpha_midpoints=w*h, exact_original_flat_shadow_subpixels=shadow_checks))
report = dict(schema=1, status='passed', source_bank_sha256=hashlib.sha256(bank).hexdigest(), geometry_sha256=sha(geometry_path), generation_records_sha256=sha(generation_path), palette_contract_sha256=sha(palette_path), script_sha256=sha(Path(__file__)), assets=rows, source_alpha_midpoints=sum(r['source_alpha_midpoints'] for r in rows), exact_original_shadow_subpixels=sum(r['exact_original_flat_shadow_subpixels'] for r in rows))
output = HERE / 'verification/packing-independent-v3.json'
output.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({k:report[k] for k in ['status', 'source_alpha_midpoints', 'exact_original_shadow_subpixels']}))
