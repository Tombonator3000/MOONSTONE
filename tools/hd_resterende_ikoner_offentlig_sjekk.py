#!/usr/bin/env python3
"""Kontroller at Pages faktisk serverer de ferdige ikonfilene."""
import argparse
import concurrent.futures
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / 'art/hd-remaining-icons-2026-10-11'
ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument('--url', default='https://tombonator3000.github.io/MOONSTONE/')
args = ap.parse_args()
base = args.url.rstrip('/') + '/'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def fetch(path):
    request = Request(base + path, headers={'Cache-Control': 'no-cache'})
    with urlopen(request, timeout=60) as response:
        return response.read()


local_manifest = (ROOT / 'web/hd/manifest.json').read_bytes()
public_manifest = fetch('hd/manifest.json')
assert public_manifest == local_manifest, 'Offentlig manifest er ikke siste lokale pakke'
manifest = json.loads(public_manifest)
packing = json.loads((ART / 'packing-report.json').read_bytes())
paths = {'icons.json'}
for asset in packing['assets']:
    paths.add(asset['key'] + '.png')
    paths.update(variant['key'] + '.png' for variant in asset.get('variants', []))
assert len(paths) == 93, f'Forventet metadata og 92 nye PNG-er, fikk {len(paths)}'
files = {row['path']: row for row in manifest['files']}


def check(path):
    data = fetch('hd/' + path)
    expected = files[path]
    assert len(data) == expected['bytes'] and sha(data) == expected['sha256'], path
    return dict(path=path, bytes=len(data), sha256=sha(data))


with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    checked = list(pool.map(check, sorted(paths)))
page = fetch('index.html')
assert b'rasterIkonVariant' in page and b'ikonVariantBilde' in page, 'Siste renderer mangler'
report = dict(status='passed', url=base,
              checked_at_utc=datetime.now(timezone.utc).isoformat(),
              manifest_sha256=sha(public_manifest), html_sha256=sha(page),
              icon_routes=102, newly_redrawn_routes=76,
              checked_pngs=92, files=checked,
              scope='Offentlige byte-/hashbevis. Faktisk spillvisning kontrolleres separat.')
(ART / 'verification/public').mkdir(parents=True, exist_ok=True)
(ART / 'verification/public/public-assets.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({key: value for key, value in report.items() if key != 'files'}))
