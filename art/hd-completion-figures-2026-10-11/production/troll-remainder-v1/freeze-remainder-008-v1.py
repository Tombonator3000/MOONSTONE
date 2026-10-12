"""Frys tretten kilde- og fixturekontrollerte Troll-ruter for aattende leveranse."""
from pathlib import Path
import hashlib
import json
import sys
from PIL import Image

H = Path(__file__).resolve().parent
R = H.parents[3]
F = H.parents[1]
sys.path.insert(0, str(R / 'tools'))
import moonfiles as mf
from hd_bestilling import utvid_indekser

sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
rel = lambda p: str(p.relative_to(R))
rows = json.loads((H / 'runtime-geometries-remainder-v1.json').read_text())
candidates = {r['key']: r for r in json.loads((H / 'candidates-remainder-v1.json').read_text())}
proof_path = H / 'verification/fixtures-remainder-008-v1/test.json'
proof = json.loads(proof_path.read_text())
assert proof['status'] == 'passed' and not proof['errors']
assert len(proof['fixtures']) == 26 and len(proof['negative']) == 130
assert proof['actual_runtime_observed'] is False
assert sha(H / 'runtime-fixtures-remainder-v1.cjs') == proof['test_sha256']
assert sha(H / 'runtime-geometries-remainder-v1.json') == proof['geometry_sha256']
assert sha(proof_path.parent / 'loaded.html') == proof['html_sha256']
for name, digest in proof['production_code_sha256'].items():
    assert sha(R / name) == digest, 'Kandidaten maa bindes til gjeldende visningskode'
game = mf.Spill(str(R / 'Moonstonecd32-AMIGA.zip'))
entries, qa = [], []
extras = set()
for row in rows:
    key = row['key']
    candidate = candidates[key]
    png = R / candidate['candidate']
    assert sha(png) == candidate['candidate_sha256'] == proof['assets'][key]
    source_bank = game.les('data/' + row['bank'])
    assert hashlib.sha256(source_bank).hexdigest() == row['source_bank_sha256']
    src = mf.cel_les(source_bank)[0][row['frame']]
    w, h = src['bredde'], src['hoyde']
    indices = utvid_indekser(mf.plan_til_indeks(src['data'], src['plan'], w, h), src['maske'])
    assert list(indices) == row['indices'] and hashlib.sha256(indices).hexdigest() == row['indices_sha256']
    image = Image.open(png)
    assert image.mode == 'RGBA' and image.size == (w * 4, h * 4)
    for y in range(h):
        for x in range(w):
            assert (image.getpixel((x * 4 + 2, y * 4 + 2))[3] >= 128) == bool(indices[y * w + x]), key
    entry = dict(key=key, bank=row['bank'], frame=row['frame'], source_bank_sha256=row['source_bank_sha256'], indices_sha256=row['indices_sha256'], png=rel(png), png_sha256=sha(png), actual_runtime_observed=False, runtime_proof=rel(proof_path), runtime_asset_sha256=sha(png))
    if candidate.get('art_record'):
        art_path = R / candidate['art_record']
        art = json.loads(art_path.read_text())
        assert sha(art_path) == candidate['art_record_sha256']
        assert art['candidate_sha256'] == sha(png)
        raw, prompt = R / art['raw_file'], R / art['prompt']
        assert sha(raw) == art['raw_sha256'] and sha(prompt) == art['prompt_sha256']
        entry.update(raw=rel(raw), raw_sha256=sha(raw), prompt=rel(prompt), prompt_sha256=sha(prompt), generation_tool='builtin_image_gen', art_record=rel(art_path), art_record_sha256=sha(art_path), photographic_scope='body_or_foot' if row['frame'] in [16, 18, 19, 10] else 'source_bound_motion_material')
        patch = art.get('eye_source_binding', {}).get('generated_eyeless_skin_patch')
        if patch:
            entry['additional_generated_material'] = {k: patch[k] for k in ['raw', 'raw_sha256', 'prompt', 'prompt_sha256']}
            assert sha(R / patch['raw']) == patch['raw_sha256'] and sha(R / patch['prompt']) == patch['prompt_sha256']
            extras.update(R / patch[k] for k in ['raw', 'prompt'])
        if candidate.get('generation_record'):
            generation = R / candidate['generation_record']
            extras.add(generation)
            record = json.loads(generation.read_text())
            assert record['raw_sha256'] == sha(raw) and record['prompt_sha256'] == sha(prompt)
        if art.get('original_flat_shadow_packing'):
            for y in range(h * 4):
                for x in range(w * 4):
                    if indices[y // 4 * w + x // 4] == 5:
                        assert image.getpixel((x, y)) == (0, 0, 0, 255)
    else:
        assert set(indices) == {0, 5} and row['frame'] == 12
        expected = bytes(v for y in range(h * 4) for x in range(w * 4) for v in (0, 0, 0, 255 if indices[y // 4 * w + x // 4] else 0))
        assert image.tobytes() == expected
        entry.update(raw=candidate['raw'], raw_sha256=candidate['raw_sha256'], prompt=candidate['prompt'], prompt_sha256=candidate['prompt_sha256'], generation_tool='preserved_original_black_shadow')
    entries.append(entry)
    qa.append(dict(key=key, checked_source_midpoints=w * h, missing=0, filled_holes=0, png_sha256=sha(png)))
qa_path = H / 'source-qa-remainder-008-v1.json'
qa_path.write_text(json.dumps(dict(status='passed', entries=qa, checks=sum(r['checked_source_midpoints'] for r in qa)), indent=2) + '\n')
review_path = H / 'visual-review-remainder-008-v1.json'
review = json.loads(review_path.read_text())
assert review['status'] == 'approved' and review['keys'] == [r['key'] for r in rows]
for screen in review['screenshots']:
    assert sha(R / screen['path']) == screen['sha256']
companions = [Path(__file__), H / 'prepare-references-v2.py', H / 'prepare-remainder-v1.py', H / 'runtime-fixtures-remainder-v1.cjs', H / 'runtime-geometries-remainder-v1.json', H / 'pack-exact-shadow-v2.py', H / 'shadow-correction-v2.json', H / 'motion/pack-v1.py', H / 'motion/source-qa-v1.json', H / 'source-qa-four-v1-rejected.json', qa_path, review_path, F / 'palettes/cases/troll.json', H.parent / 'eye_pack.py', H.parent / 'effect_pack.py']
companions.extend(sorted(extras))
contract = dict(schema=1, visual_status='reviewed_original_and_runtime', source_zip_sha256=proof['source_zip_sha256'], production_code_sha256=proof['production_code_sha256'], wasm_core_sha256=proof['wasm_core_sha256'], proofs=[dict(path=rel(proof_path), sha256=sha(proof_path), html_path=rel(proof_path.parent / 'loaded.html'), html_sha256=proof['html_sha256'])], companion_derivations=[dict(path=rel(p), sha256=sha(p)) for p in companions], scope='Tretten resterende Troll-ruter, fire separate figur/fot-mastere og aatte separate fotografiske bevegelsesmaterialer, pluss en eksakt original svart skygge. Originalens ditherhull og brune makropalett beholdes i klubbebevegelser. Bare normal/speil og strenge negative frontend-fixturer er bevist; ingen faktisk kampobservasjon av de nye HD-rutene paastaas.', photographic_body_foot_masters=4, photographic_motion_materials=8, preserved_black_shadows=1, fixture_only=[r['key'] for r in rows], entries=entries)
out = H / 'activation-set-remainder-008-v1.json'
data = json.dumps(contract, ensure_ascii=False, indent=2) + '\n'
if out.exists():
    assert out.read_text() == data
else:
    out.write_text(data)
files = set(companions + [out, proof_path, H / 'comparison-four-v2.png', H / 'motion/comparison-v1.png'])
files.update(proof_path.parent.glob('*.png'))
for entry in entries:
    files.update(R / entry[k] for k in ['png', 'raw', 'prompt', 'art_record'] if entry.get(k))
(H / 'delivery-remainder-008-files.txt').write_text('\n'.join(sorted(rel(p) for p in files)) + '\n')
print(json.dumps(dict(status='frozen_not_activated', routes=13, png=13, runtime_checks=len(proof['checks']), contract_sha256=sha(out))))
