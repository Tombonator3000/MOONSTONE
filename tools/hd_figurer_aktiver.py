#!/usr/bin/env python3
"""Kontroller en eksplisitt gjennomgaatt figurleveranse foer standardpakken endres."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

from PIL import Image
import moonfiles as mf
import hd_bestilling as bestilling

ROOT = Path(__file__).resolve().parents[1]
sha = lambda data: hashlib.sha256(data).hexdigest()


def checked(path, digest):
    source = (ROOT / path).resolve()
    assert source.is_relative_to(ROOT), 'Fil utenfor prosjektet: ' + path
    assert sha(source.read_bytes()) == digest, 'Endret fil: ' + path
    return source


def validate(delivery):
    assert delivery['schema'] == 1
    assert delivery['visual_status'] == 'reviewed_original_and_runtime'
    game = mf.Spill(str(ROOT / 'Moonstonecd32-AMIGA.zip'))
    checked('Moonstonecd32-AMIGA.zip', delivery['source_zip_sha256'])
    for path, digest in delivery['production_code_sha256'].items():
        checked(path, digest)
    checked('web/build/moonstone-core.js', delivery['wasm_core_sha256'])
    proofs = {}
    for proof in delivery['proofs']:
        data = checked(proof['path'], proof['sha256']).read_bytes()
        report = json.loads(data)
        assert report['status'] == 'passed' and not report.get('errors'), proof['path']
        assert report['html_sha256'] == proof['html_sha256'], 'Annen runtime-HTML'
        html = checked(proof['html_path'], proof['html_sha256']).read_bytes()
        for path in [*delivery['production_code_sha256'], 'web/build/moonstone-core.js']:
            code = (ROOT / path).read_bytes().replace(b'</script', b'<\\/script')
            assert code in html, 'Runtime-HTML inneholder annen kode: ' + path
        proofs[proof['path']] = data.decode()
    assert proofs
    files = {}
    for entry in delivery['entries']:
        key = entry['key']
        bank, name = key.split('/')
        assert name == '%03d.png' % entry['frame'] and bank == entry['bank']
        original_bank = game.les('data/' + bank)
        assert sha(original_bank) == entry['source_bank_sha256'], 'Annen originalbank: ' + key
        original = mf.cel_les(original_bank)[0][entry['frame']]
        packed = mf.plan_til_indeks(original['data'], original['plan'], original['bredde'], original['hoyde'])
        indices = bestilling.utvid_indekser(packed, original['maske'])
        assert sha(indices) == entry['indices_sha256'], 'Annen originalrute: ' + key
        source = checked(entry['png'], entry['png_sha256'])
        with Image.open(source) as image:
            assert image.mode == 'RGBA'
            assert image.size == (original['bredde'] * 4, original['hoyde'] * 4)
        assert entry['runtime_asset_sha256'] == entry['png_sha256'], 'Runtimebevis gjelder annet bilde: ' + key
        assert entry['runtime_proof'] in proofs
        assert entry['runtime_asset_sha256'] in proofs[entry['runtime_proof']], 'PNG mangler bindende runtimebevis: ' + key
        if entry.get('master_key'):
            assert entry['master_key'] in {r['key'] for r in delivery['entries']}
            master = next(r for r in delivery['entries'] if r['key'] == entry['master_key'])
            assert master['indices_sha256'] == entry['indices_sha256']
            assert master['png_sha256'] == entry['png_sha256']
        else:
            checked(entry['raw'], entry['raw_sha256'])
            checked(entry['prompt'], entry['prompt_sha256'])
            assert entry['generation_tool'] == 'builtin_image_gen'
        assert key.lower() not in {p.lower() for p in files}, 'Duplikat: ' + key
        files[key] = source
        live = bestilling.maskefarger(bank, entry['frame'])
        if live.intersection(indices):
            mask = checked(entry['mask'], entry['mask_sha256'])
            with Image.open(mask) as image:
                assert image.mode == 'RGBA' and image.size == (original['bredde'] * 4, original['hoyde'] * 4)
                pixels = image.load()
                for y in range(image.height):
                    for x in range(image.width):
                        index = indices[(y // 4) * original['bredde'] + x // 4]
                        red, green, blue, alpha = pixels[x, y]
                        assert red == (index + 1 if index in live else 0), 'Feil levende indeks: ' + key
                        assert alpha == 255 and (blue == 255 if red else blue == 0)
            assert entry['mask_sha256'] in proofs[entry['runtime_proof']], 'Masken mangler runtimebevis'
            files[key.replace('.png', '.mask.png')] = mask
        else:
            assert not entry.get('mask'), 'Uventet levende maske: ' + key
    return files


def activate(delivery, files):
    manifest_path = ROOT / 'web/hd/manifest.json'
    manifest = json.loads(manifest_path.read_text())
    old = {r['path'].lower(): r for r in manifest['files']}
    assert not ({p.lower() for p in files} & set(old)), 'Aktive figurer skal erstattes i en egen eksplisitt revisjon'
    for key, source in files.items():
        target = ROOT / 'web/hd' / key
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        data = target.read_bytes()
        manifest['files'].append(dict(path=key, bytes=len(data), sha256=sha(data), kind='base'))
    manifest['files'].sort(key=lambda r: r['path'])
    manifest['images'] = sum(r['path'].endswith('.png') for r in manifest['files'])
    assert all(next(r for r in manifest['files'] if r['path'].lower() == key) == row for key, row in old.items())
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('delivery', type=Path)
    parser.add_argument('--activate', action='store_true')
    args = parser.parse_args()
    delivery = json.loads(args.delivery.read_text())
    files = validate(delivery)
    if args.activate:
        activate(delivery, files)
    print(json.dumps(dict(status='activated' if args.activate else 'checked_not_activated',
                          routes=len(delivery['entries']), png_files=len(files))))


if __name__ == '__main__':
    main()
