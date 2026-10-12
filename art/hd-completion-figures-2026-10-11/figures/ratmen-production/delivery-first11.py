"""Frys foerste11 Ratmenruter uten aktiv metadataendring."""
import hashlib
import json
from pathlib import Path

ART = Path(__file__).resolve().parent
ROOT = ART.parents[3]
read = lambda p: json.loads(p.read_text())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
rel = lambda p: str(p.relative_to(ROOT))
write = lambda p, v: p.write_text(json.dumps(v, indent=2, ensure_ascii=False) + '\n')
selected = [c for c in read(ART/'source-contracts.json')['entries'] if c['bank'] == 'RATMEN1.CEL' and c['frame'] <= 10]
assert len(selected) == 11
keys = {c['key'] for c in selected}
record_path = ART/'generation-records-first11.json'
records = [r for r in read(ART/'generation-records.json')['assets'] if r['key'] in keys]
assert len(records) == 11
snapshot = dict(schema=1, assets=records)
if record_path.exists(): assert read(record_path) == snapshot
else: write(record_path, snapshot)
records = {r['key']: r for r in records}
production = {p: sha(ROOT/p) for p in ('web/src/core.js','web/src/render.js','web/src/scenes.js','web/src/hd.js')}
host = ART/'runtime-host-first-v1'
baseline = ART/'verification/runtime-baseline-first11/moonstone.html'
baseline.parent.mkdir(exist_ok=True)
for name in ('moonstone.html', 'package-ledger.json'):
    p = baseline.parent/name
    if p.exists(): assert sha(p) == sha(host/name)
    else: p.write_bytes((host/name).read_bytes())
proofs = {n: read(ART/f'verification/{n}/test.json') for n in ('first13-fixtures-v1','first11-actual-v2')}
for n,v in proofs.items():
    assert v['status'] == 'passed' and not v['errors']
    assert v['production_code_sha256'] == production
    assert v['wasm_core_sha256'] == sha(host/'moonstone-core-used.js')
    assert v['html_sha256'] == sha(baseline)
    assert v['package_ledger_sha256'] == sha(baseline.with_name('package-ledger.json'))
    script = ART/('runtime-ratmen1-fixtures.cjs' if n.startswith('first13') else 'runtime-ratmen-first.cjs')
    assert v['runtime_script_sha256'] == sha(script)
    for key,digest in v['packed_png_sha256'].items(): assert sha(ART/'packed'/key) == digest
packing = read(ART/'verification/packing-first13.json')
assert packing['status'] == 'passed'
entries = []
proof_path = rel(ART/'verification/first13-fixtures-v1/test.json')
for c in selected:
    r = records[c['key']]
    p = ART/'packed'/c['key']; raw = ART/'raw'/c['key']
    prompt = ART/'prompts'/f"{c['bank']}-{c['frame']:03}.txt"
    assert sha(raw) == r['raw_sha256'] and not c['needs_mask']
    entries.append(dict(key=c['key'],bank=c['bank'],frame=c['frame'],source_bank_sha256=c['source_bank']['sha256'],indices_sha256=c['indices_sha256'],png=rel(p),png_sha256=sha(p),raw=rel(raw),raw_sha256=sha(raw),prompt=rel(prompt),prompt_sha256=sha(prompt),generation_tool=r['tool'],runtime_proof=proof_path,runtime_asset_sha256=sha(p)))
generic = dict(schema=1,visual_status='reviewed_original_and_runtime',source_zip_sha256=sha(ROOT/'Moonstonecd32-AMIGA.zip'),production_code_sha256=production,wasm_core_sha256=sha(host/'moonstone-core-used.js'),proofs=[dict(path=rel(ART/f'verification/{n}/test.json'),sha256=sha(ART/f'verification/{n}/test.json'),html_path=rel(baseline),html_sha256=v['html_sha256']) for n,v in proofs.items()],entries=entries)
activation = ART/'activation-set-ratmen-first11-001.json'
write(activation,generic)
delivery = dict(schema=1,status='ready_for_sequential_integration',scope='RATMEN1/000..010: ti separate fotomaterialmastere og en uendret svart originalskygge008. Original CPU-kamp med tre init-skrivinger og ekte inndata, ingen naturlig kartreise.',visible_photo_material_masters=10,preserved_opaque_black_shadow_masters=1,preserved_shadow_keys=['RATMEN1.CEL/008.png'],source_contracts_sha256=sha(ART/'source-contracts.json'),source_color_contract_sha256=sha(ART/'identity/source-color-contract.json'),generation_records_sha256=sha(record_path),activation_set_sha256=sha(activation),packing_test_sha256=sha(ART/'verification/packing-first13.json'),production_code_sha256=production,html_sha256=sha(baseline),runtime={n:dict(path=rel(ART/f'verification/{n}/test.json'),sha256=sha(ART/f'verification/{n}/test.json'),checks=len(v['checks'])) for n,v in proofs.items()},entries=[dict(**e,source_size=[c['width'],c['height']],target_size=[c['target_width'],c['target_height']],original=c['original']) for e,c in zip(entries,selected)],limitations=['011/012 finnes i den private fixturepakken, men inngaar ikke i denne leveransen. Resten av Ratmen er under arbeid.','Begge speilretninger er kildebaserte frontend-fixturer. Faktisk kamp observerer og viser alle11 leverte ruter, med byteeksakt Original/HD-retur og uendret emulert tilstand.','Svarte008 er haandtert og originalbevart, ikke synlig fotografisk nytegning.','Bakgrunn var originalisolert i faktisk figurport; standardbakgrunner kontrolleres i samlet standardpakke.'])
write(ART/'delivery-first11.json',delivery)
files = {activation, ART/'delivery-first11.json', Path(__file__), record_path, ART/'source-contracts.json',ART/'queue-subset.json',ART/'identity/source-color-contract.json',ART/'verification/comparison-first13.png',ART/'verification/packing-first13.json',baseline.with_name('package-ledger.json')}
files.update(ART/n for n in ('prepare.py','pack.cjs','record.py','masks.py','verify.py','build-runtime.py','runtime-proof.cjs','runtime-host.cjs','runtime-ratmen-first.cjs','runtime-ratmen1-fixtures.cjs'))
files.update(ART/'identity/original-ratmen-first-v1'/n for n in ('source-observation.json','trace.txt','chip1400.bin'))
for e in entries:
    files.update(ROOT/e[k] for k in ('raw','prompt','png'))
    files.update((ART/'references'/e['key'],ART/'references'/e['key'].replace('.png','-native.png')))
for n in proofs: files.add(ART/f'verification/{n}/test.json')
for frame in ('000','004','007','008','010'):
    files.update(ART/f'verification/first11-actual-v2/{frame}-{kind}.png' for kind in ('original','hd'))
listing = ART/'delivery-first11-files.txt'; files.add(listing)
assert all(p.exists() or p == listing for p in files), [str(p) for p in files if not p.exists() and p != listing]
listing.write_text('\n'.join(sorted(rel(p) for p in files))+'\n')
print(json.dumps(dict(status=delivery['status'],routes=len(entries),checks=sum(len(v['checks']) for v in proofs.values()),activation=rel(activation),activation_sha256=sha(activation),files=len(files))))
