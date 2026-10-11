"""Uavhengig kontroll av originalkilde, silhuett og symbolregioner i pakkede kandidater."""
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from PIL import Image, ImageDraw

ART = Path(__file__).resolve().parent
ROOT = ART.parent.parent
sys.path.insert(0, str(ROOT/'tools'))
import moonfiles as mf


def sha(b):
    return hashlib.sha256(b).hexdigest()


def family(c, rgb):
    r, g, b = rgb[:3]
    if c['source']['file'] == 'ki.cel':
        return 'leaf' if g > r*1.08 and g > b else 'bark'
    if c['source']['file'] == 'dice.cel':
        if c['source']['frame'] == 1:
            return 'light' if g > r*.48 else 'field'
        if c['source']['frame'] == 0:
            return 'light' if g > r*.68 else 'field'
        return 'light' if r > g*.75 and b > g*.65 else 'field'
    return 'photo'


def expected_family(c, index):
    r, g, b = c['palette'][index][:3]
    if c['source']['file'] == 'ki.cel':
        return 'leaf' if g > r*1.1 and g > b*1.05 else 'bark'
    if c['source']['file'] == 'dice.cel':
        return 'light' if (index != 15 if c['source']['frame'] == 1 else index == 3) else 'field'
    return 'photo'


def main():
    contracts = json.loads((ART/'source-contracts.json').read_text())
    meta = {m['key']: m for m in json.loads((ART/'fragment-icons.json').read_text())['entries']}
    packing = {m['key']: m for m in json.loads((ART/'packing-report.json').read_text())['assets']}
    game = mf.Spill(str(ROOT/'Moonstonecd32-AMIGA.zip'))
    report = {'schema': 1, 'created_at': datetime.now(timezone.utc).isoformat(), 'checks': [], 'assets': [],
              'scope': 'Original ZIP/CEL/utvidede plan, native referanse, 8x RGBA, opake og transparente kildepikselmidtpunkter, materialfamilier. Visuell kvalitet vurderes separat.'}

    def check(name, passed):
        assert passed, name
        report['checks'].append(name)

    check('eleven_unique_contracts', len(contracts['entries']) == len(meta) == 11)
    gallery = Image.new('RGB', (1100, 2450), (40, 40, 40))
    draw = ImageDraw.Draw(gallery)
    for n, c in enumerate(contracts['entries']):
        key, source = c['key'], c['source']
        bank = game.les(source['file'])
        check(key+'_bank_sha', sha(bank) == source['bank_sha256'])
        frames, _ = mf.cel_les(bank)
        f = frames[source['frame']]
        w, h = f['bredde'], f['hoyde']
        check(key+'_source_size', [w, h] == [c['width'], c['height']])
        packed = mf.plan_til_indeks(f['data'], f['plan'], w, h)
        bits = [1 << p for p in range(5) if f['maske'] & (1 << p)]
        indices = [sum(bit for p, bit in enumerate(bits) if v & (1 << p)) for v in packed]
        check(key+'_expanded_indices_sha', sha(bytes(indices)) == c['indices_sha256'])
        check(key+'_frozen_indices', indices == c['indices'])
        if source['file'] in ('mys.cel', 'dice.cel'):
            piv = 'hea.piv' if source['file'] == 'mys.cel' and source['frame'] == 1 else source['file'].replace('.cel', '.piv')
            _, palette, _ = mf.piv_alle(game.les(piv))[0][0]
            palette = [mf.amiga_rgb(v) for v in palette]
            check(key+'_piv_palette', all(c['palette'][i][:3] == list(palette[i][:3]) for i in c['source_colors']))
        original = Image.open(ART/'references'/(key+'-native.png')).convert('RGBA')
        check(key+'_native_reference', list(original.getdata()) == [tuple(c['palette'][i][:3])+(255 if i else 0,) for i in indices])
        file = ART/'packed'/(key+'.png')
        image = Image.open(file)
        check(key+'_rgba', image.mode == 'RGBA')
        check(key+'_8x_dimensions', image.size == (w*8, h*8))
        check(key+'_packed_hash', sha(file.read_bytes()) == packing[key]['packed_sha256'])
        check(key+'_raster_metadata', meta[key]['render_mode'] == 'raster')
        filled = transparent = material = 0
        for y in range(h):
            for x in range(w):
                index, pixel = indices[y*w+x], image.getpixel((x*8+4, y*8+4))
                if index:
                    check(key+f'_opaque_center_{x}_{y}', pixel[3] >= 250)
                    filled += 1
                    if source['file'] != 'mys.cel':
                        check(key+f'_material_center_{x}_{y}', family(c, pixel) == expected_family(c, index))
                        material += 1
                else:
                    check(key+f'_transparent_center_{x}_{y}', pixel[3] == 0)
                    transparent += 1
        colors = len({p[:3] for p in image.getdata() if p[3] >= 250})
        check(key+'_material_not_flat_palette', colors > len(c['source_colors'])*8)
        y = n*220
        draw.text((10, y+4), key+' original / kildebundet HD-materiale', fill='white')
        for x, im in [(10, original.resize((w*8, h*8), Image.Resampling.NEAREST)), (560, image)]:
            im = im.copy()
            im.thumbnail((520, 185), Image.Resampling.NEAREST)
            gallery.paste(im, (x+(520-im.width)//2, y+25), im)
        report['assets'].append({'key': key, 'source': source, 'original_size': [w, h], 'indices_sha256': c['indices_sha256'], 'candidate': str(file.relative_to(ROOT)), 'packed_sha256': sha(file.read_bytes()), 'opaque_centers': filled, 'transparent_centers': transparent, 'material_centers': material, 'distinct_material_colors': colors})
    gallery.save(ART/'comparison.png')
    report['status'] = 'passed'
    report['check_count'] = len(report['checks'])
    (ART/'verification').mkdir(exist_ok=True)
    (ART/'verification/packing-test.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({'status': report['status'], 'checks': report['check_count'], 'assets': len(report['assets']), 'opaque_centers': sum(a['opaque_centers'] for a in report['assets']), 'transparent_centers': sum(a['transparent_centers'] for a in report['assets'])}))


if __name__ == '__main__':
    main()
