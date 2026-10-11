#!/usr/bin/env python3
"""Arkiver eksisterende HD-råbilder og bygg den kildevaliderte standardpakken."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def copy(source, target, expected=None):
    assert source.is_file(), source
    if expected:
        assert sha(source) == expected, source
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists() or sha(source) != sha(target):
        shutil.copyfile(source, target)
    assert sha(source) == sha(target)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    args = parser.parse_args()
    current = json.loads((ROOT / 'web/hd/manifest.json').read_text())
    if current.get('scenes') or any(f['path'] == 'text.json' for f in current['files']):
        parser.error('Historisk 48-bilders import kan ikke overskrive den utvidede HD-pakken. Bruk den bevarte produksjonsplanen som referanse.')
    old = args.source.resolve()
    art = ROOT / 'art/photoreal'
    art.mkdir(parents=True, exist_ok=True)
    plan = json.loads((old / 'art/photoreal/plan.json').read_text())
    package = old / 'art/photoreal/packs/title-menu-walk-moon-candidates'
    files = {}
    for row in json.loads((package / 'manifest.json').read_text())['files']:
        copy(package / row['path'], ROOT / 'web/hd' / row['path'], row['sha256'])
        files[row['path']] = row['sha256']
    for a in plan['assets']:
        if a['kind'] == 'runtime_background' and a['status'] == 'runtime_verified':
            assert a['routing']['generated_runtime_verified'] is True
            path = a['routing']['hash_path']
            copy(old / a['output']['path'], ROOT / 'web/hd' / path, a['output']['sha256'])
            files[path] = a['output']['sha256']
    images = [p for p in files if p.endswith('.png')]
    assert len(images) == 48
    manifest = {'schema': 1, 'scope': '48 eksisterende råbilder: 33 bakgrunner, 5 blå metodeposer, 5 menybilder og 5 månefaser. Øvrige arkivruter er ikke aktivert.',
                'images': len(images), 'background_cache_limit': 4,
                'files': [{'path': p, 'sha256': files[p], 'bytes': (ROOT / 'web/hd' / p).stat().st_size,
                           'kind': 'background' if p.startswith('bg/') else 'base'} for p in sorted(files)]}
    (ROOT / 'web/hd/manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    active = {files[p] for p in images}
    rows = []
    for a in plan['assets']:
        o = a.get('output') or {}
        if not o.get('path'):
            continue
        copy(old / o['path'], ROOT / o['path'], o['sha256'])
        source = a['source']
        runtime = source.get('runtime_reference')
        palette = source.get('palette_reference')
        if runtime and runtime.get('verified'):
            sp, digest, label = runtime['png_path'], runtime['png_sha256'], 'Original med målt spillpalett'
        elif palette:
            sp, digest, label = palette['path'], palette['sha256'], 'Original med arbeidsreferanse for palett'
        else:
            sp, digest, label = source['png_path'], source['png_sha256'], 'Originaluttrekk; paletten kan være forhåndsvisning'
        ref = 'art/photoreal/references/' + a['id'].replace(':', '/') + '.png'
        copy(old / sp, ROOT / ref, digest)
        rows.append({'id': a['id'], 'status': a['status'], 'photo': o['path'], 'photo_sha256': o['sha256'],
                     'source': ref, 'source_sha256': digest, 'palette_label': label,
                     'dimensions': o['dimensions'], 'prompt': o.get('prompt_path'),
                     'notes': a['qa'].get('notes', []), 'enabled_in_game': o['sha256'] in active})
    for bank, selected in [('bg1b.PIV', 'selected-80.json'), ('bg1a.PIV', 'checkpoints/044/selected-80.json')]:
        path = old / 'art/photoreal/review/piv-tiles' / bank / selected
        data = json.loads(path.read_text())
        copy(path, art / 'tile-checkpoints' / bank / 'selected.json')
        for t in data['tiles']:
            o = t.get('selected') or {}
            if not o.get('path') or not o['path'].startswith('art/photoreal/candidates/'):
                continue
            copy(old / o['path'], ROOT / o['path'], o['sha256'])
            ref = 'art/photoreal/references/piv-tiles/' + bank + '/' + str(t['local_tile']).zfill(3) + '.png'
            copy(old / t['source_png'], ROOT / ref, t['source_png_sha256'])
            rows.append({'id': t['id'], 'status': t['status'], 'photo': o['path'], 'photo_sha256': o['sha256'],
                         'source': ref, 'source_sha256': t['source_png_sha256'], 'palette_label': 'Original flis; ingen spillintegrasjon',
                         'dimensions': o['dimensions'], 'prompt': o.get('prompt_path'), 'notes': t.get('qa', {}).get('notes', []),
                         'enabled_in_game': False})
    catalog = {'schema': 1, 'scope': 'Bevarte kandidater og valgte underfliser. Spillintegrasjon og kunstnerisk sluttgodkjenning er separate.',
               'original_plan_summary': plan['summary'], 'raw_png_files': len(list((art / 'candidates').rglob('*.png'))),
               'selected_entries': len(rows), 'rows': rows}
    (art / 'catalog.json').write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + '\n')
    copy(old / 'art/photoreal/plan.json', art / 'production-plan-2026-10-03.json')
    print(json.dumps({'game_images': len(images), 'backgrounds': sum(p.startswith('bg/') for p in images),
                      'selected_entries': len(rows), 'raw_png_files': catalog['raw_png_files']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
