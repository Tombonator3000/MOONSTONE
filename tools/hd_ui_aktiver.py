#!/usr/bin/env python3
"""Kontroller UI-fragmentet; --activate kobler gjennomgaatte ruter til pakken."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT/'art/hd-ui-followup-2026-10-11'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    global ART
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--activate', action='store_true')
    ap.add_argument('--additional', action='store_true', help='Bruk den separate donasjons-/Dragon Dice-kandidaten.')
    ap.add_argument('--include-material-drafts', action='store_true',
                    help='Ta med kildekonturene som fortsatt trenger naturtro materialnytegning.')
    args = ap.parse_args()
    if args.additional:
        ART = ART/'additional'
    fragment = json.loads((ART/'fragment-icons.json').read_text())
    source = json.loads((ART/'source-contracts.json').read_text())
    packing = json.loads((ART/'packing-report.json').read_text())
    assert packing['status'] == 'passed'
    assert sha((ART/'fragment-icons.json').read_bytes()) == packing['fragment_icons_sha256'], 'Ikonmetadata endret etter pakking'
    assert sha((ART/'source-contracts.json').read_bytes()) == packing['source_contracts_sha256'], 'Kildekontrakter endret etter pakking'
    contracts = {c['key']: c for c in source['entries']}
    packed = {c['key']: c for c in packing['assets']}
    rows = [m for m in fragment['entries'] if args.include_material_drafts or
            contracts[m['key']]['quality_status'] == 'source-bound-ui-contours']
    active_path = ROOT/'web/hd/icons.json'
    active = json.loads(active_path.read_text())
    original_rasters = {m['key']: m for m in active['entries'] if m.get('render_mode') == 'raster'}
    candidate_bytes = (ART/'candidate-icons.json').read_bytes()
    assert sha(candidate_bytes) == source['candidate_icons_sha256'], 'Baseline-kandidaten er endret'
    baseline = json.loads(candidate_bytes)
    baseline_rasters = {m['key']: m for m in baseline['entries'] if m.get('render_mode') == 'raster'}
    assert len(baseline_rasters) == source['baseline_raster_count'], 'Baseline-utvalget er endret'
    assert sha(json.dumps([baseline_rasters[k] for k in sorted(baseline_rasters)], sort_keys=True).encode()) == source['baseline_raster_sha256'], 'Baseline-rasterkontrakten er endret'
    assert all(original_rasters.get(key) == m for key, m in baseline_rasters.items()), 'Et eldre rasterikon er endret'
    for m in rows:
        file = ART/'packed'/f"{m['key']}.png"
        assert sha(file.read_bytes()) == packed[m['key']]['sha256'], 'Pakket fil endret'
        assert m['indices_sha256'] == contracts[m['key']]['indices_sha256']
    runtime = json.loads((ART/'verification/bound-runtime/ui-fixtures-test.json').read_text())
    assert runtime['status'] == 'passed', 'Runtimeproeven er ikke bestatt'
    assert runtime['fragment_icons_sha256'] == packing['fragment_icons_sha256'], 'Runtimeproeven gjelder eldre metadata'
    assert {m['key'] for m in rows} <= {m['key'] for m in runtime['assets']}, 'Utvalget mangler runtimebevis'
    assert runtime['source_contracts_sha256'] == packing['source_contracts_sha256'], 'Runtimeproeven gjelder eldre kildekontrakter'
    for rel in ('web/src/render.js', 'web/src/scenes.js'):
        assert runtime['production_code_sha256'][rel] == sha((ROOT/rel).read_bytes()), 'Produksjonskode endret etter runtimeproeven: '+rel
    for m in rows:
        assert runtime['packed_png_sha256'][m['key']] == packed[m['key']]['sha256'], 'Runtimeproeven gjelder en annen PNG: '+m['key']
    if not args.activate:
        print(json.dumps(dict(status='checked_not_activated', assets=len(rows), keys=[m['key'] for m in rows])))
        return
    keys = {m['key'] for m in rows}
    active['entries'] = sorted([m for m in active['entries'] if m['key'] not in keys]+rows, key=lambda m: m['key'])
    active['banks'] = {**active.get('banks', {}), **fragment['banks']}
    active['method'] = 'source-bound-ui-contours-and-raster-redraws'
    assert {m['key']: m for m in active['entries'] if m.get('render_mode') == 'raster'} == original_rasters
    changed = {'icons.json'}
    for m in rows:
        rel = f"{m['key']}.png"
        target = ROOT/'web/hd'/rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ART/'packed'/rel, target)
        changed.add(rel)
    active_path.write_text(json.dumps(active, ensure_ascii=False, separators=(',', ':'))+'\n')
    manifest_path = ROOT/'web/hd/manifest.json'
    manifest = json.loads(manifest_path.read_text())
    manifest['files'] = [r for r in manifest['files'] if r['path'] not in changed]
    for rel in sorted(changed):
        data = (ROOT/'web/hd'/rel).read_bytes()
        manifest['files'].append(dict(path=rel, bytes=len(data), sha256=sha(data), kind='base'))
    manifest['images'] = sum(r['path'].endswith('.png') for r in manifest['files'])
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(dict(status='activated', assets=len(rows), keys=[m['key'] for m in rows])))


if __name__ == '__main__':
    main()
