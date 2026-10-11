#!/usr/bin/env python3
"""Frys en gjennomgaatt figurgruppe uten aa aktivere eller endre eldre bevis."""
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
    args = parser.parse_args()
    index = load(args.index)
    report = load(args.runtime)
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
        entry['qa'] = dict(frame=sample['frame'], mirrored=all(d['speilet'] for d in sample['visible'] if d['fil'].lower() == r['bank'].lower()), source_midpoints_missing=0, source_transparent_midpoints_filled=0, actual_original_hd_return='exact', emulated_state='unchanged', visual_original_and_runtime='reviewed_same_source_rectangle', footshadow='original_flat_retained_not_redrawn' if art.get('original_flat_shadow_packing') else None)
        entries.append(entry)
    activation = dict(schema=1, visual_status='reviewed_original_and_runtime', source_zip_sha256=report['source_zip_sha256'], production_code_sha256=codes, wasm_core_sha256=sha((ROOT / 'web/build/moonstone-core.js').read_bytes()), proofs=[dict(path=str(args.runtime.resolve().relative_to(ROOT)), sha256=sha(args.runtime.read_bytes()), html_path=str(html.resolve().relative_to(ROOT)), html_sha256=report['html_sha256'])], scope='Separate individuelt genererte ruter, sammenliknet med original og sett samlet i kontrollert originalkamp. Eksakte Original/HD-returer. Original flat skygge beholdes uten nytegningspaastand. Ingen full animasjonsdekning eller naturlig kartreise.', entries=entries)
    target = ART / ('activation-set-' + args.name + '.json')
    print(json.dumps(dict(path=str(target.relative_to(ROOT)), sha256=freeze(target, activation), routes=len(entries))))
    subprocess.run([sys.executable, str(ROOT / 'tools/hd_figurer_aktiver.py'), str(target)], check=True)


if __name__ == '__main__':
    main()
