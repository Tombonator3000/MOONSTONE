"""Kontroller aattende kohort mot egne kontrakter og uendret007-baseline."""
from pathlib import Path
import csv, hashlib, json, re, subprocess, sys

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

index = json.loads((F / 'delivery-contracts-008.json').read_text())
check(index['status'] == 'frozen_final_cohort', 'Kohort fryst')
manifest_path = R / 'web/hd/manifest.json'
manifest = json.loads(manifest_path.read_text())
check(sha(manifest_path) == index['manifest_sha256'], 'Manifest fryst')
before = subprocess.check_output(['git','show',index['baseline_commit']+':web/hd/manifest.json'], cwd=R)
check(hashlib.sha256(before).hexdigest() == index['baseline_manifest_sha256'], 'Baseline fryst')
old = {r['path']:r for r in json.loads(before)['files']}
active = {r['path']:r for r in manifest['files']}
check(len(active) == len(manifest['files']) == index['files'], 'Unike manifeststier')
check(manifest['images'] == sum(k.endswith('.png') for k in active) == index['images'], 'PNG-telling')
for key, row in active.items():
    p = R/'web/hd'/key
    check(p.stat().st_size == row['bytes'] and sha(p) == row['sha256'], 'Aktiv fil '+key)
for key, row in old.items():
    check(active[key] == row, 'Tidligere007-fil uendret '+key)

expected, routes, photos, preserved, proofs = {}, [], [], [], []
for contract in index['deliveries']:
    p = R/contract['path']
    check(sha(p) == contract['sha256'], 'Fryst kontrakt '+str(p))
    delivery = json.loads(p.read_text())
    files = validate(delivery)
    for key, source in files.items():
        check(key not in expected, 'Ingen dobbeltaktivering '+key)
        expected[key] = sha(source)
        check(active[key]['sha256'] == expected[key], 'Kontraktfil '+key)
    for row in delivery['entries']:
        if row.get('existing_master'): continue
        routes.append(row['key'])
        if row.get('generation_tool') == 'builtin_image_gen':
            photos.append(row['raw_sha256'])
        else:
            preserved.append(row['key'])
    proofs.extend(dict(path=p['path'],sha256=p['sha256']) for p in delivery['proofs'])
check(expected == index['expected_new_files'], 'Eksakt222-filsett')
check({k for k in active if k not in old} == set(expected), 'Bare navngitte nye filer')
check(len(routes) == len(set(routes)) == index['new_routes'], '202 unike kilderuter')
check(len(photos) == len(set(photos)) == index['photographic_masters'], '195 egne fotografiske mastere')
check(len(preserved) == index['preserved_original_routes'], 'Sju bevarte originalruter')

html_path = R/index['final_html']['path']
check(sha(html_path) == index['final_html']['sha256'], 'Endelig HTML')
html = html_path.read_bytes()
code = {}
for row in json.loads((R/index['source_freeze']/'source-map.json').read_text())['files']:
    source, frozen = R/row['path'], R/row['frozen_path']
    check(sha(source) == row['sha256'] == sha(frozen), 'Fryst kode '+row['path'])
    check(code_in_html(frozen.read_bytes().replace(b'</script',b'<\\/script'),html), 'Innebygd kode '+row['path'])
    code[row['path']] = row['sha256']
frontend_path = R/index['frontend_delivery']['path']
check(sha(frontend_path) == index['frontend_delivery']['sha256'], 'Frontendkontrakt fryst')
frontend = json.loads(frontend_path.read_text())
check(frontend['checks'] == 1418 and frontend['production_code_sha256'] == code, 'Samme verifiserte008-kode')
for name, value in frontend['file_sha256'].items():
    check(sha(R/name) == value, 'Frontendforelder '+name)
combined = R/frontend['combined_proof']
check(sha(combined) == frontend['combined_proof_sha256'], '1418-kombinasjon fryst')
check(json.loads(combined.read_text())['status'] == 'passed', 'Frontendregresjon bestaar')
base = json.loads((R/index['frontend_final_base']).read_text())
check(base['status'] == 'final_base_accepted', '008-base godkjent')

check(len(index['runtime_jobs']) == len(index['standard_proofs']) == 23, 'Alle23 standardporter med')
for job, name in zip(index['runtime_jobs'],index['standard_proofs']):
    p = R/name
    report = json.loads(p.read_text())
    check(report['status'] == 'passed' and not report.get('errors'), 'Standard bestaar '+name)
    check(report['html_sha256'] == sha(html_path), 'Samme standard-HTML '+name)
    hashes = [report[k] for k in ['manifest_sha256','standard_manifest_sha256','package_manifest_sha256'] if k in report]
    check(hashes and all(h == sha(manifest_path) for h in hashes), 'Samme standardmanifest '+name)
    reported = report.get('production_code_sha256',report.get('source_files',{}))
    check({k:reported.get(k) for k in code} == code, 'Samme standardkode '+name)
    check(report.get('test_sha256',report.get('runtime_script_sha256')) == job['sha256'] == sha(R/job['script']), 'Navngitt standardhelper '+name)
    proofs.append(dict(path=name,sha256=sha(p),checks=len(report['checks'])))
review_path = R/index['standard_visual_review']
review = json.loads(review_path.read_text())
check(review['status'] == 'passed' and review['html_sha256'] == sha(html_path), 'Visuell007-blokk rettet i008')
for row in review['screenshots']:
    check(sha(R/row['path']) == row['sha256'], 'Visuelt bilde '+row['path'])

rows = list(csv.DictReader((R/'docs/hd-bestilling-liste.csv').open(),delimiter=';'))
remaining = {r['hd_fil'] for r in rows}
for r in rows: remaining.update(re.findall(r'[A-Za-z0-9_.-]+/\d{3}\.png',r['merknad']))
check(not set(routes).intersection(remaining), 'Leverte ruter ute av restlisten')
check((len(rows),len(remaining),sum(r['trenger_maske']=='ja' for r in rows)) == (790,853,59), '790 mastere/853 ruter/59 masker gjenstaar')
check(sha(R/'Moonstonecd32-AMIGA.zip') == '35b7d4c67b9fae6019e257780050d0f421d6ec4c250cdde48a8f296086d67a02', 'OriginalZIP uendret')
check(sha(R/'web/build/moonstone-core.js') == 'c56094d8b992cbd7ed7e4a8ef65709c435156072124874b26bce7cf02cb8e633', 'OriginalWASM uendret')
package = dict(status='passed',checks=count,images=manifest['images'],files=len(active),backgrounds=82,previous_files_unchanged=len(old),new_png_files=len(expected),concrete_routes=len(routes),photographic_masters=len(photos),preserved_original_routes=len(preserved),new_palette_masks=sum('.mask.' in k for k in expected),remaining_masters=len(rows),remaining_routes=len(remaining),remaining_master_masks=59,manifest_sha256=sha(manifest_path),html_sha256=sha(html_path),production_code_sha256=code,source_zip_sha256=sha(R/'Moonstonecd32-AMIGA.zip'),wasm_core_sha256=sha(R/'web/build/moonstone-core.js'),standard_checks=sum(p.get('checks',0) for p in proofs),scope='Kildebundne separate ruter, egne fotografiske materialmastere og sju bevarte originalruter. 008 retter den visuelle007-blokken. Ikke full naturlig animasjonsdekning eller fysisk telefonproeve. Restlisten er fortsatt uferdig.')
(F/'verification/standard-package-008.json').write_text(json.dumps(package,indent=2,ensure_ascii=False)+'\n')
progress = dict(**{k:v for k,v in package.items() if k!='status'},status='locally_activated_standard_verified_public_pending',deliveries=index['deliveries'],proofs=proofs)
(F/'delivery-progress-008.json').write_text(json.dumps(progress,indent=2,ensure_ascii=False)+'\n')
print(json.dumps({k:package[k] for k in ['status','checks','images','new_png_files','concrete_routes','remaining_masters','standard_checks']}))
