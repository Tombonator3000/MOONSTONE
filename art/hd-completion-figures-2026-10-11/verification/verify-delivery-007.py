"""Kontroller sjuende leveranse, kildebevis og urorte tidligere filer."""
from pathlib import Path
import csv
import hashlib
import json
import re
import subprocess
import sys

R = Path(__file__).resolve().parents[3]
F = R / 'art/hd-completion-figures-2026-10-11'
sys.path.insert(0, str(R / 'tools'))
from hd_figurer_aktiver import validate, code_in_html

sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
count = 0


def check(value, name):
    global count
    assert value, name
    count += 1


index = json.loads((F / 'delivery-contracts-007.json').read_text())
check(index['status'] == 'frozen_final_cohort', 'Endelig kohort fryst')
manifest_path = R / 'web/hd/manifest.json'
manifest = json.loads(manifest_path.read_text())
check(sha(manifest_path) == index['manifest_sha256'], 'Manifest fryst')
before_bytes = subprocess.check_output(['git', 'show', index['baseline_commit'] + ':web/hd/manifest.json'], cwd=R)
check(hashlib.sha256(before_bytes).hexdigest() == index['baseline_manifest_sha256'], 'Baseline fryst')
old = {row['path']: row for row in json.loads(before_bytes)['files']}
active = {row['path']: row for row in manifest['files']}
check(len(active) == len(manifest['files']), 'Unike filstier')
check(manifest['images'] == sum(k.endswith('.png') for k in active), 'Bildetelling')
for key, row in active.items():
    p = R / 'web/hd' / key
    check(p.stat().st_size == row['bytes'], key + ' stoerrelse')
    check(sha(p) == row['sha256'], key + ' SHA')
for key, row in old.items():
    check(active[key] == row, 'Tidligere fil urort ' + key)

# Originalreferanser gjenskapes fra ZIP; de skal ikke legges i Git.
for helper in ['production/beast/next012-017-v1/prepare-v2.py',
               'production/beast/next018-029-v1/prepare-references-v1.py']:
    subprocess.run([sys.executable, str(F / helper)], cwd=R, check=True)
expected, routes, masters, aliases, proofs = set(), [], [], [], []
for contract in index['deliveries']:
    p = R / contract['path']
    check(sha(p) == contract['sha256'], 'Fryst leveranse ' + contract['path'])
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
        else:
            masters.append(row['raw_sha256'])
    proofs.extend(dict(path=p['path'], sha256=p['sha256']) for p in delivery['proofs'])
check({k for k, row in active.items() if row != old.get(k)} == expected, 'Bare navngitte nye filer')
check(len(routes) == len(set(routes)) == index['new_routes'], 'Unike bestilte kilderuter')
check(len(expected) == index['new_png_files'], 'Bestilt antall nye PNG')
check(len(masters) == len(set(masters)), 'Egen generert master per selvstendige rute')

html_path = R / index['final_html']['path']
check(sha(html_path) == index['final_html']['sha256'], 'Endelig HTML')
html = html_path.read_bytes()
code = {}
for row in json.loads((F / 'verification/source-freezes-007/source-map.json').read_text())['files']:
    source, frozen = R / row['path'], R / row['frozen_path']
    check(sha(source) == row['sha256'] == sha(frozen), 'Fryst kode ' + row['path'])
    check(code_in_html(frozen.read_bytes().replace(b'</script', b'<\\/script'), html), 'HTML-kode ' + row['path'])
    code[row['path']] = row['sha256']
frontend = json.loads((R / index['frontend_delivery']['path']).read_text())
check(frontend['status'] == 'frozen_passed' and frontend['production_code_sha256'] == code, 'Frontend v7 fryst')
for row in frontend['proofs']:
    p = R / row['path']
    check(sha(p) == row['sha256'], 'Frontendbevis ' + row['path'])
    proof = json.loads(p.read_text())
    check(proof['status'] == 'passed' and not proof.get('errors'), 'Frontendport bestaar')
for name in index['standard_proofs']:
    p = R / name
    report = json.loads(p.read_text())
    check(report['status'] == 'passed' and not report.get('errors'), 'Standardproeve ' + name)
    check(report['html_sha256'] == sha(html_path), 'Samme standard-HTML ' + name)
    check(report['manifest_sha256'] == sha(manifest_path), 'Samme standardmanifest ' + name)
    reported_code = report.get('production_code_sha256', report.get('source_files', {}))
    check({k: reported_code.get(k) for k in code} == code, 'Samme standardkode ' + name)
    check(report.get('test_sha256', report.get('runtime_script_sha256')) in {job['sha256'] for job in index['runtime_jobs']}, 'Navngitt standardhelper ' + name)
    proofs.append(dict(path=name, sha256=sha(p), checks=len(report['checks'])))

rows = list(csv.DictReader((R / 'docs/hd-bestilling-liste.csv').open(), delimiter=';'))
remaining = {row['hd_fil'] for row in rows}
for row in rows:
    remaining.update(re.findall(r'[A-Za-z0-9_.-]+/\d{3}\.png', row['merknad']))
check(not set(routes).intersection(remaining), 'Leverte ruter ute av restlisten')
package = dict(status='passed', checks=count, images=manifest['images'], files=len(active),
               backgrounds=sum(k.startswith('bg/') and k.endswith('.png') for k in active),
               previous_files_unchanged=len(old), new_png_files=len(expected), concrete_routes=len(routes),
               generated_figure_masters=len(masters), aliases=len(aliases),
               new_palette_masks=sum('.mask.' in k for k in expected), remaining_masters=len(rows),
               remaining_routes=len(remaining), remaining_master_masks=sum(row['trenger_maske'] == 'ja' for row in rows),
               manifest_sha256=sha(manifest_path), html_sha256=sha(html_path), production_code_sha256=code,
               source_zip_sha256=sha(R / 'Moonstonecd32-AMIGA.zip'),
               wasm_core_sha256=sha(R / 'web/build/moonstone-core.js'),
               scope='Kildebundne separate ruter og eksakte originalaliaser. Kontrollerte kamper og standardpakke. '
                     'Ikke full naturlig gjennomspilling eller fysisk telefonproeve. Restlisten er fortsatt uferdig.')
(F / 'verification/standard-package-007.json').write_text(json.dumps(package, indent=2, ensure_ascii=False) + '\n')
progress = dict(**{k:v for k,v in package.items() if k != 'status'},
                status='locally_activated_standard_verified_public_pending', deliveries=index['deliveries'], proofs=proofs)
(F / 'delivery-progress-007.json').write_text(json.dumps(progress, indent=2, ensure_ascii=False) + '\n')
print(json.dumps({k:package[k] for k in ['status', 'checks', 'images', 'new_png_files', 'concrete_routes', 'remaining_masters']}))
