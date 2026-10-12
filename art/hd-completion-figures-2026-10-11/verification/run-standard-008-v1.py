"""Kjoer navngitte008-standardscener lokalt eller offentlig; bevar alle forsoek."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import subprocess

R = Path(__file__).resolve().parents[3]
F = R / 'art/hd-completion-figures-2026-10-11'
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--public', action='store_true')
parser.add_argument('--names', help='Kommaseparert utvalg, ellers alle navngitte scener')
args = parser.parse_args()
index = json.loads((F / 'verification/runtime-plan-008-v1.json').read_text())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
base = (R / index['final_html']['path']).parent
assert sha(base / 'moonstone.html') == index['final_html']['sha256']
assert sha(base / 'hd/manifest.json') == index['manifest_sha256']
dest = F / 'verification' / ('public-008' if args.public else 'integration-008-final-v1')
env = os.environ.copy()
env.update(NODE_PATH='/home/tombonator3000t/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules',
           MOONSTONE_HD_SOURCE_FREEZE=str(F / 'verification/source-freezes-008'),
           MOONSTONE_HD_EXPECTED_HTML_SHA256=index['final_html']['sha256'])
if args.public:
    assets = json.loads((dest / 'assets.json').read_text())
    assert assets['status'] == 'passed'
    assert assets['html_sha256'] == index['final_html']['sha256'] and assets['manifest_sha256'] == index['manifest_sha256']
    env.update(MOONSTONE_HD_PUBLIC_URL='https://tombonator3000.github.io/MOONSTONE/',
               MOONSTONE_HD_PUBLIC_HTML_SHA256=assets['html_sha256'])
else:
    env.pop('MOONSTONE_HD_PUBLIC_URL', None)
node = '/home/tombonator3000t/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node'
selected = []
names = set(args.names.split(',')) if args.names else {job['name'] for job in index['runtime_jobs']}
assert names <= {job['name'] for job in index['runtime_jobs']}
for job in index['runtime_jobs']:
    if job['name'] not in names:
        continue
    script = R / job['script']
    assert sha(script) == job['sha256']
    for attempt in range(1, 4):
        folder = dest / (job['name'] if attempt == 1 else job['name'] + '-retry' + str(attempt - 1))
        p = folder / 'test.json'
        if p.exists():
            try:
                report = json.loads(p.read_text())
            except json.JSONDecodeError:
                print('Bevarer ugyldig rapportformat: ' + str(p), flush=True)
                continue
            if report['status'] != 'passed':
                continue
        else:
            job_env = dict(env, **job.get('environment', {}))
            job_env[job['package_env']] = str(base)
            job_env['MOONSTONE_HD_TEST_OUTPUT'] = str(folder)
            print('Kjoerer ' + job['name'] + ', forsoek ' + str(attempt), flush=True)
            subprocess.run([node, str(script)], cwd=R, env=job_env, check=True)
            report = json.loads(p.read_text())
        assert report['status'] == 'passed' and not report.get('errors')
        assert report['html_sha256'] == index['final_html']['sha256']
        manifest_hashes = [report[key] for key in ('manifest_sha256', 'standard_manifest_sha256', 'package_manifest_sha256') if key in report]
        assert manifest_hashes and all(value == index['manifest_sha256'] for value in manifest_hashes)
        assert report.get('test_sha256', report.get('runtime_script_sha256')) == sha(script)
        selected.append(dict(name=job['name'], path=str(p.relative_to(R)), sha256=sha(p), checks=len(report['checks'])))
        break
    else:
        raise RuntimeError('Tre bevarte mislykkede forsoek: ' + job['name'])
dest.mkdir(exist_ok=True)
selection = dest / ('runtime-selection.json' if not args.names else 'runtime-selection-' + '-'.join(sorted(names)).replace('/', '_') + '.json')
selection.write_text(json.dumps(dict(status='passed', runtime_proofs=selected), indent=2) + '\n')
print(json.dumps(dict(status='passed', scenes=len(selected), checks=sum(row['checks'] for row in selected))))
