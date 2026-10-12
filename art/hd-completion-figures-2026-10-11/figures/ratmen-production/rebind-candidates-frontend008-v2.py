"""Frys nye008-bevis for uendrede kunstfiler. Historiske v1-kontrakter beholdes."""
from pathlib import Path
import argparse
import copy
import hashlib
import json

ART = Path(__file__).resolve().parent
ROOT = ART.parents[3]
BASE = ART / 'verification/frontend008-candidate-v1'
PRODUCTION = ROOT / 'art/hd-completion-figures-2026-10-11/production'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_text())
rel = lambda p: str(p.relative_to(ROOT))


def frozen(path, value):
    text = json.dumps(value, indent=2, ensure_ascii=False) + '\n'
    if path.exists():
        assert path.read_text() == text, 'Bevar frossen fil: ' + rel(path)
    else:
        path.write_text(text)


args = argparse.ArgumentParser()
args.add_argument('group', choices=['shadow015', 'beast11', 'ratmen40'])
args = args.parse_args()
combined_path = BASE / 'combined-regression-v1.json'
combined = read(combined_path)
assert combined['status'] == 'passed' and combined['checks'] == 1418
ledger = read(BASE / 'package/package-ledger.json')
assert combined['production_code_sha256'] == ledger['production_code_sha256']
for name, digest in ledger['production_code_sha256'].items():
    assert sha(ROOT / name) == digest

if args.group == 'ratmen40':
    directory = ART
    old_path = ART / 'activation-set-ratmen-r1-rest40-v1.json'
    new_path = ART / 'activation-set-ratmen-r1-rest40-v2.json'
    summary_path = ART / 'verification/r1-rest40-frontend008-v1/summary.json'
    summary = read(summary_path)
    assert summary['status'] == 'passed' and summary['routes'] == 40
    proof_rows = summary['proofs']
    script = ART / 'runtime-ratmen-r1-rest40-frontend008-v1.cjs'
    photo_count, shadow_count, extra_csv_aliases = 39, 1, 0
else:
    directory = PRODUCTION / 'beast' / ('shadow015-v1' if args.group == 'shadow015' else 'next042-055-v1')
    old_path = directory / ('activation-set-shadow015-v1.json' if args.group == 'shadow015' else 'activation-set-eleven-v1.json')
    new_path = directory / ('activation-set-shadow015-v2.json' if args.group == 'shadow015' else 'activation-set-eleven-v2.json')
    proof_path = directory / ('verification/fixtures-frontend008-v1/test.json' if args.group == 'shadow015' else 'verification/runtime-frontend008-v1/test.json')
    report = read(proof_path)
    proof_rows = [dict(path=rel(proof_path), sha256=sha(proof_path), keys=[e['key'] for e in read(old_path)['entries']])]
    script = directory / ('runtime-frontend008-v1.cjs' if args.group == 'shadow015' else 'runtime-fixtures-frontend008-v1.cjs')
    photo_count, shadow_count, extra_csv_aliases = (0, 1, 0) if args.group == 'shadow015' else (10, 1, 1)

old = read(old_path)
contract = copy.deepcopy(old)
proofs, key_proofs = [], {}
files = {old_path, new_path, script, Path(__file__), combined_path}
for row in proof_rows:
    path = ROOT / row['path']
    report = read(path)
    assert sha(path) == row['sha256'] and report['status'] == 'passed' and not report.get('errors')
    assert report['production_code_sha256'] == ledger['production_code_sha256']
    assert report['wasm_core_sha256'] == ledger['wasm_core_sha256']
    assert report['html_sha256'] == ledger['html_sha256']
    assert report['runtime_script_sha256'] == sha(script)
    assert report['package_ledger_sha256'] == sha(BASE / 'package/package-ledger.json')
    html_path = path.parent / 'loaded.html'
    if not html_path.exists():
        html_path = BASE / 'package/moonstone.html'
    assert sha(html_path) == ledger['html_sha256']
    proofs.append(dict(path=rel(path), sha256=sha(path), html_path=rel(html_path), html_sha256=report['html_sha256']))
    for key in row['keys']:
        assert key not in key_proofs
        key_proofs[key] = rel(path)
    files.add(path)

assert set(key_proofs) == {e['key'] for e in old['entries']}
contract.update(production_code_sha256=ledger['production_code_sha256'], wasm_core_sha256=ledger['wasm_core_sha256'],
                proofs=proofs, actual_runtime_observed=False, fixture_only=sorted(key_proofs),
                supersedes_historical_contract=dict(path=rel(old_path), sha256=sha(old_path)),
                photographic_masters=photo_count, preserved_original_black_shadows=shadow_count,
                source_aliases_not_new_csv_masters=extra_csv_aliases,
                scope='Uendrede visuelt godkjente kunstfiler med nye bundne008-frontendbevis. '
                      'Alle ruter er fixture-only: normal/speilet, streng kilde-/eieravvisning og levende originalpaletter der aktuelt. '
                      'Ingen faktisk kampobservasjon eller naturlig kartreise paastaas. Originale svarte skygger er ingen nye fotomastere.')
companions = {r['path']: r['sha256'] for r in contract.get('companion_derivations', [])}
for p in [script, Path(__file__), combined_path]:
    companions[rel(p)] = sha(p)
if args.group == 'beast11':
    errata = directory / 'scope-alias054-errata-v1.json'
    assert read(errata)['exact_source_alias_to'] == 'Balok2.CEL/000.png'
    companions[rel(errata)] = sha(errata)
    files.add(errata)
for entry in contract['entries']:
    entry['runtime_proof'] = key_proofs[entry['key']]
    entry['actual_runtime_observed'] = False
    entry['runtime_scope'] = 'source_exact_fixture_only'
    for field in ['png', 'raw', 'prompt', 'mask', 'art_record']:
        if entry.get(field):
            files.add(ROOT / entry[field])
    assert sha(ROOT / entry['png']) == entry['png_sha256'] == entry['runtime_asset_sha256']
contract['companion_derivations'] = [dict(path=p, sha256=h) for p, h in sorted(companions.items())]
frozen(new_path, contract)
for row in contract['companion_derivations']:
    assert sha(ROOT / row['path']) == row['sha256']
    files.add(ROOT / row['path'])

# Den historiske fillisten gir alle raafiler/prompter og reproduksjonsverktøy.
# Regenererbare originalreferanser og HTML/snapshotkopier skal ikke inn i Git.
old_list = directory / ('delivery-r1-rest40-files.txt' if args.group == 'ratmen40' else 'delivery-shadow015-files.txt' if args.group == 'shadow015' else 'delivery-eleven-files.txt')
for name in old_list.read_text().splitlines():
    if '/references/' not in name and not name.endswith('.html') and not name.endswith('/package-ledger.json'):
        files.add(ROOT / name)
delivery_path = directory / ('delivery-r1-rest40-v2.json' if args.group == 'ratmen40' else 'delivery-shadow015-v2.json' if args.group == 'shadow015' else 'delivery-eleven-v2.json')
frozen(delivery_path, dict(schema=1, status='ready_not_activated', group=args.group,
                          routes=len(contract['entries']), png_files=len(contract['entries']) + sum(bool(e.get('mask')) for e in contract['entries']),
                          photographic_masters=photo_count, preserved_original_black_shadows=shadow_count,
                          source_aliases_not_new_csv_masters=extra_csv_aliases, actual_runtime_observed=False,
                          activation_contract=rel(new_path), activation_contract_sha256=sha(new_path),
                          production_code_sha256=ledger['production_code_sha256'], html_sha256=ledger['html_sha256'],
                          proofs=proofs))
files.add(delivery_path)
listing = directory / ('delivery-r1-rest40-v2-files.txt' if args.group == 'ratmen40' else 'delivery-shadow015-v2-files.txt' if args.group == 'shadow015' else 'delivery-eleven-v2-files.txt')
assert all(p.exists() for p in files)
text = '\n'.join(sorted(rel(p) for p in files)) + '\n'
if listing.exists():
    assert listing.read_text() == text
else:
    listing.write_text(text)
print(json.dumps(dict(status='ready_not_activated', group=args.group, routes=len(contract['entries']), contract=rel(new_path), sha256=sha(new_path), files=len(files))))
