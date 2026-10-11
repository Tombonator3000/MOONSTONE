#!/usr/bin/env python3
"""Kontroller en ikonpakke. --activate kopierer bare avtalte, gjennomgaatte ruter."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT/'art/hd-remaining-icons-2026-10-11'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--activate', action='store_true')
    ap.add_argument('--keys', help='Kommadelt utvalg. Standard er alle gjennomgaatte ruter.')
    args = ap.parse_args()
    report = json.loads((ART/'packing-report.json').read_text())
    candidate_bytes = (ART/'candidate-icons.json').read_bytes()
    assert sha(candidate_bytes) == report['candidate_icons_sha256'], 'Kandidatmetadata endret etter pakking'
    candidate = json.loads(candidate_bytes)
    active_path = ROOT/'web/hd/icons.json'
    active_bytes = active_path.read_bytes()
    active = json.loads(active_bytes)
    assert sha(active_bytes) == report['baseline_icons_sha256'], 'Aktive metadata endret. Pakk paa nytt foer aktivering.'
    source_baseline_bytes = (ART/'research/runtime/source-baseline-icons.json').read_bytes()
    assert sha(source_baseline_bytes) == report['source_baseline_icons_sha256'], 'Uforanderlig kildepakke endret'
    source_baseline = json.loads(source_baseline_bytes)
    old_raster = {m['key']:m for m in source_baseline['entries'] if m.get('render_mode')=='raster'}
    assert len(old_raster)==26 and set(report['preserved_raster_keys'])==set(old_raster), 'Eldre rasterutvalg endret'
    rows = report['assets']
    if args.keys:
        keys = set(args.keys.split(','))
        rows = [a for a in rows if a['key'] in keys]
        assert {a['key'] for a in rows} == keys, 'Ukjent eller ikke gjennomgaatt rute'
    assert rows, 'Tomt utvalg'
    lookup = {m['key']: m for m in candidate['entries']}
    for key in report['preserved_raster_keys']:
        assert lookup[key] == next(m for m in active['entries'] if m['key'] == key), 'Eldre rasterkontrakt endret'
        assert lookup[key] == old_raster[key], 'Eldre rasterkontrakt avviker fra originalpakken'
    changed = {'icons.json'}
    for row in rows:
        key = row['key']
        assert row['review_status'] == 'reviewed_for_runtime'
        assert sha((ART/row['record']).read_bytes()) == row['record_sha256'], key+' record endret'
        assert sha((ART/row['prompt']).read_bytes()) == row['prompt_sha256'], key+' prompt endret'
        assert sha((ART/row['raw']).read_bytes()) == row['raw_sha256'], key
        assert sha((ART/row['source']).read_bytes()) == row['source_sha256'], key
        if row.get('composite'):
            assert sha((ART/row['composite']['source']).read_bytes()) == row['composite']['source_sha256'], key
        packed = ART/'packed'/f'{key}.png'
        assert sha(packed.read_bytes()) == row['packed_sha256'], key
        assert lookup[key]['render_mode'] == 'raster', key
        active['entries'] = [m for m in active['entries'] if m['key'] != key] + [lookup[key]]
        changed.add(f'{key}.png')
        for variant in row.get('variants',[]):
            assert sha((ART/variant['raw']).read_bytes()) == variant['raw_sha256'], variant['key']
            assert sha((ART/'packed'/f"{variant['key']}.png").read_bytes()) == variant['packed_sha256'], variant['key']
            changed.add(f"{variant['key']}.png")
    if not args.activate:
        print(json.dumps({'status':'checked_not_activated','assets':len(rows),'keys':[a['key'] for a in rows]}))
        return
    for row in rows:
        target = ROOT/'web/hd'/f"{row['key']}.png"
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(ART/'packed'/f"{row['key']}.png",target)
        for variant in row.get('variants',[]):
            target=ROOT/'web/hd'/f"{variant['key']}.png"
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(ART/'packed'/f"{variant['key']}.png",target)
    active['entries'].sort(key=lambda m:m['key'])
    active['method']='source-bound-contours-and-raster-redraws'
    active_path.write_text(json.dumps(active,ensure_ascii=False,separators=(',',':'))+'\n')
    manifest_path=ROOT/'web/hd/manifest.json'
    manifest=json.loads(manifest_path.read_text())
    manifest['files']=[f for f in manifest['files'] if f['path'] not in changed]
    for name in sorted(changed):
        data=(ROOT/'web/hd'/name).read_bytes()
        manifest['files'].append(dict(path=name,bytes=len(data),sha256=sha(data),kind='base'))
    manifest['images']=sum(f['path'].endswith('.png') for f in manifest['files'])
    manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'status':'activated','assets':len(rows),'keys':[a['key'] for a in rows]}))


if __name__=='__main__':
    main()
