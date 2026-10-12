#!/usr/bin/env python3
"""Frys Balok3 sine26 rotgodkjente individuelle mastere paa ny frontend med kildebevist maske."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ART = Path(__file__).resolve().parent
ROOT = ART.parents[2]
sha = lambda data: hashlib.sha256(data).hexdigest()
load = lambda path: json.loads(path.read_text())


def freeze(path, value):
    data = (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()
    if path.exists():
        assert path.read_bytes() == data, str(path)
    else:
        path.write_bytes(data)
    return sha(data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--index', type=Path, required=True)
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--name', required=True)
    parser.add_argument('--existing-context', nargs='*', default=[])
    parser.add_argument('--palette-proof', type=Path, required=True)
    parser.add_argument('--visual-review', type=Path, required=True)
    args = parser.parse_args()
    review = load(args.visual_review)
    assert review['status'] == 'passed' and review['reviewer'] == 'root'
    for item in review['files']:
        assert sha((ROOT / item['path']).read_bytes()) == item['sha256']
    index = load(args.index)
    report = load(args.runtime)
    palette_report = load(args.palette_proof)
    assert palette_report['status'] == 'passed' and not palette_report['errors']
    assert palette_report['index_sha256'] == sha(args.index.read_bytes())
    assert palette_report['html_sha256'] == report['html_sha256']
    assert {r['key'] for r in palette_report['routes']} == {e['key'] for e in index['entries'] if not e.get('runtime_context_only')}
    for r in palette_report['routes']:
        assert len(r['samples']) == 10
        for mirror in (False, True):
            samples = [s for s in r['samples'] if s['mirror'] == mirror]
            assert len(samples) == 5 and len({s['fixed_sha256'] for s in samples}) == 1
            assert all(s['visible']['hd'] for s in samples)
            if any(s['visible']['maske'] for s in samples):
                assert len({s['live_sha256'] for s in samples}) == 5
            else:
                assert all(not s['live_count'] for s in samples)
    assert report['status'] == 'passed' and not report['errors']
    assert report['index_sha256'] == sha(args.index.read_bytes())
    assert sha((args.runtime.parent / 'input-index.json').read_bytes()) == report['index_sha256']
    html = args.runtime.parent / 'loaded.html'
    assert sha(html.read_bytes()) == report['html_sha256']
    game = ROOT / 'Moonstonecd32-AMIGA.zip'
    assert sha(game.read_bytes()) == report['source_zip_sha256']
    codes = {p: sha((ROOT / p).read_bytes()) for p in ['web/src/core.js', 'web/src/render.js', 'web/src/scenes.js']}
    for path in [*codes, 'web/build/moonstone-core.js']:
        assert (ROOT / path).read_bytes().replace(b'</script', b'<\\/script') in html.read_bytes(), path
    queue = load(ART.parent / 'queue.json')
    entries = []
    for item in index['entries']:
        if item['key'] in args.existing_context:
            active = ROOT / 'web/hd' / item['key']
            assert sha(active.read_bytes()) == item['candidate_sha256'], 'Annen aktiv kontekst: ' + item['key']
            continue
        if item.get('runtime_context_only'):
            continue
        r = next(r for r in queue['entries'] if r['key'] == item['key'])
        candidate = ROOT / item['candidate']
        record = ROOT / item['art_record']
        art = load(record)
        assert sha(record.read_bytes()) == item['art_record_sha256']
        assert sha(candidate.read_bytes()) == item['candidate_sha256'] == art['candidate_sha256']
        assert art['geometry_gate_passed'] and not art['missing_opaque_source_midpoints'] and not art['false_filled_transparent_source_midpoints']
        assert art['source_indices_sha256'] == r['indices_sha256']
        sample = report['runtime']['samples'][item['key'].lower().removesuffix('.png')]
        assert sample['state'] == sample['state_after']
        assert any(a['key'] == item['key'] and a['candidate_sha256'] == item['candidate_sha256'] for a in report['assets'])
        for path, digest in [(art['raw_file'], art['raw_sha256']), (art['prompt'], art['prompt_sha256'])]:
            assert sha((ROOT / path).read_bytes()) == digest
        subprocess.run([sys.executable, str(ART.parent / 'prepare.py'), 'pack', '--key', item['key'], '--candidate', str(candidate), '--art-record', str(record)], check=True)
        entry = dict(key=item['key'], bank=r['bank'], frame=r['frame'], source_bank_sha256=r['source_bank']['sha256'], indices_sha256=r['indices_sha256'], png=item['candidate'], png_sha256=item['candidate_sha256'], raw=art['raw_file'], raw_sha256=art['raw_sha256'], prompt=art['prompt'], prompt_sha256=art['prompt_sha256'], generation_tool='builtin_image_gen', runtime_proof=str(args.runtime.resolve().relative_to(ROOT)), runtime_asset_sha256=item['candidate_sha256'], art_record=item['art_record'], art_record_sha256=item['art_record_sha256'])
        materials = [p for p in [art.get('eye_source_binding', {}).get('generated_eyeless_skin_patch'), art.get('shoulder_join_material'), art.get('wrist_join_material'), art.get('source_join_material'), art.get('source_blood_material')] if p]
        for patch in materials:
            for name in ('raw', 'prompt'):
                assert sha((ROOT / patch[name]).read_bytes()) == patch[name + '_sha256']
        if materials:
            # Den generiske porten kontrollerer siste materiale; alle inngaaende
            # foto- og promptfiler er dessuten bundet og kontrollert her.
            entry['additional_generated_material'] = materials[-1]
            entry['additional_generated_materials'] = materials
        if item.get('mask'):
            mask = ROOT / item['mask']
            assert sha(mask.read_bytes()) == item['mask_sha256']
            assert any(a['key'] == item['key'].replace('.png', '.mask.png') and a['candidate_sha256'] == item['mask_sha256'] for a in report['assets'])
            assert art['live_knight_packing']['mask_sha256'] == item['mask_sha256']
            entry['mask'] = item['mask']
            entry['mask_sha256'] = item['mask_sha256']
        entry['qa'] = dict(frame=sample['frame'], mirrored=all(d['speilet'] for d in sample['visible'] if d['hd'] and d['fil'].lower() == r['bank'].lower() and d['bilde'] == r['frame']), source_midpoints_missing=0, source_transparent_midpoints_filled=0, actual_original_hd_return='exact', emulated_state='unchanged', visual_original_and_runtime='reviewed_same_source_rectangle', footshadow='original_flat_retained_not_redrawn' if art.get('original_flat_shadow_packing') else None)
        entries.append(entry)
    activation = dict(schema=1, visual_status='reviewed_original_and_runtime', source_zip_sha256=report['source_zip_sha256'], production_code_sha256=codes, wasm_core_sha256=sha((ROOT / 'web/build/moonstone-core.js').read_bytes()), proofs=[dict(path=str(args.runtime.resolve().relative_to(ROOT)), sha256=sha(args.runtime.read_bytes()), html_path=str(html.resolve().relative_to(ROOT)), html_sha256=report['html_sha256'])], scope='Separate individuelt genererte ruter, sammenliknet med original og sett samlet i kontrollert originalkamp. Eksakte Original/HD-returer. Original flat skygge beholdes uten nytegningspaastand. Ingen full animasjonsdekning eller naturlig kartreise.', entries=entries)
    palette_html = args.palette_proof.parent / 'loaded.html'
    assert sha(palette_html.read_bytes()) == palette_report['html_sha256']
    activation['proofs'].append(dict(path=str(args.palette_proof.resolve().relative_to(ROOT)), sha256=sha(args.palette_proof.read_bytes()), html_path=str(palette_html.resolve().relative_to(ROOT)), html_sha256=palette_report['html_sha256']))
    assert review['html_sha256'] == report['html_sha256']
    assert set(review['routes']) == {e['key'] for e in entries}
    activation['visual_reviews'] = [dict(path=str(args.visual_review), sha256=sha(args.visual_review.read_bytes()))]
    activation['scope'] = '26 separate kildebundne mastere: ni fotografiske figur-/materialfragmenter og17 egne fotografiske blodoverflater i originalens eksakte effektkontur. Alle observert i kontrollert originalCPU-kamp, femfarge/speil/negative fixturer. Original/HD-retur og emulert tilstand uendret; ingen naturlig kartreise eller full animasjonsdekning. Fire aktive B3-aliaser og tre aktive B1-kroppsdeler er uendret kontekst.'
    target = ART / ('activation-set-' + args.name + '.json')
    print(json.dumps(dict(path=str(target.relative_to(ROOT)), sha256=freeze(target, activation), routes=len(entries))))
    subprocess.run([sys.executable, str(ROOT / 'tools/hd_figurer_aktiver.py'), str(target)], check=True)


if __name__ == '__main__':
    main()
