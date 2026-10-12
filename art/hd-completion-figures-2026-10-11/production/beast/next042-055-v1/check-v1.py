"""Uavhengig kilde-, foto-, alfa- og maskekontroll for be1.c/042..054."""
from pathlib import Path
import hashlib
import json
import sys
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT / 'tools'))
import moonfiles as mf
from hd_bestilling import utvid_indekser, maskefarger

sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
geometry_path = HERE / 'geometries-v1.json'
geometry = json.loads(geometry_path.read_text())
generation_path = HERE / 'generation-records-v1.json'
generation = json.loads(generation_path.read_text())
palette_path = HERE.parents[2] / 'palettes/cases/beast.json'
palette = json.loads(palette_path.read_text())
bank = mf.Spill(ROOT / 'Moonstonecd32-AMIGA.zip').les('be1.c')
assert hashlib.sha256(bank).hexdigest() == palette['source_banks']['be1.c']
assert len({g['raw_sha256'] for g in generation}) == len(generation) == 10
assert len({g['generation_call_id'] for g in generation}) == 10
assert next(g for g in generation if g['key']=='be1.c/049.png')['raw']=='raw/049-v2.png'
assert next(g for g in generation if g['key']=='be1.c/050.png')['raw']=='raw/050-v2.png'
originals = mf.cel_les(bank)[0]
rows = []
sheet = Image.new('RGB', (1200, 4 * 265), '#303030')
draw = ImageDraw.Draw(sheet)
for position, c in enumerate(geometry):
    source = originals[c['frame']]
    w, h = source['bredde'], source['hoyde']
    indices = utvid_indekser(mf.plan_til_indeks(source['data'], source['plan'], w, h), source['maske'])
    assert list(indices) == c['indices']
    assert hashlib.sha256(indices).hexdigest() == c['indices_sha256']
    assert c['source_palette_contract_sha256'] == sha(palette_path)
    photo = next((g for g in generation if g['key'] == c['key']), None)
    if photo:
        for name in ['raw','prompt','reference']:assert sha(HERE/photo[name])==photo[name+'_sha256']
    else:assert c['preserved_original_black_shadow'] and c['frame']==54
    path = HERE / 'packed-v1' / c['key']
    image = Image.open(path)
    assert image.mode == 'RGBA' and image.size == (w * 4, h * 4)
    mask = Image.new('RGBA', image.size, (0, 0, 0, 255))
    used = maskefarger('be1.c', c['frame']) & set(indices)
    assert bool(used) == c['needs_mask']
    for y in range(h * 4):
        for x in range(w * 4):
            index = indices[(y // 4) * w + x // 4]
            if index in used:
                r, g, b, a = image.getpixel((x, y))
                assert r == g == b, (c['key'], x, y, 'neutral photographic cloth')
                mask.putpixel((x, y), (index + 1, r, 255, 255))
    mask_path = path.with_name(path.stem + '.mask.png')
    if c['needs_mask']:
        # Masken er en produksjonskandidat; originalbanken endres ikke.
        if mask_path.exists():
            assert Image.open(mask_path).tobytes() == mask.tobytes()
        else:
            mask.save(mask_path)
    if c['preserved_original_black_shadow']:
        expected = Image.new('RGBA', (w, h))
        expected.putdata([(0, 0, 0, 255) if i else (0, 0, 0, 0) for i in indices])
        assert image.tobytes() == expected.resize((w * 4, h * 4), Image.Resampling.NEAREST).tobytes(), 'Hele originalskyggen maa vaere identisk'
    motion_checks = 0
    for q, index in enumerate(indices):
        x, y = q % w, q // w
        r, g, b, a = image.getpixel((x * 4 + 2, y * 4 + 2))
        assert (a >= 128) == bool(index), (c['key'], q, 'source alpha')
        if not index:
            continue
        material = c['material_labels'][q]
        if index==5:assert (r,g,b)==(0,0,0),(c['key'],q,'svart originalcelle')
        if material==11:assert r>20 and r>g*1.5 and r>b*1.5,(c['key'],q,'roedt fotomateriale')
        if material == 1:
            assert max(r, g, b) <= 90, (c['key'], q, 'dark mane')
        if material in (8, 9):
            assert r == g == b, (c['key'], q, 'neutral metal or cloth')
        if q in c['original_motion_cells']:
            assert index == 3
            for dy in range(4):
                for dx in range(4):
                    assert image.getpixel((x * 4 + dx, y * 4 + dy)) == tuple(c['palette'][3][:3] + [255])
                    motion_checks += 1
    if c['frame'] == 41:
        detached = [cc for cc in c['alpha_connected_components'] if {indices[q] for q in cc} == {4}]
        assert detached and all(q not in c['original_motion_cells'] for cc in detached for q in cc)
    original = Image.new('RGBA', (w, h))
    original.putdata([tuple(c['palette'][i][:3] + [255]) if i else (0, 0, 0, 0) for i in indices])
    display = image.copy()
    if c['needs_mask']:
        for y in range(h * 4):
            for x in range(w * 4):
                i, light, active, _ = mask.getpixel((x, y))
                if active:
                    display.putpixel((x, y), tuple(min(255, round(v * light / 128)) for v in c['palette'][i - 1][:3]) + (image.getpixel((x, y))[3],))
    # Kilde og kandidat bruker samme utsnitt og sideforhold.
    sx, sy = position % 3 * 400, position // 3 * 265
    draw.text((sx + 8, sy + 5), f"{c['number']} original / HD   {w}x{h}", fill='white')
    scale = min(2, 190 / (w * 4), 220 / (h * 4))
    size = (max(1, round(w * 4 * scale)), max(1, round(h * 4 * scale)))
    for col, im in enumerate([original.resize((w * 4, h * 4), Image.Resampling.NEAREST), display]):
        im = im.resize(size, Image.Resampling.NEAREST if col == 0 else Image.Resampling.LANCZOS)
        sheet.paste(im, (sx + 6 + col * 198, sy + 30), im)
    rows.append(dict(key=c['key'], png_sha256=sha(path), raw_sha256=photo['raw_sha256'] if photo else None, source_alpha_midpoints=w*h, source_plane_mask=source['maske'], exact_original_motion_subpixels=motion_checks, mask_sha256=sha(mask_path) if c['needs_mask'] else None, mask_cells=sum(i in used for i in indices)))
report = dict(schema=1, status='passed', source_bank_sha256=hashlib.sha256(bank).hexdigest(), geometry_sha256=sha(geometry_path), generation_records_sha256=sha(generation_path), palette_contract_sha256=sha(palette_path), script_sha256=sha(Path(__file__)), assets=rows, source_alpha_midpoints=sum(r['source_alpha_midpoints'] for r in rows), exact_original_motion_subpixels=sum(r['exact_original_motion_subpixels'] for r in rows))
(HERE / 'verification/packing-independent-v1.json').write_text(json.dumps(report, indent=2) + '\n')
sheet.save(HERE / 'comparison-v1.png')
runtime = []
for c, row in zip(geometry, rows):
    runtime.append({**c, 'packed_candidate_path': str((HERE / 'packed-v1' / c['key']).relative_to(ROOT)), 'candidate_png_sha256': row['png_sha256'], 'mask_path': str((HERE / 'packed-v1' / c['key']).with_name(c['number'] + '.mask.png').relative_to(ROOT)) if c['needs_mask'] else None, 'candidate_mask_sha256': row['mask_sha256'], 'mask_plane_mask': row['source_plane_mask']})
(HERE / 'runtime-geometries-v1.json').write_text(json.dumps(runtime, indent=2) + '\n')
print(json.dumps({k: report[k] for k in ['status', 'source_alpha_midpoints', 'exact_original_motion_subpixels']}))
