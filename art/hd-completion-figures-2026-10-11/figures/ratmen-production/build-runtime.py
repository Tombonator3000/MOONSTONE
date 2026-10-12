"""Lag en uforanderlig runtimekopi med kontrollerte standardfiler."""
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
target = Path(sys.argv[1]).resolve()
assert not target.exists(), 'Velg en ny snapshotkatalog'
target.mkdir(parents=True)
subprocess.run([sys.executable, str(ROOT/'web/pakk.py'), str(ROOT/'web/build/moonstone-core.js'), str(target/'moonstone.html')], check=True)
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
html = target / 'moonstone.html'
data = html.read_text()
embedded = json.loads(re.search(r'const manifest = (\{.*?\});\n    const base', data, re.S)[1])
manifest = json.loads((ROOT / 'web/hd/manifest.json').read_text())
assert embedded == manifest, 'HTML og diskmanifest er forskjellige'
# HTML er pakket direkte i egen kandidatkatalog; felles web/build er urørt.
shutil.copy2(ROOT / 'web/build/moonstone-core.js', target / 'moonstone-core-used.js')
(target / 'hd').mkdir(exist_ok=True)
shutil.copy2(ROOT / 'web/hd/manifest.json', target / 'hd/manifest.json')
for f in manifest['files']:
    original = ROOT / 'web/hd' / f['path']
    assert sha(original) == f['sha256'] and original.stat().st_size == f['bytes'], f['path']
    destination = target / 'hd' / f['path']
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(original, destination)
    assert sha(destination) == f['sha256']
ledger = dict(schema=1, status='all_manifest_files_byte_and_hash_verified',
              html_sha256=sha(target / 'moonstone.html'),
              wasm_core_sha256=sha(target / 'moonstone-core-used.js'),
              manifest_sha256=sha(target / 'hd/manifest.json'),
              images=manifest['images'], files=manifest['files'],
              production_code_sha256={f'web/src/{n}': sha(ROOT / 'web/src' / n)
                  for n in ['core.js', 'render.js', 'scenes.js', 'hd.js']})
(target / 'package-ledger.json').write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(dict(host=str(target), images=ledger['images'], files=len(ledger['files']),
                     html_sha256=ledger['html_sha256'], ledger_sha256=sha(target / 'package-ledger.json'))))
