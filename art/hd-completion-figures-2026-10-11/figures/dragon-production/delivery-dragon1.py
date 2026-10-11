"""Frys DRAGON1-kandidater uten aa aktivere dem."""
import hashlib
import json
from pathlib import Path

ART = Path(__file__).resolve().parent
ROOT = ART.parents[3]
read = lambda p: json.loads(p.read_text())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
rel = lambda p: str(p.relative_to(ROOT))
contracts = read(ART / 'source-contracts.json')
contracts['entries'] = [c for c in contracts['entries'] if c['bank'].lower() == 'dragon1.cel']
queue = read(ART / 'queue-subset.json')
queue['aliases'] = []
packing = read(ART / 'verification/packing-test-dragon1.json')
records = {r['key']: r for r in read(ART / 'generation-records-dragon1.json')['assets'] if r['key'].startswith('DRAGON1.CEL/')}
record_snapshot = ART / 'generation-records-dragon1.json'
record_bytes = json.dumps(dict(schema=1, assets=list(records.values())), indent=2) + '\n'
if record_snapshot.exists(): assert record_snapshot.read_text() == record_bytes
else: record_snapshot.write_text(record_bytes)
production = {p: sha(ROOT / p) for p in ('web/src/core.js', 'web/src/render.js', 'web/src/scenes.js', 'web/src/hd.js')}
host = ART / 'runtime-host-dragon1-final-v2'
baseline = ART / 'verification/runtime-baseline-dragon1/moonstone.html'
baseline.parent.mkdir(exist_ok=True)
if baseline.exists():
    assert sha(baseline) == sha(host / 'moonstone.html')
else:
    baseline.write_bytes((host / 'moonstone.html').read_bytes())
ledger = baseline.with_name('package-ledger.json')
if ledger.exists():
    assert sha(ledger) == sha(host / 'package-ledger.json')
else:
    ledger.write_bytes((host / 'package-ledger.json').read_bytes())
proofs = {n: read(ART / f'verification/{n}/test.json') for n in ('dragon1-all-routes-final', 'dragon1-actual-final')}
assert len(contracts['entries']) == len(records) == len(packing['assets']) == 16
assert len(queue['aliases']) == 0 and packing['status'] == 'passed'
assert packing['source_contracts_sha256'] == sha(ART / 'source-contracts.json')
for name, proof in proofs.items():
    assert proof['status'] == 'passed' and not proof['errors'], (name, proof.get('failure'))
    assert proof['source_contracts_sha256'] == sha(ART / 'source-contracts.json'), name
    assert proof['production_code_sha256'] == production, name
    assert proof['wasm_core_sha256'] == sha(host / 'moonstone-core-used.js'), name
    assert proof['html_sha256'] == sha(host / 'moonstone.html'), name
    assert proof['package_ledger_sha256'] == sha(ledger), name
    script = ART / ('runtime-dragon1-fixtures.cjs' if name == 'dragon1-all-routes-final' else 'runtime-dragon1.cjs')
    assert proof['runtime_script_sha256'] == sha(script), name
assert len(proofs['dragon1-all-routes-final']['assets']) == 16
assert len(proofs['dragon1-all-routes-final']['packed_png_sha256']) == 16
for proof in proofs.values():
    for key, digest in proof['packed_png_sha256'].items():
        assert sha(ART / 'packed' / key) == digest, key

proof_path = rel(ART / 'verification/dragon1-all-routes-final/test.json')
entries = []
for c in [*contracts['entries'], *queue['aliases']]:
    p = ART / 'packed' / c['key']
    e = dict(key=c['key'], bank=c['bank'], frame=c['frame'],
             source_bank_sha256=c['source_bank']['sha256'], indices_sha256=c['indices_sha256'],
             png=rel(p), png_sha256=sha(p), runtime_proof=proof_path, runtime_asset_sha256=sha(p))
    if c.get('role') == 'redraw':
        r = records[c['key']]
        raw = ART / 'raw' / c['key']
        prompt = ART / 'prompts' / (c['bank'] + '-' + str(c['frame']).zfill(3) + '.txt')
        assert sha(raw) == r['raw_sha256']
        e.update(raw=rel(raw), raw_sha256=sha(raw), prompt=rel(prompt), prompt_sha256=sha(prompt),
                 generation_tool=r['tool'])
    else:
        e['master_key'] = c['master_key']
        if c['bank'] == 'HE2.ob':
            e['index_remap'] = c['index_remap']
    if c['needs_mask']:
        m = p.with_name(p.stem + '.mask.png')
        e.update(mask=rel(m), mask_sha256=sha(m))
    entries.append(e)

generic = dict(schema=1, visual_status='reviewed_original_and_runtime',
               source_zip_sha256=sha(ROOT / 'Moonstonecd32-AMIGA.zip'), production_code_sha256=production,
               wasm_core_sha256=sha(host / 'moonstone-core-used.js'),
               proofs=[dict(path=rel(ART / f'verification/{n}/test.json'),
                            sha256=sha(ART / f'verification/{n}/test.json'),
                            html_path=rel(baseline), html_sha256=v['html_sha256'])
                       for n, v in proofs.items()], entries=entries)
(ART / 'activation-set-dragon1-001.json').write_text(json.dumps(generic, indent=2, ensure_ascii=False) + '\n')
by_key = {c['key']: c for c in contracts['entries']}
delivery = dict(schema=1, status='ready_for_sequential_integration',
    scope='16 separate fotografiske DRAGON1-mastere006..021: hode, horn, kjever og membraner.16PNG, ingen levende riddermasker eller aliaser. Ingen aktive metadata endret.',
    visible_photo_material_masters=16, preserved_opaque_black_shadow_masters=0,
    preserved_shadow_keys=[c['key'] for c in contracts['entries'] if set(c['indices']) <= {0,5}],
    source_contracts_sha256=sha(ART / 'source-contracts.json'), queue_subset_sha256=sha(ART / 'queue-subset.json'),
    source_color_contract=dict(path='identity/source-color-contract.json', sha256=sha(ART / 'identity/source-color-contract.json')),
    package_ledger=dict(path=rel(ledger), sha256=sha(ledger)),
    generation_records_sha256=sha(record_snapshot), packing_test_sha256=sha(ART / 'verification/packing-test-dragon1.json'),
    activation_set_sha256=sha(ART / 'activation-set-dragon1-001.json'),
    visual_review_sha256=sha(ART / 'verification/visual-review-dragon1.json'),
    production_code_sha256=production, wasm_core_sha256=generic['wasm_core_sha256'], html_sha256=sha(host / 'moonstone.html'),
    runtime={n: dict(path=f'verification/{n}/test.json', sha256=sha(ART / f'verification/{n}/test.json'), checks=len(v['checks'])) for n,v in proofs.items()},
    entries=[dict(**e, source_size=[by_key[e['key']]['width'], by_key[e['key']]['height']],
                  target_size=[by_key[e['key']]['target_width'], by_key[e['key']]['target_height']],
                  original=by_key[e['key']]['original'],
                  quality_status='preserved_original_black_shadow_no_generation_or_photo_change' if set(by_key[e['key']]['indices']) <= {0,5} else 'source_silhouette_bound_new_photographic_material')
             for e in entries if e['key'] in by_key], aliases=[e for e in entries if e['key'] not in by_key],
    limitations=['Alle16ruter normal/speilet i kildebaserte WASM-frontend-fixturer; dette er ikke naturlig gameplay for hver rute.',
                 'Original CPU-dragekamp med tre scenestartskrivinger viser007+008 sammen med uendrede originaldeler ved1252. Ingen palett- eller tegnelisteskriving.',
                 'Original bakgrunn beholdes for figurkontroll. Andre standardfigurer beholdes og posekontrakter er0.',
                 'Alle16mastere har separat builtin-bildegenkall.009v1 er avvist;009v2 bevarer det skyggefulle midthornet som bein.',
                 'Dragon2/5 produseres videre separat og er ikke del av denne frosne banken.'])

(ART / 'delivery-dragon1.json').write_text(json.dumps(delivery, indent=2, ensure_ascii=False) + '\n')
print(json.dumps(dict(status=delivery['status'], masters=16, aliases=0, png_files=16,
                      runtime_checks=sum(len(v['checks']) for v in proofs.values()),
                      delivery_sha256=sha(ART / 'delivery-dragon1.json'), activation_sha256=sha(ART / 'activation-set-dragon1-001.json'))))
