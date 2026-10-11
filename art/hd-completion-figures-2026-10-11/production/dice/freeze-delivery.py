"""Frys 17 selvstendige DICE-mastere etter samlet TAV-prove i fire farger."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
ART = HERE.parents[1]
TAV = ROOT/'art/hd-embedded-tavern-2026-10-11'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
rel = lambda p: str(p.relative_to(ROOT))
proofs = [TAV/f'verification/runtime-v11-{n}/dice-runtime.json' for n in range(4)]
reports = [json.loads(p.read_text()) for p in proofs]
assert all(r['status'] == 'passed' and len(r['checks']) == 57 and not r['errors'] for r in reports)
assert all(r['assets'] == reports[0]['assets'] for r in reports)
html = TAV/'verification/runtime-v9-package/moonstone.html'
assert all(sha(html) == r['html_sha256'] for r in reports)
materials = [
    dict(raw=rel(TAV/'raw/tav-clean-v1.png'), raw_sha256=sha(TAV/'raw/tav-clean-v1.png'),
         prompt=rel(TAV/'prompts/tav-clean-v1.txt'), prompt_sha256=sha(TAV/'prompts/tav-clean-v1.txt')),
    dict(raw=rel(TAV/'raw/player-v3.png'), raw_sha256=sha(TAV/'raw/player-v3.png'),
         prompt=rel(TAV/'prompts/player-v3.txt'), prompt_sha256=sha(TAV/'prompts/player-v3.txt'))]
entries = []
for n in range(6, 23):
    key = f'dice.cel/{n:03}.png'
    route = json.loads((ART/f'routes/{key[:-4]}.json').read_text())
    record_path = HERE/f'records/dice-{n:03}-final.json'
    record = json.loads(record_path.read_text())
    pack = ART/f'packs/dice.cel/{n:03}/{record["candidate_sha256"][:16]}'
    png = pack/'hd'/key
    assert sha(png) == record['candidate_sha256'] == reports[0]['assets'][key]
    frozen_record = pack/'art-record.json'
    assert frozen_record.read_bytes() == record_path.read_bytes()
    entry = dict(key=key, bank='dice.cel', frame=n,
        source_bank_sha256=route['source_bank']['sha256'], indices_sha256=route['indices_sha256'],
        png=rel(png), png_sha256=sha(png), raw=rel(HERE/record['raw']), raw_sha256=record['raw_sha256'],
        prompt=rel(HERE/record['prompt']), prompt_sha256=record['prompt_sha256'],
        generation_tool='builtin_image_gen', runtime_proof=rel(proofs[0]), runtime_asset_sha256=sha(png),
        art_record=rel(frozen_record), art_record_sha256=sha(frozen_record),
        additional_generated_materials=materials[:2 if n < 8 else 1],
        qa=dict(source_centers_opaque=record['opaque_source_centers'],
                source_centers_empty=record['empty_source_centers'], source_midpoints_missing=0,
                source_transparent_midpoints_filled=0, four_original_player_palettes=True,
                original_hd_return='exact', emulated_state='unchanged'))
    if n < 8:
        mask = pack/'hd'/key.replace('.png', '.mask.png')
        assert sha(mask) == record['mask_sha256'] == reports[0]['assets'][key.replace('.png', '.mask.png')]
        entry.update(mask=rel(mask), mask_sha256=sha(mask))
    entries.append(entry)
delivery = dict(schema=1, visual_status='reviewed_original_and_runtime',
    source_zip_sha256=sha(ROOT/'Moonstonecd32-AMIGA.zip'),
    production_code_sha256=reports[0]['production_code_sha256'], wasm_core_sha256=reports[0]['wasm_core_sha256'],
    proofs=[dict(path=rel(p), sha256=sha(p), html_path=rel(html), html_sha256=sha(html)) for p in proofs],
    scope='17 egne foto-raabilder: fire tavernahansker/arm006..009 og13ruter med tre kastede terninger010..022. '
          'Originalgeometri og bordplassering.210kildeidentiske stasjonare kappepiksler i006/007 deler TAV-materiale. '
          'Samlet med TAV-fastfigur, NN-maske og ren bakgrunn i fire originalpaletter. Kontrollert originalinngang, ikke naturlig kartreise.',
    entries=entries)
(HERE/'activation-set-dice-001.json').write_text(json.dumps(delivery, ensure_ascii=False, indent=2)+'\n')
print('Frosset17DICE-mastere og2NN-masker mot228samlede runtimekontroller')
