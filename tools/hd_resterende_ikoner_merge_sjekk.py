#!/usr/bin/env python3
"""Bind nye CEL- og vernproever til kode og assets etter fletting av main."""
import json
from pathlib import Path

from hd_resterende_ikoner_dekning_sjekk import ROOT, ART, sha, read, proof, contract_sha

OUT = ART/'research/runtime/post-main-merge'


def main():
    current = {f: sha((ROOT/f).read_bytes()) for f in ('web/src/render.js', 'web/src/scenes.js')}
    assert current == read(OUT/'runtime-contract.json'), 'Produksjonskode endret etter frys'
    candidate_bytes = (ART/'candidate-icons.json').read_bytes()
    candidate_sha = sha(candidate_bytes)
    candidate = json.loads(candidate_bytes)
    final = {m['key']: m for m in candidate['entries']}
    active = {m['key']: m for m in read(ROOT/'web/hd/icons.json')['entries']}
    assert final == active, 'Aktiv pakke er ikke kandidaten som ble testet'
    rows = {r['key']: r for r in read(ART/'packing-report.json')['assets']}
    batch = read(OUT/'cel/cel-fixtures-batches-test.json')
    assert batch['status'] == 'passed' and batch['candidate_icons_sha256'] == candidate_sha
    assert batch['production_code_sha256'] == current
    report = {'status': 'running', 'scope': 'Ny full CEL-fixturebatch etter PR27/main-fletting, uten gjenbruk av de tidligere 833 kontrollene. Ikke naturlig kjoep eller bruk av alle objekter.',
              'production_code_sha256': current, 'candidate_icons_sha256': candidate_sha,
              'active_icons_sha256': sha((ROOT/'web/hd/icons.json').read_bytes()),
              'contracts': len(final), 'assets': [], 'checks': 0, 'supplemental_tests': []}
    done = set()
    for b in batch['batches']:
        assert not b['reused'], 'Denne nye rendererbasen skal ikke gjenbruke gamle CEL-proever'
        file = ROOT/b['report']
        result = read(file)
        assert result['status'] == 'passed' and not result['errors']
        assert result['production_code_sha256'] == current
        assert result['candidate_icons_sha256'] == candidate_sha
        report['checks'] += len(result['checks'])
        for tested in result['assets']:
            key = tested['key']
            assert key not in done
            done.add(key)
            row = rows[key]
            for field in ('raw', 'source', 'record', 'prompt'):
                assert sha((ART/row[field]).read_bytes()) == row[field+'_sha256'], key+' '+field
            assert sha((ART/'packed'/f'{key}.png').read_bytes()) == row['packed_sha256']
            assert sha((ROOT/'web/hd'/f'{key}.png').read_bytes()) == row['packed_sha256']
            for v in row.get('variants', []):
                assert sha((ART/v['raw']).read_bytes()) == v['raw_sha256']
                assert sha((ART/'packed'/f"{v['key']}.png").read_bytes()) == v['packed_sha256']
                assert sha((ROOT/'web/hd'/f"{v['key']}.png").read_bytes()) == v['packed_sha256']
            assert len(tested['samples']) == 2 and {s['mirror'] for s in tested['samples']} == {False, True}
            for sample in tested['samples']:
                name = key.replace('/', '-')+('-mirrored' if sample['mirror'] else '')
                for mode in ('original', 'hd'):
                    assert sha((file.parent/f'{name}-{mode}.png').read_bytes()) == sample[mode+'_sha256']
                assert sample['original_sha256'] != sample['hd_sha256']
            report['assets'].append({**proof(row), 'source_contract_sha256': contract_sha(final[key]),
                                     'test_report': str(file.relative_to(ROOT)), 'sample_count': len(tested['samples']),
                                     'generated_palette_samples': len(tested.get('palette_samples', []))})
    expected = {key for key in rows if key.startswith(('ki.cel/', 'mi.c/'))}
    assert done == expected and len(done) == 62 and len(final) == 102
    for name, file in [('ownership', OUT/'ownership/ownership-test.json'),
                       ('pulse', OUT/'pulse/pulse-test.json'),
                       ('variant-import', OUT/'variant-import/variant-import-test.json'),
                       ('counter', OUT/'counter/counter-test.json')]:
        result = read(file)
        assert result['status'] == 'passed' and not result.get('errors')
        code = result.get('production_code_sha256') or {
            'web/src/render.js': result['source_after_render_sha256'],
            'web/src/scenes.js': result['scene_code_sha256']}
        assert code == current, name+' kodehash'
        if result.get('candidate_icons_sha256'):
            assert result['candidate_icons_sha256'] == candidate_sha
        report['supplemental_tests'].append({'name': name, 'report': str(file.relative_to(ROOT)),
                                            'checks': len(result['checks'])})
    report['tested_CEL_routes'] = len(done)
    report['supplemental_checks'] = sum(t['checks'] for t in report['supplemental_tests'])
    report['status'] = 'passed'
    target = OUT/'merged-runtime-coverage-test.json'
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({'status': report['status'], 'contracts': len(final), 'tested_CEL_routes': len(done),
                      'CEL_checks': report['checks'], 'supplemental_checks': report['supplemental_checks'],
                      'report': str(target.relative_to(ROOT))}))


if __name__ == '__main__':
    main()
