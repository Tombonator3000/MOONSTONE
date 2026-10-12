"""Gjenskap007-kandidatbevisenes HTML uten aa endre aktiv pakke eller fryste filer."""
from pathlib import Path
import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile

R = Path(__file__).resolve().parents[3]
F = R / 'art/hd-completion-figures-2026-10-11'
index = json.loads((F / 'delivery-contracts-007.json').read_text())
expected_html = '8fd1d2517aca80f0f71abafc178cccd9c48dd4157f3e3d76de2f98e63b90abf5'
sha = lambda b: hashlib.sha256(b).hexdigest()
manifest_bytes = subprocess.check_output(['git', 'show', index['baseline_commit'] + ':web/hd/manifest.json'], cwd=R)
assert sha(manifest_bytes) == index['baseline_manifest_sha256']
manifest = json.loads(manifest_bytes)
with tempfile.TemporaryDirectory(prefix='moonstone-frozen007-') as directory:
    base = Path(directory)
    web = base / 'web'
    for folder in ['src', 'vendor']:
        for name in subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', index['baseline_commit'], 'web/' + folder], cwd=R, text=True).splitlines():
            p = base / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(subprocess.check_output(['git', 'show', index['baseline_commit'] + ':' + name], cwd=R))
    for row in json.loads((F / 'verification/source-freezes-007/source-map.json').read_text())['files']:
        data = (R / row['frozen_path']).read_bytes()
        assert sha(data) == row['sha256']
        (base / row['path']).write_bytes(data)
    hd = web / 'hd'
    hd.mkdir()
    (hd / 'manifest.json').write_bytes(manifest_bytes)
    for row in manifest['files']:
        original = R / 'web/hd' / row['path']
        data = original.read_bytes()
        assert sha(data) == row['sha256'] and len(data) == row['bytes']
        p = hd / row['path']
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
    # pakk.py leses fra samme baseline; frontendens fire avtalte filer er overlagt.
    pack_path = web / 'pakk.py'
    pack_path.write_bytes(subprocess.check_output(['git', 'show', index['baseline_commit'] + ':web/pakk.py'], cwd=R))
    spec = importlib.util.spec_from_file_location('moonstone_frozen_pack', pack_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    target = base / 'package/moonstone.html'
    sys.argv = [str(pack_path), str(R / 'web/build/moonstone-core.js'), str(target)]
    module.main()
    data = target.read_bytes()
    assert sha(data) == expected_html, 'Gjenskapt HTML avviker'
    paths = set()
    for row in index['deliveries']:
        for proof in json.loads((R / row['path']).read_text())['proofs']:
            assert proof['html_sha256'] == expected_html
            paths.add(proof['html_path'])
    for name in paths:
        p = R / name
        assert p.resolve().is_relative_to(R)
        if p.exists():
            assert sha(p.read_bytes()) == expected_html, 'Eksisterende fryst fil avviker: ' + name
        else:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)
print(json.dumps(dict(status='passed', html_sha256=expected_html, proof_html_paths=len(paths))))
