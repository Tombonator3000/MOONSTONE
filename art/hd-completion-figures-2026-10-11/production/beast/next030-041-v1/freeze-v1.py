"""Frys tolv kildeverifiserte beistruter med eksplisitt faktisk/fixture-avgrensing."""
from pathlib import Path
import hashlib
import json

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
rel = lambda p: str(p.relative_to(ROOT))
geometry_path = HERE / 'runtime-geometries-v1.json'
geometry = json.loads(geometry_path.read_text())
generation_path = HERE / 'generation-records-v1.json'
generation = json.loads(generation_path.read_text())
packing = json.loads((HERE / 'verification/packing-v1.json').read_text())
independent = json.loads((HERE / 'verification/packing-independent-v1.json').read_text())
proof_paths = [HERE / f'verification/runtime-{profile}-v1/test.json' for profile in ['right', 'fire']]
proofs = [json.loads(p.read_text()) for p in proof_paths]
assert len(geometry) == len(generation) == 12
assert independent['status'] == 'passed'
assert packing['geometry_sha256'] == independent['geometry_sha256'] == sha(HERE / 'geometries-v1.json')
assert packing['generation_records_sha256'] == independent['generation_records_sha256'] == sha(generation_path)
assert packing['packing_script_sha256'] == sha(HERE / 'pack-v1.cjs')
assert independent['script_sha256'] == sha(HERE / 'check-v1.py')
for proof, path in zip(proofs, proof_paths):
    assert proof['status'] == 'passed' and not proof['errors']
    assert proof['geometry_sha256'] == sha(geometry_path)
    assert proof['test_sha256'] == sha(HERE / 'runtime-v1.cjs')
    assert proof['html_sha256'] == sha(path.parent / 'loaded.html')
    for file, digest in proof['production_code_sha256'].items():
        assert sha(ROOT / file) == digest
assert len(proofs[0]['fixtures']) == 24 and len(proofs[0]['negative']) == 120
assert len(proofs[0]['palette_variants']) == 8
actual = {key + '.png': (path, row) for path, proof in zip(proof_paths, proofs) for key, row in proof['runtime']['seen'].items()}
assert set(actual) == {f'be1.c/{frame:03}.png' for frame in range(34, 42)}
fixture_only = sorted(set(proofs[0]['assets']) - set(actual))
assert fixture_only == [f'be1.c/{frame:03}.png' for frame in range(30, 34)]

def frozen(path, value):
    data = json.dumps(value, indent=2) + '\n'
    if path.exists():
        assert path.read_text() == data, 'Bevar frossen leveranse: ' + rel(path)
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(data)

entries = []
files = {HERE / name for name in ['freeze-v1.py', 'prepare-geometries-v1.py', 'prepare-references-v1.py', 'pack-v1.cjs', 'check-v1.py', 'runtime-v1.cjs', 'sources-v1.json', 'geometries-v1.json', 'runtime-geometries-v1.json', 'generation-records-v1.json', 'verification/packing-v1.json', 'verification/packing-independent-v1.json', 'comparison-v1.png']}
files.update(proof_paths)
for c in geometry:
    generated = next(g for g in generation if g['key'] == c['key'])
    packed = next(g for g in packing['assets'] if g['key'] == c['key'])
    png = ROOT / c['packed_candidate_path']
    assert sha(png) == packed['candidate_sha256'] == proofs[0]['assets'][c['key']]
    for name in ['raw', 'prompt', 'reference']:
        assert sha(HERE / generated[name]) == generated[name + '_sha256']
        files.add(HERE / generated[name])
    files.add(png)
    files.add(ROOT / c['source_palette_contract'])
    observed = c['key'] in actual
    record = {**generated, **packed, 'candidate_sha256': sha(png), 'visual_status': 'reviewed_original_and_runtime', 'actual_runtime_observed': observed, 'runtime_scope': 'Original CPU-kamp med tre dokumenterte sceneinit-skrivinger og faktisk right/fire-inndata. Ikke naturlig kartreise.' if observed else 'Bare normal/speil, negative frontendporter og uavhengig kilde-/foto-/alfakontroll. Native kall i eksisterende profiler ligger helt utenfor skjermen; ingen faktisk synlig-kamppastand.', 'neutral_template': c['neutral_template'], 'exact_original_gray_motion_cells': c['original_motion_cells'], 'geometry_sha256': sha(HERE / 'geometries-v1.json'), 'packing_script_sha256': packing['packing_script_sha256'], 'method': packing['scope']}
    record_path = HERE / f"records/{c['number']}-final-v1.json"
    frozen(record_path, record)
    files.add(record_path)
    entry = dict(key=c['key'], bank='be1.c', frame=c['frame'], source_bank_sha256=c['source_bank_sha256'], indices_sha256=c['indices_sha256'], png=rel(png), png_sha256=sha(png), raw=rel(HERE / generated['raw']), raw_sha256=generated['raw_sha256'], prompt=rel(HERE / generated['prompt']), prompt_sha256=generated['prompt_sha256'], generation_tool='builtin_image_gen', runtime_proof=rel(proof_paths[0]), runtime_asset_sha256=sha(png), art_record=rel(record_path), art_record_sha256=sha(record_path), actual_runtime_observed=observed, qa=dict(source_alpha_midpoints=c['width'] * c['height'], source_midpoints_missing=0, source_transparent_midpoints_filled=0, normal_and_mirror=True, negative_source_owner_checks=True, five_original_knight_palettes=c['needs_mask'], original_hd_return='exact', emulated_state='unchanged'))
    if c['needs_mask']:
        mask = ROOT / c['mask_path']
        assert sha(mask) == proofs[0]['mask_sha256'][c['key'].replace('.png', '.mask.png')]
        entry.update(mask=rel(mask), mask_sha256=sha(mask))
        files.add(mask)
    if observed:
        actual_path, sample = actual[c['key']]
        entry['actual_runtime_proof'] = rel(actual_path)
        entry['actual_runtime_frame'] = sample['frame']
        for mode in ['original', 'hd']:
            path = actual_path.parent / f"combat-{c['number']}-{mode}.png"
            assert sha(path) == sample[mode + '_sha256']
            files.add(path)
    entries.append(entry)
delivery = dict(schema=1, visual_status='reviewed_original_and_runtime', source_zip_sha256=proofs[0]['source_zip_sha256'], production_code_sha256=proofs[0]['production_code_sha256'], wasm_core_sha256=proofs[0]['wasm_core_sha256'], proofs=[dict(path=rel(path), sha256=sha(path), html_path=rel(path.parent / 'loaded.html'), html_sha256=proof['html_sha256']) for path, proof in zip(proof_paths, proofs)], companion_derivations=[dict(path=rel(path), sha256=sha(path)) for path in sorted(files) if path.suffix in ['.py', '.cjs', '.json']], scope='Tolv individuelle fotografiske originalruter. Alle har normal/speil og strenge kilde-/forgrunnsporter; aatte ridderfragmenter har fem palettmaskefixturer og faktisk original CPU-kamp. Fire beistfragmenter030..033 er fixture-only og merket actual_runtime_observed=false. Ingen naturlig kartreise, ingen frontendendring og ingen aktivering fra denne frysen.', fixture_only=fixture_only, entries=entries)
activation_path = HERE / 'activation-set-twelve-v1.json'
frozen(activation_path, delivery)
files.add(activation_path)
summary = dict(schema=1, status='frozen_not_activated', routes=12, png_files=20, photographic_masters=12, actual_runtime_observed=sorted(actual), fixture_only=fixture_only, source_alpha_midpoints=independent['source_alpha_midpoints'], exact_original_gray_motion_subpixels=independent['exact_original_motion_subpixels'], runtime_checks=sum(len(p['checks']) for p in proofs), activation_contract=rel(activation_path), activation_sha256=sha(activation_path), file_sha256={rel(path): sha(path) for path in sorted(files)})
summary_path = HERE / 'delivery-twelve-v1.json'
frozen(summary_path, summary)
files.add(summary_path)
file_list = HERE / 'delivery-twelve-files.txt'
value = '\n'.join(rel(p) for p in sorted(files)) + '\n'
if file_list.exists():
    assert file_list.read_text() == value
else:
    file_list.write_text(value)
print(json.dumps({k: summary[k] for k in ['status', 'routes', 'png_files', 'runtime_checks', 'activation_sha256']}))
