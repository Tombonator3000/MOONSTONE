"""Aktiver gjennomgaatte Math-fragmenter og kildeavgrenset fastfigur samlet."""
import argparse
import json
import shutil
from pathlib import Path
from PIL import Image
import hd_figurer_aktiver as figures
import moonfiles as mf

ROOT = figures.ROOT
checked = figures.checked
sha = figures.sha

def validate(delivery):
    files = figures.validate(delivery)
    for item in delivery['material_derivations']:
        checked(item['path'], item['sha256'])
    for item in delivery['entries']:
        record = json.loads(checked(item['pack_record'], item['pack_record_sha256']).read_text())
        assert record['output_sha256'] == item['png_sha256']
    alpha = delivery['alpha_proof']
    assert json.loads(checked(alpha['path'], alpha['sha256']).read_text())['status'] == 'passed'
    game = mf.Spill(ROOT/'Moonstonecd32-AMIGA.zip')
    manifest = json.loads((ROOT/'web/hd/manifest.json').read_text())
    for item in delivery['embedded_entries']:
        contract = json.loads(checked(item['source_contract'], item['source_contract_sha256']).read_text())
        original = game.les(contract['source_file'])
        assert sha(original) == item['source_file_sha256'] == contract['source_file_sha256']
        planes, raw_palette, data = mf.piv_alle(original)[0][0]
        indices = mf.plan_til_indeks(data, planes)
        assert sha(indices) == contract['source_indices_sha256']
        mask_path = Path(item['source_contract']).parent/'source/math-static-mask.bin'
        mask = checked(str(mask_path), item['source_mask_sha256']).read_bytes()
        x0,y0,x1,y1 = contract['rect']
        w,h = x1-x0,y1-y0
        assert len(mask) == w*h and sum(mask) == item['mask_pixels'] == 9758
        scene = next(s for s in manifest['scenes'] if s['id'] == item['scene_id'])
        assert scene['source_sha256'] == item['source_file_sha256']
        assert scene['preserve_regions'] == contract['preserve_regions']
        allowed_shadow = set(contract['additional_original_head_shadow']['local_positions'])
        for y in range(h):
            for x in range(w):
                i = y*w+x
                if not mask[i]:
                    continue
                c = indices[(y0+y)*320+x0+x]
                in_preserve = any(r['rect'][0]<=x0+x<r['rect'][2] and r['rect'][1]<=y0+y<r['rect'][3] and c in r['indices'] for r in scene['preserve_regions'])
                assert in_preserve or (i in allowed_shadow and c in (2,3,4,5))
        checked(item['raw'], item['raw_sha256'])
        checked(item['prompt'], item['prompt_sha256'])
        png = checked(item['png'], item['png_sha256'])
        assert any(item['png_sha256'] in checked(p['path'],p['sha256']).read_text() for p in delivery['proofs'])
        with Image.open(png) as image:
            assert image.mode == 'RGBA' and image.size == (w*4,h*4)
            pixels = image.load()
            for y in range(h):
                for x in range(w):
                    assert (pixels[x*4+2,y*4+2][3]>=128) == bool(mask[y*w+x])
        assert not any(f['path'].lower() == item['key'].lower() for f in manifest['files'])
        assert not any(o['key'] == item['overlay']['key'] for o in scene.get('overlays',[]))
    return files

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('delivery', type=Path)
    p.add_argument('--activate', action='store_true')
    a = p.parse_args()
    delivery = json.loads(a.delivery.read_text())
    files = validate(delivery)
    if a.activate:
        figures.activate(delivery, files)
        path = ROOT/'web/hd/manifest.json'
        manifest = json.loads(path.read_text())
        for item in delivery['embedded_entries']:
            target = ROOT/'web/hd'/item['key']
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(ROOT/item['png'],target)
            manifest['files'].append(dict(path=item['key'],bytes=target.stat().st_size,sha256=sha(target.read_bytes()),kind='base'))
            scene = next(s for s in manifest['scenes'] if s['id'] == item['scene_id'])
            scene.setdefault('overlays',[]).append(item['overlay'])
        manifest['files'].sort(key=lambda f:f['path'])
        manifest['images'] = sum(f['path'].endswith('.png') for f in manifest['files'])
        path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(status='activated' if a.activate else 'checked',fragments=len(delivery['entries']),embedded=len(delivery['embedded_entries']),PNG=len(files)+len(delivery['embedded_entries']))))

if __name__ == '__main__':
    main()
