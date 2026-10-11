#!/usr/bin/env python3
"""Frys faktisk HTML og bytevaliderte standardfiler til egen lokal testvert."""
import hashlib
import json
import shutil
import tempfile
from pathlib import Path

ART = Path(__file__).resolve().parent
ROOT = ART.parents[1]
sha = lambda b: hashlib.sha256(b).hexdigest()
html = (ROOT / 'web/build/moonstone.html').read_bytes()
text = html.decode('utf-8')
start = text.index('const manifest =', text.index('const StandardHd =')) + len('const manifest =')
manifest, _ = json.JSONDecoder().raw_decode(text[start:].lstrip())
snapshot = Path(tempfile.mkdtemp(prefix='moonstone-tav-frozen-'))
(snapshot / 'moonstone.html').write_bytes(html)
ledger = []
for item in manifest['files']:
    rel = Path(item['path'])
    assert not rel.is_absolute() and '..' not in rel.parts
    source = ROOT / 'web/build/hd' / rel
    data = source.read_bytes()
    assert len(data) == item['bytes'] and sha(data) == item['sha256'], item['path']
    target = snapshot / 'hd' / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    ledger.append({'path': item['path'], 'sha256': sha(data), 'bytes': len(data)})
record = {'schema': 1, 'status': 'frozen', 'snapshot': str(snapshot),
    'html_sha256': sha(html), 'files': ledger,
    'source_files': {f: sha((ROOT / f).read_bytes()) for f in ('web/src/render.js', 'web/src/scenes.js', 'web/src/core.js', 'web/src/hd.js', 'web/build/moonstone-core.js', 'Moonstonecd32-AMIGA.zip')}}
verification = ART / 'verification/runtime-v9-package'
verification.mkdir(parents=True, exist_ok=True)
(verification / 'moonstone.html').write_bytes(html)
(verification / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
(verification / 'snapshot.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'snapshot': str(snapshot), 'html': sha(html), 'files': len(ledger)}))
