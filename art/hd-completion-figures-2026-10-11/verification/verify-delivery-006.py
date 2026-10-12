"""Kontroller sjette leveranse og alle tidligere publiserte filer."""
from pathlib import Path
import csv, hashlib, json, re, subprocess, sys

R = Path(__file__).resolve().parents[3]
F = R / 'art/hd-completion-figures-2026-10-11'
sys.path.insert(0, str(R / 'tools'))
from hd_figurer_aktiver import validate, code_in_html

sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
rel = lambda p: str(p.relative_to(R))
count = 0


def check(value, label):
    global count
    assert value, label
    count += 1


index_path = F / 'delivery-contracts-006.json'
index = json.loads(index_path.read_text())
check(index['status'] == 'frozen_final_cohort', 'Endelig kohort maa vaere fryst')
manifest_path = R / 'web/hd/manifest.json'
manifest = json.loads(manifest_path.read_text())
before = json.loads(subprocess.check_output(['git', 'show', '284f308:web/hd/manifest.json'], cwd=R))
old = {r['path']: r for r in before['files']}
active = {r['path']: r for r in manifest['files']}
check(len(active) == len(manifest['files']), 'Unike manifeststier')
check(manifest['images'] == sum(k.endswith('.png') for k in active), 'Bildetelling')
for row in manifest['files']:
    p = R / 'web/hd' / row['path']
    check(p.stat().st_size == row['bytes'], row['path'] + ' stoerrelse')
    check(sha(p) == row['sha256'], row['path'] + ' SHA')
for key, row in old.items():
    check(active[key] == row, 'Tidligere fil urort ' + key)

expected, routes, generated, aliases, shadows, proofs = set(), [], [], [], [], []
for contract in index['deliveries']:
    p = R / contract['path']
    check(sha(p) == contract['sha256'], 'Fryst kontrakt ' + rel(p))
    delivery = json.loads(p.read_text())
    files = validate(delivery)
    for key, source in files.items():
        check(key not in expected, 'Ingen dobbeltaktivering ' + key)
        expected.add(key)
        check(active[key]['sha256'] == sha(source), 'Aktiv kontraktfil ' + key)
    for row in delivery['entries']:
        if row.get('existing_master'):
            continue
        routes.append(row['key'])
        if row.get('master_key'):
            aliases.append(row['key'])
        elif row['generation_tool'] == 'preserved_original_black_shadow':
            shadows.append(row['key'])
        else:
            generated.append(row['raw_sha256'])
    for proof in delivery['proofs']:
        proofs.append(dict(path=proof['path'], sha256=proof['sha256']))

background = index['background']
bg_receipt_path = R / background['path']
check(sha(bg_receipt_path) == background['sha256'], 'Guardian-bakgrunnsaktivering')
bg_receipt = json.loads(bg_receipt_path.read_text())
check(bg_receipt['status'] == 'locally_activated_actual_verified_public_pending', 'Guardian-bakgrunn aktiv')
expected.add('bg/cbc31cbf.png')
bg_pack_path = F / 'production/guardian-background/packing-v1.json'
bg_pack = json.loads(bg_pack_path.read_text())
check(sha(bg_pack_path) == bg_receipt['packing_record_sha256'], 'Fryst bakgrunnspakking')
for path_key, sha_key in [('runtime_proof_path', 'runtime_proof_sha256'),
                          ('original_background_proof_path', 'original_background_proof_sha256')]:
    p = R / bg_receipt[path_key]
    report = json.loads(p.read_text())
    check(sha(p) == bg_receipt[sha_key] and report['status'] == 'passed' and not report.get('errors'), 'Bakgrunnens kilde-/runtimebevis')
for key in ['raw', 'prompt', 'png']:
    check(sha(bg_pack_path.parent / bg_pack[key]) == bg_pack[key + '_sha256'], 'Guardian-bakgrunn ' + key)
check(active['bg/cbc31cbf.png']['sha256'] == bg_pack['png_sha256'], 'Aktiv Guardian-bakgrunn')
coverage = json.loads((F / 'verification/background-coverage-006.json').read_text())
check(coverage['status'] == 'passed' and len(coverage['active_composites']) == 32, '32 terrengkompositter')
check(sha(R / coverage['source_audit']) == coverage['source_audit_sha256'], 'Fryst original terrengaudit')
for row in coverage['active_composites']:
    check(active[row['key']]['sha256'] == row['sha256'], 'Uendret terrengbakgrunn ' + row['key'])
check({k for k, v in active.items() if old.get(k) != v} == expected, 'Bare bestilte nye filer')
check(len(routes) == len(set(routes)), 'Unike kilderuter')
check(len(generated) == len(set(generated)), 'Ingen gjenbrukt figurmaster')

html_path = R / index['final_html']['path']
check(sha(html_path) == index['final_html']['sha256'], 'Endelig standard-HTML')
html = html_path.read_bytes()
code = {}
for row in json.loads((F / 'verification/source-freezes-006/source-map.json').read_text())['files']:
    check(sha(R / row['path']) == row['sha256'] == sha(R / row['frozen_path']), 'Fryst kode ' + row['path'])
    code[row['path']] = row['sha256']
    check(code_in_html((R / row['frozen_path']).read_bytes().replace(b'</script', b'<\\/script'), html), 'HTML inneholder ' + row['path'])
for name in index['standard_proofs']:
    p = R / name
    report = json.loads(p.read_text())
    check(report['status'] == 'passed' and not report.get('errors'), 'Standardproeve ' + name)
    check(report['html_sha256'] == sha(html_path), 'Samme standard-HTML ' + name)
    check(report['manifest_sha256'] == sha(manifest_path), 'Samme standardmanifest ' + name)
    proofs.append(dict(path=name, sha256=sha(p), checks=len(report['checks'])))

rows = list(csv.DictReader((R / 'docs/hd-bestilling-liste.csv').open(), delimiter=';'))
remaining_routes = {r['hd_fil'] for r in rows}
for row in rows:
    remaining_routes.update(re.findall(r'[A-Za-z0-9_.-]+/\d{3}\.png', row['merknad']))
package = dict(status='passed', checks=count, images=manifest['images'], files=len(active),
               backgrounds=sum(k.startswith('bg/') and k.endswith('.png') for k in active),
               previous_files_unchanged=len(old), new_png_files=len(expected), concrete_routes=len(routes),
               generated_figure_masters=len(generated), generated_background_masters=1,
               aliases=len(aliases), preserved_original_black_shadows=shadows,
               new_palette_masks=sum('.mask.' in k for k in expected),
               remaining_masters=len(rows), remaining_routes=len(remaining_routes),
               remaining_master_masks=sum(r['trenger_maske'] == 'ja' for r in rows),
               manifest_sha256=sha(manifest_path), html_sha256=sha(html_path), production_code_sha256=code,
               source_zip_sha256=sha(R / 'Moonstonecd32-AMIGA.zip'), wasm_core_sha256=sha(R / 'web/build/moonstone-core.js'),
               scope='Kildebundne separate ruter, kontrollerte originale kamper og standardpakke. Ingen full naturlig gjennomspilling eller fysisk telefonproeve. Restlisten er fortsatt uferdig.')
(F / 'verification/standard-package-006.json').write_text(json.dumps(package, indent=2, ensure_ascii=False) + '\n')
(F / 'delivery-progress-006.json').write_text(json.dumps(dict(status='locally_activated_standard_verified_public_pending', **{k:v for k,v in package.items() if k != 'status'}, deliveries=index['deliveries'], proofs=proofs), indent=2, ensure_ascii=False) + '\n')
print(json.dumps({k:package[k] for k in ['status', 'checks', 'images', 'new_png_files', 'concrete_routes', 'remaining_masters']}))
