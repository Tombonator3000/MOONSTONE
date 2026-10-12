"""Bind ferdige samlede008-proever til samme uendrede kilde- og pakkefrys."""
from pathlib import Path
import hashlib
import json

ART = Path(__file__).resolve().parent
ROOT = ART.parents[3]
BASE = ART / 'verification/frontend008-candidate-v1'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_text())
rel = lambda p: str(p.relative_to(ROOT))


def frozen(path, value):
    text = json.dumps(value, indent=2, ensure_ascii=False) + '\n'
    if path.exists():
        assert path.read_text() == text, 'Bevar frossen fil: ' + rel(path)
    else:
        path.write_text(text)


ledger_path = BASE / 'package/package-ledger.json'
ledger = read(ledger_path)
assert ledger['html_sha256'] == '1bee3c056f771612b427df9750901ca8829099be8829da55779fb859edf612c3'
assert sha(BASE / 'package/moonstone.html') == ledger['html_sha256']
assert sha(BASE / 'package/moonstone-core-used.js') == ledger['wasm_core_sha256']
assert sha(ROOT / 'web/build/moonstone-core.js') == ledger['wasm_core_sha256']
assert sha(BASE / 'package/hd/manifest.json') == ledger['manifest_sha256']
source_map_path = BASE / 'sources/source-map.json'
source_map = read(source_map_path)
for row in source_map['files']:
    assert sha(ROOT / row['frozen_path']) == sha(ROOT / row['path']) == row['sha256']
assert {r['path']: r['sha256'] for r in source_map['files']} == ledger['production_code_sha256']
for row in ledger['files']:
    path = BASE / 'package/hd' / row['path']
    assert path.stat().st_size == row['bytes'] and sha(path) == row['sha256']

production = ROOT / 'art/hd-completion-figures-2026-10-11/production'
cases = [
    ('ratmen_actual', BASE / 'ratmen-v2/test.json', 316, ART / 'runtime-standard-public-v5.cjs'),
    ('balok025_actual', BASE / 'balok-025/test.json', 106, production / 'runtime-balok-025-frontend008-v1.cjs'),
    ('balok_standard', BASE / 'balok-standard/test.json', 393, production / 'runtime-balok-standard-frontend008-v1.cjs'),
    ('natural_font', BASE / 'font/font-runtime-test.json', 35, production / 'runtime-tekst-eierskap-font-v1.cjs'),
    ('text_negative', BASE / 'text-fixtures/text-owner-fixtures.json', 59, production / 'runtime-tekst-eierskap-fixtures-v1.cjs'),
    ('ratmen_baking_VM', ART / 'verification/baked-background-fixtures-v1/test.json', 40, ART / 'test-baked-background-v1.cjs'),
    ('old_combat_VM', ART / 'verification/original-combat-background-v1.json', 469, ART / 'test-original-combat-background-v1.cjs'),
]
proofs = []
for name, path, count, script in cases:
    report = read(path)
    assert report['status'] == 'passed' and not report.get('errors'), name
    assert len(report['checks']) == count, (name, len(report['checks']))
    script_hash = report.get('runtime_script_sha256', report.get('test_sha256', report.get('script_sha256')))
    assert script_hash == sha(script), (name, script_hash)
    if name.endswith('_VM'):
        assert report['scenes_sha256'] == ledger['production_code_sha256']['web/src/scenes.js']
    else:
        assert report['html_sha256'] == ledger['html_sha256'], name
        if report.get('production_code_sha256'):
            assert report['production_code_sha256'] == ledger['production_code_sha256'], name
        if report.get('render_sha256'):
            assert report['render_sha256'] == ledger['production_code_sha256']['web/src/render.js']
    proofs.append(dict(name=name, path=rel(path), sha256=sha(path), checks=count,
                       runtime_script=rel(script), runtime_script_sha256=sha(script)))

reviewed = []
for subdir, names in [
    ('ratmen-v2', ['047-original', '047-hd', '048-original', '048-hd', '050-original', '050-hd']),
    ('balok-025', ['Balok3.CEL-025-original', 'Balok3.CEL-025-hd']),
]:
    for name in names:
        path = BASE / subdir / (name + '.png')
        reviewed.append(dict(path=rel(path), sha256=sha(path)))

out = BASE / 'combined-regression-v1.json'
frozen(out, dict(schema=1, status='passed', checks=sum(r['checks'] for r in proofs),
                combined_balok_text_checks=593, scene_VM_checks=509, ratmen_actual_checks=316,
                html_sha256=ledger['html_sha256'], manifest_sha256=ledger['manifest_sha256'],
                package_ledger_sha256=sha(ledger_path), source_map_sha256=sha(source_map_path),
                production_code_sha256=ledger['production_code_sha256'], wasm_core_sha256=ledger['wasm_core_sha256'],
                proofs=proofs, representative_images=reviewed,
                scope='Samme uendrede008-kandidat. Standardpakke uten privatimport i Ratmen/Balok/naturfont. '
                      'Kontrollerte originalkamper, kilde- og tekstfixturer oppgis separat. '
                      'Original/HD-retur og uendret emulertstate kontrolleres ved fangst. '
                      'Alle originaldeltaer vernes; ingen generell aksept av ukjent forgrunn. '
                      'Ingen ny aktivering eller endret spillkjerne.'))
print(json.dumps(dict(status='passed', checks=1418, combined=593, VM=509, actual_ratmen=316, proof_sha256=sha(out))))
