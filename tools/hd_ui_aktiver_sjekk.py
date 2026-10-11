#!/usr/bin/env python3
"""Prov aktiveringsporten i en midlertidig kopi, aldri mot aktiv pakke."""
import contextlib
import copy
import importlib.util
import io
import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    spec = importlib.util.spec_from_file_location('ui_activate', ROOT/'tools/hd_ui_aktiver.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    checks = []
    with tempfile.TemporaryDirectory(prefix='moonstone-ui-gate-') as tmp:
        sandbox = Path(tmp)
        art = sandbox/'art/hd-ui-followup-2026-10-11'
        src = ROOT/'art/hd-ui-followup-2026-10-11'
        for rel in ('fragment-icons.json', 'source-contracts.json', 'candidate-icons.json',
                    'packing-report.json', 'verification/bound-runtime/ui-fixtures-test.json'):
            target = art/rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src/rel, target)
        shutil.copytree(src/'packed', art/'packed')
        for rel in ('web/hd/icons.json', 'web/hd/manifest.json',
                    'web/src/render.js', 'web/src/scenes.js'):
            target = sandbox/rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT/rel, target)
        module.ROOT, module.ART = sandbox, art
        sys.argv = ['hd_ui_aktiver.py']
        proof = art/'verification/bound-runtime/ui-fixtures-test.json'
        original = json.loads(proof.read_text())
        before = (sandbox/'web/hd/icons.json').read_bytes()
        with contextlib.redirect_stdout(io.StringIO()):
            module.main()
        checks.append('fresh_proof_accepted')
        for name, change in (
            ('different_tested_png_rejected', lambda p: p['packed_png_sha256'].__setitem__('mi.c/021', '0'*64)),
            ('different_source_contract_rejected', lambda p: p.__setitem__('source_contracts_sha256', '0'*64)),
            ('stale_render_proof_rejected', lambda p: p['production_code_sha256'].__setitem__('web/src/render.js', '0'*64)),
            ('stale_scene_proof_rejected', lambda p: p['production_code_sha256'].__setitem__('web/src/scenes.js', '0'*64)),
        ):
            changed = copy.deepcopy(original)
            change(changed)
            proof.write_text(json.dumps(changed))
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    module.main()
            except AssertionError:
                checks.append(name)
            else:
                raise AssertionError('Ugyldig runtimebevis ble godtatt: '+name)
        assert before == (sandbox/'web/hd/icons.json').read_bytes()
        checks.append('dry_run_and_rejections_preserve_metadata')
    print(json.dumps({'status': 'passed', 'checks': checks}))


if __name__ == '__main__':
    main()
