"""Frys DRAGON5-kandidater uten aa aktivere dem."""
import hashlib
import json
from pathlib import Path

ART = Path(__file__).resolve().parent
ROOT = ART.parents[3]
read = lambda p: json.loads(p.read_text())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
rel = lambda p: str(p.relative_to(ROOT))
contracts = read(ART / 'source-contracts.json')
contracts['entries'] = [c for c in contracts['entries'] if c['bank'].lower() == 'dragon5.cel']
queue = read(ART / 'queue-subset.json')
queue['aliases'] = [c for c in queue['aliases'] if c['bank'].lower() == 'dragon5.cel']
packing = read(ART / 'verification/packing-test-dragon5.json')
records = {r['key']: r for r in read(ART / 'generation-records-dragon5.json')['assets'] if r['key'].startswith('DRAGON5.CEL/')}
record_snapshot = ART / 'generation-records-dragon5.json'
assert record_snapshot.exists() and len(records) == 43
production = {p: sha(ROOT / p) for p in ('web/src/core.js', 'web/src/render.js', 'web/src/scenes.js', 'web/src/hd.js')}
host = ART / 'runtime-host-retention-v3'
baseline = ART / 'verification/runtime-baseline-dragon5/moonstone.html'
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
proofs = {n: read(ART / f'verification/{n}/test.json') for n in ('dragon5-all-routes-final-v3', 'dragon5-actual-retention-v2', 'retention-fixtures-final-v3', 'balok-actual-retention-v2')}
assert len(contracts['entries']) == len(records) == len(packing['assets']) == 43
assert len(queue['aliases']) == 1 and packing['status'] == 'passed'
assert packing['source_contracts_sha256'] == sha(ART / 'source-contracts.json')
for name, proof in proofs.items():
    assert proof['status'] == 'passed' and not proof['errors'], (name, proof.get('failure'))
    if 'source_contracts_sha256' in proof: assert proof['source_contracts_sha256'] == sha(ART / 'source-contracts.json'), name
    assert proof['production_code_sha256'] == production, name
    assert proof['wasm_core_sha256'] == sha(host / 'moonstone-core-used.js'), name
    assert proof['html_sha256'] == sha(host / 'moonstone.html'), name
    assert proof['package_ledger_sha256'] == sha(ledger), name
    script = ART / {'dragon5-all-routes-final-v3': 'runtime-dragon5-fixtures.cjs', 'dragon5-actual-retention-v2': 'runtime-dragon5.cjs', 'retention-fixtures-final-v3': 'runtime-retention-fixtures.cjs', 'balok-actual-retention-v2': 'runtime-balok-retention.cjs'}[name]
    assert proof['runtime_script_sha256'] == sha(script), name
assert len(proofs['dragon5-all-routes-final-v3']['assets']) == 44
assert len(proofs['dragon5-all-routes-final-v3']['packed_png_sha256']) == 46
for proof in proofs.values():
    for key, digest in proof.get('packed_png_sha256', {}).items():
        assert sha(ART / 'packed' / key) == digest, key

proof_path = rel(ART / 'verification/dragon5-all-routes-final-v3/test.json')
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
        if c.get('index_remap') and any(int(k) != v for k, v in c['index_remap'].items()):
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
(ART / 'activation-set-dragon5-001.json').write_text(json.dumps(generic, indent=2, ensure_ascii=False) + '\n')
by_key = {c['key']: c for c in contracts['entries']}
delivery = dict(schema=1, status='ready_for_sequential_integration',
    scope='DRAGON5:43 separate builtinmaterialmastere, hvorav35 figur-/ildfragmenter og8 flate bokstavelige kildeeffekter. Ett eksakt alias,2 levende riddermasker,46PNG. Ingen aktive metadata endret.',
    visible_photo_material_masters=35, literal_flat_effect_material_masters=8, separate_generated_masters=43, preserved_opaque_black_shadow_masters=0,
    preserved_shadow_keys=[],
    source_contracts_sha256=sha(ART / 'source-contracts.json'), queue_subset_sha256=sha(ART / 'queue-subset.json'),
    source_color_contract=dict(path='identity/source-color-contract.json', sha256=sha(ART / 'identity/source-color-contract.json')),
    package_ledger=dict(path=rel(ledger), sha256=sha(ledger)),
    generation_records_sha256=sha(record_snapshot), packing_test_sha256=sha(ART / 'verification/packing-test-dragon5.json'),
    activation_set_sha256=sha(ART / 'activation-set-dragon5-001.json'),
    visual_review_sha256=sha(ART / 'verification/visual-review-dragon5.json'),
    production_code_sha256=production, wasm_core_sha256=generic['wasm_core_sha256'], html_sha256=sha(host / 'moonstone.html'),
    runtime={n: dict(path=f'verification/{n}/test.json', sha256=sha(ART / f'verification/{n}/test.json'), checks=len(v['checks'])) for n,v in proofs.items()},
    entries=[dict(**e, source_size=[by_key[e['key']]['width'], by_key[e['key']]['height']],
                  target_size=[by_key[e['key']]['target_width'], by_key[e['key']]['target_height']],
                  original=by_key[e['key']]['original'],
                  quality_status='literal_flat_source_effect_with_subtle_material_no_object_identity_claim' if 23 <= by_key[e['key']]['frame'] <= 30 else 'source_silhouette_bound_new_photographic_material')
             for e in entries if e['key'] in by_key], aliases=[e for e in entries if e['key'] not in by_key],
    limitations=['Alle44ruter normal/speilet i kildebaserte frontend-fixturer. To levende masker032/035 proeves i fem originale ridderpaletter; andre materialpiksler forblir identiske.',
                 'Original CPU-kamp med tre init-skrivinger viser30 av44ruter, inklusive hele komponerte flammen004/005. Ingen palett- eller tegnelisteskriving og ingen naturlig kartreise.',
                 '007 og023..035 er ikke observert naturlig i denne sekvensen. Deres kildebaserte fixturekontroll er ikke gameplaybevis.',
                 '023..030 er flate rustoransje kildeeffekter. Originalsekvens og gore-flagg er kildebevist; konkret gjenstandsidentitet er uavklart. Ingen nye objekter er funnet paa.',
                 'Noen tidligere leverte D1/D2-fragmenter kan fortsatt falle tilbake til originalen under tidlig ild; sen014 viser hele fotohodet. Streng kildevalidering er beholdt.',
                 'Frontendrettingen har170 egne negative/positive kontroller,322 faktiske Dragon5- og22 faktiske Balok-kontroller. Balok041s22 ukjente15-kildeceller beholder samtlige9 originale skjermpiksler foran HD.'])

(ART / 'delivery-dragon5.json').write_text(json.dumps(delivery, indent=2, ensure_ascii=False) + '\n')
print(json.dumps(dict(status=delivery['status'], masters=43, aliases=1, png_files=46,
                      runtime_checks=sum(len(v['checks']) for v in proofs.values()),
                      delivery_sha256=sha(ART / 'delivery-dragon5.json'), activation_sha256=sha(ART / 'activation-set-dragon5-001.json'))))
