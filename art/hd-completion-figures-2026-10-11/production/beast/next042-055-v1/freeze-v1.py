"""Frys elleve kilde- og frontendkontrollerte Beast-ruter uten aktivering."""
from pathlib import Path
import hashlib
import json
import os
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
rel = lambda p: str(p.relative_to(ROOT))
read = lambda p: json.loads(p.read_text())


def frozen(path, value):
    data = json.dumps(value, indent=2, ensure_ascii=False) + '\n'
    if path.exists():
        assert path.read_text() == data, 'Bevar frossen fil: ' + rel(path)
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(data)


geometry = read(HERE / 'runtime-geometries-v1.json')
generation = read(HERE / 'generation-records-v1.json')
packing = read(HERE / 'verification/packing-v1.json')
independent = read(HERE / 'verification/packing-independent-v1.json')
proof_path = HERE / 'verification/runtime-fixtures-v1/test.json'
proof = read(proof_path)
assert len(geometry) == 11 and len(generation) == 10
assert independent['status'] == proof['status'] == 'passed' and not proof['errors']
assert packing['geometry_sha256'] == independent['geometry_sha256'] == sha(HERE / 'geometries-v1.json')
assert packing['generation_records_sha256'] == independent['generation_records_sha256'] == sha(HERE / 'generation-records-v1.json')
assert packing['packing_script_sha256'] == sha(HERE / 'pack-v1.cjs')
assert independent['script_sha256'] == sha(HERE / 'check-v1.py')
assert proof['geometry_sha256'] == sha(HERE / 'runtime-geometries-v1.json')
assert proof['test_sha256'] == proof['runtime_script_sha256'] == sha(HERE / 'runtime-fixtures-v1.cjs')
assert proof['html_sha256'] == sha(proof_path.parent / 'loaded.html')
assert len(proof['fixtures']) == 22 and len(proof['negative']) == 110
assert len(proof['palette_variants']) == 5 and not proof['runtime']['seen']
freeze = ROOT / 'art/hd-completion-figures-2026-10-11/verification/source-freezes-007'
for name, digest in proof['production_code_sha256'].items():
    assert sha(freeze / name) == digest

review_path = HERE / 'root-review-v1.json'
frozen(review_path, dict(schema=1, status='root_visually_reviewed', scope='Root har sammenlignet alle elleve original/HD-par og godkjent dem.042/046 beholder rustning/kappefragmenter; smaa effekter foelger kildeformen.049/050v1 er avvist historikk, v2 brukes.054 er eksakt originalsvart skygge, ikke nytt fotomateriale. Alle ruter i denne frysen er fixture-only uten faktisk kampobservasjon.', comparison_sha256=sha(HERE / 'comparison-v1.png'), actual_runtime_observed=False, candidates=[dict(key=c['key'], png_sha256=c['candidate_png_sha256'], mask_sha256=c['candidate_mask_sha256']) for c in geometry]))
shadow_prompt = HERE / 'preserved-shadow054.txt'
shadow_text = 'Bevar be1.c/054 som nøyaktig4x NN fra originalens indekser0/5. Null er transparent,5 er helt svart og opak. Ingen fotogenerering eller synlig fotoendring.\n'
if shadow_prompt.exists():
    assert shadow_prompt.read_text() == shadow_text
else:
    shadow_prompt.write_text(shadow_text)

files = {HERE / n for n in ['freeze-v1.py', 'prepare-geometries-v1.py', 'prepare-references-v1.py', 'pack-v1.cjs', 'check-v1.py', 'runtime-fixtures-v1.cjs', 'sources-v1.json', 'geometries-v1.json', 'runtime-geometries-v1.json', 'generation-records-v1.json', 'verification/packing-v1.json', 'verification/packing-independent-v1.json', 'comparison-v1.png', 'root-review-v1.json', 'preserved-shadow054.txt']}
files.add(proof_path)
files.update(ROOT / n for n in ['tools/hd_resterende_ikoner_fixture.cjs', 'art/hd-completion-figures-2026-10-11/production/contours.py', 'art/hd-completion-figures-2026-10-11/figures/ratmen-production/runtime-proof.cjs', 'art/hd-completion-figures-2026-10-11/figures/kn3-production/runtime-host.cjs'])
entries = []
for c in geometry:
    png = ROOT / c['packed_candidate_path']
    assert sha(png) == c['candidate_png_sha256'] == proof['assets'][c['key']]
    generated = next((g for g in generation if g['key'] == c['key']), None)
    if generated:
        raw, prompt = HERE / generated['raw'], HERE / generated['prompt']
        for name in ['raw', 'prompt', 'reference']:
            assert sha(HERE / generated[name]) == generated[name + '_sha256']
        original_record = HERE / generated['source_generation_record']
        assert sha(original_record) == generated['source_generation_record_sha256']
        files.add(original_record)
        tool = 'builtin_image_gen'
    else:
        assert c['frame'] == 54 and c['preserved_original_black_shadow']
        raw, prompt, tool = png, shadow_prompt, 'preserved_original_black_shadow'
    packed = next(r for r in packing['assets'] if r['key'] == c['key'])
    record_path = HERE / ('records/' + c['number'] + '-final-v1.json')
    frozen(record_path, dict(schema=1, key=c['key'], generation=generated, candidate_sha256=sha(png), source_bank_sha256=c['source_bank_sha256'], indices_sha256=c['indices_sha256'], geometry_sha256=sha(HERE / 'geometries-v1.json'), packed=packed, generation_tool=tool, actual_runtime_observed=False, runtime_scope='source_exact_fixture_only', source_size=[c['width'], c['height']], target_size=[c['width']*4, c['height']*4], photo_material=bool(generated), preserved_original_black_shadow=not generated))
    entry = dict(key=c['key'], bank='be1.c', frame=c['frame'], source_bank_sha256=c['source_bank_sha256'], indices_sha256=c['indices_sha256'], png=rel(png), png_sha256=sha(png), raw=rel(raw), raw_sha256=sha(raw), prompt=rel(prompt), prompt_sha256=sha(prompt), generation_tool=tool, runtime_proof=rel(proof_path), runtime_asset_sha256=sha(png), art_record=rel(record_path), art_record_sha256=sha(record_path), actual_runtime_observed=False, runtime_scope='source_exact_fixture_only', qa=dict(source_alpha_midpoints=c['width']*c['height'], normal_and_mirror=True, negative_source_owner_checks=True, five_original_knight_palettes=c['needs_mask'], original_hd_return='exact', emulated_state='unchanged'))
    files.update([raw, prompt, png, record_path, ROOT / c['source_palette_contract']])
    if c['needs_mask']:
        mask = ROOT / c['mask_path']
        assert sha(mask) == proof['mask_sha256'][c['key'].replace('.png', '.mask.png')]
        entry.update(mask=rel(mask), mask_sha256=sha(mask))
        files.add(mask)
    entries.append(entry)

contract_path = HERE / 'activation-set-eleven-v1.json'
companions = [p for p in files if p.suffix in ['.py', '.cjs', '.json'] and p != proof_path]
contract = dict(schema=1, visual_status='reviewed_original_and_runtime', source_zip_sha256=proof['source_zip_sha256'], production_code_sha256=proof['production_code_sha256'], wasm_core_sha256=proof['wasm_core_sha256'], proofs=[dict(path=rel(proof_path), sha256=sha(proof_path), html_path=rel(proof_path.parent/'loaded.html'), html_sha256=proof['html_sha256'])], companion_derivations=[dict(path=rel(p), sha256=sha(p)) for p in sorted(companions)], entries=entries, actual_runtime_observed=False, fixture_only=[c['key'] for c in geometry], scope='Ti separate fotomastere og en uendret svart originalskygge. Elleve ruter med22 normal/speil-fixturer,110 strenge negative kilde-/eierproever og fem maskerte ruter med fem originalpaletter. Historisk fryst007-frontend.008 krever ny bundet reproof; ingen aktivering, kampfangst eller naturlig kartreise paastaas.')
frozen(contract_path, contract)
files.add(contract_path)
summary_path = HERE / 'delivery-eleven-v1.json'
frozen(summary_path, dict(schema=1, status='frozen_not_activated', routes=11, png_files=16, photographic_masters=10, preserved_original_black_shadows=1, actual_runtime_observed=False, fixture_only=contract['fixture_only'], source_alpha_midpoints=independent['source_alpha_midpoints'], runtime_checks=len(proof['checks']), activation_contract=rel(contract_path), activation_sha256=sha(contract_path), file_sha256={rel(p):sha(p) for p in sorted(files)}))
files.add(summary_path)
# Originalreferanse-PNG regenereres fra ZIP og skal ikke legges i Git.
# Bevar avviste049/050v1 som egen genereringshistorikk, aldri positiv master.
for number in ['049', '050']:
    files.update(HERE / p for p in [f'generation-{number}-v1.json', f'raw/{number}-v1.png', f'prompts/{number}-v1.txt'])
for name in ['042-original', '042-hd', '046-original', '046-hd', '054-original', '054-hd']:
    files.add(proof_path.parent / (name + '.png'))
listing = HERE / 'delivery-eleven-files.txt'
value = '\n'.join(sorted(rel(p) for p in files)) + '\n'
if listing.exists():
    assert listing.read_text() == value
else:
    listing.write_text(value)
print(json.dumps(dict(status='frozen_not_activated', routes=11, png=16, photo_masters=10, original_shadows=1, runtime_checks=len(proof['checks']), activation_sha256=sha(contract_path))))
