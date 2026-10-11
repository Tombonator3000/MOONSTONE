#!/usr/bin/env python3
"""Aktiver gjennomgaatte rasterikoner og oppdater standardpakkens hasher."""
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / 'art/faithful-hd-icons-2026-10-11'


def main():
    assets = json.loads((ART/'assets.json').read_text())['assets']
    report = {a['key']: a for a in json.loads((ART/'packing-report.json').read_text())['assets']}
    candidate = json.loads((ART/'raster-icons.json').read_text())
    active_path = ROOT/'web/hd/icons.json'
    active = json.loads(active_path.read_text())
    changed = {'icons.json'}
    for a in assets:
        if a['review_status'] != 'reviewed_for_runtime':
            continue
        key = a['key']
        packed = ART/'packed'/f'{key}.png'
        raw = ART/a['raw']
        assert hashlib.sha256(raw.read_bytes()).hexdigest() == report[key]['raw_sha256'], key
        assert hashlib.sha256(packed.read_bytes()).hexdigest() == report[key]['packed_sha256'], key
        meta = next(m for m in candidate['entries'] if m['key'] == key)
        assert meta['render_mode'] == 'raster', key
        active['entries'] = [m for m in active['entries'] if m['key'] != key] + [meta]
        target = ROOT/'web/hd'/f'{key}.png'
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(packed, target)
        changed.add(f'{key}.png')
    active['entries'].sort(key=lambda m: m['key'])
    active['method'] = 'source-bound-contours-and-raster-redraws'
    active_path.write_text(json.dumps(active, ensure_ascii=False, separators=(',', ':'))+'\n')
    manifest_path = ROOT/'web/hd/manifest.json'
    manifest = json.loads(manifest_path.read_text())
    lookup = {m['key']: m for m in active['entries']}
    for scene in manifest['scenes']:
        for overlay in scene.get('overlays', []):
            meta = lookup.get(overlay['key'])
            if meta and meta.get('render_mode') == 'raster':
                overlay['rect'] = meta['rect']
    manifest['files'] = [f for f in manifest['files'] if f['path'] not in changed]
    for name in sorted(changed):
        data = (ROOT/'web/hd'/name).read_bytes()
        manifest['files'].append(dict(path=name, bytes=len(data), sha256=hashlib.sha256(data).hexdigest(), kind='base'))
    manifest['images'] = sum(f['path'].endswith('.png') for f in manifest['files'])
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n')
    print(f"{len(changed)-1} gjennomgaatte rasterikoner aktivert")


if __name__ == '__main__':
    main()
