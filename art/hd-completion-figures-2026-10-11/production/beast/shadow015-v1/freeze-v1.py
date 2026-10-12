"""Frys den rene svartskyggen som fixture-verifisert kandidat til neste levering."""
from pathlib import Path
import hashlib
import json

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
rel = lambda p: str(p.relative_to(ROOT))
geometry = HERE / 'runtime-geometries-v1.json'
c = json.loads(geometry.read_text())[0]
proof_path = HERE / 'verification/fixtures-v1/test.json'
proof = json.loads(proof_path.read_text())
assert proof['status'] == 'passed' and not proof['errors']
assert len(proof['fixtures']) == 2 and len(proof['negative']) == 10
assert sha(geometry) == proof['geometry_sha256']
assert sha(HERE / 'runtime-v1.cjs') == proof['test_sha256']
assert sha(proof_path.parent / 'loaded.html') == proof['html_sha256']
assert set(c['indices']) == {0, 5}
png = ROOT / c['packed_candidate_path']
assert sha(png) == proof['assets'][c['key']]
companions = [HERE / name for name in ['prepare-v1.py', 'freeze-v1.py', 'runtime-v1.cjs', 'runtime-geometries-v1.json']]
companions.append(ROOT / c['source_palette_contract'])
entry = dict(key=c['key'], bank='be1.c', frame=15, source_bank_sha256=c['source_bank_sha256'], indices_sha256=c['indices_sha256'], png=rel(png), png_sha256=sha(png), raw=rel(png), raw_sha256=sha(png), prompt=rel(HERE / 'preserved-shadow.txt'), prompt_sha256=sha(HERE / 'preserved-shadow.txt'), generation_tool='preserved_original_black_shadow', actual_runtime_observed=False, runtime_proof=rel(proof_path), runtime_asset_sha256=sha(png), scope='Ren svart originalskygge, ingen ny fotomaster eller synlig fotoendring. Nøyaktig4x NN-alfa fra indeks0/5. Bare normal/speil og strenge negative frontend-fixturer er bevist.')
contract = dict(schema=1, visual_status='reviewed_original_and_runtime', source_zip_sha256=proof['source_zip_sha256'], production_code_sha256=proof['production_code_sha256'], wasm_core_sha256=proof['wasm_core_sha256'], proofs=[dict(path=rel(proof_path), sha256=sha(proof_path), html_path=rel(proof_path.parent / 'loaded.html'), html_sha256=proof['html_sha256'])], companion_derivations=[dict(path=rel(p), sha256=sha(p)) for p in companions], scope=entry['scope'], fixture_only=[c['key']], photographic_masters=0, entries=[entry])
out = HERE / 'activation-set-shadow015-v1.json'
data = json.dumps(contract, indent=2) + '\n'
if out.exists():
    assert out.read_text() == data
else:
    out.write_text(data)
paths = companions + [out, png, HERE / 'preserved-shadow.txt', proof_path]
paths += [proof_path.parent / (name + '.png') for name in ['015-original', '015-hd', '015-mirror-original', '015-mirror-hd']]
(HERE / 'delivery-shadow015-files.txt').write_text('\n'.join(rel(p) for p in sorted(paths)) + '\n')
print(json.dumps(dict(status='frozen_not_activated', routes=1, png=1, photographic_masters=0, runtime_checks=len(proof['checks']), activation_sha256=sha(out))))
