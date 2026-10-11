"""Pakk en isolert HTML fra en frosset kopi av gjeldende WASM-kjerne."""
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ART = Path(__file__).resolve().parent
ROOT = ART.parent.parent
sha = lambda b: hashlib.sha256(b).hexdigest()
host = ART/'runtime-host'
host.mkdir(exist_ok=True)
source_core = ROOT/'web/build/moonstone-core.js'
frozen = host/'moonstone-core-used.js'
frozen.write_bytes(source_core.read_bytes())
production = {f: (ROOT/f).read_bytes() for f in ('web/src/render.js', 'web/src/scenes.js')}
subprocess.run(['python3', str(ROOT/'web/pakk.py'), str(frozen), str(host/'moonstone.html')], cwd=ROOT, check=True)
assert sha(frozen.read_bytes()) == sha(source_core.read_bytes()), 'Kjernen endret under pakking'
assert all((ROOT/f).read_bytes() == b for f, b in production.items()), 'Produksjonskode endret under pakking'
report = {'created_at': datetime.now(timezone.utc).isoformat(), 'wasm_core_sha256': sha(frozen.read_bytes()),
          'html_sha256': sha((host/'moonstone.html').read_bytes()),
          'production_code_sha256': {f: sha(b) for f, b in production.items()},
          'scope': 'Isolert pakke. Kopiert gjeldende WASM og produksjons-JS, aktive HD-filer bare lest.'}
(ART/'verification/host-build.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(report))
