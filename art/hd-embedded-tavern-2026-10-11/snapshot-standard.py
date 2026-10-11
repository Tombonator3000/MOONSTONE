#!/usr/bin/env python3
"""Frys den faktisk bygde standardpakken foer tavernaprøven."""
import hashlib
import json
from pathlib import Path
import shutil
import tempfile

ART = Path(__file__).resolve().parent
ROOT = ART.parents[1]
sha = lambda b: hashlib.sha256(b).hexdigest()
out = ART / 'verification/standard-v12-package'
assert not out.exists(), 'Bevar tidligere snapshot; bruk nytt versjonsnavn'
manifest_bytes = (ROOT / 'web/build/hd/manifest.json').read_bytes()
assert manifest_bytes == (ROOT / 'web/hd/manifest.json').read_bytes()
manifest = json.loads(manifest_bytes)
html = (ROOT / 'web/build/moonstone.html').read_bytes()
files = ['web/src/core.js', 'web/src/render.js', 'web/src/scenes.js', 'web/src/hd.js',
         'web/build/moonstone-core.js', 'Moonstonecd32-AMIGA.zip']
sources = {f: sha((ROOT / f).read_bytes()) for f in files}
snapshot = Path(tempfile.mkdtemp(prefix='moonstone-tav-standard-v12-'))
shutil.copytree(ROOT / 'web/build/hd', snapshot / 'hd')
(snapshot / 'moonstone.html').write_bytes(html)
ledger = []
for row in manifest['files']:
    data = (snapshot / 'hd' / row['path']).read_bytes()
    assert sha(data) == row['sha256'] and len(data) == row['bytes']
    ledger.append({k: row[k] for k in ('path', 'sha256', 'bytes')})
assert manifest_bytes == (ROOT / 'web/build/hd/manifest.json').read_bytes()
assert html == (ROOT / 'web/build/moonstone.html').read_bytes()
assert sources == {f: sha((ROOT / f).read_bytes()) for f in files}
out.mkdir(parents=True)
(out / 'moonstone.html').write_bytes(html)
(out / 'manifest.json').write_bytes(manifest_bytes)
(out / 'snapshot.json').write_text(json.dumps(dict(schema=1, status='frozen',
    snapshot=str(snapshot), html_sha256=sha(html), manifest_sha256=sha(manifest_bytes),
    images=manifest['images'], files=ledger, source_files=sources), indent=2) + '\n')
print(json.dumps(dict(status='frozen', snapshot=str(snapshot), files=len(ledger),
    images=manifest['images'], html_sha256=sha(html), manifest_sha256=sha(manifest_bytes))))
