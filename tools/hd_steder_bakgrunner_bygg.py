#!/usr/bin/env python3
"""Koble stedsskjermer og ferdig sammensatte kampbakgrunner til HD."""
import hashlib
import json
import shutil
from pathlib import Path
from PIL import Image
import moonfiles as mf

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / 'art/hd-all-locations-2026-10-11'
SHA = lambda b: hashlib.sha256(b).hexdigest()


def main():
    manifest = json.loads((ROOT/'web/hd/manifest.json').read_text())
    plan = json.loads((ROOT/'art/photoreal/production-plan-2026-10-03.json').read_text())
    sources = {a['id']: a for a in plan['assets']}
    rows = [
        ('healer', 'hea.piv', [0, 0, 320, 161], []),
        ('mystic', 'mys.piv', [0, 0, 320, 161], []),
        ('math-tower', 'WI2.P', [0, 0, 320, 200], []),
        ('math-balcony', 'WI1.P', [0, 0, 320, 181], []),
        ('stonehenge', 'hen1.p', [0, 0, 320, 200], []),
        ('stonehenge-intro', 'bg5.piv', [0, 0, 320, 200], []),
        ('dice', 'dice.piv', [0, 0, 320, 200], []),
        ('stonehenge-knight', 'bg2a.PIV', [0, 0, 320, 200], []),
        ('stonehenge-overhead', 'bg3.PIV', [0, 0, 320, 200], []),
        ('intro-stars', 'bg8.PIV', [0, 0, 320, 200], []),
        ('message-banner', 'message.piv', [0, 0, 320, 43], [0]),
        ('mindscape-logo', 'mindscape', [0, 0, 320, 200], [0, *range(16, 32)]),
    ]
    registry = []
    for ident, name, rect, protected in rows:
        a = sources[f'piv_background:{name}:000']
        image_id = 'stonehenge' if ident == 'stonehenge-intro' else 'math-balcony-architecture' if ident == 'math-balcony' else ident
        raw = ART/'raw'/f'{image_id}.png'
        if not raw.is_file():
            continue
        key = a['routing']['hash_candidate']
        if not key:
            planes = mf.piv_alle(mf.Spill(str(ROOT/'Moonstonecd32-AMIGA.zip')).les('data/'+name))[0][0][2]
            h = 2166136261
            for b in planes.ljust(40000, b'\0'):
                h = ((h ^ b) * 16777619) & 0xffffffff
            key = f'bg/{h:08x}.png'
        assert key and key.startswith('bg/')
        ref = ROOT/'assets/gfx'/name/'0.png'
        assert SHA(ref.read_bytes()) == a['source']['png_sha256']
        target_ref = ART/'references'/f'{ident}.png'
        shutil.copyfile(ref, target_ref)
        target = ROOT/'web/hd'/key
        shutil.copyfile(raw, target)
        row = dict(id=ident, file=name, frame=0,
                   source_sha256=a['source']['archive_file_sha256'],
                   hash=Path(key).stem, rect=rect, minimum_match=0.90,
                   minimum_detail=0.90, foreground_padding=0,
                   uv_rect=[0, 0, 320, 200])
        if protected:
            row['protected_indices'] = protected
        if ident == 'dice':
            row['protected'] = [[157, 117, 317, 185]]
        if ident == 'message-banner':
            row['minimum_match'] = 0.90
        if ident == 'stonehenge-knight':
            # Den animerte rustningsarmen krever romsligere fullbildematching.
            # Hele bildet kontrolleres, saa en annen Stonehenge-scene avvises.
            row['minimum_match'] = row['minimum_detail'] = 0.85
            # Indeks 0 er et hull der program viser tidligere bakgrunn/fliser.
            row['match_ignore_indices'] = [0]
            row['protected_indices'] = [0]
            row['preserve_regions'] = [dict(rect=[185, 0, 320, 200], indices=[*range(1, 12), *range(19, 23)])]
        if ident == 'stonehenge-overhead':
            row['protected'] = [[145, 91, 175, 116]]
            row['preserve_regions'] = [dict(rect=[112, 70, 214, 140], indices=[1, 2, 3, 4, 5])]
        if ident == 'intro-stars':
            row['protected'] = [[0, 0, 320, 142]]
            row['preserve_regions'] = [dict(rect=[130, 126, 180, 184], indices=[5, 8, 15, 19, 20, 21, 30, 31])]
        if ident == 'math-balcony':
            # Math er delvis bakt i PIV og delvis animert i Wi1.C.
            # Bevar figuren mens bare arkitekturen faar nytt materiale.
            row['preserve_regions'] = [
                dict(rect=[20, 32, 270, 166], indices=[6,7,8,9,10,11,12,15,16,17,18,19,20,21,23,24,26]),
                dict(rect=[140, 38, 178, 74], indices=[0,1,22]),
            ]
        manifest['scenes'] = [s for s in manifest.get('scenes', []) if s['id'] != ident] + [row]
        registry.append(dict(id=ident, kind='place', source=name, frame=0,
            reference=f'references/{ident}.png', raw=f'raw/{image_id}.png', route=key,
            source_sha256=a['source']['archive_file_sha256'], raw_sha256=SHA(raw.read_bytes()),
            dimensions=list(Image.open(raw).size), prompt=f'prompts/{image_id}.txt',
            tool='ChatGPT built-in image generator', exact_model_version=None))
    for a in sources.values():
        if a['kind'] != 'runtime_background':
            continue
        name = a['id'].split(':')[1]
        raw = ART/'raw'/f'{name}.png'
        if not raw.is_file():
            continue
        key = a['routing']['hash_path']
        ref = ROOT/'art/photoreal/references/runtime_background'/f'{name}.png'
        assert SHA(ref.read_bytes()) == a['source']['png_sha256']
        shutil.copyfile(ref, ART/'references'/f'{name}.png')
        shutil.copyfile(raw, ROOT/'web/hd'/key)
        registry.append(dict(id=name, kind='combat', source=name,
            reference=f'references/{name}.png', raw=f'raw/{name}.png', route=key,
            source_sha256=a['source']['archive_file_sha256'], raw_sha256=SHA(raw.read_bytes()),
            dimensions=list(Image.open(raw).size), prompt=f'prompts/{name}.txt',
            tool='ChatGPT built-in image generator', exact_model_version=None))
    files = {f['path']: f for f in manifest['files']}
    for row in registry:
        p = ROOT/'web/hd'/row['route']
        files[row['route']] = dict(path=row['route'], sha256=SHA(p.read_bytes()),
            bytes=p.stat().st_size, kind='background')
    manifest['files'] = sorted(files.values(), key=lambda f: f['path'])
    manifest['images'] = sum(f['path'].endswith('.png') for f in manifest['files'])
    (ROOT/'web/hd/manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n')
    (ART/'assets.json').write_text(json.dumps(dict(schema=1, assets=registry), ensure_ascii=False, indent=2)+'\n')
    print(f'{len(registry)} bakgrunnskoblinger registrert, {len(set(r["route"] for r in registry))} ulike bilder.')


if __name__ == '__main__':
    main()
