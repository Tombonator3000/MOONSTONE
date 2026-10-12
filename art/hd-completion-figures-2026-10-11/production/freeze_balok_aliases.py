#!/usr/bin/env python3
"""Frys fem eksakte kildealiaser av allerede aktiverte Balok2-mastere."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from PIL import Image

ART = Path(__file__).resolve().parent
ROOT = ART.parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
import moonfiles as mf
import hd_bestilling as order
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
load = lambda p: json.loads(p.read_text())


def freeze(path, value):
    data = (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()
    if path.exists():
        assert path.read_bytes() == data, 'Bevar tidligere frys: ' + str(path)
    else:
        path.write_bytes(data)


def main():
    original = ART / 'activation-set-balok-022-b2-ten-v7.json'
    source = load(original)
    index_path = ART / 'balok/candidates-b2-five-aliases-v7.json'
    index = load(index_path)
    actual = ART / 'verification/runtime-a23c476d56192a8d-366c0f91/test.json'
    fixtures = ART / 'verification/balok-live-fixtures-e2674b1281bfa2c9-1ce920d2/test.json'
    fixture_report = load(fixtures)
    assert fixture_report['status'] == 'passed' and not fixture_report['errors']
    assert fixture_report['index_sha256'] == sha(index_path)
    assert len(fixture_report['routes']) == 5
    assert load(actual)['status'] == 'passed' and not load(actual)['errors']
    assert load(actual)['html_sha256'] == fixture_report['html_sha256']
    assert len(load(actual)['runtime']['samples']) == 4
    game = mf.Spill(str(ROOT / 'Moonstonecd32-AMIGA.zip'))
    balok = load(ART.parent / 'palettes/cases/balok.json')
    beast = load(ART.parent / 'palettes/cases/beast.json')
    queue = load(ART.parent / 'queue.json')['entries']
    delivery = {k: v for k, v in source.items() if k != 'entries'}
    delivery['entries'] = []
    proof_rows = []
    for path in (actual, fixtures):
        html = path.parent / 'loaded.html'
        assert sha(html) == load(path)['html_sha256']
        delivery['proofs'].append(dict(path=str(path.relative_to(ROOT)), sha256=sha(path), html_path=str(html.relative_to(ROOT)), html_sha256=sha(html)))
    for item in index['entries']:
        master = next(e.copy() for e in source['entries'] if e['key'] == item['master_key'])
        master['existing_master'] = True
        delivery['entries'].append(master)
        bank, filename = item['key'].split('/')
        frame = int(filename[:3])
        row = next(r for r in queue if r['key'] == item['key'])
        assert row['master_key'] == master['key']
        raw_bank = game.les('data/' + bank)
        src = mf.cel_les(raw_bank)[0][frame]
        packed = mf.plan_til_indeks(src['data'], src['plan'], src['bredde'], src['hoyde'])
        indices = order.utvid_indekser(packed, src['maske'])
        assert hashlib.sha256(raw_bank).hexdigest() == row['source_bank']['sha256']
        assert hashlib.sha256(indices).hexdigest() == master['indices_sha256'] == row['indices_sha256']
        photo = Image.open(ROOT / master['png']).convert('RGBA')
        assert photo.size == (src['bredde'] * 4, src['hoyde'] * 4)
        missing = filled = 0
        for y in range(src['hoyde']):
            for x in range(src['bredde']):
                opaque = photo.getpixel((x * 4 + 2, y * 4 + 2))[3] >= 128
                source_opaque = bool(indices[y * src['bredde'] + x])
                missing += source_opaque and not opaque
                filled += opaque and not source_opaque
        assert not missing and not filled
        active_case = beast if bank == 'be1.c' else balok
        assert all(active_case['colors'][i] == balok['colors'][i] for i in set(indices))
        proof = fixtures if bank == 'be1.c' else actual
        entry = dict(key=item['key'], bank=bank, frame=frame, source_bank_sha256=row['source_bank']['sha256'], indices_sha256=row['indices_sha256'], png=master['png'], png_sha256=master['png_sha256'], master_key=master['key'], runtime_proof=str(proof.relative_to(ROOT)), runtime_asset_sha256=master['png_sha256'], qa=dict(source_midpoints_missing=missing, source_transparent_midpoints_filled=filled, method='Eksakt originalindeksalias med byteidentisk masterfoto. Ingen egen nytegning paastaas.', actual_combat=bank != 'be1.c', limitation='be1/057 er ikke observert i aktuelle kampforloep; eksakt kilde og kildebasert frontendfixture er kontrollert.' if bank == 'be1.c' else None))
        live = order.maskefarger(bank, frame).intersection(indices)
        assert live.issubset({6, 7, 8})
        if live:
            entry['mask'], entry['mask_sha256'] = master['mask'], master['mask_sha256']
            assert entry['mask_sha256'] == item['mask_sha256']
        else:
            assert not item.get('mask')
        samples = next(r['samples'] for r in fixture_report['routes'] if r['key'] == item['key'])
        assert len(samples) == 10 and all(s['visible']['hd'] and s['visible']['maske'] == bool(live) for s in samples)
        for mirror in (False, True):
            subset = [s for s in samples if s['mirror'] == mirror]
            assert len(subset) == 5 and len({s['fixed_sha256'] for s in subset}) == 1
            assert (len({s['live_sha256'] for s in subset}) == 5) if live else all(not s['live_count'] for s in subset)
        delivery['entries'].append(entry)
        proof_rows.append(dict(key=item['key'], master_key=master['key'], source_bank_sha256=row['source_bank']['sha256'], source_indices_sha256=row['indices_sha256'], source_plane_mask=src['maske'], source_size=[src['bredde'], src['hoyde']], used_indices=sorted(set(indices)), live_indices=sorted(live), identical_used_source_palette=True, candidate_sha256=master['png_sha256'], mask_sha256=entry.get('mask_sha256'), source_opaque_midpoints_missing=missing, source_transparent_midpoints_filled=filled, actual_combat=bank != 'be1.c'))
    derivation = ART / 'balok/five-aliases-source-proof-v7.json'
    freeze(derivation, dict(schema=1, status='passed', errors=[], source_zip_sha256=source['source_zip_sha256'], original_context_contract=str(original.relative_to(ROOT)), original_context_contract_sha256=sha(original), records=proof_rows, html_sha256=fixture_report['html_sha256'], scope='Fem eksakte originalindeksaliaser, to byteidentiske levende masker. FireB3 faktisk i originalCPU; be1/057 bare kilde-/farge-/speilfixture, ikke faktisk observert. Ingen nye fotomastere eller aktivering.'))
    delivery['companion_derivations'] = [dict(path=str(derivation.relative_to(ROOT)), sha256=sha(derivation))]
    delivery['scope'] = 'Fem eksakte aliaser av fem uendrede aktive Balok2-mastere. FireB3-ruter er kontrollert i originalkamp; be1/057 har eksakt kilde og frontendfixture uten observert kampforekomst. To masker kopieres byteidentisk. Ingen nye fotomastere eller aktivering.'
    target = ART / 'activation-set-balok-023-five-aliases-v7.json'
    freeze(target, delivery)
    subprocess.run([sys.executable, str(ROOT / 'tools/hd_figurer_aktiver.py'), str(target)], check=True)
    print(json.dumps(dict(path=str(target.relative_to(ROOT)), sha256=sha(target), new_routes=5, new_pngs=7, existing_context=5)))


if __name__ == '__main__':
    main()
