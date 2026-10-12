#!/usr/bin/env python3
"""Lag kilde- og runtimebundet TAV-leveranse etter godkjent samlet bilde."""
import argparse
import hashlib
import json
from pathlib import Path

ART = Path(__file__).resolve().parent
ROOT = ART.parents[1]
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
relative = lambda p: str(p.relative_to(ROOT))
item = lambda p: {'path': relative(p), 'sha256': sha(p)}
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--runtime-version', default='v11')
p.add_argument('--visual-reviewed', action='store_true')
a = p.parse_args()
contract_file = ART / 'player-source-contract.json'
contract = json.loads(contract_file.read_text())
packing_file = ART / 'verification/packing-v1.json'
packing = json.loads(packing_file.read_text())
assert packing['status'] == 'passed'
assert packing['source_contract_sha256'] == sha(contract_file)
proofs, expected_assets, code, wasm, html = [], None, None, None, None
for color in range(4):
    path = ART / f'verification/runtime-{a.runtime_version}-{color}/dice-runtime.json'
    report = json.loads(path.read_text())
    assert report['status'] == 'passed' and report['controlled_color'] == color
    assert report['player_contract_sha256'] == sha(contract_file)
    assert report['source_zip_sha256'] == contract['source_zip_sha256']
    assert 'last_imported_background_is_clean_candidate' in report['checks']
    assert report['runtime']['imports']['bg/44898895.png'] == sha(ART / 'raw/tav-clean-v1.png')
    assert len(report['assets']) == 22
    assert sorted(map(int, report['runtime']['seen'])) == list(range(6, 23))
    if expected_assets is None:
        expected_assets = report['assets']
        code, wasm, html = report['production_code_sha256'], report['wasm_core_sha256'], report['html_sha256']
    assert expected_assets == report['assets']
    assert code == report['production_code_sha256']
    assert wasm == report['wasm_core_sha256'] and html == report['html_sha256']
    proofs.append(item(path))
for f, h in code.items():
    assert sha(ROOT / f) == h
assert sha(ROOT / 'web/build/moonstone-core.js') == wasm
original_palettes = json.loads((ART / 'source-audit.json').read_text())['active_knight_palettes_rgb4']
for color, named in enumerate(('0_blue', '1_yellow', '2_green', '3_red')):
    report = json.loads((ART / f'verification/runtime-{a.runtime_version}-{color}/dice-runtime.json').read_text())
    assert report['runtime']['palette'][6:11] == [int(v, 16) for v in original_palettes[named]]
photo, mask = ART / 'packed/embedded/tav-player.png', ART / 'packed/embedded/tav-player.mask.png'
background = ART / 'raw/tav-clean-v1.png'
for key, file in (('embedded/tav-player.png', photo), ('embedded/tav-player.mask.png', mask), ('bg/44898895.png', background)):
    assert expected_assets[key] == sha(file)
record = dict(schema=1,
    status='reviewed_original_and_runtime' if a.visual_reviewed else 'candidate_requires_visual_review',
    scope='En ekstra innebygd TAV.PIV-spillerfigur, separat fra CEL-mastertellingen. Ren tavernabakgrunn og alle17 DICE-mastere testes samlet. Ingen WI2-fastfigur finnes i originalen.',
    production_code_sha256=code, wasm_core_sha256=wasm, html_sha256=html,
    runtime_html=item(ART / 'verification/runtime-v9-package/moonstone.html'),
    package_manifest=item(ART / 'verification/runtime-v9-package/manifest.json'),
    package_ledger=item(ART / 'verification/runtime-v9-package/snapshot.json'),
    runtime_test=item(ART / 'runtime.cjs'),
    source_zip_sha256=contract['source_zip_sha256'], source_file='data/tav.piv',
    source_file_sha256=contract['source_file_sha256'], source_contract=item(contract_file),
    source_indices=item(ART / 'source/player-indices.bin'), source_mask=item(ART / 'source/player-mask.bin'),
    packing_proof=item(packing_file), packing_record=item(ART / 'packed/embedded/tav-player.json'),
    source_audit=item(ART / 'source-audit.json'),
    generation_record=item(ART / 'generation-record-player-v3.json'),
    raw=item(ART / 'raw/player-v3.png'), prompt=item(ART / 'prompts/player-v3.txt'),
    material_derivations=[item(ART / 'register-player-v3.cjs'), item(ART / 'material/player-v3-registered.json'), item(ART / 'material/player-v3-registered.png'), item(ART / 'verification/frozen-player-before-fixed/tav-player.png'), item(ART / 'normalize-fixed-material-v2.cjs'), item(ART / 'material/fixed-material-v2.json')],
    companion_derivations=[item(ROOT / 'art/hd-completion-figures-2026-10-11/production/dice' / name)
        for name in ('pack.cjs', 'join-cloth.py', 'freeze-packing.py', 'freeze-delivery.py')]
        + [item(ART / 'verification/dice-source-cloth.json')],
    embedded_entries=[dict(key='embedded/tav-player.png', png=item(photo), mask=item(mask),
        original_rect=contract['rect'], original_selected_pixels=7431,
        original_live_pixels=3682, excluded_other_live_pixels=16, scene_id='tavern',
        overlay=dict(key='embedded/tav-player', rect=contract['rect'], uv_rect=[0, 0, 1, 1], foreground=False, palette_mask=True))],
    background=dict(key='bg/44898895.png', png=item(background), prompt=item(ART / 'prompts/tav-clean-v1.txt'), ownership='Root generated and visually checked this clean background; this delivery binds the exact shared RGB file.'),
    proofs=proofs, runtime_assets=expected_assets,
    notes=['Hver DICE-rute har egen fotografisk master; DICE-proveniens og aktivering eies av root.',
        'Kappens6..10 og hjelmfjær bruker faktisk originalpalett for alle fire farger. Indeks11 er fast original mørkerød og er ikke med i levende masken.',
        'Original albue har dithrede svarte indekser.14 åpne originale nullskygger mellom samme rads originale stålankre er dokumentert i kildemasken.',
        'Disse prøvene bruker kontrollert originalinngang08a1f0 og originalt bettrykk. Ingen naturlig kartreise eller full gjennomspilling påstås.'])
output = ART / 'activation-set-001.json'
output.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'status': record['status'], 'path': relative(output), 'sha256': sha(output)}))
