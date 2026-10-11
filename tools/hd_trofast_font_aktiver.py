#!/usr/bin/env python3
"""Kontroller eller aktiver den visuelt vurderte originaltro fontkandidaten.

Standard er bare kontroll. --activate kopierer 144 kontrollerte PNG-filer og
oppdaterer tekst-/pakkemetadata; eksisterende logo og rasterikoner bevares.
"""
import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image
import moonfiles as mf

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT/'art/hd-faithful-text-2026-10-11'
HD = ROOT/'web/hd'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def raster_identity():
    icons = json.loads((HD/'icons.json').read_text())
    rows = [m for m in icons['entries'] if m.get('render_mode') == 'raster']
    baseline = json.loads((ROOT/'art/hd-remaining-icons-2026-10-11/candidate-icons.json').read_text())
    baseline = [m for m in baseline['entries'] if m.get('render_mode') == 'raster']
    active = {m['key']: m for m in rows}
    assert len(baseline) == 102 and all(active.get(m['key']) == m for m in baseline), 'De 102 eksisterende rasterkontraktene avviker'
    paths = {m['key']+'.png' for m in rows}
    paths |= {v['key']+'.png' for m in rows for v in m.get('palette_variants', [])}
    return dict(count=len(rows), contracts_sha256=sha(json.dumps(sorted(rows, key=lambda m: m['key']), sort_keys=True).encode()),
                images_sha256=sha(json.dumps({p: sha((HD/p).read_bytes()) for p in sorted(paths)}, sort_keys=True).encode()))


def write_atomic(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name+'.font-tmp')
    temporary.write_bytes(data)
    os.replace(temporary, path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--activate', action='store_true')
    args = parser.parse_args()
    fragment = json.loads((ART/'fragment-text.json').read_text())
    proof = json.loads((ART/'packing-report.json').read_text())
    contracts = json.loads((ART/'source-contracts.json').read_text())
    assert proof['status'] == 'passed' and len(proof['assets']) == 144
    assert len(fragment['glyphs']) == 144
    expected = {(bank, frame) for bank in ('bold.f', 'small.font') for frame in range(72) if frame != 69}
    expected |= {('bold.f', 74), ('bold.f', 75)}
    selected = {(g['file'], g['frame']) for g in fragment['glyphs']}
    assert selected == expected and len(selected) == len(fragment['glyphs'])
    game = mf.Spill(str(ROOT/'Moonstonecd32-AMIGA.zip'))
    assert sha((ROOT/'Moonstonecd32-AMIGA.zip').read_bytes()) == contracts['original_zip_sha256']
    for bank, digest in fragment['banks'].items():
        assert sha(game.les(bank)) == digest == contracts['banks'][bank]
    proof_assets = {m['key']+'.png': m for m in proof['assets']}
    payloads = {}
    for g in fragment['glyphs']:
        relative = g['file']+f'/{g["frame"]:03}.png'
        assert g['path'] == relative and relative in proof_assets
        data = (ART/'packed'/relative).read_bytes()
        assert sha(data) == g['sha256'] == proof_assets[relative]['sha256']
        with Image.open(ART/'packed'/relative) as image:
            assert image.mode == 'RGBA' and image.size == (g['width']*8, g['height']*8)
        payloads[relative] = data
    manifest_before = (HD/'manifest.json').read_bytes()
    package = json.loads(manifest_before)
    text_before = (HD/'text.json').read_bytes()
    text = json.loads(text_before)
    logo = next(g for g in text['glyphs'] if g['file'] == 'bold.f' and g['frame'] == 73)
    logo_bytes = (HD/'bold.f/073.png').read_bytes()
    raster_before = raster_identity()
    text['glyphs'] = [g for g in text['glyphs'] if (g['file'], g['frame']) not in selected]+fragment['glyphs']
    text['glyphs'].sort(key=lambda g: (g['file'], g['frame']))
    text['banks'] = {**text['banks'], **fragment['banks']}
    text['scale'] = 8
    text['method'] = 'original-source-contours'
    text['font_provenance'] = {'source': 'Moonstonecd32-AMIGA.zip', 'banks': fragment['banks'],
                               'glyphs': 144, 'scope': '142 originale bokstavformer og to originale opphavsrettsfelt. Logoen leveres separat.'}
    payloads['text.json'] = (json.dumps(text, ensure_ascii=False, indent=2)+'\n').encode()
    paths = set(payloads)
    existing = {f['path'] for f in package['files']}
    for row in package['files']:
        if row['path'] in paths:
            data = payloads[row['path']]
            row.update(sha256=sha(data), bytes=len(data), kind='base')
    for relative in sorted(paths-existing):
        data = payloads[relative]
        package['files'].append({'path': relative, 'sha256': sha(data), 'bytes': len(data), 'kind': 'base'})
    package['images'] = sum(f['path'].endswith('.png') for f in package['files'])
    manifest_after = (json.dumps(package, ensure_ascii=False, indent=2)+'\n').encode()
    result = dict(mode='activate' if args.activate else 'check', fonts=144, raster_icons_preserved=raster_before['count'], original_raster_icons_preserved=102,
                  logo_sha256=sha(logo_bytes), logo_metadata_sha256=sha(json.dumps(logo, sort_keys=True).encode()),
                  raster_contracts_sha256=raster_before['contracts_sha256'], raster_images_sha256=raster_before['images_sha256'],
                  manifest_before_sha256=sha(manifest_before), manifest_after_sha256=sha(manifest_after),
                  text_before_sha256=sha(text_before), text_after_sha256=sha(payloads['text.json']),
                  images=package['images'], files=len(package['files']))
    if args.activate:
        # Preflight er ferdig foer noen aktiv fil skrives. Oppdag en parallell
        # manifestoppdatering og stopp foer fontene kopieres.
        assert (HD/'manifest.json').read_bytes() == manifest_before, 'Manifestet ble endret under kontrollen'
        assert (HD/'text.json').read_bytes() == text_before, 'Tekstmetadata ble endret under kontrollen'
        for relative, data in payloads.items():
            write_atomic(HD/relative, data)
        write_atomic(HD/'manifest.json', manifest_after)
        assert (HD/'bold.f/073.png').read_bytes() == logo_bytes
        assert next(g for g in json.loads((HD/'text.json').read_text())['glyphs'] if g['file'] == 'bold.f' and g['frame'] == 73) == logo
        assert raster_identity() == raster_before
        result['created_at'] = datetime.now(timezone.utc).isoformat()
        (ART/'activation-receipt.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
