"""Velg bare sjette leveranses navngitte filer, uten Git-endring."""
from pathlib import Path
import json, subprocess

R = Path(__file__).resolve().parents[3]
F = R / 'art/hd-completion-figures-2026-10-11'
files = set()


def add(p):
    p = p.resolve()
    assert p.is_relative_to(R) and p.is_file(), p
    rel = str(p.relative_to(R))
    if p.suffix in {'.html', '.wasm', '.pyc', '.bin', '.s'} or any(t in rel for t in ['/__pycache__/', '/package/', '/original-runtime/']):
        return
    if p.suffix == '.png' and (p.name == 'source-nine.png' or any(t in rel for t in ['/references/', '/references4x/', '/source/'])):
        return
    files.add(rel)


def strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for x in value:
            yield from strings(x)
    elif isinstance(value, dict):
        for x in value.values():
            yield from strings(x)


def refs(p):
    add(p)
    for value in strings(json.loads(p.read_text())):
        if len(value) > 500 or '\n' in value or value.startswith('data:'):
            continue
        for base in [R, p.parent]:
            q = base / value
            if q.is_file() and q.resolve().is_relative_to(R):
                add(q)


index = json.loads((F / 'delivery-contracts-006.json').read_text())
assert index['status'] == 'frozen_final_cohort'
for item in index['deliveries']:
    p = R / item['path']
    refs(p)
    d = json.loads(p.read_text())
    for row in d['entries']:
        for key in ['png', 'mask', 'raw', 'prompt', 'art_record']:
            if row.get(key):
                add(R / row[key])
        if row.get('art_record'):
            refs(R / row['art_record'])
    for proof in d['proofs']:
        p = R / proof['path']
        add(p)
        for image in p.parent.glob('*.png'):
            add(image)
for name in index['file_lists']:
    listing = R / name
    add(listing)
    for line in listing.read_text().splitlines():
        if line and not line.startswith('#'):
            add(R / line)

bg = F / 'production/guardian-background'
for name in ['pack-v1.cjs', 'packing-v1.json', 'activate-v1.py', 'activation-v1.json']:
    refs(bg / name) if name.endswith('.json') else add(bg / name)
for name in ['verification/actual-v1', 'verification/candidate-v1']:
    for p in (bg / name).glob('*'):
        if p.suffix in {'.json', '.png'}:
            add(p)
for name in ['production/guardian/export-background.py', 'production/guardian/runtime-export-background.cjs',
             'production/guardian/audit-test-backgrounds.py', 'production/guardian/audit-background-deltas.py']:
    p = F / name
    if p.exists():
        add(p)
audit = F / 'production/guardian/verification/test-background-audit-v1'
for name in ['audit.json', 'later-runtime-deltas.json', 'manifest-at-audit.json']:
    add(audit / name)
for p in (F / 'verification/source-freezes-006').rglob('*'):
    if p.is_file():
        add(p)
for p in (F / 'verification/public-005').rglob('*.json'):
    add(p)
for name in index['standard_proofs']:
    p = R / name
    add(p)
    for image in p.parent.glob('*.png'):
        add(image)
for name in ['README.md', 'delivery-contracts-006.json', 'delivery-progress-006.json',
             'verification/verify-delivery-006.py', 'verification/standard-package-006.json',
             'verification/background-coverage-006.json', 'verification/historical-gates-005.py',
             'verification/historical-gates-005.json', 'verification/public-assets-005.py',
             'verification/run-public-005.py', 'production/verification/balok-012-017-review-006.png',
             'production/guardian/runtime-standard-public-v6.cjs']:
    add(F / name)
for p in (F / 'verification/historical-gates-005').glob('*.json'):
    add(p)
for name in index.get('additional_files', []):
    add(R / name)

manifest = json.loads((R / 'web/hd/manifest.json').read_text())
old = json.loads(subprocess.check_output(['git', 'show', '284f308:web/hd/manifest.json'], cwd=R))
before = {r['path']: r for r in old['files']}
changed = [r for r in manifest['files'] if r != before.get(r['path'])]
for row in changed:
    add(R / 'web/hd' / row['path'])
for name in ['web/hd/manifest.json', 'web/src/render.js', 'docs/hd-bestilling-liste.csv', 'docs/hd-bestilling-chatgpt.md',
             'todo.md', 'log.md', 'memory.md']:
    add(R / name)
add(Path(__file__))
ignored = subprocess.run(['git', 'check-ignore', '--stdin'], cwd=R, input='\n'.join(files)+'\n', text=True, capture_output=True)
assert ignored.returncode in (0, 1)
files.difference_update(ignored.stdout.splitlines())
out = F / 'delivery-files-006.txt'
files.add(str(out.relative_to(R)))
out.write_text('\n'.join(sorted(files))+'\n')
print(json.dumps(dict(files=len(files), bytes=sum((R / p).stat().st_size for p in files), new_png=len(changed))))
