#!/usr/bin/env python3
"""Frys tre kildeeksakte svarte Balok-skygger etter visuell og frontendkontroll."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ART = Path(__file__).resolve().parent
ROOT = ART.parents[2]
OUT = ART / 'balok/retained-black-shadows-v1'
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
load = lambda path: json.loads(path.read_text())
rel = lambda path: str(path.resolve().relative_to(ROOT))


def freeze(path, value):
    data = (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()
    if path.exists():
        assert path.read_bytes() == data, 'Frosne bevis overskrives ikke: ' + str(path)
    else:
        path.write_bytes(data)


def main():
    index_path = OUT / 'candidates.json'
    index = load(index_path)
    proof = ART / 'verification/balok-black-fixtures-008274d71a524674-04ad1af2/test.json'
    report = load(proof)
    assert report['status'] == 'passed' and not report['errors']
    assert report['index_sha256'] == sha(index_path)
    assert len(report['checks']) == 51 and len(report['routes']) == 3
    assert not report['actual_runtime_observed']
    html = proof.parent / 'loaded.html'
    assert sha(html) == report['html_sha256']
    codes = {p: sha(ROOT / p) for p in ['web/src/core.js', 'web/src/render.js', 'web/src/scenes.js']}
    assert all(report['production_code_sha256'][p] == digest for p, digest in codes.items())
    review = OUT / 'root-visual-review-v8.json'
    contact = OUT / 'three-original-retained-comparison.png'
    freeze(review, dict(schema=1, reviewer='root', status='approved', review_basis='Direkte godkjenning fra rotagenten etter visning av alle tre originale/bevarte svarte felt.', comparison=rel(contact), comparison_sha256=sha(contact), note='Eksakt bevarte originalfelt, ingen fotografisk nytegning eller naturlig runtime-observasjon paastatt.'))
    entries = []
    queue = load(ART.parent / 'queue.json')['entries']
    for item in index['entries']:
        row = next(r for r in queue if r['key'] == item['key'])
        route = next(r for r in report['routes'] if r['key'] == item['key'])
        assert len(route['samples']) == 2 and {s['mirror'] for s in route['samples']} == {False, True}
        assert all(s['hit']['hd'] and not s['hit']['maske'] and s['original_sha256'] == s['hd_sha256'] for s in route['samples'])
        assert not route['negative'].get('hit', {}).get('hd')
        for field in ['candidate', 'raw', 'prompt']:
            assert sha(ROOT / item[field]) == item[field + '_sha256']
        entries.append(dict(key=item['key'], bank=row['bank'], frame=row['frame'], source_bank_sha256=item['source_bank_sha256'], indices_sha256=item['indices_sha256'], png=item['candidate'], png_sha256=item['candidate_sha256'], raw=item['raw'], raw_sha256=item['raw_sha256'], prompt=item['prompt'], prompt_sha256=item['prompt_sha256'], generation_tool='preserved_original_black_shadow', runtime_proof=rel(proof), runtime_asset_sha256=item['candidate_sha256'], qa=dict(method='preserved_original_black_shadow', counts_as_individual_redraw=False, actual_runtime_observed=False, runtime_scope='source_exact_frontend_fixture_only', directions='normal_and_mirrored', original_hd_rgba='byteidentical', emulated_state='unchanged', visual='root_reviewed_exact_original_retention', source_midpoints_missing=0, source_transparent_midpoints_filled=0)))
    target = ART / 'activation-set-balok-026-three-original-shadows-v8.json'
    freeze(target, dict(schema=1, visual_status='reviewed_original_and_runtime', source_zip_sha256=index['source_zip_sha256'], production_code_sha256=codes, wasm_core_sha256=sha(ROOT / 'web/build/moonstone-core.js'), proofs=[dict(path=rel(proof), sha256=sha(proof), html_path=rel(html), html_sha256=sha(html))], companion_derivations=[dict(path=rel(review),sha256=sha(review)),dict(path=rel(contact),sha256=sha(contact)),dict(path=rel(index_path),sha256=sha(index_path))], scope='Tre originale svarte skygger bevart eksakt4x, ikke fotografiske nytegninger. Kilde- og normal/speilet frontend-fixture bevist med streng ukjent-opak negativ. Ingen faktisk eller naturlig kampobservasjon av disse HD-rutene paastatt.', entries=entries))
    subprocess.run([sys.executable, str(ROOT / 'tools/hd_figurer_aktiver.py'), str(target)], check=True)
    files = {target, review, contact, index_path, proof, proof.parent / 'input-index.json', Path(__file__).resolve(), ART / 'runtime-balok-retained-black-fixtures-v8.cjs', ART / 'runtime-local.cjs', ROOT / 'tools/hd_resterende_ikoner_fixture.cjs', ART.parent / 'palettes/cases/balok.json'}
    files.update(proof.parent.glob('*.png'))
    for item in index['entries']:
        files.update(ROOT / item[field] for field in ['candidate', 'raw', 'prompt'])
        row = next(r for r in queue if r['key'] == item['key'])
        files.add(ART.parent / row['packed_original']['path'])
    listing = ART / 'delivery-balok-three-original-shadows-v8-files.txt'
    data = ('\n'.join(sorted(rel(p) for p in files)) + '\n').encode()
    if listing.exists():
        assert listing.read_bytes() == data
    else:
        listing.write_bytes(data)
    freeze(OUT / 'delivery-provenance-v8.json', dict(schema=1, activation_set=rel(target), activation_set_sha256=sha(target), file_list=rel(listing), file_list_sha256=sha(listing), files=[dict(path=rel(p), sha256=sha(p), bytes=p.stat().st_size) for p in sorted(files)], excluded='Historiske HTML-filer bevares lokalt; ingen aktivering, metadataendring eller bildegenenerering.'))
    print(json.dumps(dict(contract=rel(target),sha256=sha(target),routes=len(entries),files=len(files),file_list=rel(listing))))


if __name__ == '__main__':
    main()
