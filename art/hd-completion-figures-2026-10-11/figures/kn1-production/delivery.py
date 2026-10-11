"""Frys KN1-kandidatene og lag en eksplisitt, uaktivert leveransekontrakt."""
import hashlib
import json
from pathlib import Path

ART = Path(__file__).resolve().parent
ROOT = ART.parents[3]
read = lambda p: json.loads(p.read_text())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
rel = lambda p: str(p.relative_to(ROOT))
contracts = read(ART / 'source-contracts.json')
queue = read(ART / 'queue-subset.json')
packing = read(ART / 'verification/packing-test.json')
records = {r['key']: r for r in read(ART / 'generation-records.json')['assets']}
production = {p: sha(ROOT / p) for p in ('web/src/core.js', 'web/src/render.js', 'web/src/scenes.js')}
host = ART / 'runtime-host'
baseline = ART / 'verification/runtime-baseline/moonstone.html'
assert sha(baseline) == sha(host / 'moonstone.html')
proofs = {n: read(ART / f'verification/{n}/test.json') for n in ('all-routes', 'composed-first-pair', 'composed-walk', 'standard-retired-poses')}
assert len(contracts['entries']) == len(records) == len(packing['assets']) == 60
assert len(queue['aliases']) == 45 and packing['status'] == 'passed'
assert packing['source_contracts_sha256'] == sha(ART / 'source-contracts.json')
for name, proof in proofs.items():
    assert proof['status'] == 'passed' and not proof['errors'], (name, proof.get('failure'))
    assert proof['source_contracts_sha256'] == sha(ART / 'source-contracts.json'), name
    assert proof['production_code_sha256'] == production, name
    assert proof['wasm_core_sha256'] == sha(host / 'moonstone-core-used.js'), name
    assert proof['html_sha256'] == sha(host / 'moonstone.html'), name
assert len(proofs['all-routes']['assets']) == 105
for key, digest in proofs['all-routes']['packed_png_sha256'].items():
    assert sha(ART / 'packed' / key) == digest, key

proof_path = rel(ART / 'verification/all-routes/test.json')
entries = []
for c in [*contracts['entries'], *queue['aliases']]:
    p = ART / 'packed' / c['key']
    e = dict(key=c['key'], bank=c['bank'], frame=c['frame'],
             source_bank_sha256=c['source_bank']['sha256'], indices_sha256=c['indices_sha256'],
             png=rel(p), png_sha256=sha(p), runtime_proof=proof_path, runtime_asset_sha256=sha(p))
    if c.get('role') == 'redraw':
        r = records[c['key']]
        raw = ART / 'raw' / c['key']
        prompt = ART / 'prompts' / ('KN1-' + str(c['frame']).zfill(3) + '.txt')
        assert sha(raw) == r['raw_sha256']
        e.update(raw=rel(raw), raw_sha256=sha(raw), prompt=rel(prompt), prompt_sha256=sha(prompt),
                 generation_tool=r['tool'])
    else:
        e['master_key'] = c['master_key']
        if c['bank'] == 'HE1.ob':
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
(ART / 'activation-set-kn1-001.json').write_text(json.dumps(generic, indent=2, ensure_ascii=False) + '\n')
by_key = {c['key']: c for c in contracts['entries']}
delivery = dict(schema=1, status='ready_for_sequential_integration',
    scope='59 separate KN1-mastere med nye synlige fotomaterialer og én bevart svart originalskygge, 45 originalbundne HE1-indeksaliaser. Ingen aktive metadata er endret.',
    visible_photo_material_masters=59, preserved_opaque_black_shadow_masters=1,
    preserved_shadow_keys=[c['key'] for c in contracts['entries'] if set(c['indices']) <= {0,5}],
    source_contracts_sha256=sha(ART / 'source-contracts.json'), queue_subset_sha256=sha(ART / 'queue-subset.json'),
    generation_records_sha256=sha(ART / 'generation-records.json'), packing_test_sha256=sha(ART / 'verification/packing-test.json'),
    activation_set_sha256=sha(ART / 'activation-set-kn1-001.json'),
    production_code_sha256=production, wasm_core_sha256=generic['wasm_core_sha256'], html_sha256=sha(host / 'moonstone.html'),
    runtime={n: dict(path=f'verification/{n}/test.json', sha256=sha(ART / f'verification/{n}/test.json'), checks=len(v['checks'])) for n,v in proofs.items()},
    entries=[dict(**e, source_size=[by_key[e['key']]['width'], by_key[e['key']]['height']],
                  target_size=[by_key[e['key']]['target_width'], by_key[e['key']]['target_height']],
                  original=by_key[e['key']]['original'],
                  quality_status='preserved_original_black_shadow_no_visible_photo_change' if set(by_key[e['key']]['indices']) <= {0,5} else 'source_silhouette_bound_new_photographic_material')
             for e in entries if e['key'] in by_key], aliases=[e for e in entries if e['key'] not in by_key],
    limitations=['Alle105 ruter er kontrollert normal/speilet i kildebaserte frontend-fixturer; dette paastaar ikke naturlig gameplay for hver rute.',
                 'Reell original CPU-kamp med tre dokumenterte scenetestskrivinger viser sammensetning av de fem KN1-kropp/fot-parene000/001,002/003,004/005,006/007,008/009 med KN4-sverd. Ingen palett skrives.',
                 'Originalens ditherhull, svarte skygger og adskilte blodfragmenter bevares; animasjonsnavn per rute er ikke utledet uten kildebevis.',
                 '038 er en ren0/5-skygge. Separate genereringer og originalbundne PNG-er finnes, men ruten telles som bevart skygge, ikke synlig nytegnet foto. Runtime krever ikke ulike piksler for denne ruten.',
                 'HE1 bruker samme RGB-master, men egen maske med originalens indeksflytting6..8 til9..11.',
                 'Standardpakkens eldre KN1-helposeprioritet er beholdt. Denne pakken endrer ingen renderer eller aktiv metadata.'])
(ART / 'delivery.json').write_text(json.dumps(delivery, indent=2, ensure_ascii=False) + '\n')
print(json.dumps(dict(status=delivery['status'], masters=60, aliases=45,
                      png_files=len(proofs['all-routes']['packed_png_sha256']),
                      runtime_checks=sum(len(v['checks']) for v in proofs.values()),
                      delivery_sha256=sha(ART / 'delivery.json'), activation_sha256=sha(ART / 'activation-set-kn1-001.json'))))
