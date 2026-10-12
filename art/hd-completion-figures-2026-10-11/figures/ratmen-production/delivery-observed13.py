"""Frys13 faktisk viste Ratmenruter uten aktiv metadataendring."""
import hashlib
import json
from pathlib import Path

ART = Path(__file__).resolve().parent
ROOT = ART.parents[3]
read = lambda p: json.loads(p.read_text())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
rel = lambda p: str(p.relative_to(ROOT))
write = lambda p, v: p.write_text(json.dumps(v, indent=2, ensure_ascii=False) + '\n')
selected_frames = {38,39,40,41,42,43,45,46,47,48,49,50,52}
selected = [c for c in read(ART/'source-contracts.json')['entries'] if c['bank'] == 'RATMEN1.CEL' and c['frame'] in selected_frames]
assert len(selected) == 13
keys = {c['key'] for c in selected}
record_path = ART/'generation-records-observed13.json'
records = [r for r in read(ART/'generation-records.json')['assets'] if r['key'] in keys]
assert len(records) == 13
snapshot = dict(schema=1, assets=records)
if record_path.exists(): assert read(record_path) == snapshot
else: write(record_path, snapshot)
records = {r['key']: r for r in records}
production = {p: sha(ROOT/p) for p in ('web/src/core.js','web/src/render.js','web/src/scenes.js','web/src/hd.js')}
host = ART.parent/'dragon-production/runtime-host-retention-v7'
baseline = ART/'verification/runtime-baseline-observed13/moonstone.html'
baseline.parent.mkdir(exist_ok=True)
for name in ('moonstone.html', 'package-ledger.json'):
    p = baseline.parent/name
    if p.exists(): assert sha(p) == sha(host/name)
    else: p.write_bytes((host/name).read_bytes())
proof_file = lambda n: ART/f'verification/{n}'/('proof-summary.json' if n == 'observed14-actual-v1' else 'test.json')
proofs = {n: read(proof_file(n)) for n in ('observed14-fixtures-v1','observed14-actual-v1')}
for n,v in proofs.items():
    assert v['status'] == 'passed' and not v['errors']
    assert v['production_code_sha256'] == production
    assert v['wasm_core_sha256'] == sha(host/'moonstone-core-used.js')
    assert v['html_sha256'] == sha(baseline)
    assert v['package_ledger_sha256'] == sha(baseline.with_name('package-ledger.json'))
    script = ART/('runtime-ratmen-observed14-fixtures-v1.cjs' if 'fixtures' in n else 'runtime-ratmen-observed14-v1.cjs')
    assert v['runtime_script_sha256'] == sha(script)
    for key,digest in v['packed_png_sha256'].items(): assert sha(ART/'packed'/key) == digest
packing = read(ART/'verification/packing-observed14.json')
assert packing['status'] == 'passed'
entries = []
proof_path = rel(ART/'verification/observed14-fixtures-v1/test.json')
for c in selected:
    r = records[c['key']]
    p = ART/'packed'/c['key']; raw = ART/'raw'/c['key']
    prompt = ART/'prompts'/f"{c['bank']}-{c['frame']:03}.txt"
    assert sha(raw) == r['raw_sha256'] and not c['needs_mask']
    entries.append(dict(key=c['key'],bank=c['bank'],frame=c['frame'],source_bank_sha256=c['source_bank']['sha256'],indices_sha256=c['indices_sha256'],png=rel(p),png_sha256=sha(p),raw=rel(raw),raw_sha256=sha(raw),prompt=rel(prompt),prompt_sha256=sha(prompt),generation_tool=r['tool'],runtime_proof=proof_path,runtime_asset_sha256=sha(p)))
generic = dict(schema=1,visual_status='reviewed_original_and_runtime',source_zip_sha256=sha(ROOT/'Moonstonecd32-AMIGA.zip'),production_code_sha256=production,wasm_core_sha256=sha(host/'moonstone-core-used.js'),proofs=[dict(path=rel(proof_file(n)),sha256=sha(proof_file(n)),html_path=rel(baseline),html_sha256=v['html_sha256']) for n,v in proofs.items()],entries=entries)
activation = ART/'activation-set-ratmen-observed13-001.json'
write(activation,generic)
delivery = dict(schema=1,status='ready_for_sequential_integration',scope='RATMEN1/038..043,045..050,052:13 separate fotomaterialmastere. Alle13 har faktisk HD-fangst fra original CPU-kamp med tre init-skrivinger og ekte inndata. Ingen naturlig kartreise.',visible_photo_material_masters=13,preserved_opaque_black_shadow_masters=0,source_contracts_sha256=sha(ART/'source-contracts.json'),source_color_contract_sha256=sha(ART/'identity/source-color-contract.json'),generation_records_sha256=sha(record_path),activation_set_sha256=sha(activation),packing_test_sha256=sha(ART/'verification/packing-observed14.json'),production_code_sha256=production,html_sha256=sha(baseline),runtime={n:dict(path=rel(proof_file(n)),sha256=sha(proof_file(n)),checks=len(v['checks'])) for n,v in proofs.items()},entries=[dict(**e,source_size=[c['width'],c['height']],target_size=[c['target_width'],c['target_height']],original=c['original']) for e,c in zip(entries,selected)],actual_source_center_proof=dict(path=rel(ART/'verification/observed13-actual-source-centers.json'),sha256=sha(ART/'verification/observed13-actual-source-centers.json')),native_observed_without_HD_capture=['RATMEN1.CEL/051.png'],not_observed_011_054=[f'RATMEN1.CEL/{i:03}.png' for i in range(11,55) if i not in selected_frames and i!=51],limitations=['051 inngaar bare i den private14ruters testpakken, aldri i denne13ruters aktiveringen. Nativekall er observert, men ingen HD-fangst i aktuell kampsekvens.','Begge speilretninger er kildebaserte frontend-fixturer. Faktisk kamp viser alle13 aktiveringsruter med eksakt Original/HD-retur og uendret emulert tilstand.','Noen originale effektceller og svartskygger beholdes foran HD-materialet. Ingen udokumentert forgrunn godtas.','Bakgrunn er originalisolert i figurporten; standardbakgrunner kontrolleres separat.','055..061 nylig genererte raafiler er utenfor denne leveransen. Resten av Ratmen er uferdig.'])
write(ART/'delivery-observed13.json',delivery)
files = {activation, ART/'delivery-observed13.json', Path(__file__), record_path, ART/'source-contracts.json',ART/'queue-subset.json',ART/'identity/source-color-contract.json',ART/'comparison-observed14.png',ART/'comparison-observed13-actual-v2.png',ART/'verify-observed13-actual.py',ART/'selection-observed14.json',ART/'identity/observed-rest-v1.json',ART/'verification/observed13-actual-source-centers.json',ART/'verification/packing-observed14.json',baseline.with_name('package-ledger.json')}
files.update(ART/n for n in ('prepare.py','pack-v2.cjs','record.py','masks.py','verify.py','build-runtime.py','runtime-proof.cjs','runtime-host.cjs','runtime-ratmen-observed14-v1.cjs','runtime-ratmen-observed14-fixtures-v1.cjs'))
files.update(ART/'identity/original-ratmen-first-v1'/n for n in ('source-observation.json','trace.txt','chip1400.bin'))
for e in entries:
    files.update(ROOT/e[k] for k in ('raw','prompt','png'))
    files.update((ART/'references'/e['key'],ART/'references'/e['key'].replace('.png','-native.png')))
for n in proofs: files.add(proof_file(n))
#051 er bare en foerhaandskandidat i runtimeporten, aldri aktivert her.
files.add(ART/'packed/RATMEN1.CEL/051.png')
for frame in ('039','043','045','049','052'):
    files.update(ART/f'verification/observed14-actual-v1/{frame}-{kind}.png' for kind in ('original','hd'))
listing = ART/'delivery-observed13-files.txt'; files.add(listing)
assert all(p.exists() or p == listing for p in files), [str(p) for p in files if not p.exists() and p != listing]
listing.write_text('\n'.join(sorted(rel(p) for p in files))+'\n')
print(json.dumps(dict(status=delivery['status'],routes=len(entries),checks=sum(len(v['checks']) for v in proofs.values()),activation=rel(activation),activation_sha256=sha(activation),files=len(files))))
