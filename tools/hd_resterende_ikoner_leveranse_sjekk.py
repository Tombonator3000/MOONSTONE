#!/usr/bin/env python3
"""Uavhengig kontroll av ikonleveransen mot den publiserte bakgrunnsbasen."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / 'art/hd-remaining-icons-2026-10-11'
ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument('--baseline', default='4365315fa98f9a0ed27125a05d5515ebf781f289')
args = ap.parse_args()


def old(name):
    return subprocess.check_output(['git', 'show', f'{args.baseline}:{name}'], cwd=ROOT)


def sha(data):
    return hashlib.sha256(data).hexdigest()


baseline = json.loads(old('web/hd/manifest.json'))
previous = json.loads(old('web/hd/icons.json'))['entries']
manifest = json.loads((ROOT / 'web/hd/manifest.json').read_bytes())
current = json.loads((ROOT / 'web/hd/icons.json').read_bytes())['entries']
lookup = {m['key']: m for m in current}
packing = json.loads((ART / 'packing-report.json').read_bytes())
changed = {a['key'] + '.png' for a in packing['assets']} | {'icons.json'}
assert len(current) == len(lookup) == 102
assert all(m.get('render_mode') == 'raster' for m in current)
assert len(packing['assets']) == 76
expected_new = {f'mi.c/{i:03}' for i in list(range(19)) + [20, 31, 33, 42, 43, 44, 45, 46]}
assert set(lookup) - {m['key'] for m in previous} == expected_new
preserved = [m for m in previous if m.get('render_mode') == 'raster']
assert len(preserved) == 26
assert all(lookup[m['key']] == m for m in preserved)
assert len(manifest['files']) == 376 and manifest['images'] == 370
assert len({f['path'] for f in manifest['files']}) == 376
files = {f['path']: f for f in manifest['files']}
for f in manifest['files']:
    data = (ROOT / 'web/hd' / f['path']).read_bytes()
    assert len(data) == f['bytes'] and sha(data) == f['sha256'], f['path']
unchanged = []
for f in baseline['files']:
    if f['path'] in changed:
        continue
    assert files[f['path']] == f, f['path']
    unchanged.append(f['path'])
assert len(unchanged) == 283
assert sum(n.startswith('bg/') and n.endswith('.png') for n in unchanged) == 75
assert old('Moonstonecd32-AMIGA.zip') == (ROOT / 'Moonstonecd32-AMIGA.zip').read_bytes()
core_changes = subprocess.check_output(
    ['git', 'diff', '--name-only', args.baseline, '--', 'port/', 'disasm/', 'windows/'], cwd=ROOT).decode().splitlines()
assert not core_changes, core_changes
report = dict(status='passed', baseline=args.baseline, icon_routes=102,
              newly_redrawn_routes=76, preserved_icon_routes=26,
              new_static_map_routes=27, images=370, manifest_files=376,
              unchanged_previous_manifest_files=len(unchanged), unchanged_backgrounds=75,
              original_archive_unchanged=True, core_changes=core_changes,
              scope='Fil-/kontraktbevis. Runtime og motivkontroll dokumenteres separat.')
(ART / 'verification').mkdir(exist_ok=True)
(ART / 'verification/delivery-integrity.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report))
