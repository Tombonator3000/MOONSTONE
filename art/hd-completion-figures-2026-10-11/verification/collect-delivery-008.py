"""Velg bare navngitte filer i aattende leveranse, uten Git-endring."""
from pathlib import Path
import hashlib
import json
import subprocess

R = Path(__file__).resolve().parents[3]
F = R / 'art/hd-completion-figures-2026-10-11'
index = json.loads((F / 'delivery-contracts-008.json').read_text())
files = set()


def add(p):
    p = p.resolve()
    assert p.is_relative_to(R) and p.is_file(), p
    rel = str(p.relative_to(R))
    if p.suffix in {'.html', '.wasm', '.pyc', '.bin', '.s'}:
        return
    if any(part in rel for part in ['/__pycache__/', '/package/', '/original-runtime/']):
        return
    if p.suffix == '.png' and (any(part in rel for part in ['/references/', '/references4x/', '/source/'])
                              or p.name == 'Balok1.CEL-026-original-shadow4x.png'):
        return
    files.add(rel)


for name in index['file_lists']:
    listing = R / name
    add(listing)
    for line in listing.read_text().splitlines():
        if line and not line.startswith('#'):
            add(R / line)
for row in index['deliveries']:
    p = R / row['path']
    assert hashlib.sha256(p.read_bytes()).hexdigest() == row['sha256']
    add(p)
    delivery = json.loads(p.read_text())
    for entry in delivery['entries']:
        for key in ['png', 'mask', 'raw', 'prompt', 'art_record']:
            if entry.get(key):
                add(R / entry[key])
    for row in delivery.get('companion_derivations', []):
        companion = R / row['path']
        assert hashlib.sha256(companion.read_bytes()).hexdigest() == row['sha256']
        add(companion)
    for proof in delivery['proofs']:
        p = R / proof['path']
        add(p)
        for image in p.parent.glob('*.png'):
            add(image)
for p in list((F / 'verification/source-freezes-008').rglob('*')) + list((F / 'verification/source-freezes-008-candidate-v1').rglob('*')):
    if p.is_file():
        add(p)
for name in index.get('standard_proofs', []):
    add(R / name)
    for picture in (R / name).parent.glob('*.png'):
        add(picture)
if index.get('standard_visual_review'):
    review_path = R / index['standard_visual_review']
    add(review_path)
    for row in json.loads(review_path.read_text())['screenshots']:
        add(R / row['path'])
for name in index.get('additional_files', []):
    add(R / name)
manifest = json.loads((R / 'web/hd/manifest.json').read_text())
old = json.loads(subprocess.check_output(['git', 'show', index['baseline_commit'] + ':web/hd/manifest.json'], cwd=R))
before = {row['path']: row for row in old['files']}
changed = [row for row in manifest['files'] if row != before.get(row['path'])]
for row in changed:
    add(R / 'web/hd' / row['path'])
for name in ['web/hd/manifest.json', 'web/src/render.js', 'web/src/scenes.js',
             'docs/hd-bestilling-liste.csv', 'docs/hd-bestilling-chatgpt.md', 'todo.md', 'log.md', 'memory.md',
             'art/hd-completion-figures-2026-10-11/README.md',
             'art/hd-completion-figures-2026-10-11/verification/public-assets-008.py',
             'art/hd-completion-figures-2026-10-11/verification/standard-package-008.json',
             'art/hd-completion-figures-2026-10-11/delivery-progress-008.json',
             'art/hd-completion-figures-2026-10-11/delivery-contracts-008.json']:
    add(R / name)
add(Path(__file__))
ignored = subprocess.run(['git', 'check-ignore', '--stdin'], cwd=R, input='\n'.join(files) + '\n',
                         text=True, capture_output=True)
assert ignored.returncode in (0, 1)
files.difference_update(ignored.stdout.splitlines())
out = F / 'delivery-files-008.txt'
files.add(str(out.relative_to(R)))
out.write_text('\n'.join(sorted(files)) + '\n')
print(json.dumps(dict(files=len(files), bytes=sum((R / p).stat().st_size for p in files), new_png=len(changed))))
